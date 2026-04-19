TERMINOLOGY POLICY
Set an artifact-wide borrowing and localization policy before drafting.

Policy requirements:
- Decide which terms should remain in English, which should be localized, and which are context-sensitive in {{target_locale}}.
- Prefer the term a native technical reader in {{target_locale}} would expect in serious editorial prose.
- Apply the same decision consistently across title, excerpt, tags, headings, and body text.
- Respect DO_NOT_TRANSLATE_ENTITIES exactly.
- Preserve social correctness for Brazilian technical writing, not dictionary literalism.

LOCALE DIRECTION
- Source locale: {{source_locale}}
- Target locale: {{target_locale}}
- Translation direction: {{locale_direction}}

STYLE CONSTRAINTS
{{style_constraints}}

SOURCE ANALYSIS JSON
{{source_analysis_json}}

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
  "keep_english": ["string"],
  "localize": ["string"],
  "context_sensitive": ["string"],
  "do_not_translate": ["string"],
  "consistency_rules": ["string"],
  "rationale_notes": ["string"]
}
END_OUTPUT_JSON
