"""Localization pipeline orchestration helpers."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import CVTranslationOutput, TranslationOutput, TranslationRequest
from .providers import OpenCodeProviderLoopResult, OpenCodeTranslationProvider


@dataclass(slots=True)
class LocalizationPipeline:
    """Thin orchestration layer around the provider stage graph."""

    provider: OpenCodeTranslationProvider

    def run(
        self,
        request: TranslationRequest,
        *,
        existing_translation: TranslationOutput | CVTranslationOutput | None = None,
    ) -> OpenCodeProviderLoopResult:
        return self.provider.run_translation_pipeline(
            request,
            existing_translation=existing_translation,
        )

