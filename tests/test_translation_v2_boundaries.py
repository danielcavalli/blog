"""Boundary and cache-policy regression tests for translation_v2."""

from __future__ import annotations

import ast
import os
import sys
from pathlib import Path


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from translation_v2.contracts import CritiqueOutput, StageResult, TranslationOutput  # noqa: E402
from translation_v2.orchestrator import TranslationV2PostOrchestrator  # noqa: E402


REPO_ROOT = Path(__file__).resolve().parent.parent


class _CacheProbeProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def translate(self, request):  # noqa: ANN001
        self.calls.append("translate")
        return StageResult(
            run_id=request.run_id,
            stage="translate",
            model="fake/model",
            payload=TranslationOutput(
                title="Titulo",
                excerpt="Resumo",
                tags=["ia"],
                content="Conteudo traduzido",
            ),
        )

    def critique(self, request, translated):  # noqa: ANN001
        self.calls.append("critique")
        return StageResult(
            run_id=request.run_id,
            stage="critique",
            model="fake/model",
            payload=CritiqueOutput(
                score=99.0,
                feedback="Looks good",
                needs_refinement=False,
                findings=[],
                dimension_scores={
                    "accuracy_completeness": 99.0,
                    "terminology_entities": 99.0,
                    "markdown_code_link_fidelity": 99.0,
                },
                critical_errors=0,
                major_core_errors=0,
                confidence=1.0,
            ),
        )

    def refine(self, request, translated, critique):  # noqa: ANN001
        raise AssertionError("refine should not run when critique accepts")


def _post() -> dict[str, str | list[str]]:
    return {
        "slug": "boundary-post",
        "lang": "en-us",
        "title": "Boundary Post",
        "excerpt": "Boundary excerpt",
        "tags": ["translation"],
        "raw_content": "Boundary markdown body",
        "content": "<p>Boundary markdown body</p>",
    }


def _make_orchestrator(
    tmp_path: Path,
    *,
    monkeypatch,
    style_brief: str,
    prompt_fingerprint: str = "prompt-fingerprint-v1",
) -> tuple[TranslationV2PostOrchestrator, _CacheProbeProvider]:
    monkeypatch.setattr("translation_v2.orchestrator.load_writing_style_brief", lambda: style_brief)
    monkeypatch.setattr(
        "translation_v2.orchestrator.compute_prompt_pack_fingerprint",
        lambda *, prompt_version, artifact_type: f"{prompt_fingerprint}:{artifact_type}:{prompt_version}",
    )
    orchestrator = TranslationV2PostOrchestrator(
        provider_name="opencode",
        strict_validation=False,
        cache_path=tmp_path / "translation-cache.json",
        run_id="boundary-run",
    )
    provider = _CacheProbeProvider()
    orchestrator.provider = provider  # type: ignore[assignment]
    orchestrator._model_id = "fake/model"
    return orchestrator, provider


def test_active_translation_path_does_not_import_legacy_translator_module():
    targets = [
        REPO_ROOT / "_source" / "build.py",
        REPO_ROOT / "_source" / "translation_v2" / "orchestrator.py",
    ]

    for target in targets:
        tree = ast.parse(target.read_text(encoding="utf-8"))
        offending_imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                offending_imports.extend(alias.name for alias in node.names if alias.name == "translator")
            if isinstance(node, ast.ImportFrom) and node.module == "translator":
                offending_imports.append(node.module)
        assert offending_imports == [], f"{target.name} still imports legacy translator: {offending_imports}"


def test_cache_invalidates_when_writing_style_changes(tmp_path, monkeypatch):
    post = _post()

    orchestrator_one, provider_one = _make_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        style_brief="style one",
    )
    translated_one = orchestrator_one.translate_if_needed(post, target_locale="pt-br")
    assert translated_one is not None
    assert provider_one.calls == ["translate", "critique"]

    orchestrator_two, provider_two = _make_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        style_brief="style two",
    )
    translated_two = orchestrator_two.translate_if_needed(post, target_locale="pt-br")
    assert translated_two is not None
    assert provider_two.calls == ["translate", "critique"]

    orchestrator_three, provider_three = _make_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        style_brief="style two",
    )
    translated_three = orchestrator_three.translate_if_needed(post, target_locale="pt-br")
    assert translated_three is not None
    assert provider_three.calls == []


def test_cache_invalidates_when_prompt_fingerprint_changes(tmp_path, monkeypatch):
    post = _post()

    orchestrator_one, provider_one = _make_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        style_brief="stable-style",
        prompt_fingerprint="prompt-a",
    )
    translated_one = orchestrator_one.translate_if_needed(post, target_locale="pt-br")
    assert translated_one is not None
    assert provider_one.calls == ["translate", "critique"]

    orchestrator_two, provider_two = _make_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        style_brief="stable-style",
        prompt_fingerprint="prompt-b",
    )
    translated_two = orchestrator_two.translate_if_needed(post, target_locale="pt-br")
    assert translated_two is not None
    assert provider_two.calls == ["translate", "critique"]


def test_artifact_cache_reuses_about_and_cv_across_fresh_orchestrators(tmp_path, monkeypatch):
    orchestrator_one, provider_one = _make_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        style_brief="stable-style",
    )

    about_source = "# ABOUT\n\nP1\n\nP2\n\nP3\n\nP4"
    cv_source = '{\n  "name": "Daniel",\n  "skills": ["python"]\n}'

    orchestrator_one.translate_artifact_if_needed(
        slug="about",
        source_text=about_source,
        source_locale="en-us",
        target_locale="pt-br",
        artifact_type="about",
        frontmatter={"title": "ABOUT", "excerpt": "", "tags": []},
        attach_path="_source/config.py",
    )
    orchestrator_one.translate_artifact_if_needed(
        slug="cv",
        source_text=cv_source,
        source_locale="en-us",
        target_locale="pt-br",
        artifact_type="cv",
        frontmatter={"title": "Daniel", "excerpt": "CV", "tags": ["cv"]},
        attach_path="cv_data.yaml",
        do_not_translate_entities=["Nubank"],
    )
    assert provider_one.calls == ["translate", "critique", "translate", "critique"]

    orchestrator_two, provider_two = _make_orchestrator(
        tmp_path,
        monkeypatch=monkeypatch,
        style_brief="stable-style",
    )
    orchestrator_two.translate_artifact_if_needed(
        slug="about",
        source_text=about_source,
        source_locale="en-us",
        target_locale="pt-br",
        artifact_type="about",
        frontmatter={"title": "ABOUT", "excerpt": "", "tags": []},
        attach_path="_source/config.py",
    )
    orchestrator_two.translate_artifact_if_needed(
        slug="cv",
        source_text=cv_source,
        source_locale="en-us",
        target_locale="pt-br",
        artifact_type="cv",
        frontmatter={"title": "Daniel", "excerpt": "CV", "tags": ["cv"]},
        attach_path="cv_data.yaml",
        do_not_translate_entities=["Nubank"],
    )
    assert provider_two.calls == []
