"""Provider abstraction for translation_v2 execution backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .contracts import (
    CVTranslationOutput,
    CritiqueOutput,
    FinalReviewOutput,
    RevisionOutput,
    StageResult,
    TerminologyPolicyPacket,
    TranslationOutput,
    TranslationRequest,
    VoiceIntentPacket,
)


class TranslationProvider(ABC):
    """Backend interface for localization-focused v2 stage execution."""

    @abstractmethod
    def source_analysis(self, request: TranslationRequest) -> StageResult[VoiceIntentPacket]:
        """Analyze source rhetoric and authorial intent."""

    @abstractmethod
    def terminology_policy(
        self,
        request: TranslationRequest,
        source_analysis: VoiceIntentPacket,
    ) -> StageResult[TerminologyPolicyPacket]:
        """Build artifact-wide terminology and borrowing policy."""

    @abstractmethod
    def translate(
        self,
        request: TranslationRequest,
        source_analysis: VoiceIntentPacket,
        terminology_policy: TerminologyPolicyPacket,
    ) -> StageResult[TranslationOutput | CVTranslationOutput]:
        """Run localized draft generation."""

    @abstractmethod
    def critique(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,
        *,
        source_analysis: VoiceIntentPacket | None = None,
        terminology_policy: TerminologyPolicyPacket | None = None,
    ) -> StageResult[CritiqueOutput]:
        """Run editorial critique over a localized draft."""

    @abstractmethod
    def revise(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,
        critique: CritiqueOutput,
        *,
        source_analysis: VoiceIntentPacket | None = None,
        terminology_policy: TerminologyPolicyPacket | None = None,
    ) -> StageResult[RevisionOutput | CVTranslationOutput]:
        """Run revision stage and return structured revised output."""

    @abstractmethod
    def final_review(
        self,
        request: TranslationRequest,
        translated: TranslationOutput | CVTranslationOutput,
        *,
        source_analysis: VoiceIntentPacket | None = None,
        terminology_policy: TerminologyPolicyPacket | None = None,
    ) -> StageResult[FinalReviewOutput]:
        """Run final review and acceptance decision."""


ProviderPayload = (
    VoiceIntentPacket
    | TerminologyPolicyPacket
    | TranslationOutput
    | CVTranslationOutput
    | CritiqueOutput
    | RevisionOutput
    | FinalReviewOutput
)
