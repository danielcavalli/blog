"""Tests for revision manifest routing and legacy translation upgrade behavior."""

from __future__ import annotations

import json
import os
import sys


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from translation_v2.cache_adapter import TranslationV2CacheAdapter, compute_source_hash  # noqa: E402
from translation_v2.contracts import CritiqueOutput, RefinementOutput, StageResult  # noqa: E402
from translation_v2.orchestrator import TranslationV2PostOrchestrator  # noqa: E402
from translation_v2.prompt_registry import compute_prompt_pack_fingerprint  # noqa: E402
from translation_v2.revision_manifest import TranslationRevisionManifest  # noqa: E402
from translation_v2.style_loader import (  # noqa: E402
    compute_writing_style_fingerprint,
    load_writing_style_brief,
)
from translation_v2.voice_profile import (  # noqa: E402
    compute_author_voice_fingerprint,
    load_author_voice_profile,
)


class _FakeRevisionProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def critique(self, request, translated):  # noqa: ANN001
        self.calls.append("critique")
        return StageResult(
            run_id=request.run_id,
            stage="critique",
            model="fake/model",
            payload=CritiqueOutput(
                score=82.0,
                feedback="Tighten tone and fix stale wording",
                needs_refinement=True,
                findings=["major: stale wording"],
                dimension_scores={
                    "accuracy_completeness": 82.0,
                    "terminology_entities": 90.0,
                    "markdown_code_link_fidelity": 95.0,
                },
                critical_errors=0,
                major_core_errors=1,
                confidence=0.9,
            ),
        )

    def refine(self, request, translated, critique):  # noqa: ANN001
        self.calls.append("refine")
        return StageResult(
            run_id=request.run_id,
            stage="refine",
            model="fake/model",
            payload=RefinementOutput(
                title="Titulo revisado",
                excerpt="Resumo revisado",
                tags=["ia"],
                content="Conteudo revisado",
                applied_feedback=["fixed stale wording"],
            ),
        )

    def translate(self, request):  # noqa: ANN001
        raise AssertionError("translate should not run during legacy revision path")


class _NoOpProvider:
    def critique(self, request, translated):  # noqa: ANN001
        raise AssertionError("provider should not be called on satisfied revision marker")

    def refine(self, request, translated, critique):  # noqa: ANN001
        raise AssertionError("provider should not be called on satisfied revision marker")

    def translate(self, request):  # noqa: ANN001
        raise AssertionError("provider should not be called on satisfied revision marker")


def _post() -> dict[str, object]:
    return {
        "title": "Original title",
        "excerpt": "Original excerpt",
        "tags": ["AI"],
        "slug": "post-one",
        "lang": "en-us",
        "raw_content": "Original markdown body",
        "content": "<p>Original markdown body</p>",
    }


def _cache_source(post: dict[str, object]) -> str:
    frontmatter = {
        "title": post["title"],
        "excerpt": post["excerpt"],
        "tags": post["tags"],
    }
    prompt_fingerprint = compute_prompt_pack_fingerprint(
        prompt_version="v1",
        artifact_type="post",
    )
    writing_style_fingerprint = compute_writing_style_fingerprint(load_writing_style_brief())
    author_voice_fingerprint = compute_author_voice_fingerprint(load_author_voice_profile())
    return (
        str(post["raw_content"])
        + json.dumps(frontmatter, ensure_ascii=False, sort_keys=True)
        + "|en-us|pt-br|artifact=post"
        + f"|prompt_fingerprint={prompt_fingerprint}"
        + f"|writing_style_fingerprint={writing_style_fingerprint}"
        + f"|author_voice_fingerprint={author_voice_fingerprint}"
    )


def test_revision_manifest_resolves_locale_specific_entry(tmp_path):
    manifest_path = tmp_path / "translation_revision.yaml"
    manifest_path.write_text(
        "posts:\n"
        "  post-one:\n"
        "    pt-br:\n"
        "      reason: stale ai studio translation\n"
        "      notes: revisit tone\n",
        encoding="utf-8",
    )

    manifest = TranslationRevisionManifest(path=manifest_path)
    entry = manifest.get(slug="post-one", target_locale="pt-br")

    assert entry is not None
    assert entry.payload["reason"] == "stale ai studio translation"
    assert entry.payload["notes"] == "revisit tone"
    assert entry.marker


