"""Deterministic tests for the settled translation_v2 stage pipeline.

Run only this suite:
    uv run --extra dev pytest tests/test_opencode_provider_loop.py -q
"""

from __future__ import annotations

import os
import sys
import types

import pytest


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)
_mock_provider_stub = types.ModuleType("translation_v2.mock_provider")
_mock_provider_stub.DeterministicMockTranslationProvider = object
sys.modules.setdefault("translation_v2.mock_provider", _mock_provider_stub)

from translation_v2.artifacts import TranslationRunArtifacts  # noqa: E402
from translation_v2.contracts import (  # noqa: E402
    CritiqueFinding,
    CritiqueOutput,
    FinalReviewOutput,
    RevisionOutput,
    StageResult,
    TerminologyPolicyPacket,
    TranslationOutput,
    TranslationRequest,
    VoiceIntentPacket,
)
from translation_v2.errors import MissingFieldError  # noqa: E402
from translation_v2.providers.opencode import (  # noqa: E402
    OpenCodeProviderLoopError,
    OpenCodeTranslationProvider,
)


class _FakeRunner:
    def __init__(self, scripted: list[StageResult | Exception]) -> None:
        self._scripted = list(scripted)
        self.calls: list[dict[str, str]] = []

    def run_stage(
        self,
        *,
        request: TranslationRequest,  # noqa: ARG002
        post_slug: str,
        stage: str,
        prompt_text: str,
        attach_path: str,
        artifacts: TranslationRunArtifacts,  # noqa: ARG002
        pass_name: str | None = None,
    ) -> StageResult:
        self.calls.append(
            {
                "stage": stage,
                "prompt_text": prompt_text,
                "attach_path": attach_path,
                "post_slug": post_slug,
                "pass_name": pass_name or "",
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
        prompt_version="v2",
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
                {"source": "throughput", "target": "vazão"},
                "latency => latência",
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
        prompt_version="v2",
        metadata={
            "slug": "provider-loop-post",
            "attach_path": "/tmp/provider-loop-source.md",
        },
    )


def _source_analysis_result(*, model: str = "openai/gpt-5.4-high") -> StageResult:
    return StageResult(
        run_id="opencode-provider-test",
        stage="source_analysis",
        model=model,
        payload=VoiceIntentPacket(
            author_voice_summary="Dry, technical, confident.",
            tone="technical",
            register="professional",
            sentence_rhythm=["medium cadence", "occasional long sentence"],
            connective_tissue=["contrastive pivots"],
            rhetorical_moves=["thesis then qualification"],
            humor_signals=["understated irony"],
            stance_markers=["first-person ownership"],
            must_preserve=["[@smith2024]"],
        ),
        raw_response={"source_analysis": True},
    )


def _terminology_policy_result(*, model: str = "openai/gpt-5.4-high") -> StageResult:
    return StageResult(
        run_id="opencode-provider-test",
        stage="terminology_policy",
        model=model,
        payload=TerminologyPolicyPacket(
            keep_english=["cache adapter", "throughput"],
            localize=["latency => latência"],
            context_sensitive=["rollout"],
            do_not_translate=["OpenCode", "CUDA"],
            consistency_rules=["Use the same borrowing decision in title and body."],
            rationale_notes=["Borrow well-known infra terms when PT-BR usage expects it."],
        ),
        raw_response={"terminology_policy": True},
    )


def _translation_result(content: str, *, model: str = "openai/gpt-5.4-high") -> StageResult:
    return StageResult(
        run_id="opencode-provider-test",
        stage="translate",
        model=model,
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
    *,
    model: str = "openai/gpt-5.2",
    description: str = "tighten terminology",
    needs_refinement: bool = False,
) -> StageResult:
    return StageResult(
        run_id="opencode-provider-test",
        stage="critique",
        model=model,
        payload=CritiqueOutput(
            score=score,
            feedback="feedback",
            needs_refinement=needs_refinement,
            findings=[
                CritiqueFinding(
                    finding_id="finding-1",
                    severity="major",
                    category="terminology",
                    source_span="throughput",
                    target_span="taxa",
                    description=description,
                    rewrite_instruction="Use the approved borrowed term.",
                )
            ],
            dimension_scores={
                "accuracy_completeness": score,
                "terminology_entities": score,
                "markdown_code_link_fidelity": score,
            },
            critical_errors=0,
            major_core_errors=0,
            confidence=0.9,
        ),
        raw_response={"critique": True},
    )


def _revision_result(
    content: str,
    *,
    model: str = "openai/gpt-5.4-high",
) -> StageResult:
    return StageResult(
        run_id="opencode-provider-test",
        stage="revise",
        model=model,
        payload=RevisionOutput(
            title="Titulo revisado",
            excerpt="Resumo revisado",
            tags=["ia", "agentes"],
            content=content,
            applied_feedback=["Applied terminology policy to the draft."],
            rewrite_summary=["Re-anchored terminology against the source."],
            unresolved_risks=[],
        ),
        raw_response={"revise": True},
    )


def _final_review_result(
    *,
    accept: bool,
    publish_ready: bool,
    model: str = "openai/gpt-5.2",
    residual_issues: list[str] | None = None,
) -> StageResult:
    return StageResult(
        run_id="opencode-provider-test",
        stage="final_review",
        model=model,
        payload=FinalReviewOutput(
            accept=accept,
            publish_ready=publish_ready,
            confidence=0.88,
            residual_issues=residual_issues or [],
            voice_score=92.0,
            terminology_score=95.0,
            locale_naturalness_score=93.0,
        ),
        raw_response={"final_review": True},
    )


def test_opencode_provider_runs_settled_stage_graph_with_model_split(tmp_path):
    runner = _FakeRunner(
        [
            _source_analysis_result(),
            _terminology_policy_result(),
            _translation_result("Conteudo inicial"),
            _critique_result(72.0, needs_refinement=True),
            _revision_result("Conteudo revisado"),
            _final_review_result(accept=True, publish_ready=True),
        ]
    )
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
    )

    result = provider.run_translation_pipeline(_request())

    assert result.stop_reason == "accepted"
    assert result.loops_completed == 1
    assert [item.stage for item in result.stage_results] == [
        "source_analysis",
        "terminology_policy",
        "translate",
        "critique",
        "revise",
        "final_review",
    ]
    assert [item.model for item in result.stage_results] == [
        "openai/gpt-5.4-high",
        "openai/gpt-5.4-high",
        "openai/gpt-5.4-high",
        "openai/gpt-5.2",
        "openai/gpt-5.4-high",
        "openai/gpt-5.2",
    ]
    assert result.final_translation.content == "Conteudo revisado"


