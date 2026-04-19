"""Provider abstraction for translation_v2 execution backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import (
    CVTranslationOutput,
    CritiqueOutput,
    RefinementOutput,
    StageResult,
    TranslationOutput,
    TranslationRequest,
)


class TranslationProvider(ABC):
    """Backend interface for translate -> critique -> refine stages."""

    @abstractmethod
    def translate(
        self, request: TranslationRequest
    ) -> StageResult[TranslationOutput | CVTranslationOutput]:
        """Run translation stage and return structured output."""

    @abstractmethod
    def critique(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,
    ) -> StageResult[CritiqueOutput]:
        """Run critique stage and return structured critique payload."""

    @abstractmethod
    def refine(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,
        critique: CritiqueOutput,
    ) -> StageResult[RefinementOutput | CVTranslationOutput]:
        """Run refinement stage and return structured refinement payload."""


ProviderPayload = TranslationOutput | CVTranslationOutput | CritiqueOutput | RefinementOutput
