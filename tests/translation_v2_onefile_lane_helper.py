"""Shared helper for the translation_v2 one-file test lane."""

from __future__ import annotations

import os
import sys
from pathlib import Path


CANONICAL_ONEFILE_LANE_COMMAND = (
    "uv run --extra dev pytest tests/test_translation_v2_onefile_lane.py -q"
)
DEFAULT_ONEFILE_RUNTIME_CEILING_SECONDS = 45.0

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "translation_v2"
MOCK_FIXTURE_PATH = FIXTURES_DIR / "representative_post_expected.json"
CONTRACT_REGRESSION_FIXTURE_PATH = FIXTURES_DIR / "onefile_contract_regression_case.json"


def ensure_source_imports() -> None:
    """Make source modules importable for the standalone test lane."""
    source_dir = os.path.join(os.path.dirname(__file__), "..", "_source")
    if source_dir not in sys.path:
        sys.path.insert(0, source_dir)



def make_source_post(*, slug: str = "deterministic-mock-post", lang: str = "en-us") -> dict:
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


class FakeAcceptedContent:
    def read_post(self, post, *, target_locale):
        return {**post, "lang": target_locale}


def configure_onefile_build(tmp_path: Path, monkeypatch, build_module, source_post: dict) -> None:
    """Configure build module state to process one markdown source file."""
    posts_dir = tmp_path / "_source" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)
    (posts_dir / f"{source_post['slug']}.md").write_text(
        "---\ntitle: x\n---\nbody", encoding="utf-8"
    )

    en_dir = tmp_path / "en"
    pt_dir = tmp_path / "pt"
    (en_dir / "blog").mkdir(parents=True, exist_ok=True)
    (pt_dir / "blog").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(build_module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(build_module, "validate_staged", lambda *a, **k: None)
    monkeypatch.setattr(build_module, "POSTS_DIR", posts_dir)
    monkeypatch.setattr(build_module, "LANG_DIRS", {"en": en_dir, "pt": pt_dir})
    monkeypatch.setattr(build_module, "STAGING_DIR", tmp_path / "_staging")
    monkeypatch.setattr(
        build_module,
        "_out",
        lambda rel_path, staging_dir: rel_path
        if staging_dir is None
        else staging_dir / rel_path.relative_to(tmp_path),
    )
    monkeypatch.setattr(build_module, "load_cv_data", lambda: {"name": "x"})
    monkeypatch.setattr(
        build_module,
        "AcceptedContent",
        lambda **_: FakeAcceptedContent(),
    )
    monkeypatch.setattr(
        build_module,
        "parse_markdown_post",
        lambda *_a, **_k: source_post.copy(),
    )
    monkeypatch.setattr(build_module, "generate_post_html", lambda *a, **k: "<html>post</html>")
    monkeypatch.setattr(
        build_module,
        "generate_index_html",
        lambda *a, **k: "<html>index</html>",
    )
    monkeypatch.setattr(
        build_module,
        "generate_about_html",
        lambda *a, **k: "<html>about</html>",
    )
    monkeypatch.setattr(build_module, "generate_cv_html", lambda *a, **k: "<html>cv</html>")
    monkeypatch.setattr(build_module, "generate_root_index", lambda: "<html>root</html>")
    monkeypatch.setattr(build_module, "generate_sitemap", lambda *a, **k: "<xml />")
