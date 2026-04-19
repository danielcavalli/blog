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
    translation_common.py - Shared translation safety/validation helpers
"""

import os
import shutil
import sys
import importlib
import json
from pathlib import Path
import argparse
from typing import Any

from config import (
    BASE_PATH,
    LANGUAGES,
    DEFAULT_TRANSLATION_V2_PROVIDER,
    get_language_codes,
)
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
from translation_common import validate_translation
from translation_v2 import TranslationV2PostOrchestrator
from translation_v2.console import (
    configure_console,
    log_blank,
    log_block,
    log_build_footer,
    log_line,
    shutdown_console,
)

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


def resolve_translation_provider(
    cli_provider: str | None = None,  # noqa: ARG001
    *,
    use_translation_v2: bool = False,  # noqa: ARG001
) -> str:
    """Resolve build translation provider.

    Build runtime is OpenCode-only for post translation.
    """
    return DEFAULT_TRANSLATION_V2_PROVIDER


def resolve_translation_v2_enabled(cli_enabled: bool | None = None) -> bool:  # noqa: ARG001
    """Build runtime always uses translation_v2 orchestration."""
    return True


def select_markdown_files(md_files: list[Path], selector: str | None) -> list[Path]:
    """Filter markdown files by slug or path selector."""
    if not selector:
        return md_files

    needle = selector.strip()
    if not needle:
        return md_files

    needle_path = Path(needle)
    selected: list[Path] = []
    for md_file in md_files:
        source_rel = md_file.as_posix()
        if (
            md_file.stem == needle
            or md_file.name == needle
            or source_rel == needle
            or source_rel.endswith(needle)
            or md_file.resolve() == needle_path.resolve()
        ):
            selected.append(md_file)

    return selected


def _log_translation_v2_debug_context(post_translator: object | None) -> None:
    """Print run-scoped debug context for translation_v2 lanes."""
    if post_translator is None:
        return

    run_id = getattr(post_translator, "run_id", None)
    artifact_dir = getattr(post_translator, "artifact_run_dir", None)
    if run_id is None or artifact_dir is None:
        return

    log_block(
        "translation_v2 runtime",
        [
            ("Run ID", run_id),
            ("Artifacts", artifact_dir),
        ],
    )


def _serialize_about_artifact(about_payload: dict[str, Any]) -> str:
    return "\n\n".join(
        [
            f"# {str(about_payload.get('title', '')).strip()}",
            str(about_payload.get("p1", "")).strip(),
            str(about_payload.get("p2", "")).strip(),
            str(about_payload.get("p3", "")).strip(),
            str(about_payload.get("p4", "")).strip(),
        ]
    ).strip()


def _deserialize_about_artifact(translated: dict[str, Any]) -> dict[str, str]:
    title = str(translated.get("title", "")).strip()
    content = str(translated.get("content", "")).strip()
    paragraphs = [part.strip() for part in content.split("\n\n") if part.strip()]

    if not title and paragraphs and paragraphs[0].startswith("# "):
        title = paragraphs.pop(0)[2:].strip()
    elif paragraphs and paragraphs[0].startswith("# "):
        paragraphs.pop(0)

    if len(paragraphs) != 4:
        raise RuntimeError(
            f"Translated about artifact did not contain exactly four paragraphs; got {len(paragraphs)}"
        )

    return {
        "title": title,
        "p1": paragraphs[0],
        "p2": paragraphs[1],
        "p3": paragraphs[2],
        "p4": paragraphs[3],
    }


def _translate_about_to_pt_v2(
    post_translator: TranslationV2PostOrchestrator,
    about_en: dict[str, Any],
) -> dict[str, str]:
    """Translate EN About payload as one artifact and return PT renderer shape."""

    translated = post_translator.translate_artifact_if_needed(
        slug="about",
        source_text=_serialize_about_artifact(about_en),
        source_locale="en-us",
        target_locale="pt-br",
        artifact_type="about",
        frontmatter={
            "title": str(about_en.get("title", "")),
            "excerpt": "",
            "tags": [],
        },
        attach_path=str(PROJECT_ROOT / "_source" / "config.py"),
    )
    return _deserialize_about_artifact(translated)


def _translate_cv_to_pt_v2(
    post_translator: TranslationV2PostOrchestrator,
    cv_data: dict[str, Any],
) -> dict[str, Any]:
    """Translate the full CV as one structured artifact."""

    do_not_translate_entities = [
        "Nubank",
        "PicPay",
        "M4U",
        "Oi S.A",
        "frete.com",
        "Kubeflow",
        "Dagster",
        "Argo",
        "Tekton",
        "Pulumi",
        "AWS",
        "SageMaker",
        "GPU",
        "CUDA",
        "MLOps",
    ]
    translated = post_translator.translate_artifact_if_needed(
        slug="cv",
        source_text=json.dumps(cv_data, ensure_ascii=False, sort_keys=True, indent=2),
        source_locale="en-us",
        target_locale="pt-br",
        artifact_type="cv",
        frontmatter={
            "title": str(cv_data.get("name", "cv")),
            "excerpt": str(cv_data.get("tagline", "")),
            "tags": ["cv"],
        },
        attach_path=str(PROJECT_ROOT / "cv_data.yaml"),
        do_not_translate_entities=do_not_translate_entities,
    )
    return translated


def build(
    strict: bool = False,
    use_staging: bool = False,
    post_selector: str | None = None,
    translation_provider: str | None = None,
    use_translation_v2: bool | None = None,
    translation_failure_policy: str | None = None,
    skip_about_cv_translation: bool = False,
    verbose: bool = False,
):
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
        strict (bool): If True, enforces strict translation validation and
                       enables staged writes for atomic publish behavior.
        use_staging (bool): If True, write all outputs to _staging/ first and
                             only promote them after a fully successful generation.
                             Automatically True when strict=True.
        post_selector (str | None): Optional slug/path selector for translating
                                    and rendering one markdown post only.
        translation_provider (str | None): Deprecated and ignored.
        use_translation_v2 (bool | None): Deprecated and ignored.
        translation_failure_policy (str | None): Deprecated and ignored.
        skip_about_cv_translation (bool): If True, skip about/cv translation API
                                          calls and reuse EN content for PT pages.
        verbose (bool): If True, keep runner-level translation detail visible.

    Returns:
        bool: True if build succeeds, False if validation or translation fails.
    """
    # Strict builds are always staged
    if strict:
        use_staging = True

    configure_console(verbose=verbose)

    translation_v2_enabled = resolve_translation_v2_enabled(use_translation_v2)
    provider_name = resolve_translation_provider(
        translation_provider,
        use_translation_v2=translation_v2_enabled,
    )
    if translation_failure_policy:
        log_line(
            "translation failure policy override is ignored in OpenCode-only build mode",
            status="error",
        )

    mode_label = "strict validation" if strict else "default validation"
    pipeline_label = "translation_v2/full-pipeline"
    log_block(
        "Building bilingual blog",
        [
            ("Validation", mode_label),
            ("Provider", provider_name),
            ("Pipeline", pipeline_label),
            ("Writes", "atomic/staged" if use_staging else "direct"),
        ],
    )
    log_blank()

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
        log_block("Staging area", [("Path", staging_dir)])
        log_blank()

    # Run validation first
    try:
        validate_module = importlib.import_module("validate")
        run_validation = getattr(validate_module, "run_validation", None)
        if not callable(run_validation):
            raise ImportError("validate.run_validation not found")

        if not run_validation(BASE_PATH, POSTS_DIR):
            log_block("Build aborted", [("Reason", "validation failures")], status="error")
            log_blank()
            return False
    except ImportError:
        log_line("Skipping validation (validate.py not found)", status="info")
        log_blank()

    # Load and validate CV data before doing any work
    # (load_cv_data() exits with SystemExit if validation fails)
    load_cv_data()

    # Initialize translator
    try:
        post_translator = TranslationV2PostOrchestrator(
            provider_name=provider_name,
            strict_validation=strict,
            cache_path=TRANSLATION_CACHE,
            prompt_version=os.getenv("TRANSLATION_V2_PROMPT_VERSION", "v2"),
        )
        _log_translation_v2_debug_context(post_translator)
        log_block(
            "Translation system initialized",
            [
                ("Provider", provider_name),
                ("Prompt version", getattr(post_translator, "prompt_version", "unknown")),
                ("Translation model", getattr(post_translator, "_model_id", "unknown")),
                ("Critique model", getattr(post_translator, "_critique_model_id", "unknown")),
                ("Revision model", getattr(post_translator, "_revision_model_id", "unknown")),
            ],
        )
        log_blank()

        if skip_about_cv_translation:
            log_line("Skipping about/cv translation for focused run", status="info")
            log_blank()
            LANGUAGES["pt"]["about"] = dict(LANGUAGES["en"]["about"])
            cv_data_en = load_cv_data()
            if not cv_data_en:
                raise Exception("Could not load cv_data.yaml for fallback")
            cv_pt_translated = cv_data_en
        else:
            log_block(
                "Translating about/cv via translation_v2 pipeline",
                [("Provider", provider_name)],
            )
            log_blank()
            LANGUAGES["pt"]["about"] = _translate_about_to_pt_v2(
                post_translator,
                dict(LANGUAGES["en"]["about"]),
            )
            cv_data_en = load_cv_data()
            if not cv_data_en:
                raise Exception("Could not load cv_data.yaml for translation")
            cv_pt_translated = _translate_cv_to_pt_v2(post_translator, cv_data_en)

    except Exception as e:
        log_block(
            "Translation system error",
            [("Error", str(e)), ("Action", "fix translation issues and retry")],
            status="error",
        )
        log_blank()
        return False

    # Get all markdown files
    md_files = sorted(POSTS_DIR.glob("*.md"))

    if not md_files:
        log_block(
            "No markdown files found",
            [("Path", "blog-posts/"), ("Action", "create .md files to get started")],
            status="error",
        )
        log_blank()
        return False

    selected_md_files = select_markdown_files(md_files, post_selector)
    if post_selector and not selected_md_files:
        log_block(
            "No markdown file matched selector",
            [("Selector", post_selector)],
            status="error",
        )
        log_blank()
        return False

    if post_selector:
        log_block(
            "Markdown discovery",
            [
                ("Found", f"{len(md_files)} file(s)"),
                ("Selected", f"{len(selected_md_files)} file(s)"),
                ("Selector", post_selector),
            ],
        )
    else:
        log_block("Markdown discovery", [("Found", f"{len(md_files)} file(s)")])
    log_blank()

    focused_post_build = bool(post_selector)

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

    for md_file in selected_md_files:
        try:
            post_source = parse_markdown_post(md_file, metadata_store)
            source_locale = post_source.get("lang", "en-us")
            source_lang_key = locale_to_lang_key(source_locale)
            target_locale = get_target_locale(source_locale)
            target_lang_key = locale_to_lang_key(target_locale)

            posts_by_lang[source_lang_key].append(post_source)
            if verbose:
                log_line(
                    f"Parsed {md_file.name} ({source_locale.upper()} -> {target_locale.upper()})",
                    indent=1,
                )

            if post_translator:
                translated_post = post_translator.translate_if_needed(
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
                if verbose:
                    log_line(
                        f"Translated {md_file.name} ({target_locale.upper()})",
                        indent=1,
                        status="success",
                    )
        except Exception as e:
            log_line(f"Error: {e}", indent=1, status="error")
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
        log_blank()
        log_block("Validating translations")
        log_blank()
        validation_failed = False

        for pair in translation_pairs:
            post_source = pair["source"]
            post_translated = pair["translated"]
            source_locale = normalize_locale(pair["source_locale"])
            target_locale = normalize_locale(pair["target_locale"])
            slug = pair["slug"]

            # Use raw markdown for validation (compares natural language,
            # not HTML tags which would inflate overlap counts).
            en_content = post_source.get("raw_content", "")
            pt_content = post_translated.get("raw_content", post_translated.get("content", ""))

            is_valid, issues = validate_translation(
                en_content,
                pt_content,
                source_locale=source_locale,
                target_locale=target_locale,
            )

            if not issues:
                quality_stats["validated_ok"] += 1
            elif is_valid:
                # Warnings only (no ERROR-level issues)
                quality_stats["validated_warnings"] += 1
                quality_stats["issues"].append((slug, issues))
                for issue in issues:
                    log_line(f"[quality] {slug}: {issue}", indent=1, status="info")
            else:
                # Has ERROR-level issues
                quality_stats["issues"].append((slug, issues))
                for issue in issues:
                    log_line(f"[quality] {slug}: {issue}", indent=1, status="error")
                if strict:
                    quality_stats["failed"] += 1
                    validation_failed = True
                    log_line(f"STRICT: validation failed for {slug}", indent=1, status="error")
                else:
                    quality_stats["validated_warnings"] += 1
                    log_line(
                        f"(non-strict: continuing despite errors for {slug})",
                        indent=1,
                        status="info",
                    )

        if validation_failed:
            log_blank()
            log_block(
                "Build aborted",
                [
                    (
                        "Reason",
                        f"{quality_stats['failed']} translation(s) failed validation in strict mode",
                    )
                ],
                status="error",
            )
            log_blank()
            return False

    posts_en = posts_by_lang["en"]
    posts_pt = posts_by_lang["pt"]

    # Sort posts by frontmatter 'date' (newest first) -- stable, author-controlled
    posts_en.sort(key=lambda p: str(p.get("published_date", p.get("date", ""))), reverse=True)
    posts_pt.sort(key=lambda p: str(p.get("published_date", p.get("date", ""))), reverse=True)

    log_blank()
    log_block("Generating HTML files")
    log_blank()

    # All writes below go through _out() so staging can redirect them.

    # Generate English site
    log_block("English version", indent=1)
    for i, post in enumerate(posts_en):
        try:
            html = generate_post_html(post, i + 1, lang="en")
            output_file = _out(LANG_DIRS["en"] / "blog" / f"{post['slug']}.html", staging_dir)
            output_file.write_text(html, encoding="utf-8")

            log_line(f"blog/{post['slug']}.html", indent=2, status="success")
        except Exception as e:
            log_line(f"Error generating {post['slug']}.html: {e}", indent=2, status="error")
            return False

    if focused_post_build:
        log_line("Skipping site-wide English index for focused post build", indent=2)
    else:
        # Generate English index
        try:
            index_html = generate_index_html(posts_en, lang="en")
            index_file = _out(LANG_DIRS["en"] / "index.html", staging_dir)
            index_file.write_text(index_html, encoding="utf-8")
            log_line("index.html", indent=2, status="success")
        except Exception as e:
            log_line(f"Error generating index.html: {e}", indent=2, status="error")
            return False

    # Generate English about
    try:
        about_html = generate_about_html(lang="en")
        about_file = _out(LANG_DIRS["en"] / "about.html", staging_dir)
        about_file.write_text(about_html, encoding="utf-8")
        log_line("about.html", indent=2, status="success")
    except Exception as e:
        log_line(f"Error generating about.html: {e}", indent=2, status="error")
        return False

    # Generate English CV
    try:
        cv_html = generate_cv_html(lang="en")
        cv_file = _out(LANG_DIRS["en"] / "cv.html", staging_dir)
        cv_file.write_text(cv_html, encoding="utf-8")
        log_line("cv.html", indent=2, status="success")
    except Exception as e:
        log_line(f"Error generating cv.html: {e}", indent=2, status="error")
        return False

    # Generate Portuguese site (if translations available)
    if posts_pt:
        log_blank()
        log_block("Portuguese version", indent=1)
        for i, post in enumerate(posts_pt):
            try:
                html = generate_post_html(post, i + 1, lang="pt")
                output_file = _out(LANG_DIRS["pt"] / "blog" / f"{post['slug']}.html", staging_dir)
                output_file.write_text(html, encoding="utf-8")
                log_line(f"blog/{post['slug']}.html", indent=2, status="success")
            except Exception as e:
                log_line(f"Error generating {post['slug']}.html: {e}", indent=2, status="error")
                return False

        if focused_post_build:
            log_line("Skipping site-wide Portuguese index for focused post build", indent=2)
        else:
            # Generate Portuguese index
            try:
                index_html = generate_index_html(posts_pt, lang="pt")
                index_file = _out(LANG_DIRS["pt"] / "index.html", staging_dir)
                index_file.write_text(index_html, encoding="utf-8")
                log_line("index.html", indent=2, status="success")
            except Exception as e:
                log_line(f"Error generating index.html: {e}", indent=2, status="error")
                return False

        # Generate Portuguese about
        try:
            about_html = generate_about_html(lang="pt")
            about_file = _out(LANG_DIRS["pt"] / "about.html", staging_dir)
            about_file.write_text(about_html, encoding="utf-8")
            log_line("about.html", indent=2, status="success")
        except Exception as e:
            log_line(f"Error generating about.html: {e}", indent=2, status="error")
            return False

        # Generate Portuguese CV
        try:
            cv_html = generate_cv_html(lang="pt", translated_cv=cv_pt_translated)
            cv_file = _out(LANG_DIRS["pt"] / "cv.html", staging_dir)
            cv_file.write_text(cv_html, encoding="utf-8")
            log_line("cv.html", indent=2, status="success")
        except Exception as e:
            log_line(f"Error generating cv.html: {e}", indent=2, status="error")
            return False

    # Generate root index.html (landing page)
    if focused_post_build:
        log_blank()
        log_block("Root landing page", indent=1)
        log_line("Skipping root landing page for focused post build", indent=2)
    else:
        log_blank()
        log_block("Root landing page", indent=1)
        try:
            root_html = generate_root_index()
            root_index = _out(PROJECT_ROOT / "index.html", staging_dir)
            root_index.write_text(root_html, encoding="utf-8")
            log_line("index.html", indent=2, status="success")
        except Exception as e:
            log_line(f"Error generating root index.html: {e}", indent=2, status="error")
            return False

    # Generate sitemap.xml
    log_blank()
    log_block("Sitemap", indent=1)
    if focused_post_build:
        log_line("Skipping sitemap.xml for focused post build", indent=2)
    else:
        try:
            sitemap_xml = generate_sitemap(posts_en, posts_pt)
            sitemap_file = _out(PROJECT_ROOT / "sitemap.xml", staging_dir)
            sitemap_file.write_text(sitemap_xml, encoding="utf-8")
            log_line("sitemap.xml", indent=2, status="success")
        except Exception as e:
            log_line(f"Error generating sitemap.xml: {e}", indent=2, status="error")
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
        log_blank()
        log_block("Promoting staged outputs", indent=1)
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
            log_line("Promotion complete", indent=2, status="success")
            log_blank()
        except Exception as e:
            log_line(f"Error during staging promotion: {e}", indent=2, status="error")
            # Rollback: restore live dirs from backup if they exist
            for lang_key in get_language_codes():
                lang_dir = LANGUAGES[lang_key]["dir"]
                backup = old_dir / lang_dir
                live = PROJECT_ROOT / lang_dir
                if backup.exists() and not live.exists():
                    try:
                        backup.rename(live)
                        log_line(f"Rolled back {lang_key}/ from backup", indent=2, status="success")
                    except Exception as rb_err:
                        log_line(f"Rollback failed for {lang_key}/: {rb_err}", indent=2, status="error")
            log_line(f"Staged outputs preserved at: {staging_dir}", indent=2)
            log_blank()
            return False

    lang_count = len(get_language_codes()) if posts_pt else 1
    log_blank()
    log_block(
        "Build summary",
        [
            ("Posts", len(posts_en)),
            ("Languages", lang_count),
        ],
        status="success",
    )

    # ---------------------------------------------------------------
    # Translation quality summary
    # ---------------------------------------------------------------
    if quality_stats["translated"] > 0:
        total = quality_stats["translated"]
        ok = quality_stats["validated_ok"]
        warn = quality_stats["validated_warnings"]
        fail = quality_stats["failed"]
        mode = "strict" if strict else "default"

        log_blank()
        log_block(
            f"Translation quality report ({mode} mode)",
            [
                ("Translated", total),
                ("Validated OK", ok),
                ("Validated w/ warnings", warn),
                ("Failed", fail),
            ],
        )

        if quality_stats["issues"]:
            log_blank()
            log_block("Posts with quality warnings", indent=1)
            for slug, issues in quality_stats["issues"]:
                error_count = sum(1 for i in issues if i.startswith("ERROR:"))
                warn_count = len(issues) - error_count
                parts = []
                if error_count:
                    parts.append(f"{error_count} error(s)")
                if warn_count:
                    parts.append(f"{warn_count} warning(s)")
                log_line(f"{slug}: {', '.join(parts)}", indent=2, status="error" if error_count else "info")

        if warn > 0 and not strict:
            log_blank()
            log_line(f"{warn} translation(s) had quality warnings", indent=1, status="info")
            log_line("Run with --strict to enforce all quality gates", indent=1, status="info")

    log_blank()
    return True


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for the blog build."""

    parser = argparse.ArgumentParser(description="Build bilingual blog outputs")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict translation validation and staged writes",
    )
    parser.add_argument(
        "--post",
        default=None,
        help="Build/translate only one post by slug or markdown path",
    )
    parser.add_argument(
        "--skip-about-cv-translation",
        action="store_true",
        help="Skip about/cv translation API calls for focused test runs",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show runner-level translation details in the live dashboard",
    )

    args = parser.parse_args(argv)

    # STRICT_BUILD=1 remains as env fallback for non-CLI automation.
    strict_mode = args.strict or os.environ.get("STRICT_BUILD") == "1"
    try:
        success = build(
            strict=strict_mode,
            use_staging=strict_mode,
            post_selector=args.post,
            skip_about_cv_translation=args.skip_about_cv_translation,
            verbose=args.verbose,
        )
    except KeyboardInterrupt:
        shutdown_console()
        log_build_footer(outcome="interrupted")
        return 130

    shutdown_console()
    log_build_footer(success=success)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
