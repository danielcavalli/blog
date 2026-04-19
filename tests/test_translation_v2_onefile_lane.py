"""One-file translation_v2 lane tests.

Canonical command:
    uv run --extra dev pytest tests/test_translation_v2_onefile_lane.py -q
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from translation_v2.contracts import validate_translation_output

from tests.translation_v2_onefile_lane_helper import (
    CANONICAL_ONEFILE_LANE_COMMAND,
    CONTRACT_REGRESSION_FIXTURE_PATH,
    DEFAULT_ONEFILE_RUNTIME_CEILING_SECONDS,
    MOCK_FIXTURE_PATH,
    configure_onefile_build,
    ensure_runtime_stubs,
    make_source_post,
)


ensure_runtime_stubs()
import build  # noqa: E402  # isort: skip


def _runtime_ceiling_seconds() -> float:
    raw = os.getenv("TRANSLATION_V2_ONEFILE_MAX_SECONDS", "").strip()
    if not raw:
        return DEFAULT_ONEFILE_RUNTIME_CEILING_SECONDS
    return float(raw)


def test_onefile_lane_runs_end_to_end_with_debuggable_logs(
    monkeypatch,
    tmp_path,
    capsys,
):
    source_post = make_source_post(slug="deterministic-mock-post", lang="en-us")
    configure_onefile_build(tmp_path, monkeypatch, build, source_post)
    monkeypatch.setenv("TRANSLATION_V2_MOCK_FIXTURE", str(MOCK_FIXTURE_PATH))

    started = time.monotonic()
    ok = build.build(
        strict=False,
        use_staging=False,
        post_selector=source_post["slug"],
        skip_about_cv_translation=True,
    )
    elapsed = time.monotonic() - started

    captured = capsys.readouterr().out

    assert ok is True
    assert elapsed <= _runtime_ceiling_seconds()
    assert "Markdown discovery" in captured
    assert "Selected" in captured
    assert source_post["slug"] in captured
    assert "translation_v2 runtime" in captured
    assert "Run ID" in captured
    assert "Artifacts" in captured
    assert CANONICAL_ONEFILE_LANE_COMMAND.endswith("tests/test_translation_v2_onefile_lane.py -q")

    run_match = re.search(r"test-run|build-v2-[0-9]+", captured)
    assert run_match is not None

    run_id = run_match.group(0)
    artifact_dir = tmp_path / "_cache" / "translation-runs" / run_id
    assert artifact_dir.exists()
    assert artifact_dir.name == run_id
    assert (tmp_path / "pt" / "blog" / "deterministic-mock-post.html").exists()


def test_contract_regression_fixture_preserves_critical_entities():
    case = json.loads(CONTRACT_REGRESSION_FIXTURE_PATH.read_text(encoding="utf-8"))
    payload = case["translated_output"]
    validated = validate_translation_output(
        payload,
        run_id="onefile-contract-regression",
        stage="translate",
    )

    assert validated.title == case["expected_title"]
    assert validated.excerpt == case["expected_excerpt"]
    assert validated.tags == case["expected_tags"]
    for token in case["must_preserve_tokens"]:
        assert token in validated.content
