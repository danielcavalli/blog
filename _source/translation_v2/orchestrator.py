"""Build-facing translation_v2 orchestration for post translation only."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from markdown_refs import render_markdown_with_internal_refs
from translation_common import (
    sanitize_translation_html,
    sanitize_translation_text,
    validate_translation,
)


from .artifacts import TranslationRunArtifacts
from .cache_adapter import TranslationV2CacheAdapter
from .console import (
    fail_artifact_status,
    finish_artifact_status,
    log_block,
    start_artifact_status,
)
from .contracts import (
    CVEducationEntry,
    CVExperienceEntry,
    CVTranslationOutput,
    CritiqueOutput,
    RefinementOutput,
    StageResult,
    TranslationOutput,
    TranslationRequest,
)
from .mock_provider import DeterministicMockTranslationProvider
from .opencode_runner import OpenCodeHeadlessRunner
from .provider import TranslationProvider
from .prompt_registry import compute_prompt_pack_fingerprint
from .providers import OpenCodeTranslationProvider
from .revision_manifest import TranslationRevisionManifest
from .run_logging import TranslationRunEventLogger
from .style_loader import (
    compute_writing_style_fingerprint,
    load_writing_style_brief,
)
from .trigger import (
    build_post_finished_trigger_event,
    build_request_from_trigger_event,
)


def _to_dict(
    payload: TranslationOutput | CVTranslationOutput | CritiqueOutput | RefinementOutput | dict[str, Any],
) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    return asdict(payload)


class TranslationV2PostOrchestrator:
    """Orchestrates translation_v2 for build post translation with cache parity."""

    def __init__(
        self,
        *,
        provider_name: str,
        strict_validation: bool,
        cache_path: str | Path,
        prompt_version: str = "v1",
        mock_fixture_path: str | Path | None = None,
        run_id: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        self.provider_name = provider_name.strip().lower()
        self.strict_validation = bool(strict_validation)
        self.prompt_version = prompt_version
        self.cache = TranslationV2CacheAdapter(cache_path=cache_path)
        self.revision_manifest = TranslationRevisionManifest()
        self.run_id = run_id or datetime.now(timezone.utc).strftime("build-v2-%Y%m%d%H%M%S")
        self.correlation_id = correlation_id or self.run_id
        self.writing_style_brief = load_writing_style_brief()
        self.writing_style_fingerprint = compute_writing_style_fingerprint(
            self.writing_style_brief
        )
        self._prompt_fingerprint_cache: dict[str, str] = {}
        self.artifact_base_dir = Path(
            os.getenv("TRANSLATION_V2_ARTIFACT_BASE_DIR", "_cache/translation-runs")
        )
        self.artifacts = TranslationRunArtifacts(
            run_id=self.run_id,
            base_dir=self.artifact_base_dir,
        )
        self.artifact_run_dir = self.artifacts.run_dir
        self.event_logger = TranslationRunEventLogger(
            run_id=self.run_id,
            base_dir=self.artifact_base_dir,
        )

        if self.provider_name == "mock":
            if mock_fixture_path is None:
                env_fixture = os.getenv("TRANSLATION_V2_MOCK_FIXTURE", "").strip()
                if env_fixture:
                    mock_fixture_path = env_fixture
            if mock_fixture_path is None:
                raise ValueError(
                    "TRANSLATION_V2_MOCK_FIXTURE is required for translation provider 'mock'"
                )
            self.provider: TranslationProvider = (
                DeterministicMockTranslationProvider.from_fixture_file(mock_fixture_path)
            )
            self._model_id = "mock/deterministic-translation-v2"
            return

        if self.provider_name == "opencode":
            model_id = os.getenv("TRANSLATION_V2_MODEL", "openai/gpt-5.4").strip()
            attach_path = os.getenv("TRANSLATION_V2_ATTACH_PATH", "_source/posts")
            runner = OpenCodeHeadlessRunner(model_id=model_id)
            self.provider = OpenCodeTranslationProvider(
                runner=runner,
                artifacts=self.artifacts,
                default_attach_path=attach_path,
            )
            self._model_id = model_id
            return

        raise ValueError(
            f"Unsupported translation_v2 provider '{self.provider_name}'. Use 'opencode' or 'mock'."
        )

    def translate_if_needed(
        self,
        post: dict[str, Any],
        *,
        target_locale: str = "pt-br",
    ) -> dict[str, Any] | None:
        """Translate one post and return build-compatible translated payload."""
        source_locale = str(post.get("lang") or "en-us")
        if source_locale.lower() == target_locale.lower():
            return post

        content_to_translate = str(post.get("raw_content", post.get("content", "")))
        translation = self.translate_artifact_if_needed(
            slug=str(post.get("slug") or ""),
            source_text=content_to_translate,
            source_locale=source_locale,
            target_locale=target_locale,
            artifact_type="post",
            frontmatter={
                "title": post.get("title", ""),
                "excerpt": post.get("excerpt", ""),
                "tags": post.get("tags", []),
            },
        )

        translated_markdown = str(translation.get("content", ""))
        translated_post = post.copy()
        translated_post["lang"] = target_locale
        translated_post["title"] = sanitize_translation_text(
            str(translation.get("title", post.get("title", "")))
        )
        translated_post["excerpt"] = sanitize_translation_text(
            str(translation.get("excerpt", post.get("excerpt", "")))
        )
        translated_post["tags"] = [
            sanitize_translation_text(str(tag))
            for tag in translation.get("tags", post.get("tags", []))
        ]
        translated_post["raw_content"] = translated_markdown
        translated_post["content"] = sanitize_translation_html(
            render_markdown_with_internal_refs(translated_markdown)
        )

        if self.strict_validation:
            is_valid, issues = validate_translation(
                content_to_translate,
                translated_markdown,
                source_locale=source_locale,
                target_locale=target_locale,
            )
            if not is_valid:
                issue_text = "; ".join(issues) if issues else "unknown validation error"
                raise RuntimeError(f"translation_v2 strict validation failed: {issue_text}")

        return translated_post

    def translate_artifact_if_needed(
        self,
        *,
        slug: str,
        source_text: str,
        source_locale: str,
        target_locale: str,
        artifact_type: str,
        frontmatter: dict[str, Any] | None = None,
        attach_path: str | None = None,
        do_not_translate_entities: list[str] | None = None,
    ) -> dict[str, Any]:
        frontmatter = frontmatter or {"title": slug, "excerpt": "", "tags": []}
        prompt_fingerprint = self._prompt_fingerprint(artifact_type)
        cache_source = self._build_cache_source(
            source_text=source_text,
            frontmatter=frontmatter,
            source_locale=source_locale,
            target_locale=target_locale,
            artifact_type=artifact_type,
            prompt_fingerprint=prompt_fingerprint,
        )
        cached_record = self.cache.get_translation_record(
            slug=slug,
            source_text=cache_source,
            source_locale=source_locale.lower(),
            target_locale=target_locale.lower(),
            provider=self.provider_name,
            model=self._model_id,
            prompt_version=self.prompt_version,
        )

        trigger_event = build_post_finished_trigger_event(
            slug=slug,
            source_locale=source_locale,
            target_locale=target_locale,
            source_text=source_text,
            frontmatter=frontmatter,
            correlation_id=self.correlation_id,
            run_id=self.run_id,
        )
        request = build_request_from_trigger_event(
            event=trigger_event,
            prompt_version=self.prompt_version,
            attach_path=attach_path,
        )
        request.metadata["artifact_type"] = artifact_type
        request.metadata["writing_style_brief"] = self.writing_style_brief
        request.metadata["writing_style_fingerprint"] = self.writing_style_fingerprint
        request.metadata["prompt_fingerprint"] = prompt_fingerprint
        if do_not_translate_entities:
            request.metadata["do_not_translate_entities"] = list(do_not_translate_entities)
        self.artifacts.write_trigger_event(trigger_event.slug, trigger_event)

        revision_request = self.revision_manifest.get(slug=slug, target_locale=target_locale)
        request.metadata["revision_requested"] = revision_request is not None
        if revision_request is not None:
            request.metadata["revision_request"] = revision_request.payload
            request.metadata["revision_marker"] = revision_request.marker

        should_revise = self._should_revise(
            cached_record=cached_record,
            revision_marker=revision_request.marker if revision_request else None,
        )

        if cached_record is not None and not should_revise:
            log_block(
                f"translation_v2 {artifact_type}:{trigger_event.slug}",
                [
                    ("Cache", "hit"),
                    ("Action", "reuse cached translation"),
                    ("Result", "cache_hit"),
                ],
                indent=1,
            )
            translation = dict(cached_record.translation)
            outcome = "cache_hit"
        elif cached_record is not None:
            start_artifact_status(
                artifact_key=f"{artifact_type}:{trigger_event.slug}",
                title=f"translation_v2 {artifact_type}:{trigger_event.slug}",
                details=[
                    ("Cache", "stale"),
                    ("Action", "reassess cached translation"),
                    (
                        "Revision",
                        revision_request.marker if revision_request is not None else "requested",
                    ),
                ],
            )
            try:
                translation = self._revise_translation(
                    request,
                    cached_record.translation,
                    artifact_type=artifact_type,
                )
            except Exception as exc:
                fail_artifact_status(str(exc))
                raise
            self.cache.store_translation(
                source_text=cache_source,
                source_locale=source_locale.lower(),
                target_locale=target_locale.lower(),
                provider=self.provider_name,
                model=self._model_id,
                prompt_version=self.prompt_version,
                translation=translation,
                metadata=self._cache_metadata(
                    workflow="revision",
                    revision_marker=revision_request.marker if revision_request else None,
                    revised_from_cache_source=cached_record.source,
                    artifact_type=artifact_type,
                    prompt_fingerprint=prompt_fingerprint,
                ),
            )
            outcome = "revision"
        else:
            start_artifact_status(
                artifact_key=f"{artifact_type}:{trigger_event.slug}",
                title=f"translation_v2 {artifact_type}:{trigger_event.slug}",
                details=[
                    ("Cache", "miss"),
                    ("Action", "launch translation pipeline"),
                ],
            )
            try:
                translation = self._run_pipeline(request, artifact_type=artifact_type)
            except Exception as exc:
                fail_artifact_status(str(exc))
                raise
            self.cache.store_translation(
                source_text=cache_source,
                source_locale=source_locale.lower(),
                target_locale=target_locale.lower(),
                provider=self.provider_name,
                model=self._model_id,
                prompt_version=self.prompt_version,
                translation=translation,
                metadata=self._cache_metadata(
                    workflow="translate",
                    revision_marker=revision_request.marker if revision_request else None,
                    revised_from_cache_source=None,
                    artifact_type=artifact_type,
                    prompt_fingerprint=prompt_fingerprint,
                ),
            )
            outcome = "cache_miss"

        self.event_logger.emit_stage_event(
            post_slug=trigger_event.slug,
            stage="trigger_dispatch",
            attempt=1,
            model=self.provider_name,
            duration_ms=0,
            outcome=outcome,
            metadata={
                "schema_version": trigger_event.schema_version,
                "idempotency_key": trigger_event.idempotency_key,
                "correlation_id": trigger_event.correlation_id,
                "build_run_id": trigger_event.run_id,
                "request_run_id": request.run_id,
                "artifact_type": artifact_type,
                "revision_requested": revision_request is not None,
                "revision_marker": revision_request.marker if revision_request else None,
            },
        )
        if outcome in {"cache_miss", "revision"}:
            finish_artifact_status(outcome)

        return translation

    def _build_cache_source(
        self,
        *,
        source_text: str,
        frontmatter: dict[str, Any],
        source_locale: str,
        target_locale: str,
        artifact_type: str,
        prompt_fingerprint: str,
    ) -> str:
        stable_frontmatter = json.dumps(frontmatter, ensure_ascii=False, sort_keys=True)
        return (
            source_text
            + stable_frontmatter
            + f"|{source_locale.lower()}|{target_locale.lower()}|artifact={artifact_type}"
            + f"|prompt_fingerprint={prompt_fingerprint}"
            + f"|writing_style_fingerprint={self.writing_style_fingerprint}"
        )

    def _prompt_fingerprint(self, artifact_type: str) -> str:
        fingerprint = self._prompt_fingerprint_cache.get(artifact_type)
        if fingerprint is None:
            fingerprint = compute_prompt_pack_fingerprint(
                prompt_version=self.prompt_version,
                artifact_type=artifact_type,
            )
            self._prompt_fingerprint_cache[artifact_type] = fingerprint
        return fingerprint

    def _run_pipeline(self, request: TranslationRequest, *, artifact_type: str) -> dict[str, Any]:
        if isinstance(self.provider, OpenCodeTranslationProvider):
            loop_result = self.provider.run_translation_loop(request)
            return _to_dict(loop_result.final_translation)

        translated_stage = self.provider.translate(request)
        translated_payload = translated_stage.payload
        if not isinstance(translated_payload, (TranslationOutput, CVTranslationOutput)):
            raise TypeError("translate stage did not return a supported translation payload")

        critique_stage = self.provider.critique(request, translated_payload)
        critique_payload = critique_stage.payload
        if not isinstance(critique_payload, CritiqueOutput):
            raise TypeError("critique stage did not return CritiqueOutput")

        if not critique_payload.needs_refinement:
            return _to_dict(translated_payload)

        refined_stage = self.provider.refine(request, translated_payload, critique_payload)
        return _to_dict(refined_stage.payload)

    def _revise_translation(
        self,
        request: TranslationRequest,
        existing_translation: dict[str, Any],
        *,
        artifact_type: str,
    ) -> dict[str, Any]:
        if artifact_type == "cv":
            existing_output: TranslationOutput | CVTranslationOutput = CVTranslationOutput(
                name=str(existing_translation.get("name", "")),
                tagline=str(existing_translation.get("tagline", "")),
                location=str(existing_translation.get("location", "")),
                contact={k: str(v) for k, v in existing_translation.get("contact", {}).items()},
                skills=[str(item) for item in existing_translation.get("skills", [])],
                languages_spoken=[
                    str(item) for item in existing_translation.get("languages_spoken", [])
                ],
                summary=str(existing_translation.get("summary", "")),
                experience=[
                    CVExperienceEntry(
                        title=str(item.get("title", "")),
                        company=str(item.get("company", "")),
                        location=str(item.get("location", "")),
                        period=str(item.get("period", "")),
                        description=str(item.get("description", "")),
                        achievements=[str(x) for x in item.get("achievements", [])],
                    )
                    for item in existing_translation.get("experience", [])
                ],
                education=[
                    CVEducationEntry(
                        degree=str(item.get("degree", "")),
                        school=str(item.get("school", "")),
                        period=str(item.get("period", "")),
                    )
                    for item in existing_translation.get("education", [])
                ],
            )
        else:
            existing_output = TranslationOutput(
                title=str(existing_translation.get("title", "")),
                excerpt=str(existing_translation.get("excerpt", "")),
                tags=[str(tag) for tag in existing_translation.get("tags", [])],
                content=str(existing_translation.get("content", "")),
            )

        if isinstance(self.provider, OpenCodeTranslationProvider):
            loop_result = self.provider.run_revision_loop(request, existing_output)
            return _to_dict(loop_result.final_translation)

        critique_stage = self.provider.critique(request, existing_output)
        critique_payload = critique_stage.payload
        if not isinstance(critique_payload, CritiqueOutput):
            raise TypeError("critique stage did not return CritiqueOutput")
        if not critique_payload.needs_refinement:
            return _to_dict(existing_output)

        refined_stage = self.provider.refine(request, existing_output, critique_payload)
        return _to_dict(refined_stage.payload)

    def _should_revise(
        self,
        *,
        cached_record: Any,
        revision_marker: str | None,
    ) -> bool:
        if cached_record is None:
            return False
        if getattr(cached_record, "is_legacy", False):
            return True
        cached_marker = None
        metadata = getattr(cached_record, "metadata", None)
        if isinstance(metadata, dict):
            cached_marker = metadata.get("revision_marker")
        return revision_marker is not None and cached_marker != revision_marker

    def _cache_metadata(
        self,
        *,
        workflow: str,
        revision_marker: str | None,
        revised_from_cache_source: str | None,
        artifact_type: str,
        prompt_fingerprint: str,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "workflow": workflow,
            "writing_style_fingerprint": self.writing_style_fingerprint,
            "artifact_type": artifact_type,
            "prompt_fingerprint": prompt_fingerprint,
        }
        if revision_marker is not None:
            metadata["revision_marker"] = revision_marker
        if revised_from_cache_source is not None:
            metadata["revised_from_cache_source"] = revised_from_cache_source
        return metadata
