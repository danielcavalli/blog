TRANSLATE
Produce a localized draft that preserves the author's voice, argumentative structure, and rhetorical layering while reading as native {{target_locale}} prose.

Execution rules:
- Translate from {{source_locale}} to {{target_locale}}.
- Preserve markdown structure and semantics exactly.
- Keep heading levels, list nesting, tables, blockquotes, and callout boundaries unchanged.
- Keep markdown link destinations byte-for-byte unchanged and preserve the link text intent.
- Keep inline code, fenced code, placeholders, XML-like tags, citation handles, bibliography keys, URLs, version strings, and file paths unchanged where they are protected.
- Do not translate items in DO_NOT_TRANSLATE_ENTITIES.
- Rewrite idioms, metaphors, sentence rhythm, and connective phrasing by meaning when a literal transfer would sound imported or translated.
- Preserve specificity, nuance, and caveats. Do not flatten strong opinions into generic neutral prose.
- Keep the JSON contract exact and return only the final artifact JSON.

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
- Include all required keys with correct primitive types.

BEGIN_OUTPUT_JSON
{
  "title": "string",
  "excerpt": "string",
  "tags": ["string"],
  "content": "string"
}
END_OUTPUT_JSON
