FINAL REVIEW
Review the revised artifact as the final linguistic gate.

Accept only if all of these are true:
- the revised artifact is faithful to the source
- the prose reads as native {{target_locale}} writing rather than translated carryover
- terminology choices are internally consistent
- voice, force, and rhetorical layering still feel authored
- markdown structure and all protected material remain intact
- every critique finding was either fixed or explicitly declined for a valid protection-rule reason

LOCALE DIRECTION
- Source locale: {{source_locale}}
- Target locale: {{target_locale}}
- Translation direction: {{locale_direction}}

SOURCE ANALYSIS JSON
{{source_analysis_json}}

TERMINOLOGY POLICY JSON
{{terminology_policy_json}}

SOURCE MARKDOWN
{{source_markdown}}

REVISED CANDIDATE JSON
{{translated_json}}

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
