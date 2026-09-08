"""Explicit localization updates backed by accepted revisions and stage checkpoints."""

from __future__ import annotations

import os
from dataclasses import asdict
from datetime import datetime, timezone
from functools import cached_property
from pathlib import Path
from typing import Any
from uuid import uuid4

from .artifacts import TranslationRunArtifacts
from .contracts import TranslationRequest
from .durable import DurableTranslationRuntime
from .opencode_runner import DEFAULT_MODEL_ID, OpenCodeHeadlessRunner
from .prompt_registry import compute_localization_prompt_fingerprint
from .providers.opencode import OpenCodeTranslationProvider
from .revision_manifest import TranslationRevisionManifest
from .style_loader import compute_writing_style_fingerprint, load_writing_style_brief


class TranslationV2PostOrchestrator:
    """Localize uncached source with an unattended, guidance-driven agent."""

    provider_name = "opencode"

    def __init__(
        self,
        *,
        strict_validation: bool,
        cache_dir: str | Path,
        accepted_path: str | Path,
        prompt_version: str = "v2",
        run_id: str | None = None,
        correlation_id: str | None = None,
        refresh: bool = False,
    ) -> None:
        cache_dir = Path(cache_dir)
        self.strict_validation = strict_validation
        self.prompt_version = prompt_version
        self.durable = DurableTranslationRuntime(self, accepted_path, refresh=refresh)
        self.revision_manifest = TranslationRevisionManifest()
        self.run_id = run_id or (
            datetime.now(timezone.utc).strftime("build-v2-%Y%m%d%H%M%S-") + uuid4().hex[:12]
        )
        self.correlation_id = correlation_id or self.run_id
        self._prompt_fingerprint_cache: dict[str, str] = {}
        self.artifacts = TranslationRunArtifacts(
            run_id=self.run_id,
            base_dir=os.getenv("TRANSLATION_V2_ARTIFACT_BASE_DIR", str(cache_dir / "translation-runs")),
        )
        self._model_id = os.getenv("TRANSLATION_V2_TRANSLATION_MODEL", DEFAULT_MODEL_ID).strip()
        translation_runner = OpenCodeHeadlessRunner(model_id=self._model_id, reasoning_effort="high")
        self.provider = OpenCodeTranslationProvider(
            runner=translation_runner,
            artifacts=self.artifacts,
            default_attach_path=os.getenv("TRANSLATION_V2_ATTACH_PATH", "_source/posts"),
            checkpoint_dir=str(cache_dir / "translation-stages"),
        )

    @cached_property
    def writing_style_brief(self) -> str:
        return load_writing_style_brief()

    @cached_property
    def writing_style_fingerprint(self) -> str:
        return compute_writing_style_fingerprint(self.writing_style_brief)

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
        return self.durable.resolve(
            slug=slug, source_text=source_text, source_locale=source_locale,
            target_locale=target_locale, artifact_type=artifact_type,
            frontmatter=frontmatter, attach_path=attach_path,
            do_not_translate_entities=do_not_translate_entities,
        )

    def _prompt_fingerprint(self, artifact_type: str) -> str:
        if artifact_type not in self._prompt_fingerprint_cache:
            self._prompt_fingerprint_cache[artifact_type] = compute_localization_prompt_fingerprint(
                prompt_version=self.prompt_version, artifact_type=artifact_type,
            )
        return self._prompt_fingerprint_cache[artifact_type]

    def _run_pipeline(
        self, request: TranslationRequest, *, existing_translation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        self.last_pipeline_result = self.provider.run_translation_pipeline(
            request, existing_translation=existing_translation,
        )
        return asdict(self.last_pipeline_result.final_translation)
