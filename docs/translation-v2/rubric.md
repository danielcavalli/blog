# Translation v2 Rubric

This document is a high-level companion to the scoring policy in `_source/translation_v2/rubric.py`.

It is not the runtime source of truth. The actual contracts and thresholds live in code and in the active prompt pack.

The current runtime is no longer a simple `translate -> critique -> refine` loop. The active flow also includes `source_analysis`, `terminology_policy`, and `final_review`.

## Dimensions and Weights

- accuracy_completeness: 30
- terminology_entities: 20
- markdown_code_link_fidelity: 20
- linguistic_conventions: 10
- style_register: 10
- locale_conventions: 5
- audience_clarity: 5

Total: 100.

## Anchored Scale (0.0 to 5.0)

- 5.0: No meaningful issues; publication-ready.
- 4.0: Minor edits needed; meaning preserved.
- 3.0: Noticeable issues; requires revision before publish.
- 2.0: Significant quality problems.
- 1.0: Severe failures in fidelity or readability.
- 0.0: Unusable output.

Dimension scores are mapped to a 0-100 range and combined with weights.

## Hard Constraints

- Any critical finding in core dimensions fails the attempt.
- Core minimums must be met:
  - accuracy_completeness >= 85
  - terminology_entities >= 80
  - markdown_code_link_fidelity >= 95

## Score-to-Action Thresholds

- accept:
  - overall_score >= 92
  - core minimums met
  - major_core_errors == 0
- auto_refine:
  - overall_score >= 88 and major_core_errors <= 1, or
  - overall_score >= 75 with no hard-fail conditions
- escalate:
  - confidence < 0.6
  - loop stagnation reached
  - max loop count reached
  - severe unresolved issues that do not hard-fail
- fail:
  - critical_errors > 0
  - overall_score < 60

## Bounded Loop Stopping Criteria

- max_loops: 3
- min_score_delta between loop iterations: 3.0
- max_stagnant_loops: 2

When stopping criteria are hit, the policy returns escalate.

## JSON Schemas

Schemas are codified in `_source/translation_v2/rubric.py`.

- CRITIQUE_OUTPUT_SCHEMA:
  - Includes overall_score, decision_hint, confidence, dimension scores, error summary, and findings.
  - Findings require evidence-linked fields: source_span, target_span, and evidence quotes.
- REFINEMENT_PLAN_SCHEMA:
  - Includes action, planned_edits, and revised_content.
  - Planned edits tie back to finding IDs with operation + instruction.

These schemas are intended to be consumed by provider and evaluation harness stories.
