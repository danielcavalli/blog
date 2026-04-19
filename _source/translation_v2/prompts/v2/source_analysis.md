SOURCE ANALYSIS
Analyze the source artifact as authored writing, not as plain information.

Your job is to extract what must survive localization:
- tone and register
- sentence rhythm and pacing
- connective tissue between ideas
- rhetorical moves
- humor or irony signals
- stance markers
- stylistic signals that are essential to preserve in {{target_locale}}

LOCALE DIRECTION
- Source locale: {{source_locale}}
- Target locale: {{target_locale}}
- Translation direction: {{locale_direction}}

STYLE CONSTRAINTS
{{style_constraints}}

WRITING STYLE BRIEF
{{writing_style_brief}}

AUTHOR VOICE PROFILE
{{author_voice_profile}}

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
