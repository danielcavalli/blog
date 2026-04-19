"""OpenCode-backed localization provider for translation_v2."""

from __future__ import annotations

import json
import inspect
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any, Protocol

from ..artifacts import TranslationRunArtifacts
from ..console import finish_stage_status, start_stage_status
from ..contracts import (
    CVRevisionOutput,
    CVTranslationOutput,
    CritiqueOutput,
    FinalReviewOutput,
    ProviderPayload,
    RevisionOutput,
    StageResult,
    TerminologyPolicyPacket,
    TranslationOutput,
    TranslationRequest,
    VoiceIntentPacket,
)
from ..errors import ContractValidationError
from ..locale_rules import get_default_locale_rules
from ..prompt_registry import compute_prompt_pack_fingerprint, render_prompt_template
from ..provider import TranslationProvider
from ..source_analysis import build_source_analysis_context
from ..terminology_policy import (
    build_terminology_policy_context,
    build_translation_policy_context,
)
from ..voice_profile import AuthorVoiceProfile


class OpenCodeRunnerLike(Protocol):
    def run_stage(
        self,
        *,
        request: TranslationRequest,
        post_slug: str,
        stage: str,
        prompt_text: str,
        attach_path: str,
        artifacts: TranslationRunArtifacts,
        pass_name: str | None = None,
    ) -> StageResult[ProviderPayload]:
        ...


@dataclass(slots=True)
class OpenCodeProviderLoopResult:
    """Result envelope for one localization pipeline run."""

    final_translation: TranslationOutput | CVTranslationOutput
    stage_results: list[StageResult[ProviderPayload]]
    loops_completed: int
    stop_reason: str


class OpenCodeProviderLoopError(RuntimeError):
    """Raised when the localization loop cannot produce a publishable output."""


