FINAL REVIEW
Review the localized About page as the final linguistic gate.

Accept only if all of these are true:
- the About page is faithful to the source
- the prose reads as native {{target_locale}} writing rather than translated carryover
- terminology choices are internally consistent
- borrowing choices, punctuation, and discourse movement fit native editorial usage in {{target_locale}}
- voice, force, humor, and autobiographical structure still feel authored
- markdown structure and all protected material remain intact
- if critique_json.needs_refinement is true, every critique finding was either fixed or explicitly declined for a valid protection-rule reason
- if critique_json.needs_refinement is false, absence of revision_report changes is expected; do not reject merely because informational or minor findings were not applied
- when a revision report exists, the critique findings and revision report agree with the actual About page; do not approve if the report claims a fix that is not visible in the artifact

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

CRITIQUE JSON
{{critique_json}}

REVISION REPORT JSON
{{revision_report_json}}

SOURCE MARKDOWN
{{source_markdown}}

REVISED CANDIDATE JSON
{{translated_json}}

REVIEW INSTRUCTIONS
- Use critique_json explicitly to verify whether findings require revision.
- Use revision_report_json explicitly to verify claimed applied fixes, declined findings, and protection-based exceptions when critique_json.needs_refinement is true.
- If critique_json.needs_refinement is false, evaluate the About page directly and reject only for material defects that make it not publish-ready.
- If critique_json.needs_refinement is true and critique_json and revision_report_json disagree, treat the mismatch as a residual issue and do not infer that the revision is complete.

OUTPUT CONTRACT
- Return exactly one JSON object.
- Do not wrap in markdown fences.

BEGIN_OUTPUT_JSON
{
  "accept": true,
  "publish_ready": true,
  "confidence": 1.0,
  "residual_issues": ["string"],
  "voice_score": 0,
  "terminology_score": 0,
  "locale_naturalness_score": 0
}
END_OUTPUT_JSON
