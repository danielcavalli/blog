"""Shared path constants and directory initialization for the blog builder.

Every module that needs project paths imports them from here, ensuring a
single source of truth for the filesystem layout.
"""

from pathlib import Path

from config import LANGUAGES

# Project structure paths
PROJECT_ROOT = Path(__file__).parent.parent  # Go up from _source to project root
POSTS_DIR = Path(__file__).parent / "posts"   # _source/posts/
CACHE_DIR = PROJECT_ROOT / "_cache"           # _cache/
STATIC_DIR = PROJECT_ROOT / "static"          # static/
CV_DATA_FILE = PROJECT_ROOT / "cv_data.yaml"  # CV source of truth (structured YAML)

# Output directories (at project root for GitHub Pages)
# Derived from LANGUAGES config so adding a language only requires a config change.
LANG_DIRS = {
    code: PROJECT_ROOT / meta['dir']
    for code, meta in LANGUAGES.items()
}

# Staging directory for atomic builds (used when strict=True or --staging)
STAGING_DIR = PROJECT_ROOT / '_staging'

# Cache files
METADATA_FILE = CACHE_DIR / "post-metadata.json"
TRANSLATION_CACHE = CACHE_DIR / "translation-cache.json"

# Ensure directories exist at import time
POSTS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

for _lang_dir in LANG_DIRS.values():
    _lang_dir.mkdir(parents=True, exist_ok=True)
    (_lang_dir / 'blog').mkdir(parents=True, exist_ok=True)
