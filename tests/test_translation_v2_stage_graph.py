"""Settled v2 stage-graph expectations for prompt registry coverage."""

from __future__ import annotations

import json
import os
import sys
import types
from pathlib import Path


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
if _SOURCE not in sys.path:
    sys.path.insert(0, _SOURCE)
_mock_provider_stub = types.ModuleType("translation_v2.mock_provider")
_mock_provider_stub.DeterministicMockTranslationProvider = object
sys.modules.setdefault("translation_v2.mock_provider", _mock_provider_stub)

from translation_v2.prompt_registry import (  # noqa: E402
    PROMPT_STAGES,
    PROMPT_STAGES_V2,
    build_prompt_artifact_metadata,
    load_prompt_pack,
    prompt_template_path,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "translation_v2"
STAGE_GRAPH_FIXTURE = FIXTURES_DIR / "stage_graph_v2.json"


def _expected_stages() -> tuple[str, ...]:
    payload = json.loads(STAGE_GRAPH_FIXTURE.read_text(encoding="utf-8"))
    return tuple(stage["name"] for stage in payload["stages"])


def test_prompt_registry_exposes_settled_v2_stage_graph():
    assert PROMPT_STAGES_V2 == _expected_stages()
    assert PROMPT_STAGES == _expected_stages()
    assert tuple(load_prompt_pack(prompt_version="v2").keys()) == _expected_stages()


def test_prompt_templates_exist_for_each_settled_stage_and_artifact_type():
    for stage in _expected_stages():
        assert prompt_template_path(stage, prompt_version="v2").exists()
        assert prompt_template_path(stage, prompt_version="v2", artifact_type="cv").exists()


def test_prompt_artifact_metadata_accepts_final_review_stage():
    metadata = build_prompt_artifact_metadata(
        stage="final_review",
        prompt_version="v2",
        prompt_fingerprint="stage-graph-fingerprint",
    )

    assert metadata == {
        "stage": "final_review",
        "prompt_version": "v2",
        "prompt_fingerprint": "stage-graph-fingerprint",
    }
