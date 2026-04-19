# dan.rio

Minimal bilingual blog (EN / PT-BR) with smooth View Transitions. Static site generator built with Python.

## Structure

```
blog/
├── _source/              # Build system and content
│   ├── posts/            # Markdown blog posts (source of truth)
│   ├── build.py          # Build orchestrator (entry point)
│   ├── config.py         # Site configuration (paths, languages, metadata)
│   ├── helpers.py        # Pure utilities (hashing, formatting, dates, paths)
│   ├── renderer.py       # All HTML page generation (posts, index, about, CV, landing)
│   ├── seo.py            # JSON-LD structured data and sitemap generation
│   ├── content_loader.py # Markdown parsing and sidecar metadata manifest
│   ├── cv_parser.py      # CV YAML loading and schema validation
│   ├── paths.py          # Filesystem constants and directory creation
│   ├── translator.py     # Translation validation helpers
│   └── translation_v2/   # OpenCode translation pipeline
├── _cache/               # Build artifacts (git-ignored)
│   ├── translation-cache.json
│   └── post-metadata.json
├── static/               # Shared assets
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript
│   └── images/           # Images
├── en/                   # Generated English site
├── pt/                   # Generated Portuguese site
├── cv_data.yaml          # CV source of truth (structured YAML, parsed at build time)
├── index.html            # Landing page (served at dan.rio/)
├── sitemap.xml           # Generated sitemap with hreflang
├── build.sh              # Unix build wrapper
└── build.bat             # Windows build wrapper
```

## Quick Start

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras

# Build site (from project root)
uv run python _source/build.py

# Or use wrapper scripts:
./build.sh          # Unix/Linux/Mac
build.bat           # Windows

# Serve locally
uv run python -m http.server 8000
```

## Build Modes

`_source/build.py` supports two execution modes:

- **Default mode:** `python _source/build.py`
  - Runs the OpenCode translation pipeline and quality checks.
  - Translation quality issues are reported, but non-fatal issues do not stop the build.
- **Strict mode:** `python _source/build.py --strict`
  - Runs the same translation pipeline with strict quality-gate enforcement.
  - Any error-level translation validation issue fails the build.
  - Enables staged/atomic output promotion.

If you run through `uv`, use the same commands prefixed with `uv run`.

For release readiness, run strict mode before pushing to the production branch:

```bash
uv run python _source/build.py --strict
```

The validation pipeline also checks generated internal links:

```bash
uv run python _source/link_checker.py
```

And validates generated HTML syntax:

```bash
uv run --extra dev python _source/html_validator.py
```

## Writing Posts

Create Markdown files in `_source/posts/`:

```markdown
---
title: Post Title
date: 2025-10-23
excerpt: Brief description
tags: [web, python]
order: 1
---

Your content here.
```

Posts can be written in either English or Brazilian Portuguese. The build system keeps the site bilingual by translating each source post into the opposite locale at build time.

## Translation

The build translation runtime is OpenCode-only via `_source/translation_v2/`.

- `build.py` is the single interface for translation work.
- The full pipeline is always active during builds.
- Posts are translated in either direction based on the source locale: `EN -> PT-BR` or `PT-BR -> EN-US`.
- Cached translations are reused when the source and translation state have not changed.
- About and CV are translated through OpenCode by default.
- `WRITING_STYLE.md` is loaded into prompt context so translations preserve voice, structure, and understated humor.
- `_source/translation_revision.yaml` can mark specific slug/locale pairs for reassessment.
- `--skip-about-cv-translation` exists for focused one-file/debug runs where About/CV API calls should be skipped.
- Build quality checks validate translated pairs in the active direction for each source post.

Translations are stored in `_cache/translation-cache.json` with source hashes and workflow metadata, so unchanged content can be reused without another model call.

Operational commands:

```bash
# Full build
uv run python _source/build.py

# Full build with strict quality-gate enforcement
uv run python _source/build.py --strict

# One-file run
uv run python _source/build.py --post _source/posts/<post-file>.md

# One-file focused bypass (skip About/CV translation)
uv run python _source/build.py --post _source/posts/<post-file>.md --skip-about-cv-translation
```

To request a revision pass for an existing translation, add an entry to `_source/translation_revision.yaml`:

```yaml
posts:
  dont-outsource-the-thinking:
    pt-br:
      reason: revisit early AI Studio translation
      notes: keep the dry humor and connective tissue tighter
```

Revision behavior:

- Legacy AI Studio translations are treated as revision candidates by default.
- A matching revision marker first reassesses the existing translation against the current source text.
- If the existing translation is salvageable, the build runs `critique -> refine` on that translation.
- If revision does not converge cleanly, the build falls back to the full translation loop.
- Once a marked revision succeeds, the refreshed translation is cached and reused until the source or revision marker changes.

See [`docs/translation_v2_opencode_runbook.md`](docs/translation_v2_opencode_runbook.md) for operational triage details.

For deterministic translation_v2 provider tests with no network usage:

```bash
uv run --extra dev pytest tests/test_translation_v2_mock_provider.py -q
uv run --extra dev pytest tests/test_build_translation_v2_integration.py -q
uv run --extra dev pytest tests/test_translation_v2_onefile_lane.py -q
```

### Canonical one-file translation_v2 lane (fast CI/debug path)

Use this command to validate the one-file translation flow end-to-end in test mode:

```bash
uv run --extra dev pytest tests/test_translation_v2_onefile_lane.py -q
```

- Runtime ceiling: set `TRANSLATION_V2_ONEFILE_MAX_SECONDS` (default `45`) to bound lane runtime.
- Build logs print `run_id=<...>` and `artifact_dir=<...>` so each run can be traced.
- Artifacts are persisted under `_cache/translation-runs/<run_id>/` for CI upload/debugging.

## Configuration

Edit `_source/config.py`:

```python
BASE_PATH = ""       # Local development / root domain
# or
BASE_PATH = "/blog"  # GitHub Pages subdirectory
```

## Deployment

### GitHub Pages

This repo is currently deployed with GitHub Pages by publishing generated static files from the repository.

Recommended publish flow:

1. Set `BASE_PATH` in `_source/config.py`
2. Run `uv run python _source/build.py --strict`
3. Commit generated files (`en/`, `pt/`, `index.html`, `sitemap.xml`)
4. Push to the GitHub Pages branch/source (for this repo, typically `main`)
5. Ensure `.nojekyll` exists when serving from repository root

## Pages

- **Blog** — Post index with filtering (year/month/tag) and sorting
- **About** — Author bio (translated to PT-BR via OpenCode at build time)
- **CV** — Parsed from `cv_data.yaml`, translated via OpenCode at build time

## Features

- **Bilingual**: Automatic EN ↔ PT-BR translation with OpenCode pipeline
- **View Transitions API**: Smooth page morphing between routes
- **FLIP Animations**: Card sorting and reordering
- **Theme Toggle**: Dark/light mode
- **Language Continuity**: Preserves scroll position and filters across language switches
- **SEO**: JSON-LD structured data, Open Graph, hreflang sitemap

## Browser Support

Full experience: Chrome/Edge 111+
Graceful degradation for other browsers.

## Stack

- Python (markdown, frontmatter, pyyaml, python-dotenv)
- OpenCode headless runner (translation_v2)
- View Transitions API (Chromium)
- Vanilla JS + CSS animations
- No build tools or frameworks
