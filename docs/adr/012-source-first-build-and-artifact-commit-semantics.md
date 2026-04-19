# ADR 12: Source-First Build and Artifact Commit Semantics

## Status

Accepted

## Context

The build used to behave too much like a phase-batched pipeline. Translation could succeed for one artifact, but that success might remain only in memory until much later in the build. If a later artifact failed, already accepted work could fail to reach live output during that run, which made the system operationally brittle and made failures harder to reason about.

The build also needed to distinguish between source rendering and translation work more clearly. A bilingual blog is not just a translation process. It is a build that first has to render the source-language site correctly, then localize the complementary surfaces.

## Decision

The build will be source-first.

The execution order is:

1. Parse source artifacts.
2. Render and write source-language post outputs.
3. Render and write source-language static pages.
4. Update source indexes and sitemap.
5. Initialize the translation runtime.
6. Run the static translation lane (`about`, `cv`).
7. Run the post translation lane.

Accepted translation work becomes durable immediately. Once an artifact is accepted, the build must:

- persist translation cache
- persist run artifacts
- render and write the translated HTML output
- update dependent outputs when applicable

This is the artifact commit point.

The build keeps static translation (`about`, `cv`) as a separate lane from post translation, but both obey the same durability semantics.

If a cached translation exists but the translated HTML output is missing, the build does not blindly re-render from cache. It marks the artifact for revision and re-enters the normal workflow.

## Consequences

Source outputs are no longer blocked behind translation work. In direct mode, the source-language site can be live even if translation later fails.

Accepted translation work is durable within the same run. The system no longer behaves as if an accepted translation only “counted” after the entire rest of the build happened to succeed. This makes the build more honest and reduces wasted rework.

The build is also easier to observe because source rendering and translation are now distinct lanes with different semantics, rather than one long blended loop.
