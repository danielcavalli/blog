"""Granular scoring rubric and policy for critique-refine loops."""

from __future__ import annotations

from dataclasses import dataclass


SCORE_DIMENSION_WEIGHTS = {
    "accuracy_completeness": 30,
    "terminology_entities": 20,
    "markdown_code_link_fidelity": 20,
    "linguistic_conventions": 10,
    "style_register": 10,
    "locale_conventions": 5,
    "audience_clarity": 5,
}

ANCHORED_SCALE = {
    5.0: "No meaningful issues; publication-ready.",
    4.0: "Minor edits needed; meaning preserved.",
    3.0: "Noticeable issues; requires revision before publish.",
    2.0: "Significant quality problems.",
    1.0: "Severe failures in fidelity or readability.",
    0.0: "Unusable output.",
}


CRITIQUE_OUTPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "overall_score",
        "decision_hint",
        "confidence",
        "dimensions",
        "error_summary",
        "findings",
    ],
    "properties": {
        "overall_score": {"type": "number", "minimum": 0, "maximum": 100},
        "decision_hint": {
            "type": "string",
            "enum": ["accept", "auto_refine", "escalate", "fail"],
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "dimensions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "name",
                    "weight",
                    "raw_0_5",
                    "score_100",
                    "rationale",
                ],
                "properties": {
                    "name": {"type": "string"},
                    "weight": {"type": "number"},
                    "raw_0_5": {"type": "number", "minimum": 0, "maximum": 5},
                    "score_100": {"type": "number", "minimum": 0, "maximum": 100},
                    "rationale": {"type": "string"},
                },
            },
        },
        "error_summary": {
            "type": "object",
            "required": ["minor", "major", "critical"],
            "properties": {
                "minor": {"type": "integer", "minimum": 0},
                "major": {"type": "integer", "minimum": 0},
                "critical": {"type": "integer", "minimum": 0},
            },
        },
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "id",
                    "dimension",
                    "severity",
                    "description",
                    "source_span",
                    "target_span",
                    "fix_hint",
                    "evidence",
                ],
                "properties": {
                    "id": {"type": "string"},
                    "dimension": {"type": "string"},
                    "severity": {
                        "type": "string",
                        "enum": ["minor", "major", "critical"],
                    },
                    "description": {"type": "string"},
                    "source_span": {"type": "string"},
                    "target_span": {"type": "string"},
                    "fix_hint": {"type": "string"},
                    "evidence": {
                        "type": "object",
                        "required": ["source_quote", "target_quote"],
                        "properties": {
                            "source_quote": {"type": "string"},
                            "target_quote": {"type": "string"},
                        },
                    },
                },
            },
        },
    },
}


REFINEMENT_PLAN_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["action", "requires_human", "planned_edits", "revised_content"],
    "properties": {
        "action": {
            "type": "string",
            "enum": ["accept", "refine_applied", "escalate", "fail"],
        },
        "requires_human": {"type": "boolean"},
        "planned_edits": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["finding_id", "operation", "instruction", "priority"],
                "properties": {
                    "finding_id": {"type": "string"},
                    "operation": {
                        "type": "string",
                        "enum": [
                            "rewrite_segment",
                            "term_replace",
                            "markdown_fix",
                            "link_fix",
                            "code_preserve",
                        ],
                    },
                    "instruction": {"type": "string"},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                },
            },
        },
        "revised_content": {"type": "string"},
        "unresolved_findings": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
}


@dataclass(slots=True)
class RubricThresholds:
    """Thresholds and loop controls for decision policy."""

    accept_score: float = 92.0
    refine_score: float = 88.0
    escalate_score: float = 75.0
    fail_score: float = 60.0

    min_accuracy: float = 85.0
    min_terminology: float = 80.0
    min_markdown_fidelity: float = 95.0

    min_confidence: float = 0.6
    max_loops: int = 3
    max_major_core_errors: int = 1
    min_score_delta: float = 3.0
    max_stagnant_loops: int = 2


@dataclass(slots=True)
class RubricDecisionInput:
    """Input metrics used to choose next action."""

    overall_score: float
    dimension_scores: dict[str, float]
    critical_errors: int = 0
    major_core_errors: int = 0
    confidence: float = 1.0
    loops_completed: int = 0
    score_delta: float | None = None
    stagnant_loops: int = 0


def decide_score_action(
    decision_input: RubricDecisionInput,
    thresholds: RubricThresholds = RubricThresholds(),
) -> str:
    """Map rubric scores and loop metrics to a deterministic action."""

    if decision_input.critical_errors > 0:
        return "fail"

    if decision_input.loops_completed >= thresholds.max_loops:
        return "escalate"

    if decision_input.stagnant_loops >= thresholds.max_stagnant_loops:
        return "escalate"

    if decision_input.score_delta is not None and decision_input.loops_completed > 0:
        if decision_input.score_delta < thresholds.min_score_delta:
            return "escalate"

    if decision_input.confidence < thresholds.min_confidence:
        return "escalate"

    if decision_input.overall_score < thresholds.fail_score:
        return "fail"

    core_mins_met = _core_dimension_mins_met(decision_input, thresholds)
    if not core_mins_met:
        return "auto_refine"

    if decision_input.overall_score >= thresholds.accept_score:
        if decision_input.major_core_errors == 0:
            return "accept"
        return "auto_refine"

    if decision_input.overall_score >= thresholds.refine_score:
        if decision_input.major_core_errors <= thresholds.max_major_core_errors:
            return "auto_refine"
        return "escalate"

    if decision_input.overall_score >= thresholds.escalate_score:
        return "auto_refine"

    return "escalate"


def _core_dimension_mins_met(
    decision_input: RubricDecisionInput,
    thresholds: RubricThresholds,
) -> bool:
    accuracy = decision_input.dimension_scores.get("accuracy_completeness", 0.0)
    terminology = decision_input.dimension_scores.get("terminology_entities", 0.0)
    fidelity = decision_input.dimension_scores.get("markdown_code_link_fidelity", 0.0)
    return (
        accuracy >= thresholds.min_accuracy
        and terminology >= thresholds.min_terminology
        and fidelity >= thresholds.min_markdown_fidelity
    )
