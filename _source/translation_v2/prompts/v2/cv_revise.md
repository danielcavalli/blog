REVISE
Rewrite the translated CV candidate using the source CV and critique.

Revision rules:
- Preserve everything already correct.
- Fix every justified critique finding.
- Re-anchor disputed wording in the source CV rather than paraphrasing loosely.
- Preserve professional tone, credibility, and hiring signal while correcting accuracy or terminology defects.
- Keep invariant identity/reference fields unchanged.
- Keep JSON structure unchanged.
- If a critique request conflicts with invariant-field protection, keep the protected value unchanged.

LOCALE DIRECTION
- Source locale: {{source_locale}}
- Target locale: {{target_locale}}
- Translation direction: {{locale_direction}}

SOURCE ANALYSIS JSON
{{source_analysis_json}}

TERMINOLOGY POLICY JSON
{{terminology_policy_json}}

STYLE CONSTRAINTS
{{style_constraints}}

WRITING STYLE BRIEF
{{writing_style_brief}}

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
}
END_OUTPUT_JSON

TRANSLATED CANDIDATE JSON
{{translated_json}}

CRITIQUE JSON
{{critique_json}}
