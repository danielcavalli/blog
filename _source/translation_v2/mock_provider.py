"""Deterministic mock provider for translation_v2 tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from .contracts import (
    CritiqueOutput,
    RefinementOutput,
    StageResult,
    TranslationOutput,
    TranslationRequest,
    validate_critique_output,
    validate_refinement_output,
    validate_translation_output,
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

    def translate(self, request: TranslationRequest) -> StageResult[TranslationOutput]:
        fixture = self._fixture_for_request(request)
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
        self, request: TranslationRequest, translated: TranslationOutput
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

    def refine(
        self,
        request: TranslationRequest,
        translated: TranslationOutput,
        critique: CritiqueOutput,
    ) -> StageResult[RefinementOutput]:
        fixture = self._fixture_for_request(request)
        refined_payload = validate_refinement_output(
            fixture["refined"], run_id=request.run_id, stage="refine"
        )
        result: StageResult[RefinementOutput] = StageResult(
            run_id=request.run_id,
            stage="refine",
            model=self._model,
            payload=refined_payload,
            raw_response={"fixture_slug": request.metadata.get("slug", "")},
        )
        return result
