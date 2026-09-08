"""OpenCode-backed localization provider for translation_v2."""

from __future__ import annotations

import json
import inspect
from time import monotonic
from ..checkpoints import StageCheckpoints
from ..run_logging import TranslationRunEventLogger
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from typing import Any, Protocol, Literal, overload

from ..artifacts import TranslationRunArtifacts
from ..console import finish_stage_status, start_stage_status
from ..contracts import (
    CVTranslationOutput,
    ProviderPayload,
    StageResult,
    TerminologyPolicyPacket,
    TranslationOutput,
    TranslationRequest,
    VoiceIntentPacket,
)
from ..errors import ContractValidationError
from ..locale_rules import get_default_locale_rules
from ..prompt_registry import compute_localization_prompt_fingerprint, render_prompt_template
from ..terminology_policy import (
    build_translation_policy_context,
)


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


class OpenCodeTranslationProvider:
    """An unattended writer governed by source and committed localization guidance."""

    def __init__(
        self, *, runner: OpenCodeRunnerLike, artifacts: TranslationRunArtifacts,
        default_attach_path: str, checkpoint_dir: str | None = None,
    ) -> None:
        self._translation_runner = runner
        self._artifacts = artifacts
        self._default_attach_path = default_attach_path
        self._fingerprint_cache: dict[str, str] = {}
        self._checkpoints = StageCheckpoints(checkpoint_dir) if checkpoint_dir else None
        self._events = TranslationRunEventLogger(artifacts.run_id, artifacts.base_dir)

    def run_translation_pipeline(
        self, request: TranslationRequest, *,
        existing_translation: TranslationOutput | CVTranslationOutput | dict[str, Any] | None = None,
    ) -> OpenCodeProviderLoopResult:
        """Localize once; the durable runtime owns validation and bounded repair."""
        if existing_translation is not None and (
            request.metadata.get("revision_request") or request.metadata.get("deterministic_findings")
        ):
            request.metadata["previous_translation"] = (
                existing_translation if isinstance(existing_translation, dict)
                else _payload_to_dict(existing_translation)
            )
        result = self.localize(request)
        return OpenCodeProviderLoopResult(result.payload, [result], 1, "localized")

    def localize(self, request: TranslationRequest) -> StageResult[TranslationOutput | CVTranslationOutput]:
        """Run the unattended writer directly against source and committed guidance."""
        return self._run_stage_with_repair(
            runner=self._translation_runner, request=request, stage="translate",
            context=self._translation_context(request, source_analysis=None, terminology_policy=None),
        )


    @overload
    def _run_stage_with_repair(self, *, runner: OpenCodeRunnerLike,
        request: TranslationRequest, stage: Literal["translate"], context: Mapping[str, str],
        pass_name: str | None = None) -> StageResult[TranslationOutput | CVTranslationOutput]: ...


    @overload
    def _run_stage_with_repair(self, *, runner: OpenCodeRunnerLike,
        request: TranslationRequest, stage: str, context: Mapping[str, str],
        pass_name: str | None = None) -> StageResult[ProviderPayload]: ...

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
        prompt_text = (
            "UNATTENDED LOCALIZATION AGENT\n"
            "Complete the localization using the supplied source and official repository "
            "locale guidance. Do not ask questions, request approval, or propose next steps. "
            "Check your text against the guidance before returning the completed artifact.\n\n"
            "LOCALIZATION AUTHORITY\n"
            "The source controls meaning. The human-written localization brief and locale "
            "rules control target-language expression. Explicit owner instructions and "
            "protected source material remain binding. Writing references describe the "
            "author's voice; their English examples are not Portuguese sentence templates.\n"
            "Keep parenthetical asides in parentheses around the same thought, with their "
            "contents localized. Do not replace them with commas or dashes or absorb them into "
            "the main assertion. Preserve the author's conviction, irritation, enthusiasm, "
            "irony, and deliberate rhetorical punctuation; do not add hedges or sober up "
            "a personal voice.\n\n"
            + prompt_text
        )
        # Carry owner instructions and exact frontmatter through every stage.
        # These are part of the rendered prompt, so checkpoint identity covers them.
        supplement = {
            "source_frontmatter": {key: request.metadata.get(key, "" if key != "tags" else [])
                                   for key in ("title", "excerpt", "tags")},
            "owner_revision_instructions": request.metadata.get("revision_request", {}),
            "previous_translation": request.metadata.get("previous_translation", {}),
            "deterministic_validation_findings": request.metadata.get("deterministic_findings", ""),
        }
        prompt_text += (
            "\n\nLOCALIZATION BOUNDARY\n"
            "The source is already authored and is authoritative. Writing guidance describes "
            "the rules behind it; it is context for understanding the author, not an instruction "
            "to edit, reorganize, shorten, expand, or improve the source. Preserve its argument, "
            "section order, emphasis, qualifications, evidence, and humor. Use the target-locale "
            "references to rebuild sentences naturally when necessary to preserve their effect. "
            "Do not impose an authoring checklist on the translation or repair perceived "
            "editorial shortcomings. Revision instructions apply to the localized artifact.\n"
            "\nARTIFACT CONTEXT AND OWNER REVISION INSTRUCTIONS\n"
            "Use the exact source frontmatter when translating title, excerpt and tags. "
            "Apply supplied corrections and resolve deterministic validation findings. "
            "Preserve exact source code and link destinations.\n"
            + json.dumps(supplement, ensure_ascii=False, sort_keys=True, indent=2)
        )
        if "mermaid" in request.source_text:
            prompt_text += (
                "\nFor Mermaid flowcharts, localize visible node/edge labels and "
                "accessibility text. Preserve graph identifiers, edges, shapes, directives, "
                "configuration, embedded HTML markup, and link destinations.\n"
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
        started = monotonic()
        model = getattr(runner, "model_id", type(runner).__name__)
        checkpoint_key = None
        if self._checkpoints:
            checkpoint_key = self._checkpoints.key(
                stage=stage, prompt=prompt_text, model=model,
                reasoning=getattr(runner, "reasoning_effort", "high"),
            )
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
            result = self._checkpoints.load(
                checkpoint_key, request=request, stage=stage, model=model,
            ) if self._checkpoints is not None and checkpoint_key else None
            outcome = "resumed" if result is not None else "completed"
            if result is None:
                try:
                    result = runner.run_stage(**runner_kwargs)
                except ContractValidationError as exc:
                    self._artifacts.write_error(post_slug, stage, str(exc), pass_name=pass_name)
                    repair_pass = f"{pass_name or 'initial'}-schema-repair"
                    repaired_prompt = prompt_text + (
                        "\n\nSCHEMA CORRECTION\nThe previous response failed validation: "
                        + str(exc)
                        + "\nReturn the complete response with the exact required JSON schema. "
                        "Preserve the editorial work; correct the response shape."
                    )
                    self._artifacts.write_prompt(post_slug, stage, repaired_prompt, pass_name=repair_pass)
                    runner_kwargs["prompt_text"] = repaired_prompt
                    if "pass_name" in inspect.signature(runner.run_stage).parameters:
                        runner_kwargs["pass_name"] = repair_pass
                    result = runner.run_stage(**runner_kwargs)
                if self._checkpoints is not None and checkpoint_key:
                    self._checkpoints.save(checkpoint_key, result)
            self._events.emit_stage_event(
                post_slug=post_slug, stage=stage, attempt=1, model=model,
                duration_ms=int((monotonic() - started) * 1000), outcome=outcome,
                metadata={"pass": pass_name, "checkpoint": checkpoint_key},
            )
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
            self._events.emit_stage_event(
                post_slug=post_slug, stage=stage, attempt=2, model=model,
                duration_ms=int((monotonic() - started) * 1000), outcome="schema_failed",
                metadata={"pass": pass_name, "error": str(exc)},
            )
            self._artifacts.write_error(post_slug, stage, str(exc), pass_name=pass_name)
            finish_stage_status(stage, artifact_key, error=_stage_invalid_label(stage, exc))
            raise
        except Exception as exc:
            self._events.emit_stage_event(
                post_slug=post_slug, stage=stage, attempt=1, model=model,
                duration_ms=int((monotonic() - started) * 1000), outcome="failed",
                metadata={"pass": pass_name, "error": str(exc)},
            )
            self._artifacts.write_error(post_slug, stage, str(exc), pass_name=pass_name)
            finish_stage_status(stage, artifact_key, error=str(exc))
            raise

    def _translation_context(
        self,
        request: TranslationRequest,
        *,
        source_analysis: VoiceIntentPacket | None,
        terminology_policy: TerminologyPolicyPacket | None,
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
            fingerprint = compute_localization_prompt_fingerprint(
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


def _stage_launch_label(stage: str) -> str:
    labels = {
        "source_analysis": "analyze source voice and rhetoric",
        "terminology_policy": "derive terminology and borrowing policy",
        "translate": "generate localized draft",
        "critique": "editorial critique pass",
        "revise": "localize against source and locale guidance",
        "final_review": "independent source and locale review",
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
