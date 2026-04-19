# ADR 13: Locale-Aware Localization Policy

## Status

Accepted

## Context

Translation quality failures were not limited to meaning. The real failures were often in voice, borrowing choices, connective texture, punctuation rhythm, and the social fit of the target locale. This was especially visible in PT-BR, where the difference between readable translation and publishable localized prose is often decided by context-wide term policy, discourse movement, and register rather than by dictionary equivalence.

Generic “translate naturally” prompts were not enough. The system needed an explicit locale policy layer so that localization choices were made deliberately and consistently across an artifact.

## Decision

The translation runtime will use explicit localization briefs as first-class runtime inputs.

Current locale references live under `_source/translation_v2/references/`:

- `pt_br_localization_brief.md`
- `en_us_localization_brief.md`

Locale policy is also encoded in `_source/translation_v2/locale_rules.py`, which carries:

- glossary preferences
- borrowing conventions
- punctuation conventions
- discourse conventions
- register conventions
- review checks

The runtime uses this policy in:

- source analysis
- terminology policy
- translation
- critique
- revision
- final review

Terminology decisions are artifact-wide, not sentence-local. The system distinguishes:

- terms to keep in the source language
- terms to localize
- context-sensitive terms
- protected entities and product names

Locale naturalness, borrowing consistency, and rhetorical structure are explicit review concerns rather than vague quality aspirations.

## Consequences

Localization quality is now modeled as policy, not just taste. This makes the system more inspectable and makes future regressions easier to reason about.

The prompts become more specific, but also more constrained by explicit editorial logic. That is a deliberate tradeoff. A localization system that is supposed to preserve voice and register should not be improvising its locale methodology from scratch on every run.

This also makes translation quality a more durable architectural surface. Changing the locale brief or borrowing policy is now a meaningful system change and should be treated accordingly.
