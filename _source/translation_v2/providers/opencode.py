"""OpenCode-backed translation provider with critique/refine loop controls."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any, Literal, Protocol, overload

from ..artifacts import TranslationRunArtifacts
from ..console import finish_stage_status, start_stage_status
from ..contracts import (
    CVTranslationOutput,
    CritiqueOutput,
    ProviderPayload,
    RefinementOutput,
    StageResult,
    TranslationOutput,
    TranslationRequest,
)
from ..errors import ContractValidationError
from ..locale_rules import get_default_locale_rules
from ..prompt_registry import compute_prompt_pack_fingerprint, render_prompt_template
from ..provider import TranslationProvider
from ..rubric import RubricDecisionInput, RubricThresholds, decide_score_action


_SCHEMA_EXAMPLES = {
    "translate": (
        "{\n"
        '  "title": "string",\n'
        '  "excerpt": "string",\n'
        '  "tags": ["string"],\n'
        '  "content": "string"\n'
        "}"
    ),
    "cv_translate": (
        "{\n"
        '  "name": "string",\n'
        '  "tagline": "string",\n'
        '  "location": "string",\n'
        '  "contact": {"email": "string", "linkedin": "string", "github": "string"},\n'
        '  "skills": ["string"],\n'
        '  "languages_spoken": ["string"],\n'
        '  "summary": "string",\n'
        '  "experience": [{"title": "string", "company": "string", "location": "string", "period": "string", "description": "string", "achievements": ["string"]}],\n'
        '  "education": [{"degree": "string", "school": "string", "period": "string"}]\n'
        "}"
    ),
    "critique": (
        "{\n"
        '  "score": 0,\n'
        '  "feedback": "string",\n'
        '  "needs_refinement": true,\n'
        '  "dimension_scores": {\n'
        '    "accuracy_completeness": 0,\n'
        '    "terminology_entities": 0,\n'
        '    "markdown_code_link_fidelity": 0\n'
        "  },\n"
        '  "critical_errors": 0,\n'
        '  "major_core_errors": 0,\n'
        '  "confidence": 1.0,\n'
        '  "findings": ["string"]\n'
        "}"
    ),
    "cv_critique": (
        "{\n"
        '  "score": 0,\n'
        '  "feedback": "string",\n'
        '  "needs_refinement": true,\n'
        '  "dimension_scores": {\n'
        '    "accuracy_completeness": 0,\n'
        '    "terminology_entities": 0,\n'
        '    "markdown_code_link_fidelity": 0\n'
        "  },\n"
        '  "critical_errors": 0,\n'
        '  "major_core_errors": 0,\n'
        '  "confidence": 1.0,\n'
        '  "findings": ["string"]\n'
        "}"
    ),
    "refine": (
        "{\n"
        '  "title": "string",\n'
        '  "excerpt": "string",\n'
        '  "tags": ["string"],\n'
        '  "content": "string",\n'
        '  "applied_feedback": ["string"]\n'
        "}"
    ),
    "cv_refine": (
        "{\n"
        '  "name": "string",\n'
        '  "tagline": "string",\n'
        '  "location": "string",\n'
        '  "contact": {"email": "string", "linkedin": "string", "github": "string"},\n'
        '  "skills": ["string"],\n'
        '  "languages_spoken": ["string"],\n'
        '  "summary": "string",\n'
        '  "experience": [{"title": "string", "company": "string", "location": "string", "period": "string", "description": "string", "achievements": ["string"]}],\n'
        '  "education": [{"degree": "string", "school": "string", "period": "string"}]\n'
        "}"
    ),
}


class OpenCodeRunnerLike(Protocol):
    @overload
    def run_stage(
        self,
        *,
        request: TranslationRequest,
        post_slug: str,
        stage: Literal["translate"],
        prompt_text: str,
        attach_path: str,
        artifacts: TranslationRunArtifacts,
    ) -> StageResult[TranslationOutput]: ...

    @overload
    def run_stage(
        self,
        *,
        request: TranslationRequest,
        post_slug: str,
        stage: Literal["critique"],
        prompt_text: str,
        attach_path: str,
        artifacts: TranslationRunArtifacts,
    ) -> StageResult[CritiqueOutput]: ...

    @overload
    def run_stage(
        self,
        *,
        request: TranslationRequest,
        post_slug: str,
        stage: Literal["refine"],
        prompt_text: str,
        attach_path: str,
        artifacts: TranslationRunArtifacts,
    ) -> StageResult[RefinementOutput]: ...


@dataclass(slots=True)
class OpenCodeProviderLoopResult:
    """Result envelope for the bounded critique/refine provider loop."""

    final_translation: TranslationOutput | CVTranslationOutput
    stage_results: list[StageResult[ProviderPayload]]
    loops_completed: int
    stop_reason: str


class OpenCodeProviderLoopError(RuntimeError):
    """Raised when stop policy triggers a hard fail."""


class OpenCodeTranslationProvider(TranslationProvider):
    """Translation provider that renders prompts and calls OpenCode runner."""

    def __init__(
        self,
        *,
        runner: OpenCodeRunnerLike,
        artifacts: TranslationRunArtifacts,
        default_attach_path: str,
        thresholds: RubricThresholds = RubricThresholds(),
        max_schema_repairs: int = 1,
    ) -> None:
        if max_schema_repairs < 0:
            raise ValueError("max_schema_repairs must be >= 0")

        self._runner = runner
        self._artifacts = artifacts
        self._default_attach_path = default_attach_path
        self._thresholds = thresholds
        self._max_schema_repairs = max_schema_repairs
        self._fingerprint_cache: dict[str, str] = {}

    def translate(self, request: TranslationRequest) -> StageResult[TranslationOutput | CVTranslationOutput]:
        context = self._translate_prompt_context(request)
        return self._run_stage_with_repair(
            request=request,
            stage="translate",
            context=context,
        )

    def critique(
        self, request: TranslationRequest, translated: TranslationOutput | CVTranslationOutput
    ) -> StageResult[CritiqueOutput]:
        context = self._critique_prompt_context(request, translated)
        return self._run_stage_with_repair(
            request=request,
            stage="critique",
            context=context,
        )

    def refine(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,
        critique: CritiqueOutput,
    ) -> StageResult[RefinementOutput]:
        context = self._refine_prompt_context(request, translated, critique)
        return self._run_stage_with_repair(
            request=request,
            stage="refine",
            context=context,
        )

    def run_translation_loop(self, request: TranslationRequest) -> OpenCodeProviderLoopResult:
        translate_result = self.translate(request)
        return self._run_quality_loop(
            request=request,
            current_translation=translate_result.payload,
            stage_results=[translate_result],
            allow_fallback_retranslate=False,
        )

    def run_revision_loop(
        self,
        request: TranslationRequest,
        existing_translation: TranslationOutput,
    ) -> OpenCodeProviderLoopResult:
        """Assess and revise an existing translation before falling back to retranslate."""

        return self._run_quality_loop(
            request=request,
            current_translation=existing_translation,
            stage_results=[],
            allow_fallback_retranslate=True,
        )

    @overload
    def _run_stage_with_repair(
        self,
        *,
        request: TranslationRequest,
        stage: Literal["translate"],
        context: Mapping[str, str],
    ) -> StageResult[TranslationOutput]: ...

    @overload
    def _run_stage_with_repair(
        self,
        *,
        request: TranslationRequest,
        stage: Literal["critique"],
        context: Mapping[str, str],
    ) -> StageResult[CritiqueOutput]: ...

    @overload
    def _run_stage_with_repair(
        self,
        *,
        request: TranslationRequest,
        stage: Literal["refine"],
        context: Mapping[str, str],
    ) -> StageResult[RefinementOutput]: ...

    def _run_stage_with_repair(
        self,
        *,
        request: TranslationRequest,
        stage: Literal["translate", "critique", "refine"],
        context: Mapping[str, str],
    ) -> StageResult[ProviderPayload]:
        post_slug = self._post_slug(request)
        prompt_version = request.prompt_version
        artifact_type = self._artifact_type(request)
        prompt_fingerprint = self._prompt_fingerprint(prompt_version, artifact_type=artifact_type)
        prompt_text = render_prompt_template(
            stage,
            context=context,
            prompt_version=prompt_version,
            artifact_type=artifact_type,
        )

        self._artifacts.write_prompt(
            post_slug,
            stage,
            prompt_text,
            prompt_version=prompt_version,
            prompt_fingerprint=prompt_fingerprint,
        )

        attach_path = self._resolve_attach_path(request)
        artifact_key = f"{artifact_type}:{post_slug}"
        start_stage_status(stage, artifact_key, _stage_launch_label(stage))
        try:
            stage_result = self._runner.run_stage(
                request=request,
                post_slug=post_slug,
                stage=stage,
                prompt_text=prompt_text,
                attach_path=attach_path,
                artifacts=self._artifacts,
            )
            self._artifacts.write_structured_response(
                post_slug,
                stage,
                _payload_to_dict(stage_result.payload),
            )
            finish_stage_status(
                stage,
                artifact_key,
                result=_stage_success_label(stage, stage_result.model),
            )
            return stage_result
        except ContractValidationError as exc:
            self._artifacts.write_error(post_slug, stage, str(exc))
            finish_stage_status(
                stage,
                artifact_key,
                error=_stage_invalid_label(stage, exc),
            )
            if self._max_schema_repairs == 0:
                raise

            repair_prompt = _build_schema_repair_prompt(
                stage=stage,
                invalid_prompt=prompt_text,
                validation_error=exc,
                artifact_type=artifact_type,
            )

            last_error: ContractValidationError = exc
            for repair_attempt in range(1, self._max_schema_repairs + 1):
                start_stage_status(
                    stage,
                    artifact_key,
                    f"launch schema repair ({repair_attempt}/{self._max_schema_repairs})",
                )
                try:
                    stage_result = self._runner.run_stage(
                        request=request,
                        post_slug=post_slug,
                        stage=stage,
                        prompt_text=repair_prompt,
                        attach_path=attach_path,
                        artifacts=self._artifacts,
                    )
                    self._artifacts.write_structured_response(
                        post_slug,
                        stage,
                        _payload_to_dict(stage_result.payload),
                    )
                    finish_stage_status(
                        stage,
                        artifact_key,
                        result="schema repair succeeded",
                    )
                    return stage_result
                except ContractValidationError as repair_exc:
                    last_error = repair_exc
                    self._artifacts.write_error(post_slug, stage, str(repair_exc))
                    finish_stage_status(
                        stage,
                        artifact_key,
                        error=f"schema repair failed: {repair_exc}",
                    )

            raise last_error
        except Exception as exc:
            finish_stage_status(stage, artifact_key, error=str(exc))
            raise

    def _post_slug(self, request: TranslationRequest) -> str:
        slug = str(request.metadata.get("slug", "")).strip()
        if slug:
            return slug
        return request.run_id

    def _resolve_attach_path(self, request: TranslationRequest) -> str:
        metadata_path = str(request.metadata.get("attach_path", "")).strip()
        if metadata_path:
            return metadata_path
        return self._default_attach_path

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

    def _artifact_type(self, request: TranslationRequest) -> str:
        artifact_type = str(request.metadata.get("artifact_type", "post")).strip().lower()
        return artifact_type or "post"

    def _base_prompt_context(self, request: TranslationRequest) -> dict[str, str]:
        metadata = request.metadata
        locale_defaults = get_default_locale_rules(
            source_locale=request.source_locale,
            target_locale=request.target_locale,
        )
        style_constraints = _merge_string_lists(
            locale_defaults["style_constraints"],
            metadata.get("style_constraints"),
        )
        glossary_entries = _merge_glossary_entries(
            locale_defaults["glossary"],
            metadata.get("glossary"),
        )
        do_not_translate_entities = _merge_string_lists(
            locale_defaults["do_not_translate_entities"],
            metadata.get("do_not_translate_entities"),
        )

        return {
            "source_locale": request.source_locale,
            "target_locale": request.target_locale,
            "locale_direction": str(
                metadata.get(
                    "locale_direction",
                    f"{request.source_locale}->{request.target_locale}",
                )
            ),
            "style_constraints": _format_style_constraints(style_constraints),
            "writing_style_brief": _format_writing_style_brief(
                metadata.get("writing_style_brief")
            ),
            "glossary_entries": _format_glossary(glossary_entries),
            "do_not_translate_entities": _format_entities(do_not_translate_entities),
            "source_markdown": request.source_text,
        }

    def _translate_prompt_context(self, request: TranslationRequest) -> dict[str, str]:
        return self._base_prompt_context(request)

    def _critique_prompt_context(
        self, request: TranslationRequest, translated: TranslationOutput | CVTranslationOutput
    ) -> dict[str, str]:
        context = self._base_prompt_context(request)
        context["translated_json"] = json.dumps(
            _payload_to_dict(translated),
            ensure_ascii=True,
            sort_keys=True,
            indent=2,
        )
        return context

    def _refine_prompt_context(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,
        critique: CritiqueOutput,
    ) -> dict[str, str]:
        context = self._critique_prompt_context(request, translated)
        context["critique_json"] = json.dumps(
            _payload_to_dict(critique),
            ensure_ascii=True,
            sort_keys=True,
            indent=2,
        )
        return context

    def _run_quality_loop(
        self,
        *,
        request: TranslationRequest,
        current_translation: TranslationOutput | CVTranslationOutput,
        stage_results: list[StageResult[ProviderPayload]],
        allow_fallback_retranslate: bool,
    ) -> OpenCodeProviderLoopResult:
        loops_completed = 0
        previous_score: float | None = None
        stagnant_loops = 0

        while loops_completed < self._thresholds.max_loops:
            critique_result = self.critique(request, current_translation)
            stage_results.append(critique_result)
            critique_payload = critique_result.payload

            score_delta = None
            if previous_score is not None:
                score_delta = critique_payload.score - previous_score
                if score_delta < self._thresholds.min_score_delta:
                    stagnant_loops += 1
                else:
                    stagnant_loops = 0

            decision = decide_score_action(
                RubricDecisionInput(
                    overall_score=critique_payload.score,
                    dimension_scores=critique_payload.dimension_scores,
                    critical_errors=critique_payload.critical_errors,
                    major_core_errors=critique_payload.major_core_errors,
                    confidence=critique_payload.confidence,
                    loops_completed=loops_completed,
                    score_delta=score_delta,
                    stagnant_loops=stagnant_loops,
                ),
                thresholds=self._thresholds,
            )
            artifact_key = f"{self._artifact_type(request)}:{self._post_slug(request)}"
            finish_stage_status(
                "critique",
                artifact_key,
                result=f"critique evaluated [{critique_result.model}]",
                extra_details=[
                    ("Score", f"{critique_payload.score:.1f}"),
                    (
                        "Needs refinement",
                        str(critique_payload.needs_refinement).lower(),
                    ),
                    ("Decision", decision),
                ],
            )

            if decision == "accept" and not critique_payload.needs_refinement:
                return OpenCodeProviderLoopResult(
                    final_translation=current_translation,
                    stage_results=stage_results,
                    loops_completed=loops_completed,
                    stop_reason="accepted",
                )

            if decision in {"fail", "escalate"}:
                if allow_fallback_retranslate:
                    translated = self.run_translation_loop(request)
                    return OpenCodeProviderLoopResult(
                        final_translation=translated.final_translation,
                        stage_results=stage_results + translated.stage_results,
                        loops_completed=loops_completed + translated.loops_completed,
                        stop_reason="fallback_retranslate",
                    )
                if decision == "fail":
                    raise OpenCodeProviderLoopError(
                        "Hard fail constraint triggered by critique policy"
                    )
                return OpenCodeProviderLoopResult(
                    final_translation=current_translation,
                    stage_results=stage_results,
                    loops_completed=loops_completed,
                    stop_reason="escalated",
                )

            refine_result = self.refine(request, current_translation, critique_payload)
            stage_results.append(refine_result)
            refine_payload = refine_result.payload

            if isinstance(refine_payload, CVTranslationOutput):
                current_translation = refine_payload
            else:
                current_translation = TranslationOutput(
                    title=refine_payload.title,
                    excerpt=refine_payload.excerpt,
                    tags=refine_payload.tags,
                    content=refine_payload.content,
                )
            loops_completed += 1
            previous_score = critique_payload.score

        if allow_fallback_retranslate:
            translated = self.run_translation_loop(request)
            return OpenCodeProviderLoopResult(
                final_translation=translated.final_translation,
                stage_results=stage_results + translated.stage_results,
                loops_completed=loops_completed + translated.loops_completed,
                stop_reason="fallback_retranslate",
            )

        return OpenCodeProviderLoopResult(
            final_translation=current_translation,
            stage_results=stage_results,
            loops_completed=loops_completed,
            stop_reason="max_loops_reached",
        )


def _build_schema_repair_prompt(
    *,
    stage: str,
    invalid_prompt: str,
    validation_error: ContractValidationError,
    artifact_type: str,
) -> str:
    schema_example = _SCHEMA_EXAMPLES[f"{artifact_type}_{stage}"] if artifact_type == "cv" else _SCHEMA_EXAMPLES[stage]
    return (
        "You must repair a schema-invalid response.\n"
        f"Stage: {stage}\n"
        f"Validation error: {validation_error}\n"
        "Return exactly one valid JSON object that satisfies this contract.\n"
        "Do not include markdown fences or extra keys.\n"
        "Required JSON shape:\n"
        f"{schema_example}\n\n"
        "Original stage instructions for semantic context:\n"
        f"{invalid_prompt}"
    )


def _payload_to_dict(payload: Any) -> dict[str, Any]:
    if hasattr(payload, "__dataclass_fields__"):
        return asdict(payload)
    if isinstance(payload, dict):
        return payload
    raise TypeError(f"Unsupported payload type for serialization: {type(payload)}")


def _format_style_constraints(raw_constraints: Any) -> str:
    if not isinstance(raw_constraints, list) or not raw_constraints:
        return "- Preserve technical precision and readability for the target locale"
    cleaned = [str(item).strip() for item in raw_constraints if str(item).strip()]
    if not cleaned:
        return "- Preserve technical precision and readability for the target locale"
    return "\n".join(f"- {item}" for item in cleaned)


def _format_writing_style_brief(raw_style_brief: Any) -> str:
    cleaned = str(raw_style_brief or "").strip()
    if not cleaned:
        return "- Preserve the author's voice without flattening tone or connective tissue."
    return cleaned


def _format_glossary(raw_glossary: Any) -> str:
    if not isinstance(raw_glossary, list) or not raw_glossary:
        return "- (none)"

    rendered: list[str] = []
    for entry in raw_glossary:
        if isinstance(entry, Mapping):
            source = str(entry.get("source", "")).strip()
            target = str(entry.get("target", "")).strip()
            if source and target:
                rendered.append(f"- {source} => {target}")
                continue
            rendered.append(f"- {json.dumps(dict(entry), sort_keys=True)}")
            continue
        cleaned = str(entry).strip()
        if cleaned:
            rendered.append(f"- {cleaned}")

    if not rendered:
        return "- (none)"
    return "\n".join(rendered)


def _format_entities(raw_entities: Any) -> str:
    if not isinstance(raw_entities, list) or not raw_entities:
        return "- (none)"

    rendered = [str(item).strip() for item in raw_entities if str(item).strip()]
    if not rendered:
        return "- (none)"
    return "\n".join(f"- {item}" for item in rendered)


def _merge_string_lists(default_items: list[Any], raw_items: Any) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for item in default_items:
        cleaned = str(item).strip()
        if cleaned and cleaned not in seen:
            merged.append(cleaned)
            seen.add(cleaned)

    if not isinstance(raw_items, list):
        return merged

    for item in raw_items:
        cleaned = str(item).strip()
        if cleaned and cleaned not in seen:
            merged.append(cleaned)
            seen.add(cleaned)
    return merged


def _merge_glossary_entries(default_entries: list[Any], raw_entries: Any) -> list[Any]:
    merged: list[Any] = []
    source_to_index: dict[str, int] = {}
    seen_strings: set[str] = set()

    for entry in default_entries:
        _append_or_override_glossary_entry(
            merged,
            source_to_index,
            seen_strings,
            entry,
        )

    if not isinstance(raw_entries, list):
        return merged

    for entry in raw_entries:
        _append_or_override_glossary_entry(
            merged,
            source_to_index,
            seen_strings,
            entry,
        )
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


def _stage_launch_label(stage: str) -> str:
    if stage == "translate":
        return "launch OpenCode Agent 1"
    if stage == "critique":
        return "launch Critique Agent"
    if stage == "refine":
        return "launch Refine Agent"
    return f"launch stage {stage}"


def _stage_success_label(stage: str, model: str) -> str:
    if stage == "translate":
        return f"Translation output received [{model}]"
    if stage == "critique":
        return f"Critique output received [{model}]"
    if stage == "refine":
        return f"Refine output received [{model}]"
    return f"Output received for {stage} [{model}]"


def _stage_invalid_label(stage: str, exc: ContractValidationError) -> str:
    return f"{stage} produced schema-invalid output: {exc}"
