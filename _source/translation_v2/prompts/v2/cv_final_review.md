FINAL REVIEW
Review the revised CV as the final linguistic gate.

Accept only if all of these are true:
- the CV remains faithful to the source
- the professional wording reads as native {{target_locale}} material
- terminology choices are internally consistent
- borrowing choices, punctuation, and hiring-register wording fit native editorial usage in {{target_locale}}
- the candidate's seniority and achievement signals remain intact
- education degree localization is handled consistently and matches the settled terminology policy
- invariant fields and JSON structure remain intact
- every critique finding was either fixed or explicitly declined for a valid protection-rule reason
- the critique findings and revision report agree with the actual revised CV; do not approve if the report claims a fix that is not visible in the artifact

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

SOURCE CV JSON
{{source_markdown}}

REVISED CANDIDATE JSON
{{translated_json}}

REVIEW INSTRUCTIONS
- Use critique_json explicitly to verify that each finding was resolved, validly declined, or remains an issue.
- Use revision_report_json explicitly to verify that claimed applied fixes, declined findings, and protected-field exceptions match the revised CV.
- Verify that every education.degree value follows the settled degree-localization policy in terminology_policy_json. Do not accept mixed handling unless the policy explicitly allows it.
- If critique_json and revision_report_json disagree, treat the mismatch as a residual issue and do not infer that the revision is complete.

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
