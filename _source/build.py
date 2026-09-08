#!/usr/bin/env python3
"""
Blog Builder - Compiles Markdown posts to HTML with bilingual support
Run this whenever you add or edit a blog post.

This is the orchestration entry point.  All domain logic lives in
focused modules:

    paths.py           - Filesystem constants
    helpers.py         - Pure utility functions (hashing, formatting, etc.)
    content_loader.py  - Read-only Markdown parsing
    cv_parser.py       - CV YAML loading and schema validation
    seo.py             - JSON-LD structured data and sitemap generation
    renderer.py        - All HTML page generation
    config.py          - Site configuration constants
    translation_common.py - Shared translation safety/validation helpers
"""

import os
import shutil
import sys
import json
from pathlib import Path
import argparse
from functools import wraps
from publication import publish_staged, recover_publication, validate_staged
from translation_v2.storage import file_lock
from typing import Any

import frontmatter

from config import (
    LANGUAGES,
    get_language_codes,
)
from paths import PROJECT_ROOT, POSTS_DIR, LANG_DIRS, STAGING_DIR
from helpers import _out
from content_loader import parse_markdown_post
from cv_parser import load_cv_data
from seo import generate_sitemap
from renderer import (
    generate_post_html,
    generate_index_html,
    generate_about_html,
    generate_cv_html,
    generate_root_index,
    generate_presentation_html,
)
from presentation_compiler import compile_presentation_markdown, presentation_document_to_dict
from presentation_translation import compare_presentation_translation_invariants
from accepted_content import AcceptedContent, UnavailableTranslation
from translation_v2.console import (
    configure_console,
    log_blank,
    log_block,
    log_build_footer,
    log_line,
    shutdown_console,
    start_translation_batch,
    finish_translation_batch,
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
            or source_rel.endswith(f"/{needle}")
            or md_file.resolve() == needle_path.resolve()
            or (md_file.is_file() and frontmatter.load(str(md_file)).get("slug") == needle)
        ):
            selected.append(md_file)

    return selected


def _serialize_about_artifact(about_payload: dict[str, Any]) -> str:
    paragraph_keys = _about_paragraph_keys(about_payload)
    parts = [f"# {str(about_payload.get('title', '')).strip()}"]
    parts.extend(str(about_payload.get(key, "")).strip() for key in paragraph_keys)
    return "\n\n".join(parts).strip()


def _about_paragraph_keys(about_payload: dict[str, Any]) -> list[str]:
    return sorted(
        (
            key
            for key in about_payload
            if key.startswith("p") and key[1:].isdigit()
        ),
        key=lambda key: int(key[1:]),
    )


def _deserialize_about_artifact(
    translated: dict[str, Any],
    *,
    template_about: dict[str, Any],
) -> dict[str, str]:
    title = str(translated.get("title", "")).strip()
    content = str(translated.get("content", "")).strip()
    paragraphs = [part.strip() for part in content.split("\n\n") if part.strip()]
    paragraph_keys = _about_paragraph_keys(template_about)

    if not title and paragraphs and paragraphs[0].startswith("# "):
        title = paragraphs.pop(0)[2:].strip()
    elif paragraphs and paragraphs[0].startswith("# "):
        paragraphs.pop(0)

    if len(paragraphs) != len(paragraph_keys):
        raise RuntimeError(
            "Translated about artifact did not contain the expected paragraph count; "
            f"expected {len(paragraph_keys)}, got {len(paragraphs)}"
        )

    about_payload = {"title": title}
    for key, paragraph in zip(paragraph_keys, paragraphs, strict=True):
        about_payload[key] = paragraph
    return about_payload


def _read_about_pt(
    accepted: AcceptedContent,
    about_en: dict[str, Any],
) -> dict[str, str]:
    """Read the accepted About artifact in the renderer shape."""

    translated = accepted.read_artifact(
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
    )
    return _deserialize_about_artifact(translated, template_about=about_en)


def _read_cv_pt(
    accepted: AcceptedContent,
) -> dict[str, Any]:
    """Read the accepted structured CV."""

    cv_data = load_cv_data()
    if cv_data is None:
        raise RuntimeError("Could not load cv_data.yaml")
    translated = accepted.read_artifact(
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
    )
    return translated


def _sorted_posts(posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        posts,
        key=lambda post: str(post.get("published_date", post.get("date", ""))),
        reverse=True,
    )


def _is_presentation_post(post: dict[str, Any]) -> bool:
    return str(post.get("content_type", "post")).strip().lower() == "presentation"


