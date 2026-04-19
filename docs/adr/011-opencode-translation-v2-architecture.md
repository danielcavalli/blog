# ADR 11: OpenCode Translation v2 Architecture

## Status

Accepted

## Context

The original translation system was designed under an earlier constraint set and eventually became too loose in exactly the wrong places. It could produce translations that were structurally acceptable and semantically understandable while still flattening voice, drifting on terminology, and behaving like a sentence-level translator with a quality score attached. It also concentrated too much responsibility in one legacy module and tied too much behavior to provider-specific assumptions.

By the time translation became a core publishing path rather than an experiment, the project needed a runtime that was easier to reason about, easier to inspect, and better aligned with localization rather than plain semantic transfer. The system also needed clearer contracts between stages, explicit prompt packs, durable run artifacts, and a model split that matched the actual jobs being done.

## Decision

We will use `translation_v2` as the active translation runtime for all build-time localization work. The build runtime is OpenCode-only.

The active stage graph is:

1. `source_analysis`
2. `terminology_policy`
3. `translate`
4. `critique`
5. `revise`
6. `final_review`

These stages are implemented as structured contracts under `_source/translation_v2/`, with prompt files under `_source/translation_v2/prompts/v2/` and locale/reference material under `_source/translation_v2/references/`.

Model responsibilities are split by job:

- translation: `GPT-5.4` with high reasoning
- revision: `GPT-5.4` with high reasoning
- critique: `GPT-5.2`
- final review: `GPT-5.2`

The runtime persists:

- accepted translation cache entries in `_cache/translation-cache.json`
- per-run artifacts in `_cache/translation-runs/<run_id>/`
- machine-readable stage events in `stage-events.jsonl`

The provider/orchestrator boundary is explicit. The build calls the orchestrator, the orchestrator resolves cache/revision state and contracts, and the provider implementation handles the model invocation details.

## Consequences

The translation system is now easier to inspect because every stage has a stable artifact surface. A failed translation run no longer collapses into a provider error string with no anatomy. The repo also has a cleaner separation between orchestration, provider behavior, locale policy, prompts, and deterministic validation.

The stage graph is more expensive than a single-pass translation call, but it fits the actual problem better. Translation and revision do the difficult writing work. Critique and final review do the editorial diagnosis and acceptance work. That separation is explicit rather than being left to prompt wishfulness.

The runtime is also easier to evolve. Prompt versions, locale policy, cache policy, and scoring policy can move forward without reopening the entire build system as one monolith. This is particularly important because translation quality changes are now part of the project’s normal architectural surface, not an incidental utility.
