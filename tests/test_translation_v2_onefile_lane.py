"""One-file translation_v2 lane tests.

Canonical command:
    uv run --extra dev pytest tests/test_translation_v2_onefile_lane.py -q
"""

from __future__ import annotations

import json
import os
import time

from translation_v2.contracts import validate_translation_output

from tests.translation_v2_onefile_lane_helper import (
    CONTRACT_REGRESSION_FIXTURE_PATH,
    DEFAULT_ONEFILE_RUNTIME_CEILING_SECONDS,
    MOCK_FIXTURE_PATH,
    configure_onefile_build,
    ensure_source_imports,
    make_source_post,
)


ensure_source_imports()
import build  # noqa: E402  # isort: skip


def _runtime_ceiling_seconds() -> float:
    raw = os.getenv("TRANSLATION_V2_ONEFILE_MAX_SECONDS", "").strip()
    if not raw:
        return DEFAULT_ONEFILE_RUNTIME_CEILING_SECONDS
    return float(raw)


def test_focused_build_reports_rendering_without_translation_runs(
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
    assert "Rendering source and accepted translations" in captured
    assert "Run ID" not in captured
    assert not (tmp_path / "_cache" / "translation-runs").exists()
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
