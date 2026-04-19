"""Integration-style tests for build translation routing by source locale."""

import os
import sys
import types
from pathlib import Path


# Make _source importable without installing package.
_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)


# Stub optional runtime dependencies before importing build.
_google_stub = types.ModuleType("google")
_genai_stub = types.ModuleType("google.genai")
sys.modules.setdefault("google", _google_stub)
sys.modules.setdefault("google.genai", _genai_stub)
sys.modules.setdefault("dotenv", types.ModuleType("dotenv"))
sys.modules["dotenv"].load_dotenv = lambda *a, **kw: None  # type: ignore[attr-defined]


_translator_stub = types.ModuleType("translator")
_translator_stub.MultiAgentTranslator = object  # type: ignore[attr-defined]
_translator_stub.validate_translation = lambda *a, **kw: (True, [])  # type: ignore[attr-defined]
_translator_stub.sanitize_translation_html = lambda html: html  # type: ignore[attr-defined]
_translator_stub.sanitize_translation_text = lambda text: text  # type: ignore[attr-defined]
sys.modules["translator"] = _translator_stub


import build  # noqa: E402  # imported after dependency stubs by design


def _mk_post(slug: str, lang: str) -> dict:
    return {
        "title": slug,
        "date": "2026-03-12",
        "published_date": "2026-03-12",
        "year": "2026",
        "month": "March",
        "excerpt": "excerpt",
        "slug": slug,
        "order": 0,
        "tags": ["tag"],
        "lang": lang,
        "content": "<p>content</p>",
        "raw_content": "content",
        "created_date": "2026-03-12T00:00:00",
        "updated_date": "2026-03-12T00:00:00",
        "reading_time": "1 min read",
    }


class _FakePostOrchestrator:
    def __init__(self):
        self.run_id = "test-run"
        self.prompt_version = "v1"
        self.correlation_id = "test-correlation"

    def translate_if_needed(self, post, target_locale="pt-br"):
        translated = post.copy()
        translated["lang"] = target_locale
        translated["raw_content"] = "translated"
        translated["content"] = "<p>translated</p>"
        return translated

    def _run_pipeline(self, request):
        return {
            "title": f"pt::{request.metadata.get('slug', '')}",
            "excerpt": "",
            "tags": [],
            "content": f"pt::{request.source_text}",
        }

    def translate_artifact_if_needed(
        self,
        *,
        slug,
        source_text,
        source_locale,
        target_locale,
        artifact_type,
        frontmatter=None,
        attach_path=None,
        do_not_translate_entities=None,
    ):
        if artifact_type == "about":
            return {
                "title": "pt::ABOUT",
                "excerpt": "",
                "tags": [],
                "content": "# pt::ABOUT\n\npt::p1\n\npt::p2\n\npt::p3\n\npt::p4",
            }
        if artifact_type == "cv":
            return {
                "name": "Daniel Cavalli",
                "tagline": "pt::tagline",
                "location": "Rio de Janeiro, Brazil",
                "contact": {"linkedin": "https://www.linkedin.com/in/cavallidaniel/"},
                "skills": ["MLOps"],
                "languages_spoken": ["pt::English"],
                "summary": "pt::summary",
                "experience": [],
                "education": [],
            }
        return self._run_pipeline(
            types.SimpleNamespace(metadata={"slug": slug}, source_text=source_text)
        )


