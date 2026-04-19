CRITIQUE
Evaluate the translated CV candidate as an editor reviewing a structured hiring artifact.

What to inspect:
- factual and technical accuracy against the source CV
- preservation of hiring signal, seniority cues, and credible professional tone
- consistency of role-title, skill, and achievement terminology
- punctuation, wording cadence, and borrowing choices expected by a native {{target_locale}} recruiter or hiring manager
- invariant-field protection and JSON-structure preservation
- fluency in {{target_locale}}, especially where the CV still sounds like literal transfer from the source locale

Findings policy:
- Report only concrete issues that can drive revision.
- Make findings span-based: quote the relevant source or translated span inside each finding so the editor can locate the defect quickly.
- Name the defect class plainly: mistranslation, terminology drift, invariant-field change, structure drift, calque, tone inflation, tone flattening, or similar.
- If no material defect exists, say so briefly and set needs_refinement to false.
- If any invariant field or JSON structure changed, set needs_refinement to true.

LOCALE DIRECTION
- Source locale: {{source_locale}}
- Target locale: {{target_locale}}
- Translation direction: {{locale_direction}}

LOCALIZATION BRIEF
{{localization_brief}}

SOURCE ANALYSIS JSON
{{source_analysis_json}}

TERMINOLOGY POLICY JSON
{{terminology_policy_json}}

STYLE CONSTRAINTS
{{style_constraints}}

BORROWING CONVENTIONS
{{borrowing_conventions}}

PUNCTUATION CONVENTIONS
{{punctuation_conventions}}

DISCOURSE CONVENTIONS
{{discourse_conventions}}

REGISTER CONVENTIONS
{{register_conventions}}

WRITING STYLE BRIEF
{{writing_style_brief}}

GLOSSARY
{{glossary_entries}}

DO_NOT_TRANSLATE_ENTITIES
{{do_not_translate_entities}}

LOCALE REVIEW CHECKS
{{review_checks}}

SOURCE CV JSON
{{source_markdown}}

OUTPUT CONTRACT
- Return exactly one JSON object.
- Do not wrap in markdown fences.
- score must be a number from 0 to 100.
- dimension_scores must include at least: accuracy_completeness, terminology_entities, markdown_code_link_fidelity, locale_naturalness, borrowing_consistency, rhetorical_structure.
- critical_errors and major_core_errors must be non-negative integers.
- confidence must be a number from 0 to 1.
- findings must be an array of objects with span-based diagnosis.

BEGIN_OUTPUT_JSON
{
  "score": 0,
  "feedback": "string",
  "needs_refinement": true,
  "dimension_scores": {
    "accuracy_completeness": 0,
    "terminology_entities": 0,
    "markdown_code_link_fidelity": 0,
    "locale_naturalness": 0,
    "borrowing_consistency": 0,
    "rhetorical_structure": 0
  },
  "critical_errors": 0,
  "major_core_errors": 0,
  "confidence": 1.0,
  "findings": [
    {
      "id": "finding-1",
      "severity": "major",
      "dimension": "accuracy_completeness",
      "source_span": "string",
      "target_span": "string",
      "description": "string",
      "fix_hint": "string"
    }
  ]
}
END_OUTPUT_JSON

TRANSLATED CANDIDATE JSON
{{translated_json}}
