"""Resolve accepted artifacts independently of the execution cache."""

from __future__ import annotations

from typing import Any
from dataclasses import asdict
from collections import Counter

from presentation_translation import (
    compare_presentation_translation_invariants,
    extract_markdown_destinations,
)
from translation_common import validate_translation

from .accepted import AcceptedTranslations, digest, source_identity
from .contracts import validate_cv_translation_output, validate_translation_output
from .locale_rules import get_default_locale_rules
from .errors import ContractValidationError
from .protected_markdown import protected_fences, footnote_identity
from .trigger import build_post_finished_trigger_event, build_request_from_trigger_event


def validate_artifact(source: dict[str, Any], translation: dict[str, Any], *, strict: bool) -> None:
    kind = source["artifact_type"]
    if kind == "cv":
        validate_cv_translation_output(translation, run_id="accept", stage="translate")
        import json

        original = json.loads(source["text"])
        for field in ("experience", "education", "skills", "languages_spoken"):
            if len(original.get(field, [])) != len(translation.get(field, [])):
                raise RuntimeError(f"CV translation changed the number of {field} entries")
        if original.get("contact") != translation.get("contact"):
            raise RuntimeError("CV translation changed contact details")
        return
    validate_translation_output(translation, run_id="accept", stage="translate")
    content = translation["content"]
    if footnote_identity(source["text"]) != footnote_identity(content):
        raise RuntimeError("Translation changed footnote identifiers or reference counts")
    if not content.strip():
        raise RuntimeError("Cannot accept an empty translation")
    if kind == "about":

        def paragraphs(text):
            parts = [p.strip() for p in text.split("\n\n") if p.strip()]
            return parts[1:] if parts and parts[0].startswith("# ") else parts

        if len(paragraphs(source["text"])) != len(paragraphs(content)):
            raise RuntimeError("About translation changed the paragraph count")
    if kind == "presentation":
        issues = compare_presentation_translation_invariants(source["text"], content)
        if issues:
            raise RuntimeError("; ".join(str(issue) for issue in issues))
    else:
        if protected_fences(source["text"]) != protected_fences(content):
            raise RuntimeError("Translation changed protected fenced code")
        if Counter(extract_markdown_destinations(source["text"])) != Counter(
            extract_markdown_destinations(content)
        ):
            raise RuntimeError("Translation changed protected link destinations")
        if strict:
            valid, issues = validate_translation(
                source["text"],
                content,
                source_locale=source["source_locale"],
                target_locale=source["target_locale"],
            )
            if not valid:
                raise RuntimeError("; ".join(issues))


class DurableTranslationRuntime:
    def __init__(self, owner: Any, root, *, refresh: bool):
        self.owner = owner
        self.store = AcceptedTranslations(root)
        self.refresh = refresh

    def resolve(
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
        owner = self.owner
        source = source_identity(
            slug=slug,
            source_text=source_text,
            source_locale=source_locale,
            target_locale=target_locale,
            artifact_type=artifact_type,
            frontmatter=frontmatter or {"title": slug, "excerpt": "", "tags": []},
        )
        current = self.store.current(source)
        same_source = current is not None and current["source_hash"] == digest(source)
        revision = owner.revision_manifest.get(slug=slug, target_locale=target_locale)
        pending_revision = revision is not None and (
            current is None or current["provenance"].get("revision_marker") != revision.marker
        )
        if (
            current is not None
            and same_source
            and not (self.refresh or pending_revision)
        ):
            validate_artifact(source, current["translation"], strict=owner.strict_validation)
            return dict(current["translation"])

        event = build_post_finished_trigger_event(
            slug=slug,
            source_locale=source_locale,
            target_locale=target_locale,
            source_text=source_text,
            frontmatter=source["frontmatter"],
            correlation_id=owner.correlation_id,
            run_id=owner.run_id,
        )
        request = build_request_from_trigger_event(
            event=event,
            prompt_version=owner.prompt_version,
            attach_path=attach_path,
        )
        request.metadata.update(
            {
                "artifact_type": artifact_type,
                "writing_style_brief": owner.writing_style_brief,
                "revision_request": revision.payload if revision else {},
                "previous_source": current["source"] if current and not same_source else {},
                "do_not_translate_entities": do_not_translate_entities or [],
            }
        )
        if current:
            try:
                validate_artifact(source, current["translation"], strict=owner.strict_validation)
            except (RuntimeError, ContractValidationError) as exc:
                request.metadata["deterministic_findings"] = str(exc)
        owner.artifacts.write_trigger_event(slug, event)
        recipe = {
            "provider": owner.provider_name,
            "translation_model": owner._model_id,
            "critique_model": getattr(owner, "_critique_model_id", owner._model_id),
            "revision_model": getattr(owner, "_revision_model_id", owner._model_id),
            "reasoning_effort": "high",
            "prompt_version": owner.prompt_version,
            "prompt_fingerprint": owner._prompt_fingerprint(artifact_type),
            "writing_style_fingerprint": owner.writing_style_fingerprint,
            "locale_policy_fingerprint": digest(
                get_default_locale_rules(
                    source_locale=source_locale,
                    target_locale=target_locale,
                )
            ),
            "revision_marker": revision.marker if revision else None,
            "run_id": owner.run_id,
        }
        translation = owner._run_pipeline(
            request, existing_translation=current["translation"] if current else None,
        )
        try:
            validate_artifact(source, translation, strict=owner.strict_validation)
        except (RuntimeError, ContractValidationError) as exc:
            # One bounded editorial repair, with the exact deterministic finding.
            # Never accept a shape/identity failure or silently weaken a gate.
            request.metadata["deterministic_findings"] = str(exc)
            translation = owner._run_pipeline(request, existing_translation=translation)
            validate_artifact(source, translation, strict=owner.strict_validation)
        result = getattr(owner, "last_pipeline_result", None)
        if result is not None:
            recipe["editorial_review"] = asdict(result.stage_results[-1].payload)
            recipe["stage_models"] = {stage.stage: stage.model for stage in result.stage_results}
        self.store.accept(
            source=source, translation=translation, provenance=recipe,
            expected_revision=digest(current) if current else None,
        )
        return translation
