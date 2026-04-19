"""Integration test for translation_v2 trigger interface.

Run only this suite:
    uv run --extra dev pytest tests/test_translation_trigger_interface.py -q
"""

from __future__ import annotations

import inspect
import json
import os
import sys
from typing import Any, cast


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
if _SOURCE not in sys.path:
    sys.path.insert(0, _SOURCE)

from translation_v2.contracts import TranslationOutput  # noqa: E402
from translation_v2.mock_provider import DeterministicMockTranslationProvider  # noqa: E402
from translation_v2.orchestrator import TranslationV2PostOrchestrator  # noqa: E402
from translation_v2.providers import OpenCodeProviderLoopResult  # noqa: E402
from translation_v2.trigger import (  # noqa: E402
    TRIGGER_EVENT_TYPE_POST_FINISHED,
    TRIGGER_SCHEMA_VERSION,
    derive_idempotency_key,
)


def test_trigger_interface_preserves_facade_and_persists_correlation_context(monkeypatch, tmp_path):
    captured: dict[str, Any] = {}

    def _fake_loop(self, request):  # noqa: ARG001
        captured["request"] = request
        return OpenCodeProviderLoopResult(
            final_translation=TranslationOutput(
                title="Titulo trigger",
                excerpt="Resumo trigger",
                tags=["ia", "agentes"],
                content="## Conteudo\n\nTexto traduzido.",
            ),
            stage_results=[],
            loops_completed=0,
            stop_reason="accepted",
        )

    monkeypatch.setattr(
        "translation_v2.providers.opencode.OpenCodeTranslationProvider.run_translation_loop",
        _fake_loop,
    )

    artifact_base = tmp_path / "artifacts"
    monkeypatch.setenv("TRANSLATION_V2_ARTIFACT_BASE_DIR", str(artifact_base))

    orchestrator = TranslationV2PostOrchestrator(
        provider_name="opencode",
        strict_validation=False,
        cache_path=tmp_path / "translation-cache.json",
        run_id="build-v2-correlation-001",
    )

    post = {
        "slug": "trigger-contract-post",
        "lang": "en-us",
        "title": "Trigger Contract",
        "excerpt": "Trigger excerpt",
        "tags": ["translation"],
        "raw_content": "# Trigger\n\nThis is source markdown.",
        "content": "<h1>Trigger</h1>",
    }

    translated = orchestrator.translate_if_needed(post, target_locale="pt-br")
    assert translated is not None
    assert translated["lang"] == "pt-br"

    signature = inspect.signature(TranslationV2PostOrchestrator.translate_if_needed)
    assert list(signature.parameters.keys()) == ["self", "post", "target_locale"]
    assert signature.parameters["target_locale"].default == "pt-br"

    request = cast(Any, captured["request"])
    assert request.metadata["trigger"]["schema_version"] == TRIGGER_SCHEMA_VERSION
    assert request.metadata["trigger"]["event_type"] == TRIGGER_EVENT_TYPE_POST_FINISHED
    assert request.metadata["correlation_id"] == "build-v2-correlation-001"
    assert request.metadata["build_run_id"] == "build-v2-correlation-001"

    expected_idempotency = derive_idempotency_key(
        slug="trigger-contract-post",
        source_text=post["raw_content"],
        target_locale="pt-br",
    )
    assert request.metadata["idempotency_key"] == expected_idempotency

    trigger_event_path = (
        artifact_base
        / "build-v2-correlation-001"
        / "posts"
        / "trigger-contract-post"
        / "trigger"
        / "event.json"
    )
    assert trigger_event_path.exists()
    event_payload = json.loads(trigger_event_path.read_text(encoding="utf-8"))
    assert event_payload["schema_version"] == TRIGGER_SCHEMA_VERSION
    assert event_payload["event_type"] == TRIGGER_EVENT_TYPE_POST_FINISHED
    assert event_payload["idempotency_key"] == expected_idempotency
    assert event_payload["correlation_id"] == "build-v2-correlation-001"
    assert event_payload["run_id"] == "build-v2-correlation-001"

    stage_event_path = artifact_base / "build-v2-correlation-001" / "stage-events.jsonl"
    assert stage_event_path.exists()
    lines = stage_event_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    stage_event = json.loads(lines[0])
    assert stage_event["run_id"] == "build-v2-correlation-001"
    assert stage_event["stage"] == "trigger_dispatch"
    assert stage_event["outcome"] == "cache_miss"
    assert stage_event["metadata"]["correlation_id"] == "build-v2-correlation-001"
    assert stage_event["metadata"]["build_run_id"] == "build-v2-correlation-001"
    assert stage_event["metadata"]["request_run_id"] == request.run_id


def test_mock_provider_pipeline_always_runs_critique_and_refine_when_needed(monkeypatch, tmp_path):
    fixture_path = tmp_path / "mock-fixtures.json"
    fixture_path.write_text(
        json.dumps(
            {
                "posts": {
                    "mock-post": {
                        "translated": {
                            "title": "Titulo inicial",
                            "excerpt": "Resumo inicial",
                            "tags": ["tag"],
                            "content": "Conteudo inicial",
                        },
                        "critique": {
                            "score": 82,
                            "feedback": "Refine wording",
                            "needs_refinement": True,
                            "findings": ["Use clearer wording"],
                        },
                        "refined": {
                            "title": "Titulo refinado",
                            "excerpt": "Resumo refinado",
                            "tags": ["tag"],
                            "content": "Conteudo refinado",
                            "applied_feedback": ["Use clearer wording"],
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    stage_calls: list[str] = []

    original_translate = DeterministicMockTranslationProvider.translate
    original_critique = DeterministicMockTranslationProvider.critique
    original_refine = DeterministicMockTranslationProvider.refine

    def _spy_translate(self, request):
        stage_calls.append("translate")
        return original_translate(self, request)

    def _spy_critique(self, request, translated):
        stage_calls.append("critique")
        return original_critique(self, request, translated)

    def _spy_refine(self, request, translated, critique):
        stage_calls.append("refine")
        return original_refine(self, request, translated, critique)

    monkeypatch.setattr(DeterministicMockTranslationProvider, "translate", _spy_translate)
    monkeypatch.setattr(DeterministicMockTranslationProvider, "critique", _spy_critique)
    monkeypatch.setattr(DeterministicMockTranslationProvider, "refine", _spy_refine)

    orchestrator = TranslationV2PostOrchestrator(
        provider_name="mock",
        strict_validation=False,
        cache_path=tmp_path / "translation-cache.json",
        mock_fixture_path=fixture_path,
    )

    post = {
        "slug": "mock-post",
        "lang": "en-us",
        "title": "Mock title",
        "excerpt": "Mock excerpt",
        "tags": ["translation"],
        "raw_content": "Source markdown",
        "content": "<p>Source markdown</p>",
    }

    translated = orchestrator.translate_if_needed(post, target_locale="pt-br")
    assert translated is not None
    assert translated["raw_content"] == "Conteudo refinado"
    assert stage_calls == ["translate", "critique", "refine"]
