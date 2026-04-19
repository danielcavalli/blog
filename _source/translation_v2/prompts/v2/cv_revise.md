REVISE
Rewrite the translated CV candidate using the source CV and critique. Return both the revised CV and a structured revision report.

Revision rules:
- Preserve everything already correct.
- Fix every justified critique finding.
- Re-anchor disputed wording in the source CV rather than paraphrasing loosely.
- Preserve professional tone, credibility, and hiring signal while correcting accuracy or terminology defects.
- Rewrite the full field when necessary; do not patch translated-sounding wording word by word.
- Repair borrowing drift, degree-handling drift, punctuation drift, and hiring-register drift so the CV reads as native {{target_locale}} material.
- Keep invariant identity/reference fields unchanged.
- Keep JSON structure unchanged.
- Apply the settled terminology policy consistently, including the education degree localization policy for every education.degree value.
- Every critique finding id must be represented in revision_report.applied_findings or revision_report.declined_findings.
- If a critique request conflicts with invariant-field protection, keep the protected value unchanged, record the decline, and add a protected-field exception entry.
- revision_report entries must describe actual edits or explicit non-edits, not generic promises.

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

BEGIN_OUTPUT_JSON
{
  "revised_cv": {
    "name": "string",
    "tagline": "string",
    "location": "string",
    "contact": {
      "email": "string",
      "linkedin": "string",
      "github": "string"
    },
    "skills": ["string"],
    "languages_spoken": ["string"],
    "summary": "string",
    "experience": [
      {
        "title": "string",
        "company": "string",
        "location": "string",
        "period": "string",
        "description": "string",
        "achievements": ["string"]
      }
    ],
    "education": [
      {
        "degree": "string",
        "school": "string",
        "period": "string"
      }
    ]
  },
  "revision_report": {
    "applied_findings": [
      {
        "finding_id": "finding-1",
        "field_path": "summary",
        "change_summary": "string"
      }
    ],
    "declined_findings": [
      {
        "finding_id": "finding-2",
        "reason": "string"
      }
    ],
    "protected_field_exceptions": [
      {
        "finding_id": "finding-3",
        "field_path": "contact.linkedin",
        "protected_value": "string",
        "reason": "string"
      }
    ]
  }
}
END_OUTPUT_JSON

TRANSLATED CANDIDATE JSON
{{translated_json}}

CRITIQUE JSON
{{critique_json}}
