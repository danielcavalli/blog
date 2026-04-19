"""Pure utility functions used across the blog builder.

Every function here is side-effect-free (aside from the _asset_hash_cache)
and depends only on the standard library, config, and paths.
"""

import re
import hashlib
from datetime import datetime
from pathlib import Path

from config import BASE_PATH, LANGUAGES, get_alternate_language
from paths import PROJECT_ROOT


# ---------------------------------------------------------------------------
# Asset cache-busting via content hash
# ---------------------------------------------------------------------------
# Each static asset (CSS/JS) gets a version string derived from the first 8
# characters of its SHA-256 content hash.  This is fully deterministic: the
# same file contents always produce the same query string, eliminating diff
# noise between builds that don't actually change any assets.
_asset_hash_cache: dict[str, str] = {}


def _asset_hash(logical_path: str) -> str:
    """Return the first 8 hex chars of the SHA-256 hash for an asset file.

    *logical_path* is the path as it appears in HTML (e.g.
    ``/blog/static/css/styles.css``).  The function resolves it to a real
    filesystem path relative to PROJECT_ROOT.  Results are cached for the
    lifetime of the build process.

    Falls back to ``'dev'`` if the file cannot be read (e.g. during tests).
    """
    if logical_path in _asset_hash_cache:
        return _asset_hash_cache[logical_path]
    # Strip leading BASE_PATH (which may be '/blog' or '') to get a path
    # relative to PROJECT_ROOT.
    rel = logical_path.lstrip("/")
    if rel.startswith(BASE_PATH.lstrip("/") + "/"):
        rel = rel[len(BASE_PATH.lstrip("/")) + 1 :]
    abs_path = PROJECT_ROOT / rel
    try:
        digest = hashlib.sha256(abs_path.read_bytes()).hexdigest()[:8]
    except OSError:
        digest = "dev"
    _asset_hash_cache[logical_path] = digest
    return digest


# Current year for copyright
CURRENT_YEAR = datetime.now().year


def calculate_content_hash(content):
    """Calculate SHA-256 hash of content for change detection.

    Uses SHA-256 to match the translator's hashing algorithm,
    enabling consistent cache invalidation across the pipeline.

    Args:
        content (str): Post content to hash.

    Returns:
        str: SHA-256 hexadecimal digest string.
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def tag_to_slug(tag: str) -> str:
    """Convert a tag string to a stable, canonical slug for cross-language filtering.

    Used to produce stable HTML data-tag-key attributes so that filter state
    can survive language switches (EN <-> PT). The slug is the English canonical
    form: lowercased, with spaces and non-alphanumeric characters replaced by
    hyphens, and duplicate/leading/trailing hyphens collapsed.

    Examples:
        "home server"        -> "home-server"
        "View Transitions API" -> "view-transitions-api"
        "web"                -> "web"

    Args:
        tag (str): Raw tag string (any language).

    Returns:
        str: URL-safe slug.
    """
    slug = tag.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def calculate_reading_time(content):
    """Estimate reading time based on word count.

    Assumes average reading speed of 200 words per minute.
    Minimum reading time is 1 minute.

    Args:
        content (str): Post content to analyze.

    Returns:
        int: Reading time in minutes.
    """
    words = len(content.split())
    return max(1, round(words / 200))


def format_reading_time(minutes, lang="en"):
    """Format reading time integer as a locale-aware label.

    Args:
        minutes (int): Reading time in minutes.
        lang (str): Language code ('en' or 'pt').

    Returns:
        str: Formatted reading time (e.g., "5 min read" / "5 min de leitura").
    """
    label = LANGUAGES[lang]["ui"]["min_read"]
    return f"{minutes} {label}"


def format_date(date_str, lang="en"):
    """Format date string to readable format with locale-aware month name and pattern.

    Converts YYYY-MM-DD format to a locale-specific date format.
    EN uses "January 15, 2024", PT uses "15 de Janeiro de 2024".
    Falls back to original string if parsing fails.

    Args:
        date_str (str): Date string in YYYY-MM-DD format.
        lang (str): Language code ('en' or 'pt') for month name and format pattern.

    Returns:
        str: Formatted date string in the locale's preferred format.
    """
    try:
        date = datetime.strptime(str(date_str), "%Y-%m-%d")
        en_month = date.strftime("%B")
        months_dict = LANGUAGES[lang].get("months", {})
        localized_month = months_dict.get(en_month, en_month)
        date_fmt = LANGUAGES[lang]["ui"].get("date_format", "{month} {day}, {year}")
        return date_fmt.format(month=localized_month, day=f"{date.day:02d}", year=date.year)
    except (ValueError, TypeError):
        return str(date_str)


def format_iso_date(iso_str):
    """Format ISO datetime string to readable date.

    Converts ISO 8601 datetime to full month name format.
    Falls back to original string if parsing fails.

    Args:
        iso_str (str): ISO 8601 datetime string.

    Returns:
        str: Formatted date (e.g., "January 15, 2024").
    """
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%B %d, %Y")
    except (ValueError, TypeError):
        return str(iso_str)


def get_lang_path(lang: str, path: str = "") -> str:
    """Generate language-specific path using the directory from LANGUAGES config."""
    lang_dir = LANGUAGES[lang]["dir"]
    return f"{BASE_PATH}/{lang_dir}/{path}" if path else f"{BASE_PATH}/{lang_dir}"


def get_alternate_lang(current_lang: str) -> str:
    """Get the alternate language code (config-driven)."""
    return get_alternate_language(current_lang)


def _out(rel_path: Path, staging_dir: "Path | None") -> Path:
    """Resolve an output path, redirecting to staging_dir when set.

    All generated HTML/XML outputs are written through this helper so that
    a strict (atomic) build can redirect every write to a staging directory
    and only promote the results to final destinations once generation
    completes without error.

    Args:
        rel_path (Path): The intended final output path (absolute).
        staging_dir (Path | None): Root of the staging area, or None to
            write directly to the final path.

    Returns:
        Path: The effective write path (under staging_dir if staging is active,
              otherwise rel_path unchanged).
    """
    if staging_dir is None:
        return rel_path
    # Compute path relative to PROJECT_ROOT, then place it under staging_dir.
    relative = rel_path.relative_to(PROJECT_ROOT)
    dest = staging_dir / relative
    dest.parent.mkdir(parents=True, exist_ok=True)
    return dest
