# dan.rio

Static blog generator. Markdown to HTML with View Transitions API.

## Build

```
pip install -r requirements.txt
python build.py
```

## Development

```
python -m http.server 8080
```

## Writing Posts

Create files in `blog-posts/`:

```
````markdown
# dan.rio

Minimal bilingual blog with smooth View Transitions. Static site generator built with Python.

## Structure

```
blog/
├── _source/          # Build system and content
│   ├── posts/        # Markdown blog posts
│   ├── build.py      # Build script
│   ├── config.py     # Configuration
│   └── translator.py # Translation system
├── _cache/           # Build artifacts (git-ignored)
├── static/           # Shared assets
│   ├── css/          # Stylesheets
│   ├── js/           # JavaScript
│   └── images/       # Images
├── en/               # Generated English site
├── pt/               # Generated Portuguese site
└── index.html        # Landing page (served at dan.rio/)
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Build site (from project root)
python _source/build.py
# or use convenience scripts:
./build.sh        # Unix/Linux/Mac
build.bat         # Windows

# Serve locally
python -m http.server 8000
```

## Writing Posts

Create Markdown files in `_source/posts/`:

```markdown
---
title: Post Title
date: 2025-10-23
excerpt: Brief description
order: 1
---

Your content here.
```

Posts are automatically translated to Portuguese using Gemini API.

## Configuration

Edit `_source/config.py`:

```python
BASE_PATH = "/blog"  # GitHub Pages subdirectory
# or
BASE_PATH = ""       # Root domain
```

## Deployment

1. Set `BASE_PATH` in `_source/config.py`
2. Run `python _source/build.py`
3. Commit generated files (en/, pt/, *.html)
4. Push to GitHub
5. Ensure `.nojekyll` exists

## Features

- **Bilingual**: Automatic EN ↔ PT translation
- **View Transitions API**: Smooth page morphing
- **FLIP Animations**: Card sorting and reordering
- **Theme Toggle**: Dark/light mode with calm transitions
- **Language Continuity**: Preserves scroll and filters across language switches

## Browser Support

Full experience: Chrome/Edge 111+
Graceful degradation for other browsers

## Stack

- Python (markdown, frontmatter, google-generativeai)
- View Transitions API (Chromium)
- Vanilla JS + CSS animations
- No build tools or frameworks
````
```

Run `python build.py` after creating or editing posts.

## Deployment

Edit `BASE_PATH` in `build.py`:
- Local: `BASE_PATH = ""`
- GitHub Pages: `BASE_PATH = "/blog"`

Push to GitHub. Ensure `.nojekyll` file exists.

## Stack

- Python (markdown, frontmatter)
- View Transitions API
- CSS animations
- No framework required

## Browser Support

Chrome and Edge 111+ support full transitions. Other browsers work with standard navigation.