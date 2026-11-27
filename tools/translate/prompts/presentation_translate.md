TRANSLATE
Produce a localized presentation draft that preserves the author's voice, argumentative structure, slide rhythm, and rhetorical layering while reading as native {{target_locale}} prose.

Execution rules:
- Translate from {{source_locale}} to {{target_locale}}.
- Preserve markdown structure and semantics exactly.
- Keep heading levels, list nesting, tables, blockquotes, and callout boundaries unchanged.
- Preserve presentation slide markers exactly: `<!-- presentation:slide ... -->` and `<!-- /presentation:slide -->` must remain byte-for-byte unchanged, including ids, layout, density, spacing, and order. The same holds for every other `<!-- presentation:... -->` comment (blocks, cards, columns).
- Keep markdown link destinations byte-for-byte unchanged and preserve the link text intent. The one exception is a link to another document of this site (a sibling `.md` file): it points to that document's file in {{target_locale}}, and LINKS TO OTHER DOCUMENTS gives the exact destination to write for each one.
- Keep every image's path byte-for-byte unchanged. Translate its alt text and its title (the quoted text after the path, which the page shows as the picture's caption).
- Keep inline code, placeholders, XML-like tags, citation handles, bibliography keys, URLs, version strings, and file paths unchanged where they are protected.
- Preserve fenced-code delimiters and language labels. Localize reader-facing simulated dialogue/transcript prose inside plain text fences when it is part of the presentation, while preserving technical identifiers, commands, paths, URLs, and real code semantics.
- Do not translate items in DO_NOT_TRANSLATE_ENTITIES.
- Rewrite idioms, metaphors, sentence rhythm, connective phrasing, and clause order by meaning when a literal transfer would sound imported or translated.
- Preserve authorial voice without preserving English sentence shape. Rebuild the sentence if that is what {{target_locale}} needs.
- Use terms consistently according to the human locale guidance and glossary. Resolve terminology in context using the locale references, preserving native register and source meaning.
- Normalize punctuation and paragraph flow to the target locale instead of reproducing source-language pacing.
- Preserve specificity, nuance, and caveats. Do not flatten strong opinions into generic neutral prose.
- Keep slide content concise enough for presentation use. Prefer sharper target-language phrasing over word-for-word expansion.
- For PT-BR presentation prose, prefer natural editorial terms over mechanical technical calques: use "resultado" or "resposta" for model output unless the source clearly means a technical output artifact; use "deriva" for drift unless terminology policy explicitly preserves the English borrowing; use "esquema" or "esquemas" for schema/schemas in prose unless it is a literal code token; use "base de conhecimento" for the concept and reserve "KB" for a named/system shorthand.
- For PT-BR editorial prose, prefer formal relative constructions such as "Tudo o que" when they read more polished than conversational shortcuts.
- Keep the JSON contract exact and return only the final artifact JSON.

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

WRITING STYLE BRIEF
{{writing_style_brief}}

GLOSSARY
{{glossary_entries}}

DO_NOT_TRANSLATE_ENTITIES
{{do_not_translate_entities}}

LOCALE REVIEW CHECKS
{{review_checks}}

OUTPUT CONTRACT
- Return exactly one JSON object.
- Do not wrap in markdown fences.
- Include all required keys with correct primitive types.
- `title`, `excerpt` and `tags` are the source front matter's, translated. Where the source has no excerpt, return an empty string; where it has no tags, an empty list.
- `content` is the complete translated Markdown body, without front matter.

BEGIN_OUTPUT_JSON
{
  "title": "string",
  "excerpt": "string",
  "tags": ["string"],
  "content": "string"
}
END_OUTPUT_JSON
