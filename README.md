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
│   └── translator.py     # Multi-agent translation pipeline
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

Posts are written in English. The build system automatically translates them to Brazilian Portuguese using the Gemini API.

## Translation

The build uses a multi-agent translation pipeline (`_source/translator.py`) powered by Gemini 2.5 Flash:

- **Default mode**: Translation Agent only (fast, one API call per post)
- **Strict mode** (`--strict` flag or `STRICT_BUILD=1`): Full 3-stage pipeline (Translation → Critique → Refinement)

Translations are cached in `_cache/translation-cache.json` using SHA-256 content hashes. Unchanged posts skip the API entirely.

Requires `GEMINI_API_KEY` environment variable (see `.env.example`).

See [TRANSLATION_PIPELINE.md](TRANSLATION_PIPELINE.md) for full details.

## Configuration

Edit `_source/config.py`:

```python
BASE_PATH = ""       # Local development / root domain
# or
BASE_PATH = "/blog"  # GitHub Pages subdirectory
```

## Deployment

1. Set `BASE_PATH` in `_source/config.py`
2. Run `python _source/build.py`
3. Commit generated files (`en/`, `pt/`, `index.html`, `sitemap.xml`)
4. Push to GitHub
5. Ensure `.nojekyll` exists

## Pages

- **Blog** — Post index with filtering (year/month/tag) and sorting
- **About** — Author bio (auto-translated to PT-BR at build time)
- **CV** — Parsed from `cv_data.yaml`, translated at build time

## Features

- **Bilingual**: Automatic EN ↔ PT-BR translation via Gemini API
- **View Transitions API**: Smooth page morphing between routes
- **FLIP Animations**: Card sorting and reordering
- **Theme Toggle**: Dark/light mode
- **Language Continuity**: Preserves scroll position and filters across language switches
- **SEO**: JSON-LD structured data, Open Graph, hreflang sitemap

## Browser Support

Full experience: Chrome/Edge 111+
Graceful degradation for other browsers.

## Stack

- Python (markdown, frontmatter, google-genai, pyyaml, python-dotenv)
- Gemini 2.5 Flash (translation)
- View Transitions API (Chromium)
- Vanilla JS + CSS animations
- No build tools or frameworks
