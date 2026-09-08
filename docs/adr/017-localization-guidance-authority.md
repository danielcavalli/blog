# Localization guidance governs model advice

Status: accepted, 2026-09-07.

The source and guidance authority remain in force. The multi-stage workflow below
is superseded by [unattended localization](018-unattended-localization.md).

Daniel made following the localization guidance the primary requirement. The
Maré PT-BR failure showed why stronger exhortations alone were insufficient:
the critic approved stiff Portuguese, its terminology proposal became a binding
preference, and revision mostly implemented the critic's list. A later score
of 94 for locale naturalness did not resolve those defects.

The source governs claims, agency, qualifications, emphasis, and structure. Human
locale guidance governs expression. Author instructions and protected source
material remain binding. Authoring references explain the voice; their English
examples do not prescribe Portuguese sentence structure.

Generated analysis and terminology are proposals. They cannot override human
guidance, and model-proposed entities are no longer merged into the human
do-not-translate list. A conventional, consistent borrowing is not an error just
because another model prefers a more formal synonym.

Every requested translation or revision gets a full source-grounded localization
pass. The critic cannot bypass that work with `needs_refinement: false`. The
writer must examine the whole candidate and may decline mistaken critique. It
preserves wording that already meets the source and locale guidance.

Final review independently compares the current source and candidate with the
human guidance. Earlier generated analysis, terminology, verdicts, and revision
reports are excluded from its input. Remaining issues require a concrete passage
and a relevant source or guidance violation; a positive verdict cannot overrule
nonempty residual issues. Scores are diagnostic data, never acceptance criteria.

The V2 stages and model defaults remain. The extra localization pass costs a
model call when a critic would previously have skipped it. Accepted translations
remain durable: normal builds and updates of unchanged accepted content make no
model calls. Prompt changes do not invalidate accepted text. Deterministic
structure, code, link, and protected-content checks still run before acceptance.

Validation combines deterministic tests of these authority boundaries with live
localization of the reported failure and continuous editorial reading of the
result. No deterministic test or model score can by itself prove native prose.
