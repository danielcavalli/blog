"""Tests for translation_v2 rubric thresholds, schemas, and policy actions."""

from __future__ import annotations

import json
import os
import sys


_SOURCE = os.path.join(os.path.dirname(__file__), "..", "_source")
sys.path.insert(0, _SOURCE)

from translation_v2.rubric import (  # noqa: E402
    CRITIQUE_OUTPUT_SCHEMA,
    REFINEMENT_PLAN_SCHEMA,
    SCORE_DIMENSION_WEIGHTS,
    RubricDecisionInput,
    RubricThresholds,
    decide_score_action,
)


def test_rubric_dimensions_sum_to_hundred():
    assert sum(SCORE_DIMENSION_WEIGHTS.values()) == 100


def test_rubric_policy_fixture_maps_scores_to_actions():
    fixture_path = os.path.join(
        os.path.dirname(__file__),
        "fixtures",
        "translation_v2",
        "rubric_policy_cases.json",
    )
    with open(fixture_path, encoding="utf-8") as handle:
        cases = json.load(handle)

    thresholds = RubricThresholds()
    for case in cases:
        decision_input = RubricDecisionInput(**case["input"])
        action = decide_score_action(decision_input, thresholds)
        assert action == case["expected_action"], case["name"]


def test_critique_schema_requires_evidence_linked_findings():
    required = set(CRITIQUE_OUTPUT_SCHEMA["required"])
    assert {"overall_score", "decision_hint", "findings"}.issubset(required)

    finding_schema = CRITIQUE_OUTPUT_SCHEMA["properties"]["findings"]["items"]
    finding_required = set(finding_schema["required"])
    assert "source_span" in finding_required
    assert "target_span" in finding_required
    assert "evidence" in finding_required


def test_refinement_schema_requires_action_plan_and_output():
    required = set(REFINEMENT_PLAN_SCHEMA["required"])
    assert "action" in required
    assert "planned_edits" in required
    assert "revised_content" in required
