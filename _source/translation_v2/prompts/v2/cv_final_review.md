FINAL REVIEW
Review the revised CV as the final linguistic gate.

Accept only if all of these are true:
- the CV remains faithful to the source
- the professional wording reads as native {{target_locale}} material
- terminology choices are internally consistent
- the candidate's seniority and achievement signals remain intact
- invariant fields and JSON structure remain intact
- every critique finding was either fixed or explicitly declined for a valid protection-rule reason

LOCALE DIRECTION
- Source locale: {{source_locale}}
- Target locale: {{target_locale}}
- Translation direction: {{locale_direction}}

SOURCE ANALYSIS JSON
{{source_analysis_json}}

TERMINOLOGY POLICY JSON
{{terminology_policy_json}}

SOURCE CV JSON
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