def test_opencode_provider_revision_pass_receives_source_draft_and_critique(tmp_path):
    runner = _FakeRunner(
        [
            _source_analysis_result(),
            _terminology_policy_result(),
            _critique_result(
                81.0,
                description="Replace generic wording with approved terminology.",
                needs_refinement=True,
            ),
            _revision_result("Conteudo revisado"),
            _final_review_result(accept=True, publish_ready=True),
        ]
    )
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
    )

    result = provider.run_translation_pipeline(
        _request(),
        existing_translation=TranslationOutput(
            title="Titulo atual",
            excerpt="Resumo atual",
            tags=["ia"],
            content="Rascunho atual",
        ),
    )

    assert result.stop_reason == "accepted"
    assert [item.stage for item in result.stage_results] == [
        "source_analysis",
        "terminology_policy",
        "critique",
        "revise",
        "final_review",
    ]

    revise_prompt = runner.calls[3]["prompt_text"]
    assert "## Heading" in revise_prompt
    assert '"content": "Rascunho atual"' in revise_prompt
    assert "Replace generic wording with approved terminology." in revise_prompt
    assert "Use the approved borrowed term." in revise_prompt


def test_opencode_provider_uses_final_review_as_accept_reject_gate(tmp_path):
    runner = _FakeRunner(
        [
            _source_analysis_result(),
            _terminology_policy_result(),
            _translation_result("Conteudo inicial"),
            _critique_result(78.0, needs_refinement=True),
            _revision_result("Conteudo revisado 1"),
            _final_review_result(
                accept=False,
                publish_ready=False,
                residual_issues=["Voice still sounds imported."],
            ),
            _critique_result(
                88.0,
                description="Tighten the second paragraph.",
                needs_refinement=True,
            ),
            _revision_result("Conteudo revisado 2"),
            _final_review_result(
                accept=False,
                publish_ready=False,
                residual_issues=["Terminology still drifts."],
            ),
        ]
    )
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
        max_revision_passes=2,
    )

    with pytest.raises(OpenCodeProviderLoopError, match="Final review rejected"):
        provider.run_translation_pipeline(_request())

    assert [call["stage"] for call in runner.calls] == [
        "source_analysis",
        "terminology_policy",
        "translate",
        "critique",
        "revise",
        "final_review",
        "critique",
        "revise",
        "final_review",
    ]


