"""Tests for translation_v2 run logging and artifact persistence."""

from __future__ import annotations

import json
import os
import sys


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from translation_v2.artifacts import TranslationRunArtifacts  # noqa: E402
from translation_v2.run_logging import (  # noqa: E402
    BuildSummaryCounters,
    TranslationRunEventLogger,
    event_has_required_schema,
)


def test_run_event_logger_writes_required_jsonl_schema(tmp_path):
    logger = TranslationRunEventLogger(run_id="run-logs-1", base_dir=tmp_path)

    event = logger.emit_stage_event(
        post_slug="my-post",
        stage="translate",
        attempt=1,
        model="opencode/gpt-5.4",
        duration_ms=1210,
        outcome="success",
    )

    assert logger.events_path.exists()
    assert event_has_required_schema(event)

    lines = logger.events_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    loaded = json.loads(lines[0])

    assert loaded["run_id"] == "run-logs-1"
    assert loaded["post_slug"] == "my-post"
    assert loaded["stage"] == "translate"
    assert loaded["attempt"] == 1
    assert loaded["model"] == "opencode/gpt-5.4"
    assert loaded["duration_ms"] == 1210
    assert loaded["outcome"] == "success"


def test_run_artifacts_persist_prompt_response_error_and_runner_logs(tmp_path):
    artifacts = TranslationRunArtifacts(run_id="run-artifacts-1", base_dir=tmp_path)

    prompt_path = artifacts.write_prompt("post/slug", "critique", "Prompt body")
    response_path = artifacts.write_structured_response(
        "post/slug",
        "critique",
        {
            "score": 91,
            "token": "secret-value",
            "nested": {"api_key": "another-secret"},
        },
    )
    error_path = artifacts.write_error("post/slug", "critique", "timeout")
    stdout_path = artifacts.write_runner_stdout("post/slug", "critique", "stdout-data")
    stderr_path = artifacts.write_runner_stderr("post/slug", "critique", "stderr-data")

    assert prompt_path.exists()
    assert response_path.exists()
    assert error_path.exists()
    assert stdout_path.exists()
    assert stderr_path.exists()

    assert "run-artifacts-1" in prompt_path.parts
    assert "posts" in prompt_path.parts
    assert prompt_path.read_text(encoding="utf-8") == "Prompt body"
    assert error_path.read_text(encoding="utf-8") == "timeout"
    assert stdout_path.read_text(encoding="utf-8") == "stdout-data"
    assert stderr_path.read_text(encoding="utf-8") == "stderr-data"

    response_payload = json.loads(response_path.read_text(encoding="utf-8"))
    assert response_payload["token"] == "[REDACTED]"
    assert response_payload["nested"]["api_key"] == "[REDACTED]"


def test_build_summary_counters_expose_concise_metrics():
    counters = BuildSummaryCounters()
    counters.increment_cache_hit()
    counters.increment_cache_miss()
    counters.increment_retries(2)
    counters.increment_failures()

    as_dict = counters.as_dict()
    assert as_dict == {
        "cache_hit": 1,
        "cache_miss": 1,
        "retries": 2,
        "failures": 1,
    }

    line = counters.to_summary_line()
    assert "cache_hit=1" in line
    assert "cache_miss=1" in line
    assert "retries=2" in line
    assert "failures=1" in line
