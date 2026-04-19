# ADR 15: Current Testing and Validation Strategy

## Status

Accepted

## Context

The original test strategy was built around a smaller and less integrated system. Since then, the repo has grown a real translation runtime, a source-first build order, artifact-commit semantics, deterministic translation validation, and a larger body of regression tests that pin behavior across the build, cache, and localization layers.

The project still deliberately avoids a heavyweight toolchain. CI should remain fast, deterministic, and free of live provider calls.

## Decision

We will keep pytest as the single test framework and use focused regression suites rather than trying to exercise live provider behavior in CI.

The test strategy is split across:

- pure helper and renderer tests
- build integration tests
- translation runtime contract tests
- cache/revision boundary tests
- locale-policy and prompt-policy tests
- one-file lane regression tests

CI does not run live provider calls. Instead, it relies on:

- mock provider coverage
- structured fixture coverage
- focused integration tests that exercise build orchestration without network dependency

Validation also includes focused non-pytest commands where appropriate:

- `html_validator.py`
- `link_checker.py`
- targeted build commands for source/render regression checks

## Consequences

The validation strategy is stronger than the earlier pure-unit approach while still avoiding the cost and instability of live translation in CI.

The test suite now documents the system more effectively. Build order, revision semantics, cache behavior, prompt/version wiring, and locale-policy expectations are all pinned explicitly.

The tradeoff is that some real provider behaviors still require local operational validation. That is acceptable for a personal static site so long as the repo preserves focused, high-signal regression coverage around everything the project controls directly.
