# ADR 14: Translation Quality Gates and Validation Split

## Status

Accepted

## Context

The project now has two different kinds of translation quality logic:

1. model-mediated editorial review inside `translation_v2`
2. deterministic build-side validation in `_source/translation_common.py`

These layers solve different problems. Treating them as one thing makes failures harder to interpret. A translation can be accepted by the model-side review loop and still trigger build-side validator flags because the deterministic checks are looking for structurally suspicious patterns such as untranslated overlap or malformed output.

The build also supports two operator modes, default and strict, so the consequences of those flags must be explicit.

## Decision

We will keep a split between model-side review and build-side deterministic validation.

Model-side review is responsible for:

- fidelity
- terminology
- locale naturalness
- rhetorical structure
- revision and final acceptance

Build-side validation is responsible for:

- untranslated overlap heuristics
- repeated identical sentence detection
- malformed code fence checks
- malformed HTML/tag checks
- suspicious length warnings

The build will always run deterministic validation after translation output is returned to `build.py`.

Mode semantics are:

- default mode:
  - logs build-side error-level issues
  - continues unless the translation runtime itself fails
- strict mode:
  - fails the build on build-side error-level validation issues

This split is part of the intended system behavior, not an inconsistency.

## Consequences

Translation failures are easier to classify. A provider or final-review failure means the localization workflow did not converge. A build-side validation failure means the returned output still matched a deterministic suspicion rule.

This also means “accepted by the translation pipeline” does not imply “passed every build-side heuristic.” That distinction is useful and should remain visible in logs and operational triage.

The downside is that operators need to understand two layers of quality logic. That is acceptable because they correspond to two different kinds of risk and produce more useful debugging information than a single blended quality number.
