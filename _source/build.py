#!/usr/bin/env python3
"""
Blog Builder - Compiles Markdown posts to HTML with bilingual support
Run this whenever you add or edit a blog post.

This is the orchestration entry point.  All domain logic lives in
focused modules:

    paths.py           - Filesystem constants and directory creation
    helpers.py         - Pure utility functions (hashing, formatting, etc.)
    content_loader.py  - Markdown parsing and sidecar metadata manifest
    cv_parser.py       - CV YAML loading and schema validation
    seo.py             - JSON-LD structured data and sitemap generation
    renderer.py        - All HTML page generation
    config.py          - Site configuration constants
    translator.py      - Gemini-powered multilingual translation
"""

import os
import shutil

from config import BASE_PATH, LANGUAGES, get_language_codes
from paths import PROJECT_ROOT, POSTS_DIR, LANG_DIRS, STAGING_DIR
from helpers import _out
from content_loader import load_post_metadata, save_post_metadata, parse_markdown_post
from cv_parser import load_cv_data
from seo import generate_sitemap
from renderer import (
    generate_post_html,
    generate_index_html,
    generate_about_html,
    generate_cv_html,
    generate_root_index,
)
from translator import MultiAgentTranslator, validate_translation

# Re-export everything that tests and external callers reference via `build.*`.
# This keeps backward compatibility while the actual implementations live in
# their focused modules.
from helpers import (  # noqa: F401
    _asset_hash,
    CURRENT_YEAR,
    calculate_content_hash,
    tag_to_slug,
    calculate_reading_time,
    format_reading_time,
    format_date,
    format_iso_date,
    get_lang_path,
    get_alternate_lang,
)
from renderer import (  # noqa: F401
    render_theme_toggle_svg,
    render_skip_link,
    render_nav,
    render_footer,
    render_head,
    generate_lang_toggle_html,
    generate_post_card,
)
from seo import render_person_jsonld, render_jsonld_script  # noqa: F401
from paths import (  # noqa: F401
    CACHE_DIR,
    STATIC_DIR,
    CV_DATA_FILE,
    METADATA_FILE,
    TRANSLATION_CACHE,
)


def normalize_locale(locale: str) -> str:
    """Normalize locale identifiers to lowercase hyphenated form."""
    return str(locale or "").strip().lower().replace("_", "-")


def locale_to_lang_key(locale: str) -> str:
    """Map locale-like values (en-us, pt-br, en, pt) to LANGUAGES keys."""
    normalized = normalize_locale(locale)
    if normalized.startswith("pt"):
        return "pt"
    return "en"


def get_target_locale(source_locale: str) -> str:
    """Return translation target locale for the configured bilingual pair."""
    source = normalize_locale(source_locale)
    if source.startswith("pt"):
        return "en-us"
    return "pt-br"


