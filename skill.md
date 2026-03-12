# dan.rio Blog — Project Skill Reference

## Project Overview
A custom **Python-based static site generator** for a bilingual (English / Portuguese-BR) personal blog.
- **Author**: Daniel Cavalli (ML Engineer at Nubank)
- **URL**: https://dan.rio
- **Hosting**: GitHub Pages with custom domain (CNAME: `dan.rio`)
- **Philosophy**: No frameworks, no heavy dependencies. Native web standards only. The site should feel like "one continuous surface that reorganizes itself" rather than discrete page loads.

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Build system | Python 3 (custom static site generator) |
| Content | Markdown with YAML frontmatter |
| Translation | Google Gemini API (`gemini-2.5-flash`) — 3-stage pipeline |
| Frontend | Vanilla HTML/CSS/JS (no frameworks) |
| Animations | View Transitions API, FLIP technique, CSS custom properties |
| Deployment | GitHub Pages (static files committed to repo) |
| Package manager | [uv](https://docs.astral.sh/uv/) with `pyproject.toml` and `uv.lock` |

### Python Dependencies
- `markdown>=3.5.0` — Markdown-to-HTML conversion
- `python-frontmatter>=1.0.0` — YAML frontmatter parsing
- `google-genai>=1.0.0` — Gemini API client for translation
- `python-dotenv>=1.0.0` — Environment variable loading
- `pyyaml>=6.0` — CV YAML parsing

## Project Structure

```
blog/
├── _source/                  # BUILD SYSTEM (source of truth)
│   ├── build.py              # Orchestrator entry point (~440 lines) — wires modules together
│   ├── config.py             # Site configuration (~160 lines) — metadata, bilingual UI strings
│   ├── helpers.py            # Pure utilities — hashing, formatting, dates, paths
│   ├── renderer.py           # HTML generation — posts, index, about, CV, landing, nav, footer
│   ├── seo.py                # JSON-LD structured data and sitemap generation
│   ├── content_loader.py     # Markdown parsing and sidecar metadata manifest
│   ├── cv_parser.py          # CV YAML loading and schema validation
│   ├── paths.py              # Filesystem constants and directory creation
│   ├── translator.py         # Multi-agent Gemini translation pipeline (~1500 lines)
│   └── posts/                # CONTENT — Markdown blog posts with YAML frontmatter
├── static/                   # HAND-WRITTEN STATIC ASSETS
│   ├── css/
│   │   ├── styles.css        # Main stylesheet (~1618 lines) — design system, View Transitions
│   │   ├── post.css          # Blog post page styles
│   │   ├── landing.css       # Landing page + morph transitions
│   │   └── cv.css            # CV page styles
│   ├── js/
│   │   ├── theme.js          # Dark/light toggle with localStorage
│   │   ├── transitions.js    # View Transitions API SPA navigation
│   │   ├── filter.js         # Post filtering with FLIP animations
│   │   └── landing.js        # Landing→site morph orchestration
│   └── images/
│       └── Logo.png          # Site logo
├── en/                       # GENERATED — English HTML output (tracked in git)
├── pt/                       # GENERATED — Portuguese HTML output (tracked in git)
├── _cache/                   # Git-ignored — translation cache, post metadata JSON
├── .github/                  # AI agent design documentation
│   ├── copilot-instructions.md
│   ├── design-philosophy.md
│   └── ui-motion-philosophy.md
├── index.html                # GENERATED — Root landing page
├── cv_data.yaml              # CV source of truth (structured YAML, loaded by build.py)
├── sitemap.xml               # GENERATED — SEO sitemap with hreflang
├── CNAME                     # GitHub Pages custom domain
├── .nojekyll                 # Disable Jekyll on GitHub Pages
├── .env.example              # Template: GEMINI_API_KEY
├── requirements.txt          # Python dependencies (removed — use uv sync)
├── build.sh / build.bat      # Convenience wrappers
├── robots.txt
├── README.md
└── TRANSLATION_PIPELINE.md   # Translation system documentation
```

### Key Directories
- **`_source/`** — The only directory with hand-written Python. All build logic lives here.
- **`_source/posts/`** — Blog post markdown files (the content).
- **`static/`** — Hand-written CSS and JS assets shared across all pages.
- **`en/`, `pt/`** — Generated HTML output. Committed to git for GitHub Pages. **Never edit directly.**
- **`_cache/`** — Build artifacts (translation cache, metadata). Git-ignored.
- **`.github/`** — Design philosophy docs for AI agents (not CI/CD).

## Commands / Development Workflow

### Build
```bash
uv run python _source/build.py       # Full build (parses posts, translates, generates HTML)
./build.sh                            # Unix wrapper (same thing)
build.bat                             # Windows wrapper
```

### Serve locally
```bash
uv run python -m http.server 8000    # Serve from project root, visit http://localhost:8000
```

### Install dependencies
```bash
uv sync --all-extras          # installs all deps including dev (pytest)
```

### Environment setup
Copy `.env.example` to `.env` and set:
- `GEMINI_API_KEY` — Google Gemini API key (required for translation)

### Deploy
Manual: build locally → commit generated HTML → push to GitHub. GitHub Pages serves the result.

## Code Conventions

### Python (`_source/*.py`)
- **Style**: PEP 8-ish, no linter enforced
- **Naming**: `snake_case` for functions/variables, `UPPER_SNAKE_CASE` for module-level constants
- **Docstrings**: Module-level docstrings on all Python modules; inline comments throughout
- **Paths**: Uses `pathlib.Path` throughout (not `os.path`)
- **HTML generation**: Python f-strings (no template engine)
- **Imports**: Standard library first, then third-party, then local modules
- **Type hints**: Used in function signatures across modules

### JavaScript (`static/js/*.js`)
- **Style**: All files wrapped in IIFEs with `'use strict'`
- **Naming**: `camelCase` for functions/variables, descriptive names
- **Documentation**: JSDoc-style `@fileoverview` block at top of each file with detailed architecture notes
- **DOM access**: `document.getElementById()` / `document.querySelector()` (no jQuery, no framework)
- **Event handling**: `addEventListener()`, custom events (`page-navigation-complete`)
- **State**: `localStorage` for persistence, `data-*` attributes for DOM state
- **Animation**: FLIP technique (First-Last-Invert-Play), View Transitions API
- **Initialization guard**: `data-*-initialized` attributes prevent duplicate setup after View Transitions

### CSS (`static/css/*.css`)
- **Architecture**: CSS custom properties design system, no preprocessor
- **Theming**: `[data-theme="dark"]` / `[data-theme="light"]` + `prefers-color-scheme` fallback
- **Naming**: BEM-ish class names (e.g., `.post-card`, `.filter-panel`, `.nav-links`)
- **View Transitions**: `view-transition-name` on elements, `::view-transition-*` pseudo-elements
- **Motion tokens**: `--motion-duration-core: 500ms`, `--motion-duration-quick: 300ms`, `--motion-easing: cubic-bezier(0.4, 0, 0.2, 1)`
- **Responsive**: Mobile-first with breakpoints
- **Accessibility**: `prefers-reduced-motion`, skip links, `focus-visible`, ARIA, print styles
- **Dark mode**: True black (#000) OLED-optimized

### Markdown Posts (`_source/posts/*.md`)
- **Frontmatter fields**: `title`, `date`, `excerpt`, `tags` (list), `order`
- **Optional fields**: `slug`, `canonical`, `updated`
- **Build metadata**: `content_hash` and timestamps are stored in `_cache/post-metadata.json`, not in frontmatter
- **Naming**: kebab-case filenames matching the post slug
- **Tags**: Title Case (e.g., "Web Development", "Gemini AI")

## Key Components

### Build System (`_source/build.py` + focused modules)
The build is orchestrated by `build.py` which delegates to focused modules:
- `content_loader.py` — Parses markdown posts, manages sidecar metadata manifest
- `renderer.py` — Generates all HTML pages (posts, index, about, CV, landing, nav, footer)
- `seo.py` — JSON-LD structured data and sitemap generation
- `cv_parser.py` — Loads and validates CV from `cv_data.yaml`
- `helpers.py` — Pure utilities (hashing, formatting, dates, paths, reading time)
- `paths.py` — Filesystem constants and directory helpers

Build workflow:
1. Parses all markdown posts from `_source/posts/`
2. Manages content hashes and timestamps via sidecar metadata
3. Initializes translator, translates content EN→PT-BR
4. Generates all HTML pages for both languages
5. Generates root landing page and sitemap.xml
6. Applies cache-busting via content-hash query strings on CSS/JS URLs
7. Optionally stages outputs and promotes atomically (strict mode)

**Key functions**: `parse_markdown_post()` (content_loader), `generate_post_html()`, `generate_index_html()`, `generate_about_html()`, `generate_cv_html()`, `generate_root_index()` (renderer), `generate_sitemap()` (seo), `render_head()`, `render_nav()`, `render_footer()` (renderer)

### Translation Pipeline (`_source/translator.py`)
Three-stage AI translation using Gemini:
1. **Translation Agent** — EN→PT-BR with detailed localization rules
2. **Critique Agent** — Reviews semantic alignment (currently disabled: `enable_critique=False` in `build.py`)
3. **Refinement Agent** — Applies critique feedback

Features: SHA-256 hash-based caching (`_cache/translation-cache.json`), 90-second rate limiting between API calls, 10 retries with exponential backoff, backtick cleanup post-processing.

### Configuration (`_source/config.py`)
Single source for all site configuration:
- `BASE_PATH` — `""` for local dev, `"/blog"` for GH Pages subdirectory
- `GEMINI_MODEL` — Translation model selection
- `LANGUAGES` — Full bilingual dictionary with UI strings, month names, About page content
- Site metadata, social links, author info

### Frontend Animation System
The site's signature feature — four JS files work together:
- **`transitions.js`** — Intercepts link clicks, fetches pages, swaps DOM inside `startViewTransition()`. Preserves scroll/filters on language switches.
- **`filter.js`** — Three-phase animation: dissolve (fade out) → reorganize (FLIP) → reveal (stagger in)
- **`landing.js`** — Morphs landing page elements into site navigation
- **`theme.js`** — Dark/light toggle with FOUC prevention

### Design Philosophy (`.github/` docs)
Three core principles:
1. **Continuity** — Single unbroken surface; the blog reconfigures, doesn't navigate
2. **Physical plausibility** — Motion echoes real physics
3. **Calm energy** — Alive but never performative

Motion vocabulary: morphing, sliding/occlusion, expansion/contraction, nudge, unfolding, dissolve. **Targets Chromium only** (Chrome/Edge) with graceful degradation.

## What NOT to Do
- **Never edit files in `en/` or `pt/`** — they are generated output; edit `_source/` or `static/` instead
- **Never edit `index.html` at root** — it's generated by `generate_root_index()` in build.py
- **Never edit `sitemap.xml`** — it's generated by `generate_sitemap()` in build.py
- **Don't add Node.js/npm** — This project deliberately avoids the JS ecosystem
- **Don't add a template engine** — HTML is generated via Python f-strings by design
- **Don't use CSS preprocessors** — Vanilla CSS with custom properties only
- **Don't add JS frameworks** — Vanilla JS with native browser APIs only

## Testing & Quality
- **Unit tests**: `tests/test_build.py` covers pure helper functions (tag slugs, reading time, date formatting, hashing, paths)
- **CI**: `.github/workflows/validate.yml` runs syntax check + pytest on push
- **No snapshot/integration tests yet** — Build-level testing is manual
- **No linting** — No ESLint, Prettier, Ruff, or any code formatting tools configured
- **No git hooks** — No pre-commit hooks or lint-staged

## Environment Variables
| Variable | Purpose | Required |
|----------|---------|----------|
| `GEMINI_API_KEY` | Google Gemini API key for translation | Yes (for translation) |
| `STRICT_BUILD` | Set to `1` to enable strict mode (same as `--strict` flag) | No |

## File Modification Guide
| To change... | Edit this file |
|--------------|---------------|
| Blog post content | `_source/posts/<slug>.md` |
| Site configuration/UI strings | `_source/config.py` |
| Build orchestration | `_source/build.py` |
| HTML templates/page generation | `_source/renderer.py` |
| Pure utilities (dates, hashing, paths) | `_source/helpers.py` |
| JSON-LD / sitemap generation | `_source/seo.py` |
| Markdown parsing / metadata | `_source/content_loader.py` |
| CV loading / validation | `_source/cv_parser.py` |
| Filesystem paths / constants | `_source/paths.py` |
| Translation behavior | `_source/translator.py` |
| Page styles | `static/css/styles.css` (main), `post.css`, `landing.css`, `cv.css` |
| Navigation/transitions | `static/js/transitions.js` |
| Filtering/sorting | `static/js/filter.js` |
| Theme toggle | `static/js/theme.js` |
| Landing page behavior | `static/js/landing.js` |
| CV content | `cv_data.yaml` (source of truth) |
| Design philosophy docs | `.github/*.md` |

After any source change, run `uv run python _source/build.py` to regenerate output.
