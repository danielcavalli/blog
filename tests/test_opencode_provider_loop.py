"""Deterministic tests for the unattended localization agent.

Run only this suite:
    uv run --extra dev pytest tests/test_opencode_provider_loop.py -q
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

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


def _source_analysis_result(*, model: str = "openai/gpt-5.5-high") -> StageResult:
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


def _terminology_policy_result(*, model: str = "openai/gpt-5.5-high") -> StageResult:
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


def _translation_result(content: str, *, model: str = "openai/gpt-5.5-high") -> StageResult:
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
    model: str = "opencode-go/deepseek-v4-pro-high",
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
    model: str = "openai/gpt-5.5-high",
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
    model: str = "opencode-go/deepseek-v4-pro-high",
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



def test_localization_is_one_unattended_agent_call(tmp_path):
    runner = _FakeRunner([_translation_result("Texto localizado.")])
    provider = OpenCodeTranslationProvider(runner=runner, artifacts=TranslationRunArtifacts("one-agent", tmp_path), default_attach_path="source.md")
    request = _request()
    result = provider.run_translation_pipeline(request)
    assert result.stop_reason == "localized"
    assert [call["stage"] for call in runner.calls] == ["translate"]
    prompt = runner.calls[0]["prompt_text"]
    assert "UNATTENDED LOCALIZATION AGENT" in prompt and "Do not ask questions" in prompt
    assert request.source_text in prompt
    assert "SOURCE ANALYSIS JSON" not in prompt and "TERMINOLOGY POLICY JSON" not in prompt


def test_refresh_starts_from_source_instead_of_anchoring_to_old_translation(tmp_path):
    runner = _FakeRunner([_translation_result("Uma nova localização.")])
    provider = OpenCodeTranslationProvider(runner=runner, artifacts=TranslationRunArtifacts("refresh", tmp_path), default_attach_path="source.md")
    provider.run_translation_pipeline(_request(), existing_translation=_translation_result("OLD_LITERAL_TRANSLATION").payload)
    assert "OLD_LITERAL_TRANSLATION" not in runner.calls[0]["prompt_text"]


@pytest.mark.parametrize("instruction", ["revision_request", "deterministic_findings"])
def test_explicit_correction_has_source_and_existing_target(tmp_path, instruction):
    runner = _FakeRunner([_translation_result("Uma correção.")])
    provider = OpenCodeTranslationProvider(runner=runner, artifacts=TranslationRunArtifacts("correction", tmp_path), default_attach_path="source.md")
    request = _request()
    request.metadata[instruction] = "KEEP_THE_ASIDE"
    provider.run_translation_pipeline(request, existing_translation=_translation_result("PREVIOUS_TRANSLATION").payload)
    prompt = runner.calls[0]["prompt_text"]
    assert request.source_text in prompt and "KEEP_THE_ASIDE" in prompt and "PREVIOUS_TRANSLATION" in prompt


def test_invalid_agent_schema_fails_after_one_repair(tmp_path):
    error = MissingFieldError("Missing required field", run_id="test", stage="translate", field="content")
    runner = _FakeRunner([error, error])
    provider = OpenCodeTranslationProvider(runner=runner, artifacts=TranslationRunArtifacts("invalid", tmp_path), default_attach_path="source.md")
    with pytest.raises(MissingFieldError):
        provider.localize(_request())
    assert len(runner.calls) == 2
    assert "Missing required field" in runner.calls[1]["prompt_text"]


def test_localization_does_not_load_retired_stage_templates(tmp_path, monkeypatch):
    from translation_v2 import prompt_registry
    template = prompt_registry.load_prompt_template("translate")
    prompts = tmp_path / "prompts/v2"
    prompts.mkdir(parents=True)
    (prompts / "translate.md").write_text(template)
    monkeypatch.setattr(prompt_registry, "PROMPTS_ROOT", Path(tmp_path / "prompts"))
    runner = _FakeRunner([_translation_result("Texto localizado.")])
    provider = OpenCodeTranslationProvider(
        runner=runner, default_attach_path=str(tmp_path),
        artifacts=TranslationRunArtifacts(run_id="active-template-only", base_dir=tmp_path),
    )
    provider.run_translation_pipeline(_request())
    assert [call["stage"] for call in runner.calls] == ["translate"]
