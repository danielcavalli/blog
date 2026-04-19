TERMINOLOGY POLICY
Set a CV-wide terminology policy before you write.

Policy requirements:
- Keep invariant identity/reference fields unchanged unless the source itself localizes them.
- Translate prose-bearing fields into the professional register expected by a native {{target_locale}} recruiter or hiring manager.
- Decide once how to handle borrowed technical terms, role titles, tooling names, and achievement verbs, then apply the decision consistently across the entire CV.
- Resolve ambiguous terms into explicit CV-wide decisions, not only category lists.
- If a term such as AI Platform is ambiguous in the source, glossary, or analysis context, include an explicit resolved decision for it.
- Explicitly settle the education degree localization policy for education.degree values. Do not leave degree handling implicit or mixed.
- Prefer target-locale hiring language that sounds credible and specific, not inflated or mechanically literal.
- Keep company names, school names, locations, contact values, periods, raw URLs, and all items in DO_NOT_TRANSLATE_ENTITIES unchanged when they function as identifiers.
- Preserve JSON structure exactly.
- If a source term is better kept in its original form for professional recognition, keep it borrowed consistently rather than translating it inconsistently.
- Treat borrowing, hiring-register wording, and degree naming as CV-wide policy choices rather than local improvisation.

LOCALE DIRECTION
- Source locale: {{source_locale}}
- Target locale: {{target_locale}}
- Translation direction: {{locale_direction}}

LOCALIZATION BRIEF
{{localization_brief}}

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

LOCALE REVIEW CHECKS
{{review_checks}}

SOURCE ANALYSIS JSON
{{source_analysis_json}}

GLOSSARY
{{glossary_entries}}

DO_NOT_TRANSLATE_ENTITIES
{{do_not_translate_entities}}

SOURCE CV JSON
{{source_markdown}}

OUTPUT CONTRACT
- Return exactly one JSON object.
- Do not wrap in markdown fences.

BEGIN_OUTPUT_JSON
{
  "keep_english": ["string"],
  "localize": ["string"],
  "context_sensitive": ["string"],
  "do_not_translate": ["string"],
  "resolved_decisions": [
    {
      "source_term": "AI Platform",
      "approved_rendering": "AI Platform",
      "decision": "keep_english",
      "scope": "cv-wide",
      "applies_to": ["tagline", "summary", "experience[].title", "experience[].description", "experience[].achievements"],
      "notes": "string"
    }
  ],
  "education_degree_localization_policy": {
    "decision": "localize_equivalent",
    "apply_consistently": true,
    "rule": "string",
    "exceptions": [
      {
        "source_degree": "string",
        "approved_rendering": "string",
        "reason": "string"
      }
    ]
  },
  "consistency_rules": ["string"],
  "rationale_notes": ["string"]
}
END_OUTPUT_JSON