def validate_presentation_translation(
    source_markdown: str,
    translated_markdown: str,
) -> tuple[bool, list[str]]:
    issues = compare_presentation_translation_invariants(
        source_markdown,
        translated_markdown,
    )
    return not issues, [issue.message for issue in issues]


def compile_markdown_presentation(markdown: str, *, slug: str = "") -> dict[str, Any]:
    document = compile_presentation_markdown(markdown)
    payload = presentation_document_to_dict(document)
    payload["slug"] = slug
    return payload


def _prepare_presentation_post(post: dict[str, Any]) -> dict[str, Any]:
    if not _is_presentation_post(post):
        return post
    prepared = post.copy()
    presentation = compile_markdown_presentation(
        str(post.get("raw_content", "")),
        slug=str(post.get("slug", "")),
    )
    prepared["presentation"] = presentation
    prepared.update(presentation)
    return prepared


def _write_output_file(relative_path: Path, content: str, staging_dir: Path | None) -> Path:
    output_path = _out(relative_path, staging_dir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def _write_post(
    post: dict[str, Any],
    *,
    lang_key: str,
    posts_for_lang: list[dict[str, Any]],
    staging_dir: Path | None,
) -> None:
    sorted_posts = _sorted_posts(posts_for_lang)
    post_number = next(
        index
        for index, candidate in enumerate(sorted_posts, start=1)
        if candidate["slug"] == post["slug"]
    )
    if _is_presentation_post(post):
        html = generate_presentation_html(post, post_number, lang=lang_key)
    else:
        html = generate_post_html(post, post_number, lang=lang_key)
    _write_output_file(
        LANG_DIRS[lang_key] / "blog" / f"{post['slug']}.html",
        html,
        staging_dir,
    )
    log_line(
        f"Rendered {lang_key}/blog/{post['slug']}.html",
        indent=2,
        status="success",
    )


def _commit_source_about_output(
    *,
    lang_key: str,
    staging_dir: Path | None,
) -> None:
    about_html = generate_about_html(lang=lang_key)
    _write_output_file(LANG_DIRS[lang_key] / "about.html", about_html, staging_dir)
    log_line(f"Rendered {lang_key}/about.html", indent=2, status="success")


def _commit_source_cv_output(
    *,
    lang_key: str,
    staging_dir: Path | None,
) -> None:
    cv_html = generate_cv_html(lang=lang_key)
    _write_output_file(LANG_DIRS[lang_key] / "cv.html", cv_html, staging_dir)
    log_line(f"Rendered {lang_key}/cv.html", indent=2, status="success")


def _commit_translated_about_output(
    about_payload: dict[str, Any],
    *,
    staging_dir: Path | None,
) -> None:
    about_html = generate_about_html(lang="pt", translated_about=about_payload)
    _write_output_file(LANG_DIRS["pt"] / "about.html", about_html, staging_dir)
    log_line("Rendered pt/about.html", indent=2, status="success")


def _commit_translated_cv_output(
    cv_payload: dict[str, Any],
    *,
    staging_dir: Path | None,
) -> None:
    cv_html = generate_cv_html(lang="pt", translated_cv=cv_payload)
    _write_output_file(LANG_DIRS["pt"] / "cv.html", cv_html, staging_dir)
    log_line("Rendered pt/cv.html", indent=2, status="success")


def _commit_language_index(
    *,
    posts: list[dict[str, Any]],
    lang_key: str,
    staging_dir: Path | None,
) -> None:
    index_html = generate_index_html(_sorted_posts(posts), lang=lang_key)
    _write_output_file(LANG_DIRS[lang_key] / "index.html", index_html, staging_dir)
    log_line(f"Rendered {lang_key}/index.html", indent=2, status="success")


def _commit_sitemap_output(
    *,
    posts_en: list[dict[str, Any]],
    posts_pt: list[dict[str, Any]],
    staging_dir: Path | None,
) -> None:
    sitemap_xml = generate_sitemap(_sorted_posts(posts_en), _sorted_posts(posts_pt))
    _write_output_file(PROJECT_ROOT / "sitemap.xml", sitemap_xml, staging_dir)
    log_line("Rendered sitemap.xml", indent=2, status="success")


def _build(
    strict: bool = False,
    post_selector: str | None = None,
    skip_about_cv_translation: bool = False,
    verbose: bool = False,
):
    """Render source and accepted translations, validate, then publish.

    Strict builds localize uncached source with an unattended agent. Non-strict
    builds render source and available translations without models. A focused build replaces
    only its rendered files. Skip-about/cv leaves all four static pages intact.

    Strict mode also enforces translation heuristics. Every build validates
    the complete proposed site before recoverable publication.
    """
    configure_console(verbose=verbose)
    log_block("Building bilingual blog", [
        ("Validation", "strict" if strict else "default"),
        ("Localization", "Generate missing or outdated translations" if strict else "Use available translations; no agent calls"),
    ])
    staging_dir = STAGING_DIR

    if not POSTS_DIR.is_dir():
        log_line(f"Posts directory not found: {POSTS_DIR}", status="error")
        return False

    # Get all markdown files
    md_files = sorted(POSTS_DIR.glob("*.md"))

    if not md_files:
        log_block(
            "No markdown files found",
            [("Path", POSTS_DIR), ("Action", "create .md files to get started")],
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

    # Resolve the complete bilingual content before writing output files.
    parsed_posts: list[dict[str, Any]] = []
    all_source_posts: list[dict[str, Any]] = []
    rendered_posts_by_lang = {"en": [], "pt": []}

    for md_file in md_files:
        try:
            post_source = parse_markdown_post(md_file)
            all_source_posts.append(post_source)
            if md_file not in selected_md_files:
                continue
            post_source = _prepare_presentation_post(post_source)
            source_locale = post_source.get("lang", "en-us")
            source_lang_key = locale_to_lang_key(source_locale)
            target_locale = get_target_locale(source_locale)
            target_lang_key = locale_to_lang_key(target_locale)

            parsed_posts.append(
                {
                    "md_file": md_file,
                    "post": post_source,
                    "source_locale": source_locale,
                    "source_lang_key": source_lang_key,
                    "target_locale": target_locale,
                    "target_lang_key": target_lang_key,
                }
            )
            rendered_posts_by_lang[source_lang_key].append(post_source)
            if verbose:
                log_line(
                    f"Parsed {md_file.name} ({source_locale.upper()} -> {target_locale.upper()})",
                    indent=1,
                )
        except Exception as e:
            log_line(f"Error: {e}", indent=1, status="error")
            return False

    translation_root = PROJECT_ROOT / "_source" / "translations"

    def translation_agent():
        from translation_v2.orchestrator import TranslationV2PostOrchestrator
        return TranslationV2PostOrchestrator(
            strict_validation=True, cache_dir=PROJECT_ROOT / "_cache", accepted_path=translation_root,
        )

    accepted = AcceptedContent(
        root=translation_root, strict_validation=strict,
        translator_factory=translation_agent if strict else None,
    )
    failures: list[str] = []
    static_content: dict[str, dict[str, Any]] = {}
    missing_pages: dict[str, str] = {}
    if strict:
        start_translation_batch(len(parsed_posts) + (0 if skip_about_cv_translation else 2),
                                next_step="Continuing with rendering and site validation.")
    else:
        log_block("Loading available translations")
    if not skip_about_cv_translation:
        for name, read in (
            ("about", lambda: _read_about_pt(accepted, dict(LANGUAGES["en"]["about"]))),
            ("cv", lambda: _read_cv_pt(accepted)),
        ):
            try:
                static_content[name] = read()
            except UnavailableTranslation as exc:
                if strict:
                    failures.append(str(exc))
                else:
                    missing_pages[f"/pt/{name}.html"] = f"/en/{name}.html"
            except Exception as exc:
                failures.append(f"{name}: {exc}")

    for parsed_post in parsed_posts:
        md_file = parsed_post["md_file"]
        post_source = parsed_post["post"]
        source_locale = parsed_post["source_locale"]
        target_locale = parsed_post["target_locale"]
        target_lang_key = parsed_post["target_lang_key"]

        try:
            translated_post = accepted.read_post(
                post_source,
                target_locale=target_locale,
            )
            rendered_posts_by_lang[target_lang_key].append(_prepare_presentation_post(translated_post))
        except UnavailableTranslation as exc:
            if strict:
                failures.append(str(exc))
            else:
                missing_pages[f"/{target_lang_key}/blog/{post_source['slug']}.html"] = (
                    f"/{parsed_post['source_lang_key']}/blog/{post_source['slug']}.html"
                )
                log_line(f"Source only: {post_source['title']} ({source_locale.upper()})")
        except Exception as exc:
            failures.append(f"{post_source['slug']}: {exc}")

    if strict:
        finish_translation_batch(error="\n".join(failures) if failures else None)
        shutdown_console()
    if failures:
        log_block("Accepted content needs attention", status="error")
        for failure in failures:
            log_line(failure, indent=1, status="error")
        return False

    # Prepare staging area: clean any previous attempt so stale files don't
    # survive into the new build, then create the skeleton directories.
    if staging_dir.exists():
        shutil.rmtree(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)
    for lang_code in get_language_codes():
        lang_dir = LANGUAGES[lang_code]["dir"]
        (staging_dir / lang_dir / "blog").mkdir(parents=True, exist_ok=True)
    log_block("Staging area", [("Path", staging_dir)])
    log_blank()

    log_block("Rendering source and accepted translations")
    try:
        for lang_key in get_language_codes():
            for post in _sorted_posts(rendered_posts_by_lang[lang_key]):
                _write_post(post, lang_key=lang_key, posts_for_lang=all_source_posts,
                            staging_dir=staging_dir)
        if not skip_about_cv_translation:
            _commit_source_about_output(lang_key="en", staging_dir=staging_dir)
            _commit_source_cv_output(lang_key="en", staging_dir=staging_dir)
            if "about" in static_content:
                _commit_translated_about_output(static_content["about"], staging_dir=staging_dir)
            if "cv" in static_content:
                _commit_translated_cv_output(static_content["cv"], staging_dir=staging_dir)
    except Exception as exc:
        log_line(f"Error rendering pages: {exc}", indent=1, status="error")
        return False

    posts_en = rendered_posts_by_lang["en"]
    posts_pt = rendered_posts_by_lang["pt"]

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

    # Collection outputs are written once, after both languages are complete.
    if not focused_post_build:
        try:
            for lang_key in get_language_codes():
                _commit_language_index(
                    posts=rendered_posts_by_lang[lang_key], lang_key=lang_key,
                    staging_dir=staging_dir,
                )
            _commit_sitemap_output(
                posts_en=posts_en, posts_pt=posts_pt,
                staging_dir=staging_dir,
            )
        except Exception as exc:
            log_line(str(exc), status="error")
            return False

    if missing_pages:
        from partial_localization import adapt_unavailable_links
        adapt_unavailable_links(staging_dir, missing_pages)
    try:
        validate_staged(PROJECT_ROOT, staging_dir, full=not focused_post_build,
                        preserve_static=skip_about_cv_translation)
        publish_staged(
            PROJECT_ROOT, staging_dir, full=not focused_post_build,
            language_dirs=[LANGUAGES[key]["dir"] for key in get_language_codes()],
            preserve_static=skip_about_cv_translation,
        )
    except Exception as exc:
        log_line(f"Publication failed: {exc}", status="error")
        return False

    log_blank()
    log_block(
        "Build summary",
        [("Posts", len(parsed_posts)),
         ("Languages", sum(bool(posts) for posts in rendered_posts_by_lang.values()))],
        status="success",
    )

    log_blank()
    return True


@wraps(_build)
def build(*args, **kwargs):
    """Serialize publication and recover an interrupted transaction first."""
    with file_lock(PROJECT_ROOT / "_cache" / "build.lock", blocking=False):
        recover_publication(PROJECT_ROOT)
        return _build(*args, **kwargs)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for the blog build."""

    parser = argparse.ArgumentParser(description="Build bilingual blog outputs")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--strict",
        action="store_true",
        default=None,
        help="Localize missing/outdated documents and enforce translation checks",
    )
    mode.add_argument("--no-strict", action="store_false", dest="strict",
                      help="Build source and available translations without calling agents")
    parser.add_argument(
        "--post",
        default=None,
        help="Render only one post by slug or markdown path",
    )
    parser.add_argument(
        "--skip-about-cv-translation",
        action="store_true",
        help="Leave both languages of About/CV untouched",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show runner-level translation details in the live dashboard",
    )

    args = parser.parse_args(argv)

    # STRICT_BUILD=1 remains as env fallback for non-CLI automation.
    strict_mode = args.strict if args.strict is not None else os.environ.get("STRICT_BUILD") == "1"
    try:
        success = build(
            strict=strict_mode,
            post_selector=args.post,
            skip_about_cv_translation=args.skip_about_cv_translation,
            verbose=args.verbose,
        )
    except Exception as exc:
        log_line(str(exc), status="error")
        success = False
    except KeyboardInterrupt:
        finish_translation_batch(error="Interrupted by user.", interrupted=True)
        shutdown_console()
        log_build_footer(outcome="interrupted")
        return 130

    shutdown_console()
    log_build_footer(success=success)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
