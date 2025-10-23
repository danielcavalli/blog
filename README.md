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
---
title: Post Title
date: 2025-10-23
excerpt: Brief description
---

Content here.
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