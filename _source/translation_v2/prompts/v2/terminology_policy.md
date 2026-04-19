TERMINOLOGY POLICY
Set an artifact-wide borrowing and localization policy before drafting.

Policy requirements:
- Decide which terms should remain in English, which should be localized, and which are context-sensitive in {{target_locale}}.
- Prefer the term a native technical reader in {{target_locale}} would expect in serious editorial prose.
- Apply the same decision consistently across title, excerpt, tags, headings, and body text.
- Resolve ambiguous terms into artifact-level decisions, not only category lists.
- If a term such as AI Platform is ambiguous in the source, glossary, or analysis context, include an explicit resolved decision for it.
- If the artifact contains education credential or degree terminology, include explicit resolved decisions for those terms rather than leaving them implied.
- Respect DO_NOT_TRANSLATE_ENTITIES exactly.
- Preserve social correctness for Brazilian technical writing, not dictionary literalism.
- Do not treat English borrowings as isolated token choices. Set a coherent artifact-wide policy that reflects the target language community.

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
  "resolved_decisions": [
    {
      "source_term": "AI Platform",
      "approved_rendering": "AI Platform",
      "decision": "keep_english",
      "scope": "artifact-wide",
      "applies_to": ["title", "excerpt", "tags", "body"],
      "notes": "string"
    }
  ],
  "consistency_rules": ["string"],
  "rationale_notes": ["string"]
}
END_OUTPUT_JSON