def build(strict: bool = False, use_staging: bool = False):
    """Main build function orchestrating entire site generation.

    Workflow:
        1. Validate post structure and metadata
        2. Parse all Markdown posts
        3. Translate posts to Portuguese (with caching)
        4. Translate About page (with caching)
        5. Generate HTML files for both languages
        6. Generate root index and landing pages
        7. Generate sitemap.xml with hreflang annotations

    Atomicity (use_staging=True):
        All HTML/XML outputs are first written to _staging/ (a temporary
        directory under PROJECT_ROOT).  Only after every file is generated
        without error are the staged outputs copied over to their final
        destinations.  If generation fails at any point, _staging/ is left in
        place for debugging and the existing live outputs are untouched.
        _cache/ writes (translation cache, sidecar manifest) bypass staging --
        they are build-time state, not site output.

    Args:
        strict (bool): If True, enables the full 3-stage translation pipeline
                       (Translation -> Critique -> Refinement). Slower but produces
                       higher quality translations. Pass --strict CLI flag or set
                       STRICT_BUILD=1 to activate. Default is False (translation-only).
        use_staging (bool): If True, write all outputs to _staging/ first and
                            only promote them after a fully successful generation.
                            Automatically True when strict=True.

    Returns:
        bool: True if build succeeds, False if validation or translation fails.
    """
    # Strict builds are always staged
    if strict:
        use_staging = True

    mode_label = "strict (critique enabled)" if strict else "fast (critique disabled)"
    staging_label = " [atomic/staged]" if use_staging else ""
    print(f"Building bilingual blog from Markdown... [{mode_label}]{staging_label}\n")

    # Determine staging directory (None = write directly)
    staging_dir = STAGING_DIR if use_staging else None

    # Prepare staging area: clean any previous attempt so stale files don't
    # survive into the new build, then create the skeleton directories.
    if staging_dir is not None:
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        staging_dir.mkdir(parents=True, exist_ok=True)
        for lang_code in get_language_codes():
            lang_dir = LANGUAGES[lang_code]["dir"]
            (staging_dir / lang_dir / "blog").mkdir(parents=True, exist_ok=True)
        print(f"   Staging area: {staging_dir}\n")

    # Run validation first
    try:
        from validate import run_validation

        if not run_validation(BASE_PATH, POSTS_DIR):
            print("Build aborted due to validation failures.\n")
            return False
    except ImportError:
        print("Skipping validation (validate.py not found)\n")

    # Load and validate CV data before doing any work
    # (load_cv_data() exits with SystemExit if validation fails)
    load_cv_data()

    # Initialize translator
    try:
        translator = MultiAgentTranslator(
            enable_critique=strict, strict_validation=strict
        )
        print("Translation system initialized\n")

        # Translate About page content
        about_en = LANGUAGES["en"]["about"]
        about_pt_translated = translator.translate_about(about_en, force=False)

        # Must have translation
        if not about_pt_translated:
            raise Exception("About page translation failed")

        LANGUAGES["pt"]["about"] = about_pt_translated

        # Translate CV content
        cv_en = load_cv_data()
        if cv_en:
            cv_pt_translated = translator.translate_cv(cv_en, force=False)
            if not cv_pt_translated:
                raise Exception("CV translation failed")
        else:
            raise Exception("Could not load cv_data.yaml for translation")

    except Exception as e:
        print(f"Translation system error: {e}")
        print("   Build aborted - fix translation issues and retry\n")
        return False

    # Get all markdown files
    md_files = sorted(POSTS_DIR.glob("*.md"))

    if not md_files:
        print("No markdown files found in blog-posts/")
        print("Create .md files in blog-posts/ to get started!\n")
        return False

    print(f"Found {len(md_files)} markdown file(s)\n")

    # Load the sidecar metadata manifest once; pass it to every parse call so
    # we can save it a single time at the end (avoids N redundant disk writes).
    metadata_store = load_post_metadata()

    # Parse all posts and route source/translated variants by output language.
    posts_by_lang = {"en": [], "pt": []}
    translation_pairs = []

    # Translation quality tracking
    quality_stats = {
        "translated": 0,
        "validated_ok": 0,
        "validated_warnings": 0,
        "failed": 0,
        "issues": [],  # (slug, [issues]) pairs for the summary
    }

    for md_file in md_files:
        try:
            post_source = parse_markdown_post(md_file, metadata_store)
            source_locale = post_source.get("lang", "en-us")
            source_lang_key = locale_to_lang_key(source_locale)
            target_locale = get_target_locale(source_locale)
            target_lang_key = locale_to_lang_key(target_locale)

            posts_by_lang[source_lang_key].append(post_source)
            print(
                f"   Parsed: {md_file.name} "
                f"({source_locale.upper()} -> {target_locale.upper()})"
            )

            if translator:
                translated_post = translator.translate_if_needed(
                    post_source,
                    target_locale=target_locale,
                )
                if not translated_post:
                    quality_stats["failed"] += 1
                    raise Exception(
                        f"Translation failed for {md_file.name} "
                        f"({source_locale} -> {target_locale})"
                    )
                posts_by_lang[target_lang_key].append(translated_post)
                translation_pairs.append(
                    {
                        "slug": post_source["slug"],
                        "source": post_source,
                        "translated": translated_post,
                        "source_locale": source_locale,
                        "target_locale": target_locale,
                    }
                )
                quality_stats["translated"] += 1
                print(f"   Translated: {md_file.name} ({target_locale.upper()})")
        except Exception as e:
            print(f"   Error: {e}")
            return False

    # Persist sidecar manifest once after all posts are parsed
    # (_cache/ writes bypass staging -- they are build-time state, not output)
    save_post_metadata(metadata_store)

    # ---------------------------------------------------------------
    # Build-level translation quality gate
    # ---------------------------------------------------------------
    # Run validate_translation() on every PT post against its EN source.
    # This catches issues that the translator's own validation may have
    # allowed through (e.g. cached translations from before validation
    # was added, or non-strict translator runs).
    #
    # In strict mode: any ERROR-level issue fails the build.
    # In default mode: issues are logged as warnings, build continues.
    if translation_pairs:
        print(f"\nValidating translations...\n")
        validation_failed = False

        for pair in translation_pairs:
            post_source = pair["source"]
            post_translated = pair["translated"]
            source_locale = normalize_locale(pair["source_locale"])
            target_locale = normalize_locale(pair["target_locale"])
            slug = pair["slug"]

            # Existing lexical validator is tuned for EN->PT checks.
            if not (source_locale.startswith("en") and target_locale.startswith("pt")):
                continue

            # Use raw markdown for validation (compares natural language,
            # not HTML tags which would inflate overlap counts).
            en_content = post_source.get("raw_content", "")
            pt_content = post_translated.get(
                "raw_content", post_translated.get("content", "")
            )

            is_valid, issues = validate_translation(en_content, pt_content)

            if not issues:
                quality_stats["validated_ok"] += 1
            elif is_valid:
                # Warnings only (no ERROR-level issues)
                quality_stats["validated_warnings"] += 1
                quality_stats["issues"].append((slug, issues))
                for issue in issues:
                    print(f"   [quality] {slug}: {issue}")
            else:
                # Has ERROR-level issues
                quality_stats["issues"].append((slug, issues))
                for issue in issues:
                    print(f"   [quality] {slug}: {issue}")
                if strict:
                    quality_stats["failed"] += 1
                    validation_failed = True
                    print(f"   STRICT: validation failed for {slug}")
                else:
                    quality_stats["validated_warnings"] += 1
                    print(f"   (non-strict: continuing despite errors for {slug})")

        if validation_failed:
            print(
                f"\nBuild aborted: {quality_stats['failed']} translation(s) failed validation in strict mode.\n"
            )
            return False

    posts_en = posts_by_lang["en"]
    posts_pt = posts_by_lang["pt"]

    # Sort posts by frontmatter 'date' (newest first) -- stable, author-controlled
    posts_en.sort(
        key=lambda p: str(p.get("published_date", p.get("date", ""))), reverse=True
    )
    posts_pt.sort(
        key=lambda p: str(p.get("published_date", p.get("date", ""))), reverse=True
    )

    print(f"\nGenerating HTML files...\n")

    # All writes below go through _out() so staging can redirect them.

    # Generate English site
    print("   English version:")
    for i, post in enumerate(posts_en):
        try:
            html = generate_post_html(post, i + 1, lang="en")
            output_file = _out(
                LANG_DIRS["en"] / "blog" / f"{post['slug']}.html", staging_dir
            )
            output_file.write_text(html, encoding="utf-8")

            print(f"      blog/{post['slug']}.html")
        except Exception as e:
            print(f"      Error generating {post['slug']}.html: {e}")
            return False

    # Generate English index
    try:
        index_html = generate_index_html(posts_en, lang="en")
        index_file = _out(LANG_DIRS["en"] / "index.html", staging_dir)
        index_file.write_text(index_html, encoding="utf-8")
        print(f"      index.html")
    except Exception as e:
        print(f"      Error generating index.html: {e}")
        return False

    # Generate English about
    try:
        about_html = generate_about_html(lang="en")
        about_file = _out(LANG_DIRS["en"] / "about.html", staging_dir)
        about_file.write_text(about_html, encoding="utf-8")
        print(f"      about.html")
    except Exception as e:
        print(f"      Error generating about.html: {e}")
        return False

    # Generate English CV
    try:
        cv_html = generate_cv_html(lang="en")
        cv_file = _out(LANG_DIRS["en"] / "cv.html", staging_dir)
        cv_file.write_text(cv_html, encoding="utf-8")
        print(f"      cv.html")
    except Exception as e:
        print(f"      Error generating cv.html: {e}")
        return False

    # Generate Portuguese site (if translations available)
    if posts_pt:
        print("\n   Portuguese version:")
        for i, post in enumerate(posts_pt):
            try:
                html = generate_post_html(post, i + 1, lang="pt")
                output_file = _out(
                    LANG_DIRS["pt"] / "blog" / f"{post['slug']}.html", staging_dir
                )
                output_file.write_text(html, encoding="utf-8")
                print(f"      blog/{post['slug']}.html")
            except Exception as e:
                print(f"      Error generating {post['slug']}.html: {e}")
                return False

        # Generate Portuguese index
        try:
            index_html = generate_index_html(posts_pt, lang="pt")
            index_file = _out(LANG_DIRS["pt"] / "index.html", staging_dir)
            index_file.write_text(index_html, encoding="utf-8")
            print(f"      index.html")
        except Exception as e:
            print(f"      Error generating index.html: {e}")
            return False

        # Generate Portuguese about
        try:
            about_html = generate_about_html(lang="pt")
            about_file = _out(LANG_DIRS["pt"] / "about.html", staging_dir)
            about_file.write_text(about_html, encoding="utf-8")
            print(f"      about.html")
        except Exception as e:
            print(f"      Error generating about.html: {e}")
            return False

        # Generate Portuguese CV
        try:
            cv_html = generate_cv_html(lang="pt", translated_cv=cv_pt_translated)
            cv_file = _out(LANG_DIRS["pt"] / "cv.html", staging_dir)
            cv_file.write_text(cv_html, encoding="utf-8")
            print(f"      cv.html")
        except Exception as e:
            print(f"      Error generating cv.html: {e}")
            return False

    # Generate root index.html (landing page)
    print("\n   Root landing page:")
    try:
        root_html = generate_root_index()
        root_index = _out(PROJECT_ROOT / "index.html", staging_dir)
        root_index.write_text(root_html, encoding="utf-8")
        print(f"      index.html")
    except Exception as e:
        print(f"      Error generating root index.html: {e}")
        return False

    # Generate sitemap.xml
    print("\n   Sitemap:")
    try:
        sitemap_xml = generate_sitemap(posts_en, posts_pt)
        sitemap_file = _out(PROJECT_ROOT / "sitemap.xml", staging_dir)
        sitemap_file.write_text(sitemap_xml, encoding="utf-8")
        print(f"      sitemap.xml")
    except Exception as e:
        print(f"      Error generating sitemap.xml: {e}")
        return False

    # Staging promotion: copy staged outputs to final destinations.
    # This only runs after all generation succeeds, making the build atomic --
    # any earlier failure leaves staging intact for debugging and the live
    # outputs untouched.
    #
    # Promotion uses POSIX rename() for atomic directory swaps:
    #   1. Move current live dirs to _staging.old/ as a backup
    #   2. Rename staged dirs to their final locations (atomic on same fs)
    #   3. Atomic-replace root-level files (index.html, sitemap.xml)
    #   4. Clean up _staging.old/ and _staging/
    # If promotion fails partway, rollback restores from _staging.old/.
    if staging_dir is not None:
        print(f"\n   Promoting staged outputs -> final destinations...")
        old_dir = PROJECT_ROOT / "_staging.old"
        try:
            # Phase 0: clean any stale backup
            if old_dir.exists():
                shutil.rmtree(old_dir)
            old_dir.mkdir(parents=True, exist_ok=True)

            # Phase 1: move live dirs to backup (so rename targets are free)
            for lang_key in get_language_codes():
                lang_dir = LANGUAGES[lang_key]["dir"]
                live = PROJECT_ROOT / lang_dir
                if live.exists():
                    live.rename(old_dir / lang_dir)

            # Phase 2: rename staged dirs to final locations (POSIX-atomic)
            for lang_key in get_language_codes():
                lang_dir = LANGUAGES[lang_key]["dir"]
                staged = staging_dir / lang_dir
                if staged.exists():
                    staged.rename(PROJECT_ROOT / lang_dir)

            # Phase 3: atomic replace for root-level files
            for name in ("index.html", "sitemap.xml"):
                src = staging_dir / name
                if src.exists():
                    src.replace(PROJECT_ROOT / name)

            # Phase 4: clean up
            if old_dir.exists():
                shutil.rmtree(old_dir)
            if staging_dir.exists():
                shutil.rmtree(staging_dir)
            print(f"   Promotion complete.\n")
        except Exception as e:
            print(f"   Error during staging promotion: {e}")
            # Rollback: restore live dirs from backup if they exist
            for lang_key in get_language_codes():
                lang_dir = LANGUAGES[lang_key]["dir"]
                backup = old_dir / lang_dir
                live = PROJECT_ROOT / lang_dir
                if backup.exists() and not live.exists():
                    try:
                        backup.rename(live)
                        print(f"   Rolled back {lang_key}/ from backup.")
                    except Exception as rb_err:
                        print(f"   Rollback failed for {lang_key}/: {rb_err}")
            print(f"   Staged outputs preserved at: {staging_dir}\n")
            return False

    lang_count = len(get_language_codes()) if posts_pt else 1
    print(f"\nBuild complete! {len(posts_en)} post(s) in {lang_count} language(s).")

    # ---------------------------------------------------------------
    # Translation quality summary
    # ---------------------------------------------------------------
    if quality_stats["translated"] > 0:
        total = quality_stats["translated"]
        ok = quality_stats["validated_ok"]
        warn = quality_stats["validated_warnings"]
        fail = quality_stats["failed"]
        mode = "strict" if strict else "default"

        print(f"\n   Translation quality report ({mode} mode):")
        print(f"      Translated:            {total}")
        print(f"      Validated OK:          {ok}")
        if warn > 0:
            print(f"      Validated w/ warnings: {warn}")
        if fail > 0:
            print(f"      Failed:                {fail}")

        if quality_stats["issues"]:
            print(f"\n      Posts with quality warnings:")
            for slug, issues in quality_stats["issues"]:
                error_count = sum(1 for i in issues if i.startswith("ERROR:"))
                warn_count = len(issues) - error_count
                parts = []
                if error_count:
                    parts.append(f"{error_count} error(s)")
                if warn_count:
                    parts.append(f"{warn_count} warning(s)")
                print(f"         {slug}: {', '.join(parts)}")

        if warn > 0 and not strict:
            print(f"\n      {warn} translation(s) had quality warnings.")
            print(f"      Run with --strict to enforce all quality gates.")

    print()
    return True


if __name__ == "__main__":
    import sys

    # --strict enables the critique/refinement pipeline (slower but higher quality)
    # STRICT_BUILD=1 environment variable has the same effect
    strict_mode = "--strict" in sys.argv or os.environ.get("STRICT_BUILD") == "1"
    success = build(strict=strict_mode, use_staging=strict_mode)
    sys.exit(0 if success else 1)
