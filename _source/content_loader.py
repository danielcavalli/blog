"""Read authored Markdown and derive renderer data without writing files."""

from datetime import datetime

import frontmatter

from helpers import calculate_reading_time
from markdown_refs import render_markdown_with_internal_refs


def parse_markdown_post(filepath):
    """Parse a source post; frontmatter owns publication dates and metadata."""
    post = frontmatter.load(filepath)
    slug = post.get("slug", filepath.stem)

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
        "source_path": str(filepath),
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
        # Frontmatter-derived dates (canonical, stable, author-controlled)
        "published_date": str(
            date_str
        ),  # frontmatter 'date' -> shown to readers, sorting, JSON-LD datePublished
        "updated_fm_date": str(
            post.get("updated") or ""
        ),  # frontmatter 'updated' -> last-updated display, sitemap lastmod, JSON-LD dateModified
    }
