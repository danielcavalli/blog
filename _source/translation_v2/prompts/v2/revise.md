REVISE
Rewrite the translated candidate using the source artifact and critique.

Revision rules:
- Localize the entire candidate against the source and the human locale brief. This pass is required even when critique says no refinement is needed.
- Read each paragraph as target-language writing. Reconstruct any imported syntax, stiff abstraction, bureaucratic phrasing, or copied punctuation from the paragraph's meaning. A critic's silence or approval does not establish that a passage is correct.
- Preserve passages that already satisfy the source and locale guidance. Fix justified critique findings, but do not limit your work to the critic's list.
- Explain substantive locale-driven rewrites in the revision report, including improvements the critic missed. Do not make a glossary substitution stand in for a prose revision.
- Treat critique as an editorial proposal. Decline a finding that misreads the source or demands source-language grammar at the expense of natural target-locale expression; explain the preserved meaning in declined_feedback.
- Re-anchor disputed passages in the source rather than paraphrasing the draft loosely.
- Preserve voice, rhetorical layering, and target-locale fluency while correcting accuracy or terminology defects.
- When the draft sounds translated, rewrite the full sentence or paragraph instead of patching individual words.
- Repair borrowing drift, punctuation drift, and connective drift so the result reads as authored {{target_locale}} prose.
- Keep markdown structure unchanged.
- Keep markdown links, URLs, inline code, fenced code, placeholders, citations, and DO_NOT_TRANSLATE_ENTITIES unchanged where protected.
- If a critique request conflicts with a protection rule, keep the protected text unchanged and record the reason in declined_feedback.
- applied_feedback should describe actual edits; declined_feedback records justified non-edits.
- Keep source claims and protected material intact when declining a finding. Locale naturalness never permits changing a fact, an actor's responsibility, or the force of a qualification.

LOCALE DIRECTION
- Source locale: {{source_locale}}
- Target locale: {{target_locale}}
- Translation direction: {{locale_direction}}

LOCALIZATION BRIEF
{{localization_brief}}

SOURCE ANALYSIS JSON (MODEL ADVICE)
{{source_analysis_json}}

TERMINOLOGY POLICY JSON (MODEL PROPOSAL)
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
  "declined_feedback": [{"finding_id": "string", "status": "declined", "rationale": "string"}],
  "rewrite_summary": ["string"],
  "unresolved_risks": ["string"]
}
END_OUTPUT_JSON

TRANSLATED CANDIDATE JSON
{{translated_json}}

CRITIQUE JSON
{{critique_json}}
