"""Deterministic tests for OpenCode provider critique/refine loop.

Run only this suite:
    uv run --extra dev pytest tests/test_opencode_provider_loop.py -q
"""

from __future__ import annotations

import os
import sys
from typing import Literal

import pytest


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from translation_v2.artifacts import TranslationRunArtifacts  # noqa: E402
from translation_v2.contracts import (  # noqa: E402
    CritiqueOutput,
    RefinementOutput,
    StageResult,
    TranslationOutput,
    TranslationRequest,
)
from translation_v2.errors import MissingFieldError  # noqa: E402
from translation_v2.providers.opencode import (  # noqa: E402
    OpenCodeProviderLoopError,
    OpenCodeTranslationProvider,
)
from translation_v2.rubric import RubricThresholds  # noqa: E402


class _FakeRunner:
    def __init__(self, scripted: list[StageResult | Exception]) -> None:
        self._scripted = list(scripted)
        self.calls: list[dict[str, str]] = []

    def run_stage(
        self,
        *,
        request: TranslationRequest,  # noqa: ARG002
        post_slug: str,
        stage: Literal["translate", "critique", "refine"],
        prompt_text: str,
        attach_path: str,
        artifacts: TranslationRunArtifacts,  # noqa: ARG002
    ) -> StageResult:
        self.calls.append(
            {
                "stage": stage,
                "prompt_text": prompt_text,
                "attach_path": attach_path,
                "post_slug": post_slug,
            }
        )

        if not self._scripted:
            raise AssertionError("runner called more times than scripted")

        next_result = self._scripted.pop(0)
        if isinstance(next_result, Exception):
            raise next_result
        return next_result


def _request() -> TranslationRequest:
    return TranslationRequest(
        run_id="opencode-provider-test",
        source_locale="en-us",
        target_locale="pt-br",
        source_text="## Heading\n\nOriginal body with [@smith2024]",
        prompt_version="v1",
        metadata={
            "slug": "provider-loop-post",
            "attach_path": "/tmp/provider-loop-source.md",
            "locale_direction": "en-us->pt-br",
            "style_constraints": [
                "Keep a practical engineering voice",
                "Prefer concise sentences",
            ],
            "writing_style_brief": (
                "Opinionated, layered, structurally aware, dry. "
                "Keep understated humor implicit."
            ),
            "glossary": [
                {"source": "throughput", "target": "vazao"},
                "latency => latencia",
            ],
            "do_not_translate_entities": ["OpenCode", "CUDA"],
        },
    )


def _request_without_locale_metadata(
    *, source_locale: str, target_locale: str
) -> TranslationRequest:
    return TranslationRequest(
        run_id="opencode-provider-test",
        source_locale=source_locale,
        target_locale=target_locale,
        source_text="## Heading\n\nOriginal body",
        prompt_version="v1",
        metadata={
            "slug": "provider-loop-post",
            "attach_path": "/tmp/provider-loop-source.md",
        },
    )


def _translation_result(content: str) -> StageResult:
    return StageResult(
        run_id="opencode-provider-test",
        stage="translate",
        model="openai/gpt-5.4",
        payload=TranslationOutput(
            title="Titulo",
            excerpt="Resumo",
            tags=["ia"],
            content=content,
        ),
        raw_response={"translate": True},
    )


def _critique_result(
    score: float,
    needs_refinement: bool,
    findings: list[str],
    *,
    dimension_scores: dict[str, float] | None = None,
    critical_errors: int = 0,
    major_core_errors: int = 0,
    confidence: float = 1.0,
) -> StageResult:
    if dimension_scores is None:
        dimension_scores = {
            "accuracy_completeness": score,
            "terminology_entities": score,
            "markdown_code_link_fidelity": score,
        }

    return StageResult(
        run_id="opencode-provider-test",
        stage="critique",
        model="openai/gpt-5.4",
        payload=CritiqueOutput(
            score=score,
            feedback="feedback",
            needs_refinement=needs_refinement,
            findings=findings,
            dimension_scores=dimension_scores,
            critical_errors=critical_errors,
            major_core_errors=major_core_errors,
            confidence=confidence,
        ),
        raw_response={"critique": True},
    )


def _refine_result(content: str) -> StageResult:
    return StageResult(
        run_id="opencode-provider-test",
        stage="refine",
        model="openai/gpt-5.4",
        payload=RefinementOutput(
            title="Titulo refinado",
            excerpt="Resumo refinado",
            tags=["ia", "agentes"],
            content=content,
            applied_feedback=["fixed tone"],
        ),
        raw_response={"refine": True},
    )


