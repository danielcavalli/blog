REVISE
Rewrite the translated presentation candidate using the source artifact and critique.

Revision rules:
- Preserve everything already correct.
- Fix every justified critique finding.
- Re-anchor disputed passages in the source rather than paraphrasing the draft loosely.
- Preserve voice, rhetorical layering, target-locale fluency, and slide rhythm while correcting accuracy or terminology defects.
- When the draft sounds translated, rewrite the full sentence or paragraph instead of patching individual words.
- Repair borrowing drift, punctuation drift, and connective drift so the result reads as authored {{target_locale}} prose.
- Keep markdown structure unchanged.
- Keep markdown links, URLs, inline code, placeholders, citations, and DO_NOT_TRANSLATE_ENTITIES unchanged where protected.
- Preserve presentation slide markers exactly: `<!-- presentation:slide ... -->` and `<!-- /presentation:slide -->` must remain byte-for-byte unchanged, including ids, layout, density, spacing, and order.
- Keep fenced-code delimiters/language labels and markdown link/image destinations byte-for-byte unchanged. Revise reader-facing simulated dialogue/transcript prose inside plain text fences when critique asks for localization, while preserving technical identifiers, commands, paths, URLs, and real code semantics.
- For PT-BR presentation prose, resolve recurring editorial drift before finalizing: prefer "resultado" or "resposta" over "saida" for model output unless a technical artifact is meant; prefer "deriva" over "drift" unless terminology policy explicitly preserves the borrowing; use "esquema" or "esquemas" for schema/schemas in prose unless it is a literal code token; use "base de conhecimento" for the concept and reserve "KB" for a named/system shorthand; prefer "Tudo o que" when formal published prose calls for it.
- If a critique request conflicts with a protection rule, keep the protected text unchanged and mention that in applied_feedback.
- applied_feedback should map to actual edits or explicit non-edits, not generic promises.

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
