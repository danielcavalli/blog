# ADR 16: Durable translations and recoverable publication

| Field | Value |
| --- | --- |
| Author(s) | Daniel Cavalli |
| Date | 2026-09-05 |

## Status

Accepted. Supersedes the build/cache lifecycle in ADRs 11 and 12. Retains the
editorial stage graph, locale policy, and validation distinction from ADRs 13–15.

## Problem

Accepted translations were reachable only by a cache key that included every
prompt, the writing style, and the translation model. Updating those settings
made unchanged source artifacts run through translation again. Missing rendered
HTML also triggered editorial revision. Concurrent cache writers could overwrite
each other's work, and a focused staged build replaced entire language directories.

## Decision

Accepted translations are versioned source artifacts under `_source/translations`.
Each artifact/locale has an atomic current pointer and immutable content-addressed
revisions. A revision contains the source text and translatable frontmatter,
translated output, parent revision, and generation or migration provenance.
Git tracks these records. They survive removal of all build caches.

Source freshness is independent of the generation recipe. Body, translatable
frontmatter, source/target locale, and artifact identity determine freshness.
Changing models, prompts, or style does not revoke a previous acceptance.

`translations.py` owns import, update, candidate comparison, and acceptance.
New and revised candidates pass the existing editorial pipeline and deterministic
artifact shape checks. Strict mode additionally enforces the existing translation
heuristics. Owner revision notes and previous final-review findings are explicit
inputs to subsequent stages. Updates use optimistic concurrency and retain history.
Program code and link destinations remain protected. Mermaid flowchart labels and
accessibility text are translatable while diagram structure and configuration stay
invariant.

`build.py` renders source and accepted translations without model calls. Missing or
outdated accepted content stops publication. Missing HTML is reconstructed from
accepted content. A focused build changes only its selected output; skipping static
pages preserves both languages.

The builder reads accepted records directly. It does not initialize the translation
runtime, load authoring guidance, or write translation cache entries. Each post and
collection is rendered once, and all builds use staged publication. The unused
Gemini implementation, its dependencies, and its build-time compatibility tests
have been removed. Import remains available for verified historical V2 cache entries.

The update command has one runtime: the V2 editorial stage graph followed by
validated acceptance. The duplicate cache-backed orchestrator, cache writer,
deferred persistence callbacks, unused forwarding modules, and eager package
exports are removed. Historical cache import remains a read-only migration tool;
it does not require keeping an obsolete generation path alive.

Markdown parsing is read-only. Publication dates come from frontmatter; the unused
post-metadata manifest and its migration/hash/write machinery are removed. Importing
content commands creates no directories and does not import the model runtime.

Links to source posts resolve during rendering, using the target's frontmatter slug
and the reader's language. The stored Markdown remains literal in both source and
accepted translations. Articles, notes, and presentations use the same resolver;
missing targets fail staged publication. This requires no link registry or cache.

The source owns the authored argument and wording. Translation reads composition,
prose, and voice references as context; locale references determine how their effect
is preserved in PT-BR or EN-US. These references cannot authorize source editing or
reorganization of the localized argument. Source revisions and model comparisons
remain explicit content operations.

Stages use disposable checkpoints keyed by the full effective prompt, model,
reasoning effort, and contracts. Successful stages can be resumed after later
failures. Model processes have bounded timeouts and are terminated on interruption.

Publication uses a build lock, complete staged HTML/link validation, per-file
replacement, and a durable transaction journal with backups. Failure rolls back
all touched files; the next build recovers a process crash before starting work.
This is a recoverable multi-file transaction, not a claim of a single atomic
filesystem snapshot. GitHub Pages receives the completed generated tree via Git.

## Migration and model upgrades

Import verifies legacy entries against their original source/recipe fingerprints.
If run artifacts recover only an older source, that revision is retained as stale;
the importer never mislabels it as current or overwrites accepted content.

Model experiments use a separate candidate store. Acceptance checks current source
identity and the baseline accepted revision. Existing accepted translations remain
available until a replacement is accepted. Fixture scores are regression evidence,
not proof that a new model improves editorial quality.
