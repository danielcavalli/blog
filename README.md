# dan.rio

Minimal bilingual blog built with a custom Python static site generator.

The site is published as generated static HTML under `en/`, `pt/`, `index.html`, and `sitemap.xml`. Source content lives under `_source/`. Translation is handled by the `translation_v2` runtime during the build.

## Structure

```text
blog/
├── _source/
│   ├── posts/                    # Markdown source posts
│   ├── build.py                  # Build orchestrator / CLI entrypoint
│   ├── content_loader.py         # Markdown parsing + post metadata sidecar
│   ├── renderer.py               # HTML rendering for all page types
│   ├── seo.py                    # Sitemap + structured data
│   ├── translation_common.py     # Build-side translation validation helpers
│   ├── translation_revision.yaml # Revision requests for specific artifacts
│   └── translation_v2/           # OpenCode translation runtime
│       ├── prompts/v2/           # Active prompt pack
│       ├── references/           # Locale briefs and localization references
│       └── ...                   # Orchestrator, contracts, cache adapter, etc.
├── _cache/                       # Build-time state (git-ignored)
│   ├── post-metadata.json        # Source change detection manifest
│   ├── translation-cache.json    # Accepted translation cache
│   └── translation-runs/         # Per-run artifacts and debug traces
├── docs/
│   ├── adr/                      # Architecture decision records
│   └── translation_v2_opencode_runbook.md
├── static/                       # Shared CSS, JS, images
├── en/                           # Generated English site
├── pt/                           # Generated Portuguese site
├── cv_data.yaml                  # Structured CV source of truth
├── index.html                    # Generated landing page
└── sitemap.xml                   # Generated sitemap
```

## Quick Start

```bash
uv sync --all-extras
uv run python _source/build.py
uv run python -m http.server 8000
```

## Build Model

The current build is source-first.

1. Parse all source posts.
2. Render source-language outputs first.
3. Render source indexes and sitemap.
4. Initialize the translation runtime.
5. Translate static artifacts (`about`, `cv`) and commit accepted outputs immediately.
6. Translate posts and commit accepted outputs immediately.

“Commit” means:
- persist accepted translation state to `_cache/translation-cache.json`
- persist per-run artifacts under `_cache/translation-runs/<run_id>/`
- render and write the corresponding HTML output immediately

This means accepted work is durable even if a later artifact fails.

## Build Modes

### Default mode

```bash
uv run python _source/build.py
```

- Builds source outputs
- Runs `translation_v2`
- Logs quality issues but continues on build-side validation errors

### Strict mode

```bash
uv run python _source/build.py --strict
```

- Same runtime, but build-side error-level translation validation fails the build
- Uses staged/atomic output promotion

### One-file mode

```bash
uv run python _source/build.py --post _source/posts/<post-file>.md
```

### One-file mode without About/CV translation

```bash
uv run python _source/build.py --post _source/posts/<post-file>.md --skip-about-cv-translation
```

## Translation Runtime

Build-time translation is OpenCode-only and lives under `_source/translation_v2/`.

The active stage graph is:

1. `source_analysis`
2. `terminology_policy`
3. `translate`
4. `critique`
5. `revise`
6. `final_review`

Current model split:
- translation: `GPT-5.4` with high reasoning
- revision: `GPT-5.4` with high reasoning
- critique: `GPT-5.2`
- final review: `GPT-5.2`

The runtime also loads:
- [WRITING_STYLE.md](WRITING_STYLE.md)
- locale briefs under [`_source/translation_v2/references/`](./_source/translation_v2/references/)

### Translation state

There are three distinct persistence layers:

- `_cache/post-metadata.json`
  - source-side content hash and timestamp tracking
- `_cache/translation-cache.json`
  - accepted translation cache
- `_cache/translation-runs/<run_id>/`
  - per-run prompts, structured responses, stage events, runner logs

### Revision requests

Use `_source/translation_revision.yaml` to force reassessment of a specific artifact/locale pair:

```yaml
posts:
  some-post-slug:
    pt-br:
      reason: revisit locale naturalness
      notes: preserve connective tissue and dry humor
```

Operational triage details live in [docs/translation_v2_opencode_runbook.md](docs/translation_v2_opencode_runbook.md).

## Validation

The build runs two different quality layers:

1. Translation-stage review inside `translation_v2`
   - critique
   - revision
   - final review

2. Build-side deterministic validation in `_source/translation_common.py`
   - untranslated overlap checks
   - repeated identical sentence detection
   - malformed code fence / HTML tag checks
   - suspicious length warnings

Default mode logs these issues and continues.
Strict mode fails on error-level build-side validation issues.

Additional validation commands:

```bash
uv run python _source/link_checker.py
uv run --extra dev python _source/html_validator.py
```

## Testing

Focused translation/runtime suites:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest \
  tests/test_build_translation_v2_integration.py \
  tests/test_build_translation_routing_integration.py \
  tests/test_translation_v2_boundaries.py \
  tests/test_translation_prompt_versions.py \
  tests/test_translation_locale_rules.py -q
```

One-file lane regression:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv run --extra dev pytest \
  tests/test_translation_v2_onefile_lane.py -q
```

## Deployment

Generated HTML is committed to git and served directly by GitHub Pages.

Recommended release flow:

```bash
uv run python _source/build.py --strict
git add en pt index.html sitemap.xml
git commit -m "publish: update generated site"
git push
```

## ADRs

The repo’s major architecture and translation-policy decisions are tracked under [docs/adr/](docs/adr/).
