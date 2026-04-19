CRITIQUE
Evaluate the translated candidate as an editor, not as a retranslator.

What to inspect:
- factual and technical accuracy against the source
- preservation of voice, intent, pacing, and rhetorical layering
- terminology consistency and borrowing/localization choices
- punctuation, clause movement, and connective texture in {{target_locale}}
- markdown, links, code, placeholders, citations, and entity protection
- fluency in {{target_locale}}, especially places that still sound like carried-over source syntax

Findings policy:
- Report only concrete issues that can drive revision.
- Make findings span-based: quote the relevant source or translated span inside each finding so the editor can locate the defect without guessing.
- Name the defect class plainly: mistranslation, omission, terminology drift, calque, tone flattening, broken protection rule, formatting drift, or similar.
- If no material defect exists, say so briefly and set needs_refinement to false.
- If any protected token or protected entity changed, set needs_refinement to true.

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

SOURCE MARKDOWN
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
