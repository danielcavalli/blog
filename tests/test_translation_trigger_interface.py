"""Integration tests for translation_v2 trigger and request metadata flow.

Run only this suite:
    uv run --extra dev pytest tests/test_translation_trigger_interface.py -q
"""

from __future__ import annotations

import inspect
import json
import os
import sys
import types
from typing import Any, cast


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
if _SOURCE not in sys.path:
    sys.path.insert(0, _SOURCE)
_mock_provider_stub = types.ModuleType("translation_v2.mock_provider")
setattr(_mock_provider_stub, "DeterministicMockTranslationProvider", object)
sys.modules.setdefault("translation_v2.mock_provider", _mock_provider_stub)

from translation_v2.orchestrator import TranslationV2PostOrchestrator  # noqa: E402
from translation_v2.trigger import (  # noqa: E402
    TRIGGER_EVENT_TYPE_POST_FINISHED,
    TRIGGER_SCHEMA_VERSION,
    derive_idempotency_key,
)


def test_trigger_interface_preserves_facade_and_persists_correlation_context(monkeypatch, tmp_path):
    captured: dict[str, Any] = {}

    def _fake_run_pipeline(self, request, *, artifact_type):  # noqa: ARG001
        captured["request"] = request
        captured["artifact_type"] = artifact_type
        return {
            "title": "Titulo trigger",
            "excerpt": "Resumo trigger",
            "tags": ["ia", "agentes"],
            "content": "## Conteudo\n\nTexto traduzido.",
        }

    monkeypatch.setattr(TranslationV2PostOrchestrator, "_run_pipeline", _fake_run_pipeline)

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
    assert captured["artifact_type"] == "post"
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

def test_trigger_interface_propagates_revision_and_voice_packet_metadata(monkeypatch, tmp_path):
    captured: dict[str, Any] = {}

    def _fake_run_pipeline(self, request, *, artifact_type):  # noqa: ARG001
        captured["request"] = request
        captured["artifact_type"] = artifact_type
        return {
            "title": "Titulo revisado",
            "excerpt": "Resumo revisado",
            "tags": ["ia"],
            "content": "Conteudo revisado",
        }

    monkeypatch.setattr(TranslationV2PostOrchestrator, "_run_pipeline", _fake_run_pipeline)

    artifact_base = tmp_path / "artifacts"
    monkeypatch.setenv("TRANSLATION_V2_ARTIFACT_BASE_DIR", str(artifact_base))

    orchestrator = TranslationV2PostOrchestrator(
        provider_name="opencode",
        strict_validation=False,
        cache_path=tmp_path / "translation-cache.json",
        run_id="build-v2-revision-001",
    )
    cast(Any, orchestrator).revision_manifest = type(
        "_Manifest",
        (),
        {
            "get": staticmethod(
                lambda *, slug, target_locale: type(
                    "_Entry",
                    (),
                    {
                        "payload": {
                            "reason": "manual linguistic review",
                            "notes": "tighten voice and terminology",
                        },
                        "marker": "revision-marker-001",
                    },
                )()
            )
        },
    )()

    translation = orchestrator.translate_artifact_if_needed(
        slug="trigger-contract-post",
        source_text="# Trigger\n\nThis is source markdown.",
        source_locale="en-us",
        target_locale="pt-br",
        artifact_type="post",
        frontmatter={
            "title": "Trigger Contract",
            "excerpt": "Trigger excerpt",
            "tags": ["translation"],
        },
        do_not_translate_entities=["OpenCode", "CUDA"],
    )

    assert translation["content"] == "Conteudo revisado"

    request = cast(Any, captured["request"])
    assert captured["artifact_type"] == "post"
    assert request.metadata["writing_style_brief"]
    assert request.metadata["writing_style_fingerprint"]
    assert request.metadata["do_not_translate_entities"] == ["OpenCode", "CUDA"]
    assert request.metadata["revision_requested"] is True
    assert request.metadata["revision_request"] == {
        "reason": "manual linguistic review",
        "notes": "tighten voice and terminology",
    }
    assert request.metadata["revision_marker"] == "revision-marker-001"

    stage_event_path = artifact_base / "build-v2-revision-001" / "stage-events.jsonl"
    lines = stage_event_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    stage_event = json.loads(lines[0])
    assert stage_event["stage"] == "trigger_dispatch"
    assert stage_event["outcome"] == "cache_miss"
    assert stage_event["metadata"]["revision_requested"] is True
    assert stage_event["metadata"]["revision_marker"] == "revision-marker-001"


def test_strict_validation_skips_generic_post_validator_for_presentations(
    monkeypatch,
    tmp_path,
):
    def _fake_run_pipeline(self, request, *, artifact_type):  # noqa: ARG001
        return {
            "title": "Deck traduzido",
            "excerpt": "Resumo",
            "tags": ["slides"],
            "content": '<!-- presentation:slide id="intro" layout="lead" density="normal" -->\n'
            "# Daniel Cavalli\n\n"
            "<content>literal transcript text\n"
            "<!-- /presentation:slide -->",
        }

    def _fail_generic_validation(*_args, **_kwargs):
        raise AssertionError("generic validator should not run for presentation artifacts")

    monkeypatch.setattr(TranslationV2PostOrchestrator, "_run_pipeline", _fake_run_pipeline)
    monkeypatch.setattr("translation_v2.orchestrator.validate_translation", _fail_generic_validation)

    orchestrator = TranslationV2PostOrchestrator(
        provider_name="opencode",
        strict_validation=True,
        cache_path=tmp_path / "translation-cache.json",
        run_id="build-v2-presentation-strict-001",
    )

    translated = orchestrator.translate_if_needed(
        {
            "slug": "deck",
            "lang": "en-us",
            "title": "Deck",
            "excerpt": "Deck excerpt",
            "tags": ["slides"],
            "content_type": "presentation",
            "raw_content": '<!-- presentation:slide id="intro" layout="lead" density="normal" -->\n'
            "# Daniel Cavalli\n\n"
            "<content>literal transcript text\n"
            "<!-- /presentation:slide -->",
            "content": "<p>Deck</p>",
        },
        target_locale="pt-br",
    )

    assert translated is not None
    assert translated["content_type"] == "presentation"
    assert translated["lang"] == "pt-br"
