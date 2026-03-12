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
sys.modules["translator"] = _translator_stub


import build


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


class _FakeTranslator:
    def translate_about(self, about_content, force=False):  # noqa: ARG002
        return {
            "title": "About",
            "p1": "p1",
            "p2": "p2",
            "p3": "p3",
            "p4": "p4",
        }

    def translate_cv(self, cv_content, force=False):  # noqa: ARG002
        return {
            "name": "Name",
            "tagline": "Tagline",
            "location": "Location",
            "contact": {},
            "skills": [],
            "languages_spoken": [],
            "summary": "Summary",
            "experience": [],
            "education": [],
        }

    def translate_if_needed(self, post, target_locale="pt-br"):
        translated = post.copy()
        translated["lang"] = target_locale
        translated["raw_content"] = "translated"
        translated["content"] = "<p>translated</p>"
        return translated


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
    monkeypatch.setattr(build, "MultiAgentTranslator", lambda **_: _FakeTranslator())

    def _parse_markdown_post(filepath, _metadata_store=None):  # noqa: ARG001
        return source_post.copy()

    monkeypatch.setattr(build, "parse_markdown_post", _parse_markdown_post)
    monkeypatch.setattr(
        build, "generate_post_html", lambda *a, **k: "<html>post</html>"
    )
    monkeypatch.setattr(
        build, "generate_index_html", lambda *a, **k: "<html>index</html>"
    )
    monkeypatch.setattr(
        build, "generate_about_html", lambda *a, **k: "<html>about</html>"
    )
    monkeypatch.setattr(build, "generate_cv_html", lambda *a, **k: "<html>cv</html>")
    monkeypatch.setattr(build, "generate_root_index", lambda: "<html>root</html>")
    monkeypatch.setattr(build, "generate_sitemap", lambda *a, **k: "<xml />")


def test_pt_br_source_routes_translated_output_to_en(monkeypatch, tmp_path):
    source_post = _mk_post("pt-source", "pt-br")
    _configure_build_for_test(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False)
    assert ok is True
    assert (tmp_path / "en" / "blog" / "pt-source.html").exists()


def test_en_us_source_routes_translated_output_to_pt(monkeypatch, tmp_path):
    source_post = _mk_post("en-source", "en-us")
    _configure_build_for_test(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False)
    assert ok is True
    assert (tmp_path / "pt" / "blog" / "en-source.html").exists()
