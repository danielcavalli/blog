FINAL REVIEW
Review the localized article directly against the source and human localization guidance.

Review method:
- Read the target prose continuously before comparing it with the source. Check every paragraph, including the opening, transitions, captions, and ending. Correct facts and grammar do not establish native writing.
- Apply the localization brief to syntax, register, connective movement, punctuation, and conventional borrowings. Look for institutional language, nested passive constructions, source-language abstractions with target-language words, and phrases a native {{target_locale}} author would reconstruct.
- Check every narrative semicolon and dash against target-locale rhythm. Do not approve a copied punctuation pattern merely because each sentence is grammatical. Code, URLs, and literal quotations have their own protection requirements.
- Compare meaning at passage level: claims, agency, uncertainty, emphasis, and humor must survive. The source's grammatical subject, clause order, metaphor, and sentence boundaries are not protected.
- Check terminology against human guidance and the actual source context. When localizing to PT-BR, conventional choices such as “app” do not become errors because another model prefers “aplicativo”.
- Keep heading levels, lists, tables, Markdown links, inline code, fenced code, placeholders, citation identifiers, HTML structure, and protected entities intact. For presentations, preserve slide markers and technical content while allowing reader-facing dialogue to be localized.
- For each remaining defect, put the exact target passage, the relevant human guidance, and the concrete failure in residual_issues. Do not manufacture findings to defend a personal preference or demand literal source grammar.
- Accept only when no source or human-guidance violation remains. A prior model's opinion, numerical score, or claimed fix cannot establish compliance.

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

GLOSSARY
{{glossary_entries}}

DO_NOT_TRANSLATE_ENTITIES
{{do_not_translate_entities}}

SOURCE MARKDOWN
{{source_markdown}}

LOCALIZED CANDIDATE JSON
{{translated_json}}

OUTPUT CONTRACT
- Return exactly one JSON object without markdown fences.
- residual_issues must be empty for acceptance; otherwise accept and publish_ready must be false.
- Numerical scores are diagnostic only and cannot excuse a guidance violation.

BEGIN_OUTPUT_JSON
{
  "accept": true,
  "publish_ready": true,
  "confidence": 1.0,
  "residual_issues": [],
  "voice_score": 0,
  "terminology_score": 0,
  "locale_naturalness_score": 0
}
END_OUTPUT_JSON