def test_revision_manifest_accepts_legacy_artifacts_root(tmp_path):
    manifest_path = tmp_path / "translation_revision.yaml"
    manifest_path.write_text(
        "artifacts:\n"
        "  post-one:\n"
        "    pt-br:\n"
        "      reason: legacy key still supported\n",
        encoding="utf-8",
    )

    manifest = TranslationRevisionManifest(path=manifest_path)
    entry = manifest.get(slug="post-one", target_locale="pt-br")

    assert entry is not None
    assert entry.payload["reason"] == "legacy key still supported"


def test_orchestrator_revises_legacy_translation_and_upgrades_cache(tmp_path):
    cache_path = tmp_path / "translation-cache.json"
    post = _post()
    cache_path.write_text(
        json.dumps(
            {
                post["slug"]: {
                    "hash": compute_source_hash(_cache_source(post)),
                    "translation": {
                        "title": "Titulo antigo",
                        "excerpt": "Resumo antigo",
                        "tags": ["ia"],
                        "content": "Conteudo antigo",
                    },
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    orchestrator = TranslationV2PostOrchestrator(
        provider_name="opencode",
        strict_validation=False,
        cache_path=cache_path,
        run_id="revision-test",
        prompt_version="v1",
    )
    fake_provider = _FakeRevisionProvider()
    orchestrator.provider = fake_provider  # type: ignore[assignment]
    orchestrator._model_id = "fake/model"

    translated_post = orchestrator.translate_if_needed(post, target_locale="pt-br")

    assert translated_post is not None
    assert translated_post["raw_content"] == "Conteudo revisado"
    assert fake_provider.calls == ["critique", "refine"]

    adapter = TranslationV2CacheAdapter(cache_path=cache_path)
    record = adapter.get_translation_record(
        slug="post-one",
        source_text=_cache_source(post),
        source_locale="en-us",
        target_locale="pt-br",
        provider="opencode",
        model="fake/model",
        prompt_version="v1",
    )

    assert record is not None
    assert record.translation["content"] == "Conteudo revisado"
    assert record.metadata["workflow"] == "revision"
    assert record.metadata["revised_from_cache_source"] == "legacy"


def test_orchestrator_reuses_v2_translation_when_revision_marker_is_satisfied(tmp_path):
    cache_path = tmp_path / "translation-cache.json"
    adapter = TranslationV2CacheAdapter(cache_path=cache_path)
    post = _post()
    marker = "marker-123"
    adapter.store_translation(
        source_text=_cache_source(post),
        source_locale="en-us",
        target_locale="pt-br",
        provider="opencode",
        model="fake/model",
        prompt_version="v1",
        translation={
            "title": "Titulo atual",
            "excerpt": "Resumo atual",
            "tags": ["ia"],
            "content": "Conteudo atual",
        },
        metadata={"workflow": "revision", "revision_marker": marker},
    )

    orchestrator = TranslationV2PostOrchestrator(
        provider_name="opencode",
        strict_validation=False,
        cache_path=cache_path,
        run_id="revision-test",
        prompt_version="v1",
    )
    orchestrator.provider = _NoOpProvider()  # type: ignore[assignment]
    orchestrator._model_id = "fake/model"
    orchestrator.revision_manifest = type(
        "_Manifest",
        (),
        {
            "get": staticmethod(
                lambda *, slug, target_locale: type(
                    "_Entry",
                    (),
                    {
                        "payload": {"reason": "manual review"},
                        "marker": marker,
                    },
                )()
            )
        },
    )()

    translated_post = orchestrator.translate_if_needed(post, target_locale="pt-br")

    assert translated_post is not None
    assert translated_post["raw_content"] == "Conteudo atual"
