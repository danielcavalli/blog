"""Fixture contract tests for the deterministic mock-provider data."""

from __future__ import annotations

import json
from pathlib import Path


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "translation_v2"
EXPECTED_FIXTURE_PATH = FIXTURES_DIR / "representative_post_expected.json"


def _load_expected_post_case() -> dict:
    fixture = json.loads(EXPECTED_FIXTURE_PATH.read_text(encoding="utf-8"))
    return fixture["posts"]["deterministic-mock-post"]


def test_representative_mock_fixture_covers_settled_stage_graph():
    expected = _load_expected_post_case()

    assert tuple(expected.keys()) == (
        "metadata",
        "source_analysis",
        "terminology_policy",
        "translated",
        "critique",
        "revised",
        "final_review",
    )


def test_representative_mock_fixture_contains_voice_and_terminology_packets():
    expected = _load_expected_post_case()

    assert expected["source_analysis"]["author_voice_summary"]
    assert expected["source_analysis"]["must_preserve"]
    assert expected["terminology_policy"]["keep_english"]
    assert expected["terminology_policy"]["do_not_translate"]


def test_representative_mock_fixture_contains_revision_and_final_review_outputs():
    expected = _load_expected_post_case()

    revised = expected["revised"]
    final_review = expected["final_review"]

    assert revised["applied_feedback"] == []
    assert revised["rewrite_summary"]
    assert revised["unresolved_risks"] == []
    assert final_review["accept"] is True
    assert final_review["publish_ready"] is True
    assert final_review["voice_score"] >= 90
    assert final_review["terminology_score"] >= 90
