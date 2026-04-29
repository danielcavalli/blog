"""Markdown post parsing and sidecar metadata management.

Handles loading posts from Markdown files with YAML frontmatter,
and managing the sidecar metadata manifest at _cache/post-metadata.json.
"""

import json
from datetime import datetime
from typing import Optional

import frontmatter

from paths import METADATA_FILE
from helpers import calculate_content_hash, calculate_reading_time
from markdown_refs import render_markdown_with_internal_refs


def load_post_metadata() -> dict:
    """Load the sidecar post metadata manifest from _cache/post-metadata.json.

    The manifest stores derived build metadata (content_hash, created_at,
    updated_at) that would otherwise be written back into source .md files.
    Keeping this data here preserves single-source-of-truth for editorial
    content in frontmatter while tracking build state separately.

    Returns:
        dict: Mapping of slug -> {content_hash, created_at, updated_at}.
              Returns empty dict if the file does not exist yet.
    """
    if METADATA_FILE.exists():
        try:
            return json.loads(METADATA_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_post_metadata(metadata: dict) -> None:
    """Persist the sidecar post metadata manifest to _cache/post-metadata.json.

    Writes atomically (temp file + rename) so a failed build never corrupts
    the manifest.

    Args:
        metadata (dict): Full manifest dict to persist.
    """
    tmp = METADATA_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(METADATA_FILE)


def parse_markdown_post(filepath, _metadata_store: Optional[dict] = None):
    """Parse Markdown file with YAML frontmatter.

    Extracts metadata and content from post, then resolves creation/modification
    timestamps and content_hash from the sidecar manifest at
    _cache/post-metadata.json -- NOT by writing back into the source .md file.

    If the manifest has no entry for this post yet (or if the .md file still
    carries legacy content_hash/created_at/updated_at fields), those values
    are migrated into the manifest on first read. The .md file is never
    modified by the build.

    Args:
        filepath (Path): Path to Markdown file to parse.
        _metadata_store (dict | None): Live manifest dict shared across all
            parse calls in a single build (mutated in-place so the caller can
            save it once after all posts are processed). If None, the function
            loads the manifest itself (useful for one-off calls).

    Returns:
        Dict: Post data with title, excerpt, tags, language metadata, dates,
              content, etc. Returns None if file doesn't exist or fails to parse.
    """
    post = frontmatter.load(filepath)

    # Get filename without extension
    filename = filepath.stem
    slug = post.get("slug", filename)

    # Calculate content hash for change detection
    content_hash = calculate_content_hash(post.content)

    # --- Sidecar manifest handling (no .md mutation) ---
    own_store = _metadata_store is None
    if own_store:
        _metadata_store = load_post_metadata()

    entry = _metadata_store.get(slug, {})

    # Migrate legacy frontmatter fields into the manifest on first encounter
    if not entry:
        entry = {
            "content_hash": post.get("content_hash", content_hash),
            "created_at": post.get("created_at") or datetime.now().isoformat(),
            "updated_at": post.get("updated_at") or datetime.now().isoformat(),
        }
        _metadata_store[slug] = entry

    now = datetime.now().isoformat()

    if entry.get("content_hash") != content_hash:
        # Content changed (or first time hash is tracked) -- record new hash/timestamp
        entry["content_hash"] = content_hash
        entry["updated_at"] = now
        if not entry.get("created_at"):
            entry["created_at"] = now
        _metadata_store[slug] = entry

    created_at = entry.get("created_at", now)
    updated_at = entry.get("updated_at", now)

    # Persist manifest when we loaded it ourselves (one-off call path)
    if own_store:
        save_post_metadata(_metadata_store)

    # --- Editorial date validation ---
    # Warn if frontmatter 'date' (publication date) is missing
    if not post.get("date"):
        print(
            f"   Warning: '{slug}' is missing frontmatter 'date' (publication date); defaulting to today"
        )

    # Warn if frontmatter 'updated' is before 'date' (likely a typo)
    fm_date_str = str(post.get("date", ""))
    fm_updated_str = str(post.get("updated", ""))
    if fm_date_str and fm_updated_str:
        try:
            fm_date_parsed = datetime.strptime(fm_date_str, "%Y-%m-%d")
            fm_updated_parsed = datetime.strptime(fm_updated_str, "%Y-%m-%d")
            if fm_updated_parsed < fm_date_parsed:
                print(
                    f"   Warning: '{slug}' has 'updated' ({fm_updated_str}) before 'date' ({fm_date_str})"
                )
        except (ValueError, TypeError):
            pass

    # Convert markdown content to HTML
    html_content = render_markdown_with_internal_refs(post.content, source_markdown=post.content)

    # Keep raw markdown for translation
    raw_markdown = post.content

    # Parse date and extract year/month
    date_str = post.get("date", datetime.now().strftime("%Y-%m-%d"))
    try:
        post_date = datetime.strptime(str(date_str), "%Y-%m-%d")
        year = post_date.year
        month = post_date.strftime("%B")  # Full month name
    except (ValueError, TypeError):
        year = datetime.now().year
        month = datetime.now().strftime("%B")

    # Get tags (default to empty list if not provided)
    tags = post.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",")]

    # Get source language
    lang = post.get("lang") or post.get("source_language") or "en-us"

    return {
        "title": post.get("title", "Untitled Post"),
        "date": date_str,
        "year": year,
        "month": month,
        "excerpt": post.get("excerpt", ""),
        "slug": slug,
        "content_type": str(post.get("content_type", "post") or "post").strip().lower(),
        "order": post.get("order", 0),
        "tags": tags,
        "lang": lang,
        # en_tags holds the canonical English tags for stable cross-language
        # filter-state restoration (data-tag-key attributes).  For EN posts
        # this is identical to 'tags'.  When the post is copied and translated
        # to PT, 'tags' gets overwritten with PT translations while 'en_tags'
        # survives the dict copy unchanged, so PT cards can still emit the EN
        # canonical slugs via data-tag-keys.
        "en_tags": tags,
        "reading_time": post.get("readingTime") or calculate_reading_time(post.content),
        "content": html_content,
        "raw_content": raw_markdown,  # Keep raw markdown for translation
        "created_date": created_at,  # build-internal: sidecar first-seen timestamp (NOT for display)
        "updated_date": updated_at,  # build-internal: sidecar last-change timestamp (NOT for display)
        "content_hash": content_hash,
        # Frontmatter-derived dates (canonical, stable, author-controlled)
        "published_date": str(
            date_str
        ),  # frontmatter 'date' -> shown to readers, sorting, JSON-LD datePublished
        "updated_fm_date": str(
            post.get("updated") or ""
        ),  # frontmatter 'updated' -> last-updated display, sitemap lastmod, JSON-LD dateModified
    }
