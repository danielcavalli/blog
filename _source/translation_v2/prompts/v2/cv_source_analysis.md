SOURCE ANALYSIS
You are preparing a localized translation for a structured CV artifact.

Before drafting or reviewing anything, silently extract:
- the candidate's professional positioning and seniority signals
- the intended tone: direct, understated, ambitious, pragmatic, technical, or leadership-heavy
- which fields carry identity/reference data and must remain invariant
- which prose fields need localization for {{target_locale}} while preserving credibility and specificity
- where literal translation would weaken hiring-signal clarity, impact framing, or idiomatic professional wording
- where Brazilian or English hiring language expects a different wording pattern than the source

Treat this analysis as working memory only. Do not output the analysis itself.

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

WRITING STYLE BRIEF
{{writing_style_brief}}

AUTHOR VOICE PROFILE
{{author_voice_profile}}

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
  "author_voice_summary": "string",
  "tone": "string",
  "register": "string",
  "sentence_rhythm": ["string"],
  "connective_tissue": ["string"],
  "rhetorical_moves": ["string"],
  "humor_signals": ["string"],
  "stance_markers": ["string"],
  "must_preserve": ["string"]
}
END_OUTPUT_JSON
