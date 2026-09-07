"""Exercise the real publication transaction under partial writes and crashes."""

import json
from pathlib import Path

import pytest

import build
from publication import publish_staged, recover_publication, validate_staged
from tests.translation_v2_onefile_lane_helper import configure_onefile_build, make_source_post


def write(root, name, content):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


@pytest.mark.parametrize("strict", [False, True])
def test_focused_build_preserves_other_posts_indexes_and_static_translations(
    tmp_path, monkeypatch, strict
):
    configure_onefile_build(tmp_path, monkeypatch, build, make_source_post(slug="focus"))
    monkeypatch.setattr(build, "validate_translation", lambda *a, **k: (True, []))
    names = [
        "en/index.html",
        "pt/index.html",
        "en/blog/other.html",
        "pt/blog/other.html",
        "pt/about.html",
        "pt/cv.html",
        "en/about.html",
        "en/cv.html",
        "sitemap.xml",
    ]
    for name in names:
        write(tmp_path, name, "previous accepted content")
    assert build.build(strict=strict, post_selector="focus", skip_about_cv_translation=True)
    for name in names:
        assert (tmp_path / name).read_text() == "previous accepted content"
    assert (tmp_path / "pt/blog/focus.html").exists()


def test_focused_build_keeps_the_full_collection_post_number(tmp_path, monkeypatch):
    selected = make_source_post(slug="focus")
    newer = {**make_source_post(slug="newer"), "published_date": "2099-01-01"}
    configure_onefile_build(tmp_path, monkeypatch, build, selected)
    write(tmp_path, "_source/posts/newer.md", "source")
    monkeypatch.setattr(
        build,
        "parse_markdown_post",
        lambda path, *a: dict(selected if path.stem == "focus" else newer),
    )
    monkeypatch.setattr(build, "validate_translation", lambda *a, **k: (True, []))
    monkeypatch.setattr(build, "generate_post_html", lambda post, number, **k: str(number))
    assert build.build(post_selector="focus", skip_about_cv_translation=True)
    assert (tmp_path / "en/blog/focus.html").read_text() == "2"
    assert (tmp_path / "pt/blog/focus.html").read_text() == "2"
    assert not (tmp_path / "en/blog/newer.html").exists()


@pytest.mark.parametrize("failure", [OSError, KeyboardInterrupt])
def test_publication_restores_every_file_after_partial_replacement(tmp_path, monkeypatch, failure):
    names = ["en/index.html", "pt/index.html", "index.html", "sitemap.xml"]
    stage = tmp_path / "_staging"
    for name in names:
        write(tmp_path, name, "old " + name)
        write(stage, name, "new " + name)
    write(tmp_path, "en/blog/deleted.html", "keep on failure")
    write(stage, "en/blog/new.html", "new page")
    replace = Path.replace

    def fail(self, target):
        if self == stage / "sitemap.xml":
            raise failure("injected failure")
        return replace(self, target)

    monkeypatch.setattr(Path, "replace", fail)
    with pytest.raises(failure):
        publish_staged(tmp_path, stage, full=True, language_dirs=["en", "pt"])
    for name in names:
        assert (tmp_path / name).read_text() == "old " + name
    assert (tmp_path / "en/blog/deleted.html").read_text() == "keep on failure"
    assert not (tmp_path / "en/blog/new.html").exists()


def test_next_build_recovers_a_process_crash(tmp_path):
    write(tmp_path, "en/index.html", "partial new site")
    write(tmp_path, "_cache/publication-backup/en/index.html", "previous site")
    write(tmp_path, "pt/blog/new.html", "partial new page")
    write(
        tmp_path,
        "_cache/publication.json",
        json.dumps(
            {
                "state": "prepared",
                "files": [
                    {"path": "en/index.html", "existed": True},
                    {"path": "pt/blog/new.html", "existed": False},
                ],
            }
        ),
    )
    recover_publication(tmp_path)
    assert (tmp_path / "en/index.html").read_text() == "previous site"
    assert not (tmp_path / "pt/blog/new.html").exists()
    recover_publication(tmp_path)  # Idempotent after a completed recovery.


def test_failed_first_publication_recovers_uncreated_directories(tmp_path, monkeypatch):
    stage = tmp_path / "_staging"
    write(stage, "en/blog/first.html", "new English")
    write(stage, "pt/blog/first.html", "new Portuguese")
    replace = Path.replace

    def fail(self, target):
        if self == stage / "en/blog/first.html":
            raise OSError("first publication failed")
        return replace(self, target)

    monkeypatch.setattr(Path, "replace", fail)
    with pytest.raises(OSError, match="first publication failed"):
        publish_staged(tmp_path, stage, full=True, language_dirs=["en", "pt"])
    assert not (tmp_path / "_cache/publication.json").exists()
    assert not (tmp_path / "pt").exists()


def test_staged_validation_checks_untouched_focused_pages(tmp_path):
    write(tmp_path, "en/index.html", '<!doctype html><a href="/pt/blog/missing.html">PT</a>')
    write(tmp_path / "_staging", "en/blog/new.html", "<!doctype html><p>New</p>")
    with pytest.raises(RuntimeError, match="missing.html"):
        validate_staged(tmp_path, tmp_path / "_staging", full=False, preserve_static=True)
