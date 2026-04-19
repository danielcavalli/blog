"""Shared helper for the translation_v2 one-file test lane."""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path


CANONICAL_ONEFILE_LANE_COMMAND = (
    "uv run --extra dev pytest tests/test_translation_v2_onefile_lane.py -q"
)
DEFAULT_ONEFILE_RUNTIME_CEILING_SECONDS = 45.0

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "translation_v2"
MOCK_FIXTURE_PATH = FIXTURES_DIR / "representative_post_expected.json"
CONTRACT_REGRESSION_FIXTURE_PATH = FIXTURES_DIR / "onefile_contract_regression_case.json"


def ensure_runtime_stubs() -> None:
    """Install import stubs used by build during deterministic tests."""
    source_dir = os.path.join(os.path.dirname(__file__), "..", "_source")
    if source_dir not in sys.path:
        sys.path.insert(0, source_dir)

    google_stub = types.ModuleType("google")
    genai_stub = types.ModuleType("google.genai")
    genai_stub.types = types.SimpleNamespace(HttpOptions=lambda **_: None)  # type: ignore[attr-defined]
    sys.modules.setdefault("google", google_stub)
    sys.modules.setdefault("google.genai", genai_stub)
    sys.modules.setdefault("dotenv", types.ModuleType("dotenv"))
    sys.modules["dotenv"].load_dotenv = lambda *a, **kw: None  # type: ignore[attr-defined]


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


class FakePostOrchestrator:
    def __init__(self, *, run_id: str, artifact_run_dir: Path):
        self.run_id = run_id
        self.artifact_run_dir = artifact_run_dir

    def translate_if_needed(self, post, target_locale="pt-br", force_revision_reason=None):  # noqa: ARG002
        translated = post.copy()
        translated["lang"] = target_locale
        return translated

    def translate_if_needed_unpersisted(
        self,
        post,
        target_locale="pt-br",
        force_revision_reason=None,
    ):
        return self.translate_if_needed(
            post,
            target_locale=target_locale,
            force_revision_reason=force_revision_reason,
        )

    def persist_artifact_translation(self, **kwargs):  # noqa: ANN003
        return None

    def consume_artifact_persist_context(self, *, slug, artifact_type):  # noqa: ARG002
        return {"outcome": "cache_miss", "revised_from_cache_source": None}


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
    monkeypatch.setattr(
        build_module,
        "TRANSLATION_CACHE",
        tmp_path / "_cache" / "translation-cache.json",
    )

    monkeypatch.setattr(build_module, "load_post_metadata", lambda: {})
    monkeypatch.setattr(build_module, "save_post_metadata", lambda *_: None)
    monkeypatch.setattr(build_module, "load_cv_data", lambda: {"name": "x"})
    monkeypatch.setattr(
        build_module,
        "TranslationV2PostOrchestrator",
        lambda **_: FakePostOrchestrator(
            run_id="test-run",
            artifact_run_dir=tmp_path / "_cache" / "translation-runs" / "test-run",
        ),
    )
    (tmp_path / "_cache" / "translation-runs" / "test-run").mkdir(parents=True, exist_ok=True)
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

    validate_mod = types.ModuleType("validate")
    validate_mod.run_validation = lambda *_a, **_k: True  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "validate", validate_mod)