def test_opencode_provider_happy_path_accepts_without_refine(tmp_path):
    runner = _FakeRunner(
        [
            _translation_result("Conteudo inicial"),
            _critique_result(96.0, False, []),
        ]
    )
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
    )

    result = provider.run_translation_loop(_request())

    assert result.stop_reason == "accepted"
    assert result.loops_completed == 0
    assert [item.stage for item in result.stage_results] == ["translate", "critique"]
    assert result.final_translation.content == "Conteudo inicial"

    translate_prompt = runner.calls[0]["prompt_text"]
    assert "Translation direction: en-us->pt-br" in translate_prompt
    assert "Keep a practical engineering voice" in translate_prompt
    assert "Keep understated humor implicit." in translate_prompt
    assert "throughput => vazao" in translate_prompt
    assert "- OpenCode" in translate_prompt
    assert "literal calques" in translate_prompt or "idiomatic target-locale prose" in translate_prompt


def test_opencode_provider_invokes_refine_when_critique_requires_it(tmp_path):
    runner = _FakeRunner(
        [
            _translation_result("Conteudo inicial"),
            _critique_result(86.0, True, ["major: phrasing issue"]),
            _refine_result("Conteudo refinado"),
            _critique_result(95.0, False, []),
        ]
    )
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
        thresholds=RubricThresholds(max_loops=3, min_score_delta=3.0),
    )

    result = provider.run_translation_loop(_request())

    assert result.stop_reason == "accepted"
    assert result.loops_completed == 1
    assert [item.stage for item in result.stage_results] == [
        "translate",
        "critique",
        "refine",
        "critique",
    ]
    assert result.final_translation.content == "Conteudo refinado"


def test_opencode_provider_schema_repair_path_is_deterministic(tmp_path):
    runner = _FakeRunner(
        [
            MissingFieldError(
                message="Missing required field",
                run_id="opencode-provider-test",
                stage="translate",
                field="content",
            ),
            _translation_result("Conteudo reparado"),
        ]
    )
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
    )

    stage_result = provider.translate(_request())

    assert stage_result.payload.content == "Conteudo reparado"
    assert [call["stage"] for call in runner.calls] == ["translate", "translate"]
    assert runner.calls[1]["prompt_text"].startswith("You must repair a schema-invalid response.")

    stage_dir = TranslationRunArtifacts(
        run_id="opencode-provider-test", base_dir=tmp_path
    ).stage_dir("provider-loop-post", "translate")
    error_path = stage_dir / "error.txt"
    assert error_path.exists()
    assert "Missing required field" in error_path.read_text(encoding="utf-8")


def test_opencode_provider_auto_refines_on_low_core_dimension(tmp_path):
    runner = _FakeRunner(
        [
            _translation_result("Conteudo inicial"),
            _critique_result(
                96.0,
                False,
                ["terminology mismatch"],
                dimension_scores={
                    "accuracy_completeness": 96.0,
                    "terminology_entities": 72.0,
                    "markdown_code_link_fidelity": 98.0,
                },
            ),
            _refine_result("Conteudo corrigido"),
            _critique_result(100.0, False, []),
        ]
    )
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
    )

    result = provider.run_translation_loop(_request())

    assert result.stop_reason == "accepted"
    assert result.loops_completed == 1
    assert [item.stage for item in result.stage_results] == [
        "translate",
        "critique",
        "refine",
        "critique",
    ]


def test_opencode_provider_fails_on_critical_errors(tmp_path):
    runner = _FakeRunner(
        [
            _translation_result("Conteudo inicial"),
            _critique_result(
                97.0,
                False,
                ["critical token corruption"],
                critical_errors=1,
            ),
        ]
    )
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
    )

    with pytest.raises(OpenCodeProviderLoopError):
        provider.run_translation_loop(_request())


def test_opencode_provider_injects_default_locale_rules_for_en_to_pt(tmp_path):
    runner = _FakeRunner([_translation_result("Conteudo inicial")])
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
    )

    provider.translate(
        _request_without_locale_metadata(source_locale="en-us", target_locale="pt-br")
    )

    translate_prompt = runner.calls[0]["prompt_text"]
    assert "Prefer natural PT-BR wording over literal English word order." in translate_prompt
    assert "Do not calque expressions literally" in translate_prompt
    assert "throughput => vazao" in translate_prompt
    assert "- OpenAPI" in translate_prompt


def test_opencode_provider_injects_default_locale_rules_for_pt_to_en(tmp_path):
    runner = _FakeRunner([_translation_result("Initial content")])
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
    )

    request = _request_without_locale_metadata(source_locale="pt-br", target_locale="en-us")
    request.metadata["glossary"] = [{"source": "vazao", "target": "data throughput"}]
    provider.translate(request)

    translate_prompt = runner.calls[0]["prompt_text"]
    assert "Prefer idiomatic US English over literal Portuguese structure." in translate_prompt
    assert "vazao => data throughput" in translate_prompt
    assert "latencia => latency" in translate_prompt
    assert "- RFC 9110" in translate_prompt
