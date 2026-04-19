"""Deterministic mock provider for translation_v2 tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .contracts import (
    CVTranslationOutput,
    CVRevisionOutput,
    CritiqueOutput,
    FinalReviewOutput,
    RevisionOutput,
    StageResult,
    TerminologyPolicyPacket,
    TranslationOutput,
    TranslationRequest,
    VoiceIntentPacket,
    validate_cv_revision_output,
    validate_cv_translation_output,
    validate_final_review_output,
    validate_critique_output,
    validate_revision_output,
    validate_terminology_policy_output,
    validate_translation_output,
    validate_voice_intent_output,
)
from .provider import TranslationProvider


class DeterministicMockTranslationProvider(TranslationProvider):
    """Fixture-backed provider with deterministic stage outputs."""

    def __init__(
        self,
        fixtures_by_slug: Mapping[str, Mapping[str, Any]],
        *,
        model: str = "mock/deterministic-translation-v2",
    ) -> None:
        if not fixtures_by_slug:
            raise ValueError("fixtures_by_slug must contain at least one fixture")
        self._fixtures_by_slug = dict(fixtures_by_slug)
        self._model = model

    @classmethod
    def from_fixture_file(
        cls,
        fixture_path: str | Path,
        *,
        model: str = "mock/deterministic-translation-v2",
    ) -> "DeterministicMockTranslationProvider":
        """Build provider from JSON fixture with a `posts` mapping."""

        fixture_obj = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
        posts = fixture_obj.get("posts", {})
        if not isinstance(posts, dict) or not posts:
            raise ValueError("fixture file must define a non-empty 'posts' mapping")
        return cls(posts, model=model)

    def _fixture_for_request(self, request: TranslationRequest) -> Mapping[str, Any]:
        slug = str(request.metadata.get("slug", "")).strip()
        if slug and slug in self._fixtures_by_slug:
            return self._fixtures_by_slug[slug]

        if len(self._fixtures_by_slug) == 1:
            return next(iter(self._fixtures_by_slug.values()))

        raise KeyError("No fixture found for request metadata slug; provide metadata['slug']")

    def source_analysis(self, request: TranslationRequest) -> StageResult[VoiceIntentPacket]:
        fixture = self._fixture_for_request(request)
        payload = validate_voice_intent_output(
            fixture.get(
                "source_analysis",
                {
                    "author_voice_summary": "Pragmatic technical voice",
                    "tone": "analytical",
                    "register": "technical blog",
                    "sentence_rhythm": ["varied"],
                    "connective_tissue": ["argument-led"],
                    "rhetorical_moves": ["contrast", "qualification"],
                    "humor_signals": ["understated"],
                    "stance_markers": ["opinionated"],
                    "must_preserve": ["voice", "cadence"],
                },
            ),
            run_id=request.run_id,
            stage="source_analysis",
        )
        return StageResult(
            run_id=request.run_id,
            stage="source_analysis",
            model=self._model,
            payload=payload,
            raw_response={"fixture_slug": request.metadata.get("slug", "")},
        )

    def terminology_policy(
        self,
        request: TranslationRequest,
        source_analysis: VoiceIntentPacket | None = None,  # noqa: ARG002
    ) -> StageResult[TerminologyPolicyPacket]:
        fixture = self._fixture_for_request(request)
        payload = validate_terminology_policy_output(
            fixture.get(
                "terminology_policy",
                {
                    "keep_english": [],
                    "localize": [],
                    "context_sensitive": [],
                    "do_not_translate": [],
                    "consistency_rules": ["stay consistent"],
                    "rationale_notes": [],
                },
            ),
            run_id=request.run_id,
            stage="terminology_policy",
        )
        return StageResult(
            run_id=request.run_id,
            stage="terminology_policy",
            model=self._model,
            payload=payload,
            raw_response={"fixture_slug": request.metadata.get("slug", "")},
        )

    def translate(
        self,
        request: TranslationRequest,
        source_analysis: VoiceIntentPacket | None = None,  # noqa: ARG002
        terminology_policy: TerminologyPolicyPacket | None = None,  # noqa: ARG002
    ) -> StageResult[TranslationOutput | CVTranslationOutput]:
        fixture = self._fixture_for_request(request)
        artifact_type = str(request.metadata.get("artifact_type", "post")).strip().lower()
        if artifact_type == "cv":
            translated_payload = validate_cv_translation_output(
                fixture["translated"], run_id=request.run_id, stage="translate"
            )
        else:
            translated_payload = validate_translation_output(
                fixture["translated"], run_id=request.run_id, stage="translate"
            )
        return StageResult(
            run_id=request.run_id,
            stage="translate",
            model=self._model,
            payload=translated_payload,
            raw_response={"fixture_slug": request.metadata.get("slug", "")},
        )

    def critique(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,  # noqa: ARG002
        *,
        source_analysis: VoiceIntentPacket | None = None,  # noqa: ARG002
        terminology_policy: TerminologyPolicyPacket | None = None,  # noqa: ARG002
    ) -> StageResult[CritiqueOutput]:
        fixture = self._fixture_for_request(request)
        critique_payload = validate_critique_output(
            fixture["critique"], run_id=request.run_id, stage="critique"
        )
        return StageResult(
            run_id=request.run_id,
            stage="critique",
            model=self._model,
            payload=critique_payload,
            raw_response={"fixture_slug": request.metadata.get("slug", "")},
        )

    def revise(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,  # noqa: ARG002
        critique: CritiqueOutput,
        *,
        source_analysis: VoiceIntentPacket | None = None,  # noqa: ARG002
        terminology_policy: TerminologyPolicyPacket | None = None,  # noqa: ARG002
    ) -> StageResult[RevisionOutput | CVRevisionOutput]:
        fixture = self._fixture_for_request(request)
        raw_revision = fixture.get("revised", fixture.get("refined", {}))
        artifact_type = str(request.metadata.get("artifact_type", "post")).strip().lower()
        if artifact_type == "cv":
            refined_payload = validate_cv_revision_output(
                raw_revision,
                run_id=request.run_id,
                stage="revise",
            )
        else:
            refined_payload = validate_revision_output(
                raw_revision,
                run_id=request.run_id,
                stage="revise",
            )
        result: StageResult[RevisionOutput | CVRevisionOutput] = StageResult(
            run_id=request.run_id,
            stage="revise",
            model=self._model,
            payload=refined_payload,
            raw_response={"fixture_slug": request.metadata.get("slug", "")},
        )
        return result

    def refine(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,
        critique: CritiqueOutput,
        *,
        source_analysis: VoiceIntentPacket | None = None,
        terminology_policy: TerminologyPolicyPacket | None = None,
    ) -> StageResult[RevisionOutput | CVRevisionOutput]:
        """Backward-compatible alias for revise."""

        return self.revise(
            request,
            translated,
            critique,
            source_analysis=source_analysis,
            terminology_policy=terminology_policy,
        )

    def final_review(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,  # noqa: ARG002
        critique: CritiqueOutput,  # noqa: ARG002
        *,
        revision_report: RevisionOutput | CVRevisionOutput | None = None,  # noqa: ARG002
        source_analysis: VoiceIntentPacket | None = None,  # noqa: ARG002
        terminology_policy: TerminologyPolicyPacket | None = None,  # noqa: ARG002
    ) -> StageResult[FinalReviewOutput]:
        fixture = self._fixture_for_request(request)
        payload = validate_final_review_output(
            fixture.get(
                "final_review",
                {
                    "accept": True,
                    "publish_ready": True,
                    "confidence": 1.0,
                    "residual_issues": [],
                    "voice_score": 95,
                    "terminology_score": 95,
                    "locale_naturalness_score": 95,
                },
            ),
            run_id=request.run_id,
            stage="final_review",
        )
        return StageResult(
            run_id=request.run_id,
            stage="final_review",
            model=self._model,
            payload=payload,
            raw_response={"fixture_slug": request.metadata.get("slug", "")},
        )