class OpenCodeTranslationProvider(TranslationProvider):
    """Translation provider that uses distinct stages for localization quality."""

    def __init__(
        self,
        *,
        runner: OpenCodeRunnerLike | None = None,
        artifacts: TranslationRunArtifacts,
        default_attach_path: str,
        analysis_runner: OpenCodeRunnerLike | None = None,
        terminology_runner: OpenCodeRunnerLike | None = None,
        critique_runner: OpenCodeRunnerLike | None = None,
        revision_runner: OpenCodeRunnerLike | None = None,
        final_review_runner: OpenCodeRunnerLike | None = None,
        voice_profile: AuthorVoiceProfile | None = None,
        max_revision_passes: int = 2,
    ) -> None:
        base_runner = runner
        if base_runner is None and any(
            current is None
            for current in (
                analysis_runner,
                terminology_runner,
                critique_runner,
                revision_runner,
                final_review_runner,
            )
        ):
            raise ValueError("runner is required when stage-specific runners are not all provided")

        self._analysis_runner = analysis_runner or base_runner
        self._terminology_runner = terminology_runner or base_runner
        self._translation_runner = base_runner or revision_runner
        self._critique_runner = critique_runner or base_runner
        self._revision_runner = revision_runner or base_runner
        self._final_review_runner = final_review_runner or critique_runner or base_runner
        self._artifacts = artifacts
        self._default_attach_path = default_attach_path
        self._voice_profile = voice_profile or AuthorVoiceProfile(brief="")
        self._fingerprint_cache: dict[str, str] = {}
        self._max_revision_passes = max_revision_passes

    def source_analysis(self, request: TranslationRequest) -> StageResult[VoiceIntentPacket]:
        lists = self._policy_lists(request)
        context = build_source_analysis_context(
            request,
            voice_profile=self._voice_profile,
            writing_style_brief=str(request.metadata.get("writing_style_brief", "")),
            style_constraints=lists["style_constraints"],
            localization_brief=lists["localization_brief"],
            borrowing_conventions=lists["borrowing_conventions"],
            punctuation_conventions=lists["punctuation_conventions"],
            discourse_conventions=lists["discourse_conventions"],
            register_conventions=lists["register_conventions"],
            review_checks=lists["review_checks"],
            glossary_entries=lists["glossary"],
            do_not_translate_entities=lists["do_not_translate_entities"],
        )
        return self._run_stage_with_repair(
            runner=self._analysis_runner,
            request=request,
            stage="source_analysis",
            context=context,
        )

    def terminology_policy(
        self,
        request: TranslationRequest,
        source_analysis: VoiceIntentPacket | None = None,
    ) -> StageResult[TerminologyPolicyPacket]:
        if source_analysis is None:
            source_analysis = self.source_analysis(request).payload
        lists = self._policy_lists(request)
        context = build_terminology_policy_context(
            request,
            source_analysis=source_analysis,
            glossary_entries=lists["glossary"],
            do_not_translate_entities=lists["do_not_translate_entities"],
            style_constraints=lists["style_constraints"],
            localization_brief=lists["localization_brief"],
            borrowing_conventions=lists["borrowing_conventions"],
            punctuation_conventions=lists["punctuation_conventions"],
            discourse_conventions=lists["discourse_conventions"],
            register_conventions=lists["register_conventions"],
            review_checks=lists["review_checks"],
        )
        return self._run_stage_with_repair(
            runner=self._terminology_runner,
            request=request,
            stage="terminology_policy",
            context=context,
        )

    def translate(
        self,
        request: TranslationRequest,
        source_analysis: VoiceIntentPacket | None = None,
        terminology_policy: TerminologyPolicyPacket | None = None,
    ) -> StageResult[TranslationOutput | CVTranslationOutput]:
        if source_analysis is None:
            source_analysis = self.source_analysis(request).payload
        if terminology_policy is None:
            terminology_policy = self.terminology_policy(request, source_analysis).payload
        context = self._translation_context(
            request,
            source_analysis=source_analysis,
            terminology_policy=terminology_policy,
        )
        return self._run_stage_with_repair(
            runner=self._translation_runner,
            request=request,
            stage="translate",
            context=context,
        )

    def critique(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,
        *,
        source_analysis: VoiceIntentPacket | None = None,
        terminology_policy: TerminologyPolicyPacket | None = None,
        pass_name: str | None = None,
    ) -> StageResult[CritiqueOutput]:
        if source_analysis is None:
            source_analysis = self.source_analysis(request).payload
        if terminology_policy is None:
            terminology_policy = self.terminology_policy(request, source_analysis).payload
        context = self._translation_context(
            request,
            source_analysis=source_analysis,
            terminology_policy=terminology_policy,
        )
        context["translated_json"] = json.dumps(
            _payload_to_dict(translated),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        return self._run_stage_with_repair(
            runner=self._critique_runner,
            request=request,
            stage="critique",
            context=context,
            pass_name=pass_name,
        )

    def revise(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,
        critique: CritiqueOutput,
        *,
        source_analysis: VoiceIntentPacket | None = None,
        terminology_policy: TerminologyPolicyPacket | None = None,
        pass_name: str | None = None,
    ) -> StageResult[RevisionOutput | CVRevisionOutput]:
        if source_analysis is None:
            source_analysis = self.source_analysis(request).payload
        if terminology_policy is None:
            terminology_policy = self.terminology_policy(request, source_analysis).payload
        context = self._translation_context(
            request,
            source_analysis=source_analysis,
            terminology_policy=terminology_policy,
        )
        context["translated_json"] = json.dumps(
            _payload_to_dict(translated),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        context["critique_json"] = json.dumps(
            _payload_to_dict(critique),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        return self._run_stage_with_repair(
            runner=self._revision_runner,
            request=request,
            stage="revise",
            context=context,
            pass_name=pass_name,
        )

    def final_review(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,
        critique: CritiqueOutput,
        *,
        revision_report: RevisionOutput | CVRevisionOutput | None = None,
        source_analysis: VoiceIntentPacket | None = None,
        terminology_policy: TerminologyPolicyPacket | None = None,
        pass_name: str | None = None,
    ) -> StageResult[FinalReviewOutput]:
        if source_analysis is None:
            source_analysis = self.source_analysis(request).payload
        if terminology_policy is None:
            terminology_policy = self.terminology_policy(request, source_analysis).payload
        context = self._translation_context(
            request,
            source_analysis=source_analysis,
            terminology_policy=terminology_policy,
        )
        context["translated_json"] = json.dumps(
            _payload_to_dict(translated),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        context["critique_json"] = json.dumps(
            _payload_to_dict(critique),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        context["revision_report_json"] = json.dumps(
            _revision_report_dict(revision_report),
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        return self._run_stage_with_repair(
            runner=self._final_review_runner,
            request=request,
            stage="final_review",
            context=context,
            pass_name=pass_name,
        )

    def run_translation_pipeline(
        self,
        request: TranslationRequest,
        *,
        existing_translation: TranslationOutput | CVTranslationOutput | None = None,
    ) -> OpenCodeProviderLoopResult:
        stage_results: list[StageResult[ProviderPayload]] = []

        source_analysis_result = self.source_analysis(request)
        stage_results.append(source_analysis_result)
        source_analysis = source_analysis_result.payload

        terminology_result = self.terminology_policy(request, source_analysis)
        stage_results.append(terminology_result)
        terminology_policy = terminology_result.payload

        if existing_translation is None:
            translate_result = self.translate(request, source_analysis, terminology_policy)
            stage_results.append(translate_result)
            current_translation = translate_result.payload
        else:
            current_translation = existing_translation

        for revision_pass in range(1, self._max_revision_passes + 1):
            pass_name = f"pass-{revision_pass}"
            critique_result = self.critique(
                request,
                current_translation,
                source_analysis=source_analysis,
                terminology_policy=terminology_policy,
                pass_name=pass_name,
            )
            stage_results.append(critique_result)

            revision_result: StageResult[RevisionOutput | CVRevisionOutput] | None = None
            revised_translation = current_translation
            if critique_result.payload.needs_refinement:
                revision_result = self.revise(
                    request,
                    current_translation,
                    critique_result.payload,
                    source_analysis=source_analysis,
                    terminology_policy=terminology_policy,
                    pass_name=pass_name,
                )
                stage_results.append(revision_result)
                revised_translation = _coerce_revision_payload(revision_result.payload)

            final_review_result = self.final_review(
                request,
                revised_translation,
                critique_result.payload,
                revision_report=revision_result.payload if revision_result is not None else None,
                source_analysis=source_analysis,
                terminology_policy=terminology_policy,
                pass_name=pass_name,
            )
            stage_results.append(final_review_result)

            if final_review_result.payload.accept and final_review_result.payload.publish_ready:
                return OpenCodeProviderLoopResult(
                    final_translation=revised_translation,
                    stage_results=stage_results,
                    loops_completed=revision_pass,
                    stop_reason="accepted",
                )

            current_translation = revised_translation

        raise OpenCodeProviderLoopError(
            "Final review rejected localized output after revision passes"
        )

    def run_translation_loop(self, request: TranslationRequest) -> OpenCodeProviderLoopResult:
        """Backward-compatible alias for the full localization pipeline."""

        return self.run_translation_pipeline(request)

    def run_revision_loop(
        self,
        request: TranslationRequest,
        existing_translation: TranslationOutput | CVTranslationOutput,
    ) -> OpenCodeProviderLoopResult:
        """Backward-compatible alias for revision-oriented entrypoint."""

        return self.run_translation_pipeline(
            request,
            existing_translation=existing_translation,
        )

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

    def _run_stage_with_repair(
        self,
        *,
        runner: OpenCodeRunnerLike,
        request: TranslationRequest,
        stage: str,
        context: Mapping[str, str],
        pass_name: str | None = None,
    ) -> StageResult[ProviderPayload]:
        post_slug = self._post_slug(request)
        artifact_type = self._artifact_type(request)
        prompt_fingerprint = self._prompt_fingerprint(
            request.prompt_version,
            artifact_type=artifact_type,
        )
        prompt_text = render_prompt_template(
            stage,
            context=context,
            prompt_version=request.prompt_version,
            artifact_type=artifact_type,
        )
        self._artifacts.write_prompt(
            post_slug,
            stage,
            prompt_text,
            prompt_version=request.prompt_version,
            prompt_fingerprint=prompt_fingerprint,
            pass_name=pass_name,
        )

        attach_path = self._resolve_attach_path(request)
        artifact_key = f"{artifact_type}:{post_slug}"
        start_stage_status(stage, artifact_key, _stage_launch_label(stage))
        try:
            runner_kwargs = {
                "request": request,
                "post_slug": post_slug,
                "stage": stage,
                "prompt_text": prompt_text,
                "attach_path": attach_path,
                "artifacts": self._artifacts,
            }
            if pass_name is not None and "pass_name" in inspect.signature(runner.run_stage).parameters:
                runner_kwargs["pass_name"] = pass_name
            result = runner.run_stage(**runner_kwargs)
            self._artifacts.write_structured_response(
                post_slug,
                stage,
                _payload_to_dict(result.payload),
                pass_name=pass_name,
            )
            finish_stage_status(
                stage,
                artifact_key,
                result=_stage_success_label(stage, result.model),
            )
            return result
        except ContractValidationError as exc:
            self._artifacts.write_error(post_slug, stage, str(exc), pass_name=pass_name)
            finish_stage_status(stage, artifact_key, error=_stage_invalid_label(stage, exc))
            raise
        except Exception as exc:
            self._artifacts.write_error(post_slug, stage, str(exc), pass_name=pass_name)
            finish_stage_status(stage, artifact_key, error=str(exc))
            raise

    def _translation_context(
        self,
        request: TranslationRequest,
        *,
        source_analysis: VoiceIntentPacket,
        terminology_policy: TerminologyPolicyPacket,
    ) -> dict[str, str]:
        lists = self._policy_lists(request)
        return build_translation_policy_context(
            request,
            source_analysis=source_analysis,
            terminology_policy=terminology_policy,
            glossary_entries=lists["glossary"],
            do_not_translate_entities=lists["do_not_translate_entities"],
            style_constraints=lists["style_constraints"],
            localization_brief=lists["localization_brief"],
            borrowing_conventions=lists["borrowing_conventions"],
            punctuation_conventions=lists["punctuation_conventions"],
            discourse_conventions=lists["discourse_conventions"],
            register_conventions=lists["register_conventions"],
            review_checks=lists["review_checks"],
            writing_style_brief=str(request.metadata.get("writing_style_brief", "")),
        )

    def _policy_lists(self, request: TranslationRequest) -> dict[str, Any]:
        metadata = request.metadata
        locale_defaults = get_default_locale_rules(
            source_locale=request.source_locale,
            target_locale=request.target_locale,
        )
        return {
            "style_constraints": _merge_string_lists(
                locale_defaults["style_constraints"],
                metadata.get("style_constraints"),
            ),
            "localization_brief": _merge_text_blocks(
                locale_defaults.get("localization_brief", ""),
                metadata.get("localization_brief"),
            ),
            "borrowing_conventions": _merge_string_lists(
                locale_defaults.get("borrowing_conventions"),
                metadata.get("borrowing_conventions"),
            ),
            "punctuation_conventions": _merge_string_lists(
                locale_defaults.get("punctuation_conventions"),
                metadata.get("punctuation_conventions"),
            ),
            "discourse_conventions": _merge_string_lists(
                locale_defaults.get("discourse_conventions"),
                metadata.get("discourse_conventions"),
            ),
            "register_conventions": _merge_string_lists(
                locale_defaults.get("register_conventions"),
                metadata.get("register_conventions"),
            ),
            "review_checks": _merge_string_lists(
                locale_defaults.get("review_checks"),
                metadata.get("review_checks"),
            ),
            "glossary": _merge_glossary_entries(
                locale_defaults["glossary"],
                metadata.get("glossary"),
            ),
            "do_not_translate_entities": _merge_string_lists(
                locale_defaults["do_not_translate_entities"],
                metadata.get("do_not_translate_entities"),
            ),
        }

    def _post_slug(self, request: TranslationRequest) -> str:
        slug = str(request.metadata.get("slug", "")).strip()
        return slug or request.run_id

    def _artifact_type(self, request: TranslationRequest) -> str:
        artifact_type = str(request.metadata.get("artifact_type", "post")).strip().lower()
        return artifact_type or "post"

    def _resolve_attach_path(self, request: TranslationRequest) -> str:
        metadata_path = str(request.metadata.get("attach_path", "")).strip()
        return metadata_path or self._default_attach_path

    def _prompt_fingerprint(self, prompt_version: str, *, artifact_type: str) -> str:
        cache_key = f"{artifact_type}:{prompt_version}"
        fingerprint = self._fingerprint_cache.get(cache_key)
        if fingerprint is None:
            fingerprint = compute_prompt_pack_fingerprint(
                prompt_version=prompt_version,
                artifact_type=artifact_type,
            )
            self._fingerprint_cache[cache_key] = fingerprint
        return fingerprint


def _merge_string_lists(defaults: Any, overrides: Any) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for source in (defaults or [], overrides or []):
        cleaned = str(source).strip()
        if not cleaned:
            continue
        normalized = cleaned.lower()
        if normalized in seen:
            continue
        seen.add(normalized)
        merged.append(cleaned)
    return merged


def _merge_text_blocks(default: Any, override: Any) -> str:
    sections = [str(value).strip() for value in (default, override) if str(value).strip()]
    return "\n\n".join(sections)


def _merge_glossary_entries(defaults: Any, overrides: Any) -> list[Any]:
    merged: list[Any] = []
    source_to_index: dict[str, int] = {}
    seen_strings: set[str] = set()
    for collection in (defaults or [], overrides or []):
        _append_or_override_glossary_entry(merged, source_to_index, seen_strings, collection)
    return merged


def _append_or_override_glossary_entry(
    merged: list[Any],
    source_to_index: dict[str, int],
    seen_strings: set[str],
    entry: Any,
) -> None:
    if isinstance(entry, Mapping):
        source = str(entry.get("source", "")).strip()
        target = str(entry.get("target", "")).strip()
        if source and target:
            normalized_source = source.lower()
            normalized_entry = {"source": source, "target": target}
            if normalized_source in source_to_index:
                merged[source_to_index[normalized_source]] = normalized_entry
            else:
                source_to_index[normalized_source] = len(merged)
                merged.append(normalized_entry)
            return

    cleaned = str(entry).strip()
    if cleaned and cleaned not in seen_strings:
        seen_strings.add(cleaned)
        merged.append(cleaned)


def _payload_to_dict(payload: ProviderPayload | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    return asdict(payload)


def _coerce_revision_payload(
    payload: RevisionOutput | CVRevisionOutput,
) -> TranslationOutput | CVTranslationOutput:
    if isinstance(payload, CVRevisionOutput):
        return payload.revised_cv
    return TranslationOutput(
        title=payload.title,
        excerpt=payload.excerpt,
        tags=payload.tags,
        content=payload.content,
    )


def _revision_report_dict(
    payload: RevisionOutput | CVRevisionOutput | None,
) -> dict[str, Any]:
    if payload is None:
        return {
            "applied_feedback": [],
            "declined_feedback": [],
            "rewrite_summary": [],
            "unresolved_risks": [],
        }
    if isinstance(payload, CVRevisionOutput):
        return asdict(payload.revision_report)
    return {
        "applied_feedback": payload.applied_feedback,
        "declined_feedback": [asdict(item) for item in payload.declined_feedback],
        "rewrite_summary": payload.rewrite_summary,
        "unresolved_risks": payload.unresolved_risks,
    }


def _stage_launch_label(stage: str) -> str:
    labels = {
        "source_analysis": "analyze source voice and rhetoric",
        "terminology_policy": "derive terminology and borrowing policy",
        "translate": "generate localized draft",
        "critique": "editorial critique pass",
        "revise": "rewrite using critique findings",
        "final_review": "final quality review",
    }
    return labels.get(stage, f"launch stage {stage}")


def _stage_success_label(stage: str, model: str) -> str:
    labels = {
        "source_analysis": f"Source analysis received [{model}]",
        "terminology_policy": f"Terminology policy received [{model}]",
        "translate": f"Localized draft received [{model}]",
        "critique": f"Critique report received [{model}]",
        "revise": f"Revised translation received [{model}]",
        "final_review": f"Final review received [{model}]",
    }
    return labels.get(stage, f"Output received for {stage} [{model}]")


def _stage_invalid_label(stage: str, exc: ContractValidationError) -> str:
    return f"{stage} produced schema-invalid output: {exc}"
