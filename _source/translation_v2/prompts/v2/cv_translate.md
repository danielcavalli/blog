TRANSLATE
Produce a localized CV draft that preserves structure, hiring signal, and professional tone while reading as native {{target_locale}} material.

Execution rules:
- Translate from {{source_locale}} to {{target_locale}}.
- Preserve the JSON structure exactly.
- Keep invariant fields unchanged when they function as identity, reference, or lookup values.
- Translate prose fields naturally and consistently across summary, experience, achievements, skills, and education-related prose.
- Use terminology_policy_json as the source of truth for ambiguous term handling, including any explicit AI Platform decision.
- Apply terminology_policy_json.education_degree_localization_policy consistently to every education.degree value. Do not mix localized and source-form degrees unless the policy explicitly allows an exception.
- Keep company names, school names, locations, periods, contact values, raw URLs, and DO_NOT_TRANSLATE_ENTITIES unchanged when they are identifiers.
- Rewrite literal source-language phrasing into idiomatic professional wording in {{target_locale}}.
- Normalize punctuation, hiring-register phrasing, and borrowing choices to the conventions of the target locale.
- Preserve achievement scope, numbers, ownership, and technical specificity.
- Keep the JSON contract exact and return only the final artifact JSON.

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
- Include all required keys with the correct primitive/container types.

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