def _configure_build_for_test(tmp_path: Path, monkeypatch, source_post: dict):
    posts_dir = tmp_path / "_source" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    (posts_dir / f"{source_post['slug']}.md").write_text(
        "---\ntitle: x\n---\nbody", encoding="utf-8"
    )

    en_dir = tmp_path / "en"
    pt_dir = tmp_path / "pt"
    (en_dir / "blog").mkdir(parents=True, exist_ok=True)
    (pt_dir / "blog").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(build, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(build, "POSTS_DIR", posts_dir)
    monkeypatch.setattr(build, "LANG_DIRS", {"en": en_dir, "pt": pt_dir})
    monkeypatch.setattr(build, "STAGING_DIR", tmp_path / "_staging")

    monkeypatch.setattr(build, "load_post_metadata", lambda: {})
    monkeypatch.setattr(build, "save_post_metadata", lambda *_: None)
    monkeypatch.setattr(build, "load_cv_data", lambda: {"name": "x"})
    monkeypatch.setattr(build, "TranslationV2PostOrchestrator", lambda **_: _FakePostOrchestrator())

    def _parse_markdown_post(filepath, _metadata_store=None):  # noqa: ARG001
        return source_post.copy()

    monkeypatch.setattr(build, "parse_markdown_post", _parse_markdown_post)
    monkeypatch.setattr(build, "generate_post_html", lambda *a, **k: "<html>post</html>")
    monkeypatch.setattr(build, "generate_index_html", lambda *a, **k: "<html>index</html>")
    monkeypatch.setattr(build, "generate_about_html", lambda *a, **k: "<html>about</html>")
    monkeypatch.setattr(build, "generate_cv_html", lambda *a, **k: "<html>cv</html>")
    monkeypatch.setattr(build, "generate_root_index", lambda: "<html>root</html>")
    monkeypatch.setattr(build, "generate_sitemap", lambda *a, **k: "<xml />")
    monkeypatch.setitem(
        build.LANGUAGES,
        "en",
        {
            **build.LANGUAGES["en"],
            "about": {
                "title": "ABOUT",
                "p1": "English paragraph one.",
                "p2": "English paragraph two.",
                "p3": "English paragraph three.",
                "p4": "English paragraph four.",
            },
        },
    )


def test_pt_br_source_routes_translated_output_to_en(monkeypatch, tmp_path):
    source_post = _mk_post("pt-source", "pt-br")
    _configure_build_for_test(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)
    assert ok is True
    assert (tmp_path / "en" / "blog" / "pt-source.html").exists()


def test_build_validates_pt_br_to_en_us_with_locale_direction(monkeypatch, tmp_path):
    source_post = _mk_post("pt-source", "pt-br")
    _configure_build_for_test(tmp_path, monkeypatch, source_post)

    calls = []

    def _fake_validate(source_text, translated_text, **kwargs):
        calls.append(
            {
                "source_text": source_text,
                "translated_text": translated_text,
                "source_locale": kwargs.get("source_locale"),
                "target_locale": kwargs.get("target_locale"),
            }
        )
        return (True, [])

    monkeypatch.setattr(build, "validate_translation", _fake_validate)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is True
    assert len(calls) == 1
    assert calls[0]["source_locale"] == "pt-br"
    assert calls[0]["target_locale"] == "en-us"


def test_strict_build_fails_on_pt_br_to_en_us_validation_error(monkeypatch, tmp_path):
    source_post = _mk_post("pt-source", "pt-br")
    _configure_build_for_test(tmp_path, monkeypatch, source_post)

    monkeypatch.setattr(
        build,
        "validate_translation",
        lambda *_a, **_k: (False, ["ERROR: paragraph 1 appears untranslated"]),
    )

    ok = build.build(strict=True, use_staging=False, skip_about_cv_translation=True)

    assert ok is False


def test_en_us_source_routes_translated_output_to_pt(monkeypatch, tmp_path):
    source_post = _mk_post("en-source", "en-us")
    _configure_build_for_test(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)
    assert ok is True
    assert (tmp_path / "pt" / "blog" / "en-source.html").exists()


def test_one_file_mode_builds_only_selected_slug_and_skips_about_cv_translation(
    monkeypatch, tmp_path
):
    source_en = _mk_post("focus-post", "en-us")
    source_pt = _mk_post("ignored-post", "pt-br")

    posts_dir = tmp_path / "_source" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    (posts_dir / "focus-post.md").write_text("---\ntitle: x\n---\nbody", encoding="utf-8")
    (posts_dir / "ignored-post.md").write_text("---\ntitle: y\n---\nbody", encoding="utf-8")

    _configure_build_for_test(tmp_path, monkeypatch, source_en)
    parse_map = {
        "focus-post.md": source_en,
        "ignored-post.md": source_pt,
    }

    def _parse_markdown_post(filepath, _metadata_store=None):  # noqa: ARG001
        return parse_map[Path(filepath).name].copy()

    monkeypatch.setattr(build, "POSTS_DIR", posts_dir)
    monkeypatch.setattr(build, "parse_markdown_post", _parse_markdown_post)

    ok = build.build(
        strict=False,
        use_staging=False,
        post_selector="focus-post",
        skip_about_cv_translation=True,
    )

    assert ok is True
    assert (tmp_path / "en" / "blog" / "focus-post.html").exists()
    assert (tmp_path / "pt" / "blog" / "focus-post.html").exists()
    assert not (tmp_path / "en" / "blog" / "ignored-post.html").exists()
    assert not (tmp_path / "pt" / "blog" / "ignored-post.html").exists()


def test_one_file_mode_does_not_overwrite_sitewide_indexes_or_sitemap(
    monkeypatch, tmp_path
):
    source_post = _mk_post("focus-post", "en-us")
    _configure_build_for_test(tmp_path, monkeypatch, source_post)

    en_index = tmp_path / "en" / "index.html"
    pt_index = tmp_path / "pt" / "index.html"
    root_index = tmp_path / "index.html"
    sitemap = tmp_path / "sitemap.xml"

    en_index.write_text("existing en index", encoding="utf-8")
    pt_index.write_text("existing pt index", encoding="utf-8")
    root_index.write_text("existing root index", encoding="utf-8")
    sitemap.write_text("existing sitemap", encoding="utf-8")

    ok = build.build(
        strict=False,
        use_staging=False,
        post_selector="focus-post",
        skip_about_cv_translation=True,
    )

    assert ok is True
    assert (tmp_path / "en" / "blog" / "focus-post.html").exists()
    assert (tmp_path / "pt" / "blog" / "focus-post.html").exists()
    assert en_index.read_text(encoding="utf-8") == "existing en index"
    assert pt_index.read_text(encoding="utf-8") == "existing pt index"
    assert root_index.read_text(encoding="utf-8") == "existing root index"
    assert sitemap.read_text(encoding="utf-8") == "existing sitemap"


def test_about_cv_translation_runs_without_skip_flag(monkeypatch, tmp_path):
    source_post = _mk_post("en-source", "en-us")
    _configure_build_for_test(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=False)

    assert ok is True
