"""Presentation marker preservation tests for translation_v2 integration."""

from __future__ import annotations

import os
import sys
from pathlib import Path


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)


import build  # noqa: E402
from content_loader import parse_markdown_post  # noqa: E402


SOURCE = """<!-- presentation:slide id="intro" layout="lead" density="normal" -->
# Title

[Docs](https://example.com/docs)
![Image](/img/x.png)
<!-- /presentation:slide -->
"""


def test_parse_markdown_post_preserves_content_type(tmp_path):
    post_path = tmp_path / "deck.md"
    post_path.write_text(
        "---\ntitle: Deck\ndate: 2026-04-29\ncontent_type: presentation\n---\n"
        + SOURCE,
        encoding="utf-8",
    )

    post = parse_markdown_post(post_path)

    assert post["content_type"] == "presentation"


def test_prompt_pack_mentions_exact_presentation_marker_preservation():
    translate_prompt = Path(
        "_source/translation_v2/prompts/v2/presentation_translate.md"
    ).read_text(encoding="utf-8")
    revise_prompt = Path("_source/translation_v2/prompts/v2/presentation_revise.md").read_text(
        encoding="utf-8"
    )

    for prompt in (translate_prompt, revise_prompt):
        assert "<!-- presentation:slide ... -->" in prompt
        assert "<!-- /presentation:slide -->" in prompt
        assert "ids, layout, density" in prompt
        assert "link" in prompt
        assert "image" in prompt


def test_presentation_validator_accepts_exact_markers_and_destinations():
    translated = SOURCE.replace("# Title", "# Titulo")

    is_valid, issues = build.validate_presentation_translation(SOURCE, translated)

    assert is_valid is True
    assert issues == []


def test_presentation_validator_rejects_marker_drift():
    translated = SOURCE.replace('id="intro"', 'id="intro-pt"')

    is_valid, issues = build.validate_presentation_translation(SOURCE, translated)

    assert is_valid is False
    assert any("Slide ids/order changed" in issue for issue in issues)


class _BadMarkerOrchestrator:
    run_id = "test-run"
    prompt_version = "v2"

    def read_post(
        self,
        post,
        *,
        target_locale="pt-br",
        force_revision_reason=None,  # noqa: ARG002
    ):
        translated = post.copy()
        translated["lang"] = target_locale
        translated["raw_content"] = SOURCE.replace('layout="lead"', 'layout="content"')
        translated["content"] = "<p>bad</p>"
        return translated




def test_build_validates_translated_presentation_markers_before_render(
    monkeypatch,
    tmp_path,
):
    posts_dir = tmp_path / "_source" / "posts"
    posts_dir.mkdir(parents=True)
    (posts_dir / "deck.md").write_text("---\ntitle: Deck\n---\n" + SOURCE, encoding="utf-8")
    en_dir = tmp_path / "en"
    pt_dir = tmp_path / "pt"
    (en_dir / "blog").mkdir(parents=True)
    (pt_dir / "blog").mkdir(parents=True)
    source_post = {
        "title": "Deck",
        "date": "2026-04-29",
        "published_date": "2026-04-29",
        "updated_fm_date": "",
        "year": "2026",
        "month": "April",
        "excerpt": "Deck",
        "slug": "deck",
        "content_type": "presentation",
        "order": 0,
        "tags": [],
        "en_tags": [],
        "lang": "en-us",
        "content": "<p>Deck</p>",
        "raw_content": SOURCE,
        "created_date": "2026-04-29T00:00:00",
        "updated_date": "2026-04-29T00:00:00",
        "reading_time": 1,
    }
    rendered: list[str] = []

    monkeypatch.setattr(build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(build, "POSTS_DIR", posts_dir)
    monkeypatch.setattr(build, "LANG_DIRS", {"en": en_dir, "pt": pt_dir})
    monkeypatch.setattr(build, "STAGING_DIR", tmp_path / "_staging")
    monkeypatch.setattr(
        build,
        "_out",
        lambda rel_path, staging_dir: rel_path
        if staging_dir is None
        else staging_dir / rel_path.relative_to(tmp_path),
    )
    monkeypatch.setattr(build, "load_cv_data", lambda: {"name": "x"})
    monkeypatch.setattr(build, "parse_markdown_post", lambda *_a, **_k: source_post.copy())
    monkeypatch.setattr(build, "generate_about_html", lambda *a, **k: "<html>about</html>")
    monkeypatch.setattr(build, "generate_cv_html", lambda *a, **k: "<html>cv</html>")
    monkeypatch.setattr(build, "generate_index_html", lambda *a, **k: "<html>index</html>")
    monkeypatch.setattr(build, "generate_root_index", lambda: "<html>root</html>")
    monkeypatch.setattr(build, "generate_sitemap", lambda *a, **k: "<xml />")
    monkeypatch.setattr(build, "validate_translation", lambda *a, **k: (True, []))
    monkeypatch.setattr(build, "AcceptedContent", lambda **_: _BadMarkerOrchestrator())
    monkeypatch.setattr(
        build,
        "generate_presentation_html",
        lambda post, post_number, lang="en": rendered.append(lang) or f"<html>{lang}</html>",
    )


    ok = build.build(strict=False, skip_about_cv_translation=True)

    assert ok is False
    assert rendered == []
    assert not (tmp_path / "pt" / "blog" / "deck.html").exists()
