REVISE
Rewrite the translated candidate using the source artifact and critique.

Revision rules:
- Preserve everything already correct.
- Fix every justified critique finding.
- Re-anchor disputed passages in the source rather than paraphrasing the draft loosely.
- Preserve voice, rhetorical layering, and target-locale fluency while correcting accuracy or terminology defects.
- Keep markdown structure unchanged.
- Keep markdown links, URLs, inline code, fenced code, placeholders, citations, and DO_NOT_TRANSLATE_ENTITIES unchanged where protected.
- If a critique request conflicts with a protection rule, keep the protected text unchanged and mention that in applied_feedback.
- applied_feedback should map to actual edits or explicit non-edits, not generic promises.

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

SOURCE MARKDOWN
{{source_markdown}}

OUTPUT CONTRACT
- Return exactly one JSON object.
- Do not wrap in markdown fences.

BEGIN_OUTPUT_JSON
{
  "title": "string",
  "excerpt": "string",
  "tags": ["string"],
  "content": "string",
  "applied_feedback": ["string"],
  "rewrite_summary": ["string"],
  "unresolved_risks": ["string"]
}
END_OUTPUT_JSON

TRANSLATED CANDIDATE JSON
{{translated_json}}

CRITIQUE JSON
{{critique_json}}