def test_opencode_provider_translate_prompt_carries_voice_and_terminology_packets(tmp_path):
    runner = _FakeRunner([_translation_result("Conteudo inicial")])
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
    )

    provider.translate(
        _request_without_locale_metadata(source_locale="en-us", target_locale="pt-br"),
        _source_analysis_result().payload,
        _terminology_policy_result().payload,
    )

    translate_prompt = runner.calls[0]["prompt_text"]
    assert "TRANSLATE" in translate_prompt
    assert "SOURCE ANALYSIS JSON" in translate_prompt
    assert '"author_voice_summary": "Dry, technical, confident."' in translate_prompt
    assert "TERMINOLOGY POLICY JSON" in translate_prompt
    assert '"keep_english": [' in translate_prompt
    assert '"cache adapter"' in translate_prompt
    assert '"OpenCode"' in translate_prompt
    assert "LOCALIZATION BRIEF" in translate_prompt
    assert "Brazilian Portuguese" in translate_prompt
    assert (
        "Localize for Brazilian Portuguese readership; do not mirror English sentence order"
        in translate_prompt
    )


def test_opencode_provider_propagates_schema_validation_failures(tmp_path):
    runner = _FakeRunner(
        [
            MissingFieldError(
                message="Missing required field",
                run_id="opencode-provider-test",
                stage="source_analysis",
                field="tone",
            )
        ]
    )
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
    )

    with pytest.raises(MissingFieldError):
        provider.source_analysis(_request())

    assert [call["stage"] for call in runner.calls] == ["source_analysis"]
    error_path = (
        TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path)
        .stage_dir("provider-loop-post", "source_analysis")
        / "error.txt"
    )
    assert error_path.exists()
    assert "Missing required field" in error_path.read_text(encoding="utf-8")


def test_opencode_provider_skips_revision_when_critique_does_not_require_it(tmp_path):
    runner = _FakeRunner(
        [
            _source_analysis_result(),
            _terminology_policy_result(),
            _translation_result("Conteudo inicial"),
            _critique_result(91.0, needs_refinement=False),
            _final_review_result(accept=True, publish_ready=True),
        ]
    )
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
    )

    result = provider.run_translation_pipeline(_request())

    assert result.stop_reason == "accepted"
    assert [item.stage for item in result.stage_results] == [
        "source_analysis",
        "terminology_policy",
        "translate",
        "critique",
        "final_review",
    ]
    assert [call["stage"] for call in runner.calls] == [
        "source_analysis",
        "terminology_policy",
        "translate",
        "critique",
        "final_review",
    ]


def test_opencode_provider_final_review_prompt_receives_critique_and_revision_report(tmp_path):
    runner = _FakeRunner(
        [
            _source_analysis_result(),
            _terminology_policy_result(),
            _translation_result("Conteudo inicial"),
            _critique_result(72.0, needs_refinement=True),
            _revision_result("Conteudo revisado"),
            _final_review_result(accept=True, publish_ready=True),
        ]
    )
    provider = OpenCodeTranslationProvider(
        runner=runner,
        artifacts=TranslationRunArtifacts(run_id="opencode-provider-test", base_dir=tmp_path),
        default_attach_path="/tmp/fallback.md",
    )

    provider.run_translation_pipeline(_request())

    final_review_prompt = runner.calls[-1]["prompt_text"]
    assert "CRITIQUE JSON" in final_review_prompt
    assert '"finding_id": "finding-1"' in final_review_prompt
    assert "REVISION REPORT JSON" in final_review_prompt
    assert '"applied_feedback": [' in final_review_prompt


def test_translation_run_artifacts_scope_revision_pass_files(tmp_path):
    artifacts = TranslationRunArtifacts(run_id="artifact-pass-scope", base_dir=tmp_path)

    artifacts.write_prompt(
        "cv",
        "critique",
        "prompt text",
        prompt_version="v2",
        prompt_fingerprint="fingerprint",
        pass_name="pass-2",
    )
    artifacts.write_structured_response(
        "cv",
        "critique",
        {"score": 82},
        pass_name="pass-2",
    )

    scoped_dir = artifacts.stage_dir("cv", "critique", pass_name="pass-2")
    assert scoped_dir.exists()
    assert (scoped_dir / "prompt.txt").exists()
    assert (scoped_dir / "structured-response.json").exists()
