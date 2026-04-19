"""Integration tests for build translation_v2 orchestration wiring.

Run only this fast suite:
    uv run --extra dev pytest tests/test_build_translation_v2_integration.py -q
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)


_google_stub = types.ModuleType("google")
_genai_stub = types.ModuleType("google.genai")
_genai_stub.types = types.SimpleNamespace(HttpOptions=lambda **_: None)  # type: ignore[attr-defined]
sys.modules.setdefault("google", _google_stub)
sys.modules.setdefault("google.genai", _genai_stub)
sys.modules.setdefault("dotenv", types.ModuleType("dotenv"))
sys.modules["dotenv"].load_dotenv = lambda *a, **kw: None  # type: ignore[attr-defined]


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
    def __init__(self, *, should_fail: bool = False):
        self.should_fail = should_fail
        self.run_id = "test-run"
        self.prompt_version = "v1"
        self.correlation_id = "test-correlation"
        self.artifact_calls: list[dict] = []

    def translate_if_needed(self, post, target_locale="pt-br"):
        if self.should_fail:
            raise RuntimeError("simulated orchestrator failure")
        translated = post.copy()
        translated["lang"] = target_locale
        return translated

    def _run_pipeline(self, request):
        if self.should_fail:
            raise RuntimeError("simulated orchestrator failure")
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
        if self.should_fail:
            raise RuntimeError("simulated orchestrator failure")
        self.artifact_calls.append(
            {
                "slug": slug,
                "source_text": source_text,
                "source_locale": source_locale,
                "target_locale": target_locale,
                "artifact_type": artifact_type,
                "frontmatter": frontmatter,
                "attach_path": attach_path,
                "do_not_translate_entities": do_not_translate_entities,
            }
        )
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
                "skills": ["MLOps", "Kubeflow"],
                "languages_spoken": ["pt::English (Full Professional)"],
                "summary": "pt::summary",
                "experience": [
                    {
                        "title": "Senior Machine Learning Engineer",
                        "company": "Nubank",
                        "location": "Brazil",
                        "period": "2026 - Present",
                        "description": "pt::description",
                        "achievements": ["pt::achievement"],
                    }
                ],
                "education": [
                    {
                        "degree": "pt::Bachelor of Economics",
                        "school": "Federal University of Rio de Janeiro",
                        "period": "2017 - 2023",
                    }
                ],
            }
        return {
            "title": f"pt::{slug}",
            "excerpt": "",
            "tags": [],
            "content": f"pt::{source_text}",
        }


def _configure(
    tmp_path: Path,
    monkeypatch,
    source_post: dict,
    *,
    should_fail: bool = False,
) -> tuple[list[dict], list[_FakePostOrchestrator]]:
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
    monkeypatch.setattr(build, "TRANSLATION_CACHE", tmp_path / "_cache" / "translation-cache.json")

    monkeypatch.setattr(build, "load_post_metadata", lambda: {})
    monkeypatch.setattr(build, "save_post_metadata", lambda *_: None)
    monkeypatch.setattr(build, "load_cv_data", lambda: {"name": "x"})
    monkeypatch.setattr(build, "parse_markdown_post", lambda *_a, **_k: source_post.copy())
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
    monkeypatch.setitem(
        build.LANGUAGES,
        "pt",
        {
            **build.LANGUAGES["pt"],
            "about": {
                "title": "",
                "p1": "",
                "p2": "",
                "p3": "",
                "p4": "",
            },
        },
    )

    validate_mod = types.ModuleType("validate")
    validate_mod.run_validation = lambda *_a, **_k: True  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "validate", validate_mod)

    init_calls: list[dict] = []
    orchestrators: list[_FakePostOrchestrator] = []

    def _fake_orchestrator_factory(**kwargs):
        init_calls.append(kwargs)
        orchestrator = _FakePostOrchestrator(should_fail=should_fail)
        orchestrators.append(orchestrator)
        return orchestrator

    monkeypatch.setattr(build, "TranslationV2PostOrchestrator", _fake_orchestrator_factory)
    return init_calls, orchestrators


def test_translation_v2_routes_en_source_to_pt_output(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "en-us")
    _configure(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is True
    assert (tmp_path / "pt" / "blog" / "deterministic-post.html").exists()
    assert (tmp_path / "en" / "about.html").exists()
    assert (tmp_path / "pt" / "about.html").exists()
    assert (tmp_path / "en" / "cv.html").exists()
    assert (tmp_path / "pt" / "cv.html").exists()


def test_translation_v2_routes_pt_source_to_en_output(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "pt-br")
    _configure(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is True
    assert (tmp_path / "en" / "blog" / "deterministic-post.html").exists()


def test_build_always_initializes_full_pipeline_for_posts(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "en-us")
    init_calls, _ = _configure(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is True
    assert init_calls
    assert init_calls[0]["provider_name"] == "opencode"
    assert "enable_critique" not in init_calls[0]
    assert init_calls[0]["strict_validation"] is False


def test_translation_failure_fails_build_without_partial_bypass(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "en-us")
    _configure(tmp_path, monkeypatch, source_post, should_fail=True)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=True)

    assert ok is False


def test_default_build_translates_about_and_cv_via_translation_v2(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "en-us")
    _configure(tmp_path, monkeypatch, source_post)

    cv_data = {
        "name": "Daniel Cavalli",
        "tagline": "Senior Machine Learning Engineer @ Nubank",
        "location": "Rio de Janeiro, Brazil",
        "contact": {"linkedin": "https://www.linkedin.com/in/cavallidaniel/"},
        "skills": ["MLOps", "Kubeflow"],
        "languages_spoken": ["English (Full Professional)"],
        "summary": "I build ML systems.",
        "experience": [
            {
                "title": "Senior Machine Learning Engineer",
                "company": "Nubank",
                "location": "Brazil",
                "period": "2026 - Present",
                "description": "Leading platform evolution.",
                "achievements": ["Built distributed pipelines."],
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Economics",
                "school": "Federal University of Rio de Janeiro",
                "period": "2017 - 2023",
            }
        ],
    }
    monkeypatch.setattr(build, "load_cv_data", lambda: cv_data)

    captured: dict = {}

    def _capture_cv_html(*, lang="en", translated_cv=None):
        if lang == "pt":
            captured["translated_cv"] = translated_cv
        return "<html>cv</html>"

    monkeypatch.setattr(build, "generate_cv_html", _capture_cv_html)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=False)

    assert ok is True
    about_pt = build.LANGUAGES["pt"]["about"]
    assert set(about_pt.keys()) == {"title", "p1", "p2", "p3", "p4"}
    assert all(str(about_pt[key]).startswith("pt::") for key in ["title", "p1", "p2", "p3", "p4"])

    translated_cv = captured["translated_cv"]
    assert set(translated_cv.keys()) == {
        "name",
        "tagline",
        "location",
        "contact",
        "skills",
        "languages_spoken",
        "summary",
        "experience",
        "education",
    }
    assert translated_cv["name"] == cv_data["name"]
    assert translated_cv["location"] == cv_data["location"]
    assert translated_cv["contact"] == cv_data["contact"]
    assert translated_cv["experience"][0]["company"] == cv_data["experience"][0]["company"]
    assert translated_cv["experience"][0]["location"] == cv_data["experience"][0]["location"]
    assert translated_cv["tagline"].startswith("pt::")
    assert translated_cv["summary"].startswith("pt::")
    assert translated_cv["experience"][0]["description"].startswith("pt::")
    assert translated_cv["experience"][0]["achievements"][0].startswith("pt::")
    assert translated_cv["education"][0]["degree"].startswith("pt::")
    assert translated_cv["languages_spoken"][0].startswith("pt::")


def test_about_and_cv_translate_as_artifact_units(monkeypatch, tmp_path):
    source_post = _mk_post("deterministic-post", "en-us")
    _init_calls, orchestrators = _configure(tmp_path, monkeypatch, source_post)

    ok = build.build(strict=False, use_staging=False, skip_about_cv_translation=False)

    assert ok is True
    assert len(orchestrators) == 1
    artifact_calls = orchestrators[0].artifact_calls
    assert [call["artifact_type"] for call in artifact_calls] == ["about", "cv"]

    about_call = artifact_calls[0]
    assert about_call["slug"] == "about"
    assert about_call["target_locale"] == "pt-br"
    assert about_call["attach_path"].endswith("_source/config.py")
    assert about_call["do_not_translate_entities"] is None
    assert about_call["source_text"].startswith("# ")
    assert "\n\n" in about_call["source_text"]

    cv_call = artifact_calls[1]
    assert cv_call["slug"] == "cv"
    assert cv_call["target_locale"] == "pt-br"
    assert cv_call["attach_path"].endswith("cv_data.yaml")
    assert cv_call["do_not_translate_entities"] is not None
    assert "Nubank" in cv_call["do_not_translate_entities"]
    assert "Kubeflow" in cv_call["do_not_translate_entities"]
    assert '"name": "x"' in cv_call["source_text"]
