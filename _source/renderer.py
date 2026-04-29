"""HTML rendering functions for all site pages.

Generates complete HTML documents for blog posts, index, about, CV,
and root landing pages. Each function returns a full HTML string.
"""

import html as _html
import re as _re

from config import (
    BASE_PATH,
    SITE_URL,
    SITE_NAME,
    SITE_DESCRIPTION,
    AUTHOR,
    AUTHOR_BIO,
    LANGUAGES,
    SOCIAL_LINKS,
    DEFAULT_LANGUAGE,
    get_language_codes,
    get_og_locale,
)
from helpers import (
    _asset_hash,
    CURRENT_YEAR,
    tag_to_slug,
    format_date,
    format_reading_time,
    get_lang_path,
    get_alternate_lang,
)
from seo import render_person_jsonld, render_jsonld_script
from cv_parser import load_cv_data


# ============================================================
# Shared HTML Template Helpers
# ============================================================


def render_theme_toggle_svg():
    """Render the sun/moon SVG icons used by all theme toggle buttons.

    Returns:
        str: SVG HTML for sun and moon icons.
    """
    return """<svg class="sun-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="5"/>
                        <line x1="12" y1="1" x2="12" y2="3"/>
                        <line x1="12" y1="21" x2="12" y2="23"/>
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
                        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
                        <line x1="1" y1="12" x2="3" y2="12"/>
                        <line x1="21" y1="12" x2="23" y2="12"/>
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
                        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
                    </svg>
                    <svg class="moon-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
                    </svg>"""


def render_skip_link(lang="en"):
    """Render skip-to-content accessibility link.

    Args:
        lang (str): Language code ('en' or 'pt').

    Returns:
        str: HTML for skip navigation link.
    """
    label = LANGUAGES[lang]["ui"]["skip_to_content"]
    return f'<a href="#main-content" class="skip-link">{label}</a>'


def render_nav(lang, active_page, lang_toggle_html):
    """Render the site navigation bar shared across all pages.

    Args:
        lang (str): Current language code ('en' or 'pt').
        active_page (str): Which nav item is active ('blog', 'about', 'cv').
        lang_toggle_html (str): Pre-rendered language toggle HTML.

    Returns:
        str: Complete <nav> HTML element.
    """
    ui = LANGUAGES[lang]["ui"]

    blog_class = ' class="active"' if active_page == "blog" else ""
    about_class = ' class="active"' if active_page == "about" else ""
    cv_class = ' class="active"' if active_page == "cv" else ""

    return f"""<nav class="nav" style="view-transition-name: site-nav;">
        <div class="nav-container">
            <a href="{get_lang_path(lang, "index.html")}" class="logo" style="view-transition-name: landing-title;">dan.rio</a>
            <div class="nav-right">
                <ul class="nav-links">
                    <li><a href="{get_lang_path(lang, "index.html")}"{blog_class} style="view-transition-name: nav-blog;">{ui["blog"]}</a></li>
                    <li><a href="{get_lang_path(lang, "about.html")}"{about_class} style="view-transition-name: nav-about;">{ui["about"]}</a></li>
                    <li><a href="{get_lang_path(lang, "cv.html")}"{cv_class} style="view-transition-name: nav-cv;">{ui["cv"]}</a></li>
                </ul>
                <div style="view-transition-name: lang-toggle;">{lang_toggle_html}</div>
                <button id="theme-toggle" class="theme-toggle" aria-label="{_html.escape(ui["toggle_theme"])}" style="view-transition-name: theme-toggle;">
                    {render_theme_toggle_svg()}
                </button>
            </div>
        </div>
    </nav>"""


def render_footer(lang="en"):
    """Render the site footer shared across all pages.

    Uses SOCIAL_LINKS from config, dynamic CURRENT_YEAR for copyright,
    and locale-aware "All Rights Reserved" text.

    Args:
        lang (str): Language code ('en' or 'pt').

    Returns:
        str: Complete <footer> HTML element.
    """
    ui = LANGUAGES[lang]["ui"]
    return f"""<footer class="footer" style="view-transition-name: site-footer;">
        <div class="footer-container">
            <div class="social-links">
                <a href="{SOCIAL_LINKS["twitter"]}" target="_blank" rel="noopener" aria-label="Twitter">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                </a>
                <a href="{SOCIAL_LINKS["github"]}" target="_blank" rel="noopener" aria-label="GitHub">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                </a>
                <a href="{SOCIAL_LINKS["linkedin"]}" target="_blank" rel="noopener" aria-label="LinkedIn">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                </a>
            </div>
            <p class="copyright">&copy; {CURRENT_YEAR} {ui["all_rights_reserved"]}.</p>
        </div>
    </footer>"""


def render_head(
    title,
    description,
    lang,
    current_url,
    other_lang=None,
    other_url=None,
    extra_meta="",
    stylesheets=None,
    scripts_head=None,
    scripts_defer=None,
):
    """Render the <head> section shared across all pages.

    Args:
        title (str): Page title for <title> tag.
        description (str): Meta description content.
        lang (str): Current language code.
        current_url (str): Canonical URL for this page.
        other_lang (str, optional): Alternate language code.
        other_url (str, optional): Alternate language URL.
        extra_meta (str): Additional meta tags (Open Graph, etc.).
        stylesheets (list, optional): CSS file paths to include.
        scripts_head (list, optional): JS files to load in head (blocking).
        scripts_defer (list, optional): JS files to load deferred.

    Returns:
        str: Complete <head> HTML element.
    """
    if stylesheets is None:
        stylesheets = [f"{BASE_PATH}/static/css/styles.css"]
    if scripts_head is None:
        scripts_head = [f"{BASE_PATH}/static/js/theme.js"]
    if scripts_defer is None:
        # Non-landing pages share the same SPA lifecycle. Keep sitewide
        # interaction scripts available everywhere so page-type features like
        # filters and post annotations are ready on first transition, not only
        # after a hard refresh.
        scripts_defer = [
            f"{BASE_PATH}/static/js/transitions.js",
            f"{BASE_PATH}/static/js/filter.js",
            f"{BASE_PATH}/static/js/annotations.js",
            f"{BASE_PATH}/static/js/presentation.js",
        ]

    # Build versioned stylesheet links (content-hash per file)
    css_links = "\n    ".join(
        f'<link rel="stylesheet" href="{css}?v={_asset_hash(css)}">' for css in stylesheets
    )

    # Build script tags (head scripts get preloaded + loaded, defer scripts get deferred)
    head_script_tags = "\n    ".join(
        f'<link rel="preload" href="{js}?v={_asset_hash(js)}" as="script">\n    <script src="{js}?v={_asset_hash(js)}"></script>'
        for js in scripts_head
    )

    defer_script_tags = "\n    ".join(
        f'<script src="{js}?v={_asset_hash(js)}" defer></script>' for js in scripts_defer
    )

    # Language alternate links (includes x-default for language-neutral fallback)
    lang_alternates = ""
    if other_lang and other_url:
        lang_alternates = f"""
    <link rel="alternate" hreflang="x-default" href="{SITE_URL}/">
    <link rel="alternate" hreflang="{lang}" href="{current_url}">
    <link rel="alternate" hreflang="{other_lang}" href="{other_url}">"""

    return f"""<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{_html.escape(title)}</title>
    <meta name="description" content="{_html.escape(description)}">
    
    <!-- Canonical URL -->
    <link rel="canonical" href="{current_url}">
    
    {extra_meta}
    
    <!-- Additional SEO -->
    <meta name="author" content="{_html.escape(AUTHOR)}">
    <meta name="robots" content="index, follow">
    {lang_alternates}
    
    {css_links}
    {head_script_tags}
    {defer_script_tags}
</head>"""


def generate_lang_toggle_html(current_lang: str, current_page: str) -> str:
    """Generate language toggle button HTML as a single unified control.

    Creates a single button showing a globe icon and both languages (EN / PT) with
    the active language highlighted by a soft ambient glow. Clicking the button
    switches to the opposite language.

    Args:
        current_lang (str): Current page language code ('en' or 'pt')
        current_page (str): Relative page path (e.g., "index.html" or "blog/post-slug.html")

    Returns:
        str: HTML string for language toggle button
    """
    other_lang = get_alternate_lang(current_lang)
    other_lang_path = get_lang_path(other_lang, current_page)

    # Build language label spans from LANGUAGES config
    lang_spans = []
    for code in LANGUAGES:
        label = LANGUAGES[code]["label"]
        active = " active" if code == current_lang else ""
        lang_spans.append(f'<span class="lang-{code}{active}">{label}</span>')
    lang_labels_html = '\n            <span class="lang-sep">/</span>\n            '.join(
        lang_spans
    )

    # Accessibility label (locale-aware)
    current_name = LANGUAGES[current_lang]["name"]
    target_name = LANGUAGES[other_lang]["name"]
    switch_tpl = LANGUAGES[current_lang]["ui"].get(
        "switch_language", "Switch to {target} (currently {current})"
    )
    aria_label = switch_tpl.format(target=target_name, current=current_name)

    return f'''<a href="{other_lang_path}" class="lang-toggle" aria-label="{_html.escape(aria_label)}" data-current-lang="{current_lang}">
        <svg class="lang-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
        <span class="lang-text">
            {lang_labels_html}
        </span>
    </a>'''


def _presentation_labels(lang):
    """Return small localized strings for presentation controls."""
    if lang == "pt":
        return {
            "back": "Voltar ao blog",
            "slides": "Slides da apresentação",
            "controls": "Controles da apresentação",
            "previous": "Slide anterior",
            "next": "Próximo slide",
            "fullscreen": "Tela cheia",
            "exit_fullscreen": "Sair da tela cheia",
            "progress": "Progresso da apresentação",
            "progress_text": "Slide {current} de {total}",
            "jump": "Ir para o slide",
            "jump_button": "Ir",
            "slide_label": "Slide {current} de {total}",
            "marker": "Apresentação",
        }

    return {
        "back": "Back to blog",
        "slides": "Presentation slides",
        "controls": "Presentation controls",
        "previous": "Previous slide",
        "next": "Next slide",
        "fullscreen": "Fullscreen",
        "exit_fullscreen": "Exit fullscreen",
        "progress": "Presentation progress",
        "progress_text": "Slide {current} of {total}",
        "jump": "Go to slide",
        "jump_button": "Go",
        "slide_label": "Slide {current} of {total}",
        "marker": "Presentation",
    }


def _presentation_attr(value):
    return _html.escape(str(value), quote=True)


def _presentation_text(value):
    if value is None:
        return ""
    return _html.escape(str(value))


def _presentation_slide_id(slide, index):
    raw_id = str(slide.get("id") or f"slide-{index + 1:02d}").strip()
    return raw_id or f"slide-{index + 1:02d}"


def _render_presentation_text_items(items, tag="p"):
    if isinstance(items, str):
        items = [items]
    if not isinstance(items, list):
        items = [items]
    return "\n".join(
        f'<{tag}>{_presentation_text(item.get("text", "") if isinstance(item, dict) else item)}</{tag}>'
        for item in items
        if item is not None
    )


def render_presentation_cards(block):
    """Render a presentation card grid block."""
    cards = block.get("cards", block.get("items", []))
    if not cards:
        return ""

    cards_html = []
    for card in cards:
        if not isinstance(card, dict):
            card = {"body": card}
        title = card.get("title") or card.get("label")
        body = card.get("body") or card.get("text") or card.get("content")
        kicker = card.get("kicker")
        parts = []
        if kicker:
            parts.append(
                f'<div class="presentation-card-kicker">{_presentation_text(kicker)}</div>'
            )
        if title:
            parts.append(f'<h3 class="presentation-card-title">{_presentation_text(title)}</h3>')
        if isinstance(body, list):
            parts.append(_render_presentation_text_items(body))
        elif body:
            parts.append(f'<p>{_presentation_text(body)}</p>')
        cards_html.append(
            '<article class="presentation-card">'
            + "\n".join(parts)
            + "</article>"
        )

    return '<div class="presentation-card-grid">\n' + "\n".join(cards_html) + "\n</div>"


def render_presentation_split(block):
    """Render a two-column presentation block."""
    columns = block.get("columns", [])
    if not columns:
        return ""

    rendered_columns = []
    for column in columns:
        if isinstance(column, dict):
            title = column.get("title")
            blocks = column.get("blocks", column.get("items", column.get("content", [])))
        else:
            title = ""
            blocks = column

        column_parts = []
        if title:
            column_parts.append(
                f'<h3 class="presentation-column-title">{_presentation_text(title)}</h3>'
            )
        if isinstance(blocks, list):
            column_parts.extend(render_presentation_block(item) for item in blocks)
        else:
            column_parts.append(render_presentation_block({"type": "paragraph", "text": blocks}))

        rendered_columns.append(
            '<div class="presentation-column">' + "\n".join(column_parts) + "</div>"
        )

    return '<div class="presentation-split">\n' + "\n".join(rendered_columns) + "\n</div>"


def render_presentation_table(block):
    """Render a responsive presentation table block."""
    headers = block.get("headers", block.get("headings", []))
    rows = block.get("rows", [])

    header_html = ""
    if headers:
        cells = "".join(f"<th>{_presentation_text(header)}</th>" for header in headers)
        header_html = f"<thead><tr>{cells}</tr></thead>"

    body_rows = []
    for row in rows:
        if isinstance(row, dict):
            row = [row.get(header, "") for header in headers] if headers else list(row.values())
        cells = "".join(f"<td>{_presentation_text(cell)}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")

    return (
        '<div class="presentation-table-wrap" data-overflow="scroll">'
        f"<table>{header_html}<tbody>{''.join(body_rows)}</tbody></table>"
        "</div>"
    )


def render_presentation_code(block):
    """Render a code block without translating or interpreting its content."""
    language = block.get("language") or block.get("lang") or "text"
    code = block.get("code", block.get("text", ""))
    return (
        f'<pre class="presentation-code" data-language="{_presentation_attr(language)}" '
        '><code>'
        f"{_presentation_text(code)}</code></pre>"
    )


def render_presentation_block(block, lang="en"):
    """Render one structured presentation block."""
    if block is None:
        return ""
    if isinstance(block, str):
        return f"<p>{_presentation_text(block)}</p>"
    if not isinstance(block, dict):
        return f"<p>{_presentation_text(block)}</p>"

    block_type = block.get("type", "paragraph")

    if block_type in {"paragraph", "text"}:
        content = block.get("text", block.get("body", block.get("content", "")))
        return _render_presentation_text_items(content)

    if block_type in {"heading", "subheading"}:
        level = 3 if block_type == "heading" else 4
        return f'<h{level}>{_presentation_text(block.get("text", ""))}</h{level}>'

    if block_type in {"list", "bullets"}:
        tag = "ol" if block.get("ordered") else "ul"
        items = block.get("items", [])
        items_html = "".join(
            f"<li>{_presentation_text(item.get('text', '') if isinstance(item, dict) else item)}</li>"
            for item in items
        )
        return f'<{tag} class="presentation-list">{items_html}</{tag}>'

    if block_type == "quote":
        text = block.get("text", block.get("quote", ""))
        cite = block.get("cite", block.get("attribution", ""))
        cite_html = f"<cite>{_presentation_text(cite)}</cite>" if cite else ""
        return f"<blockquote>{_render_presentation_text_items(text)}{cite_html}</blockquote>"

    if block_type in {"cards", "card_grid"}:
        return render_presentation_cards(block)

    if block_type == "split":
        return render_presentation_split(block)

    if block_type == "table":
        return render_presentation_table(block)

    if block_type == "code":
        return render_presentation_code(block)

    if block_type == "image":
        src = block.get("src", "")
        alt = block.get("alt", "")
        caption = block.get("caption", "")
        caption_html = (
            f"<figcaption>{_presentation_text(caption)}</figcaption>" if caption else ""
        )
        return (
            '<figure class="presentation-figure">'
            f'<img src="{_presentation_attr(src)}" alt="{_presentation_attr(alt)}" loading="lazy">'
            f"{caption_html}</figure>"
        )

    if block_type in {"callout", "emphasis"}:
        content = block.get("text", block.get("body", block.get("content", "")))
        return (
            '<div class="presentation-callout">'
            f"{_render_presentation_text_items(content)}"
            "</div>"
        )

    return f"<p>{_presentation_text(block.get('text', block.get('content', '')))}</p>"


def render_presentation_slide(slide, index, total, lang="en"):
    """Render one presentation slide with stable ids and data attributes."""
    slide_id = _presentation_slide_id(slide, index)
    layout = slide.get("layout", "content")
    density = slide.get("density", "normal")
    variant = slide.get("variant", "")
    overflow = slide.get("overflow")
    if not overflow and layout == "table":
        overflow = "scroll"

    blocks = list(slide.get("blocks", []))
    if not blocks:
        for key in ("paragraphs", "items", "cards", "columns", "rows", "code", "image"):
            if key in slide:
                block_type = {
                    "paragraphs": "paragraph",
                    "items": "list",
                    "cards": "card_grid",
                    "columns": "split",
                    "rows": "table",
                    "code": "code",
                    "image": "image",
                }[key]
                block = {"type": block_type}
                if key == "paragraphs":
                    block["content"] = slide[key]
                elif key == "rows":
                    block["headers"] = slide.get("headers", [])
                    block["rows"] = slide[key]
                elif key == "image" and isinstance(slide[key], dict):
                    block.update(slide[key])
                else:
                    block[key] = slide[key]
                blocks.append(block)
                break

    title = slide.get("title")
    subtitle = slide.get("subtitle")
    kicker = slide.get("kicker")

    header_parts = []
    if kicker:
        header_parts.append(f'<p class="presentation-kicker">{_presentation_text(kicker)}</p>')
    if title:
        header_parts.append(f"<h2>{_presentation_text(title)}</h2>")
    if subtitle:
        header_parts.append(
            f'<p class="presentation-subtitle">{_presentation_text(subtitle)}</p>'
        )
    header_html = (
        '<header class="presentation-slide-header">'
        + "\n".join(header_parts)
        + "</header>"
        if header_parts
        else ""
    )

    slide_html = slide.get("html")
    if slide_html and not blocks:
        blocks_html = str(slide_html)
    else:
        blocks_html = "\n".join(render_presentation_block(block, lang) for block in blocks)
    overflow_attr = f' data-overflow="{_presentation_attr(overflow)}"' if overflow else ""
    variant_attr = f' data-variant="{_presentation_attr(variant)}"' if variant else ""
    labels = _presentation_labels(lang)
    slide_label = labels["slide_label"].format(current=index + 1, total=total)

    return f"""<section id="{_presentation_attr(slide_id)}"
                    class="presentation-slide presentation-slide-{_presentation_attr(layout)}"
                    data-slide-index="{index}"
                    data-slide-number="{index + 1}"
                    data-slide-id="{_presentation_attr(slide_id)}"
                    data-layout="{_presentation_attr(layout)}"
                    data-density="{_presentation_attr(density)}"{variant_attr}{overflow_attr}
                    aria-label="{_presentation_attr(slide_label)}"
                    aria-hidden="{'false' if index == 0 else 'true'}">
                <div class="presentation-slide-inner">
                    {header_html}
                    <div class="presentation-slide-body">
                        {blocks_html}
                    </div>
                </div>
            </section>"""


def generate_presentation_html(presentation, post_number, lang="en"):
    """Generate HTML for a blog-native presentation page."""
    current_page = f"blog/{presentation['slug']}.html"
    lang_toggle_html = generate_lang_toggle_html(lang, current_page)
    labels = _presentation_labels(lang)

    slides = presentation.get("slides", [])
    total_slides = len(slides)
    slides_html = "\n".join(
        render_presentation_slide(slide, index, total_slides, lang)
        for index, slide in enumerate(slides)
    )

    tags_html = ""
    if presentation.get("tags"):
        tag_pills = "".join(
            f'<span class="tag-pill">{_html.escape(tag)}</span>' for tag in presentation["tags"]
        )
        tags_html = f'<div class="post-tags">{tag_pills}</div>'

    published_date = presentation.get("published_date", presentation.get("date", ""))
    published_date_display = format_date(published_date, lang)
    reading_time_raw = presentation.get("reading_time", 1)
    try:
        reading_minutes = int(str(reading_time_raw).split()[0])
    except (ValueError, IndexError):
        reading_minutes = 1
    reading_time_display = format_reading_time(reading_minutes, lang)

    other_lang = get_alternate_lang(lang)
    other_url = f"{SITE_URL}/{other_lang}/blog/{presentation['slug']}.html"
    current_url = f"{SITE_URL}/{lang}/blog/{presentation['slug']}.html"
    raw_description = presentation["excerpt"][:160]
    meta_description = _html.escape(raw_description)
    jsonld_date_modified = presentation.get("updated_fm_date") or published_date
    presentation_jsonld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": presentation["title"],
        "description": raw_description,
        "url": current_url,
        "inLanguage": lang,
        "datePublished": published_date,
        "dateModified": jsonld_date_modified,
        "author": render_person_jsonld(),
        "publisher": render_person_jsonld(),
        "genre": "Presentation",
        "learningResourceType": "Presentation",
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": current_url,
        },
    }
    if presentation.get("tags"):
        presentation_jsonld["keywords"] = ", ".join(presentation["tags"])
    jsonld = render_jsonld_script(presentation_jsonld)

    extra_meta = f"""<!-- Open Graph / Social -->
    <meta property="og:type" content="article">
    <meta property="og:url" content="{current_url}">
    <meta property="og:title" content="{_html.escape(presentation["title"])}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:site_name" content="{_html.escape(SITE_NAME)}">
    <meta property="og:locale" content="{get_og_locale(lang)}">
    <meta property="og:locale:alternate" content="{get_og_locale(other_lang)}">
    <meta property="article:published_time" content="{published_date}">
    <meta property="article:modified_time" content="{jsonld_date_modified}">
    <meta property="article:author" content="{_html.escape(AUTHOR)}">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{_html.escape(presentation["title"])}">
    <meta name="twitter:description" content="{meta_description}">

    {jsonld}"""

    head = render_head(
        title=f"{presentation['title']} – {AUTHOR} | {SITE_NAME}",
        description=raw_description,
        lang=lang,
        current_url=current_url,
        other_lang=other_lang,
        other_url=other_url,
        extra_meta=extra_meta,
        stylesheets=[
            f"{BASE_PATH}/static/css/styles.css",
            f"{BASE_PATH}/static/css/post.css",
            f"{BASE_PATH}/static/css/presentation.css",
        ],
        scripts_defer=[
            f"{BASE_PATH}/static/js/transitions.js",
            f"{BASE_PATH}/static/js/filter.js",
            f"{BASE_PATH}/static/js/annotations.js",
            f"{BASE_PATH}/static/js/presentation.js",
        ],
    )

    nav = render_nav(lang, "blog", lang_toggle_html)
    footer = render_footer(lang)
    skip_link = render_skip_link(lang)
    progress_text = labels["progress_text"].format(current=1, total=total_slides)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
{head}
<body>
    {skip_link}
    {nav}

    <main id="main-content" class="container presentation-page" data-presentation-page data-slide-count="{total_slides}">
        <article class="presentation-post" style="view-transition-name: post-container-{post_number};">
            <header class="presentation-header">
                <a href="{get_lang_path(lang, "index.html")}" class="back-link">{labels["back"]}</a>
                <h1 class="post-title-large presentation-title" style="view-transition-name: post-title-{post_number};">{_html.escape(presentation["title"].upper())}</h1>
                <div class="post-meta">
                    <time class="post-date" style="view-transition-name: post-date-{post_number};">{published_date_display}</time>
                    <span class="post-separator">•</span>
                    <span class="post-reading-time">{reading_time_display}</span>
                </div>
                {tags_html}
                <p class="lead presentation-excerpt" style="view-transition-name: post-excerpt-{post_number};">
                    {_html.escape(presentation["excerpt"])}
                </p>
            </header>

            <section class="presentation-stage"
                     data-presentation-stage
                     data-slide-count="{total_slides}"
                     aria-label="{_html.escape(labels["slides"])}"
                     data-progress-template="{_html.escape(labels["progress_text"])}"
                     tabindex="-1">
                {slides_html}
            </section>

            <nav class="presentation-controls" aria-label="{_html.escape(labels["controls"])}">
                <button type="button" class="presentation-control" data-presentation-action="previous" aria-label="{_html.escape(labels["previous"])}">
                    <span aria-hidden="true">&larr;</span>
                </button>
                <div class="presentation-progress"
                     role="progressbar"
                     aria-label="{_html.escape(labels["progress"])}"
                     aria-valuemin="1"
                     aria-valuemax="{total_slides}"
                     aria-valuenow="1">
                    <span class="presentation-progress-text" data-presentation-progress-text aria-live="polite">{progress_text}</span>
                    <div class="presentation-progress-track">
                        <div class="presentation-progress-bar"
                             data-presentation-progress-bar
                             style="width: {100 if total_slides <= 1 else round(100 / total_slides, 2)}%;"></div>
                    </div>
                </div>
                <form class="presentation-jump" data-presentation-jump-form>
                    <label class="presentation-jump-label" for="presentation-jump-input">{_html.escape(labels["jump"])}</label>
                    <input id="presentation-jump-input"
                           class="presentation-jump-input"
                           data-presentation-slide-input
                           type="number"
                           inputmode="numeric"
                           min="1"
                           max="{total_slides}"
                           value="1"
                           aria-label="{_html.escape(labels["jump"])}">
                    <button type="submit" class="presentation-jump-submit">{_html.escape(labels["jump_button"])}</button>
                </form>
                <button type="button" class="presentation-control" data-presentation-action="next" aria-label="{_html.escape(labels["next"])}">
                    <span aria-hidden="true">&rarr;</span>
                </button>
                <button type="button" class="presentation-control presentation-fullscreen-control"
                        data-presentation-action="fullscreen"
                        data-label-enter="{_html.escape(labels["fullscreen"])}"
                        data-label-exit="{_html.escape(labels["exit_fullscreen"])}"
                        aria-label="{_html.escape(labels["fullscreen"])}"
                        aria-pressed="false">
                    <span aria-hidden="true">⛶</span>
                </button>
            </nav>
        </article>
    </main>

    {footer}
</body>
</html>"""


def generate_post_html(post, post_number, lang="en"):
    """Generate HTML for individual blog post page.

    Creates complete HTML page with post content, metadata, navigation,
    theme toggle, language toggle, and view transition support.

    Args:
        post (Dict): Post data with title, content, excerpt, tags, dates, etc.
        post_number (int): Sequential post number for ordering.
        lang (str): Language code ('en' or 'pt').

    Returns:
        str: Complete HTML document for the post.
    """
    if post.get("content_type") == "presentation":
        return generate_presentation_html(post, post_number, lang)

    # Generate language-specific paths
    current_page = f"blog/{post['slug']}.html"
    lang_toggle_html = generate_lang_toggle_html(lang, current_page)
    ui = LANGUAGES[lang]["ui"]

    # Generate tags HTML for post page
    tags_html = ""
    if post.get("tags"):
        tag_pills = "".join(
            f'<span class="tag-pill">{_html.escape(tag)}</span>' for tag in post["tags"]
        )
        tags_html = f'<div class="post-tags">{tag_pills}</div>'

    # Format last updated date -- only show if frontmatter 'updated' exists
    # and differs from 'date'. Uses editorial dates, not build timestamps.
    updated_fm = post.get("updated_fm_date", "")
    published_fm = post.get("published_date", post.get("date", ""))

    last_updated_html = ""
    if updated_fm and updated_fm != published_fm:
        last_updated_html = f'<div class="last-updated">{ui["last_updated_label"]}: {format_date(updated_fm, lang)}</div>'

    # Published date for display: use frontmatter 'date' (stable, author-controlled)
    published_date_display = format_date(post.get("published_date", post.get("date", "")), lang)

    # Reading time label (locale-aware)
    reading_time_raw = post.get("reading_time", 1)
    if isinstance(reading_time_raw, int):
        reading_time_display = format_reading_time(reading_time_raw, lang)
    else:
        # Legacy string fallback (e.g. "11 min read") -- re-parse the number
        try:
            minutes = int(str(reading_time_raw).split()[0])
        except (ValueError, IndexError):
            minutes = 1
        reading_time_display = format_reading_time(minutes, lang)

    # SEO URLs
    other_lang = get_alternate_lang(lang)
    other_url = f"{SITE_URL}/{other_lang}/blog/{post['slug']}.html"
    current_url = f"{SITE_URL}/{lang}/blog/{post['slug']}.html"
    meta_description = _html.escape(post["excerpt"][:160])
    # Raw (unescaped) description for JSON-LD -- json.dumps handles its own escaping
    raw_description = post["excerpt"][:160]

    # JSON-LD: BlogPosting
    # datePublished: frontmatter 'date' (editorial publication date)
    # dateModified: frontmatter 'updated' if present, else 'date'
    jsonld_date_published = post.get("published_date", post.get("date", ""))
    jsonld_date_modified = post.get("updated_fm_date") or jsonld_date_published
    post_jsonld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post["title"],
        "description": raw_description,
        "url": current_url,
        "inLanguage": lang,
        "datePublished": jsonld_date_published,
        "dateModified": jsonld_date_modified,
        "author": render_person_jsonld(),
        "publisher": render_person_jsonld(),
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": current_url,
        },
    }
    if post.get("tags"):
        post_jsonld["keywords"] = ", ".join(post["tags"])
    jsonld = render_jsonld_script(post_jsonld)

    # Open Graph meta
    extra_meta = f"""<!-- Open Graph / Social -->
    <meta property="og:type" content="article">
    <meta property="og:url" content="{current_url}">
    <meta property="og:title" content="{_html.escape(post["title"])}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:site_name" content="{_html.escape(SITE_NAME)}">
    <meta property="og:locale" content="{get_og_locale(lang)}">
    <meta property="og:locale:alternate" content="{get_og_locale(other_lang)}">
    <meta property="article:published_time" content="{jsonld_date_published}">
    <meta property="article:modified_time" content="{jsonld_date_modified}">
    <meta property="article:author" content="{_html.escape(AUTHOR)}">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{_html.escape(post["title"])}">
    <meta name="twitter:description" content="{meta_description}">
    
    {jsonld}"""

    head = render_head(
        title=f"{post['title']} – {AUTHOR} | {SITE_NAME}",
        description=raw_description,
        lang=lang,
        current_url=current_url,
        other_lang=other_lang,
        other_url=other_url,
        extra_meta=extra_meta,
        stylesheets=[f"{BASE_PATH}/static/css/styles.css", f"{BASE_PATH}/static/css/post.css"],
    )

    nav = render_nav(lang, "blog", lang_toggle_html)
    footer = render_footer(lang)
    skip_link = render_skip_link(lang)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
{head}
<body
    data-copy-section-link="{_html.escape(ui['copy_section_link'])}"
    data-copy-passage-link="{_html.escape(ui['copy_passage_link'])}"
    data-link-copied="{_html.escape(ui['link_copied'])}"
>
    {skip_link}
    {nav}

    <main id="main-content" class="container">
        <article class="post" style="view-transition-name: post-container-{post_number};">
            <header class="post-header">
                <a href="{get_lang_path(lang, "index.html")}" class="back-link">{ui["back_to_blog"]}</a>
                {last_updated_html}
                <h1 class="post-title-large" style="view-transition-name: post-title-{post_number};">{_html.escape(post["title"].upper())}</h1>
                <div class="post-meta">
                    <time class="post-date" style="view-transition-name: post-date-{post_number};">{published_date_display}</time>
                    <span class="post-separator">•</span>
                    <span class="post-reading-time">{reading_time_display}</span>
                </div>
                {tags_html}
            </header>

            <div class="post-body">
                <p class="lead" style="view-transition-name: post-excerpt-{post_number};">
                    {_html.escape(post["excerpt"])}
                </p>
                {post["content"]}
            </div>
        </article>
    </main>

    {footer}
</body>
</html>"""


def generate_post_card(post, post_number, lang="en"):
    """Generate HTML card for post on index page.

    Creates post preview card with view transition naming for smooth
    morphing animation when navigating to full post.

    Args:
        post (Dict): Post data with title, excerpt, tags, dates, slug, etc.
        post_number (int): Sequential post number for view transition naming.
        lang (str): Language code ('en' or 'pt').

    Returns:
        str: HTML article element for the post card.
    """
    # Generate tags HTML
    content_type_marker = ""
    if post.get("content_type") == "presentation":
        marker = _presentation_labels(lang)["marker"]
        content_type_marker = (
            f'<span class="tag-pill content-type-marker" data-content-type-marker="presentation">'
            f"{_html.escape(marker)}</span>"
        )

    tags_html = ""
    if post.get("tags"):
        tag_pills = "".join(
            f'<span class="tag-pill">{_html.escape(tag)}</span>' for tag in post["tags"]
        )
        tags_html = f'<div class="post-tags">{content_type_marker}{tag_pills}</div>'
    elif content_type_marker:
        tags_html = f'<div class="post-tags">{content_type_marker}</div>'

    # Create data attributes for filtering and sorting
    tags_attr = _html.escape(",".join(post.get("tags", [])))
    # Canonical EN slugs for stable cross-language filter-state restoration
    tag_keys_attr = ",".join(tag_to_slug(t) for t in post.get("en_tags", post.get("tags", [])))
    # Use frontmatter-derived dates for client-side sort (stable, author-controlled)
    created_timestamp = post.get("published_date", post.get("date", ""))
    updated_timestamp = post.get("updated_fm_date") or post.get(
        "published_date", post.get("date", "")
    )

    # Generate language-specific blog post link
    post_url = get_lang_path(lang, f"blog/{post['slug']}.html")

    content_type_attr = (
        f' data-content-type="{_html.escape(post["content_type"])}"'
        if post.get("content_type")
        else ""
    )

    return f"""            <article class="post-card"{content_type_attr}
                     data-year="{post["year"]}" 
                     data-month="{post["month"]}" 
                     data-tags="{tags_attr}"
                     data-tag-keys="{tag_keys_attr}"
                     data-created="{created_timestamp}"
                     data-updated="{updated_timestamp}"
                     style="view-transition-name: post-container-{post_number};">
                <a href="{post_url}" class="post-link">
                    <div class="post-content">
                        <h2 class="post-title" style="view-transition-name: post-title-{post_number};">{_html.escape(post["title"].upper())}</h2>
                        <time class="post-date" style="view-transition-name: post-date-{post_number};">{format_date(post.get("published_date", post.get("date", "")), lang)}</time>
                        {tags_html}
                        <p class="post-excerpt" style="view-transition-name: post-excerpt-{post_number};">
                            {_html.escape(post["excerpt"])}
                        </p>
                    </div>
                </a>
            </article>"""


def generate_index_html(posts, lang="en"):
    """Generate main blog index page with filtering.

    Creates index.html with post cards, filter controls (year/month/tag),
    sort controls (newest/oldest/updated), and bilingual navigation.

    Args:
        posts (List[Dict]): List of all posts to display.
        lang (str): Language code ('en' or 'pt').

    Returns:
        str: Complete HTML document for the index page.
    """
    lang_toggle_html = generate_lang_toggle_html(lang, "index.html")
    ui = LANGUAGES[lang]["ui"]
    posts_html = "\n\n".join(generate_post_card(post, i + 1, lang) for i, post in enumerate(posts))

    # Collect all unique years, months, and tags for filters (only from existing posts)
    years = sorted(set(post["year"] for post in posts), reverse=True)

    # Collect only months that have posts
    months_with_posts = sorted(
        set(post["month"] for post in posts),
        key=lambda m: [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ].index(m),
    )

    all_tags = sorted(set(tag for post in posts for tag in post.get("tags", [])))

    # Build display-tag -> canonical-EN-slug mapping for data-tag-key attributes.
    # For EN posts, en_tags == tags, so tag_to_slug(en_tag) is used directly.
    # For PT posts, en_tags holds the original EN tags at the same index as the
    # translated PT tags, so we can recover the EN slug for each display tag.
    tag_key_map: dict = {}
    for post in posts:
        pt_tags = post.get("tags", [])
        en_tags_list = post.get("en_tags", pt_tags)
        for pt_tag, en_tag in zip(pt_tags, en_tags_list):
            tag_key_map.setdefault(pt_tag, tag_to_slug(en_tag))

    # Generate year options
    year_options = f'<div class="select-option" data-value="">{ui["all_years"]}</div>' + "".join(
        f'<div class="select-option" data-value="{year}">{year}</div>' for year in years
    )

    # Get month translations
    months_dict = LANGUAGES[lang].get("months", {})

    # Generate month options (only months with posts)
    month_options = f'<div class="select-option" data-value="">{ui["all_months"]}</div>' + "".join(
        f'<div class="select-option" data-value="{month}">{months_dict.get(month, month)}</div>'
        for month in months_with_posts
    )

    # Generate tag pills for filter
    tag_pills_html = "".join(
        f'<button class="filter-tag" data-tag="{_html.escape(tag)}" data-tag-key="{tag_key_map.get(tag, tag_to_slug(tag))}">{_html.escape(tag)}</button>'
        for tag in all_tags
    )

    # Generate language-specific SEO info
    other_lang = get_alternate_lang(lang)
    current_url = f"{SITE_URL}/{lang}/index.html"
    other_url = f"{SITE_URL}/{other_lang}/index.html"
    meta_description = LANGUAGES[lang]["ui"]["meta_index"]

    # JSON-LD: Blog with author
    jsonld = render_jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "Blog",
            "name": f"{AUTHOR} | Blog",
            "url": current_url,
            "description": meta_description,
            "inLanguage": lang,
            "author": render_person_jsonld(),
            "publisher": render_person_jsonld(),
        }
    )

    # Open Graph meta
    esc_meta_desc = _html.escape(meta_description)
    extra_meta = f"""<!-- Open Graph / Social -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{current_url}">
    <meta property="og:title" content="{_html.escape(AUTHOR)} | Blog">
    <meta property="og:description" content="{esc_meta_desc}">
    <meta property="og:site_name" content="{_html.escape(SITE_NAME)}">
    <meta property="og:locale" content="{get_og_locale(lang)}">
    <meta property="og:locale:alternate" content="{get_og_locale(other_lang)}">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{_html.escape(AUTHOR)} | Blog">
    <meta name="twitter:description" content="{esc_meta_desc}">
    
    {jsonld}"""

    head = render_head(
        title=f"{AUTHOR} | Blog – {SITE_NAME}",
        description=meta_description,
        lang=lang,
        current_url=current_url,
        other_lang=other_lang,
        other_url=other_url,
        extra_meta=extra_meta,
        stylesheets=[f"{BASE_PATH}/static/css/styles.css"],
    )

    nav = render_nav(lang, "blog", lang_toggle_html)
    footer = render_footer(lang)
    skip_link = render_skip_link(lang)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
{head}
<body>
    {skip_link}
    {nav}

    <main id="main-content" class="container">
        <header class="page-header" style="view-transition-name: blog-header;">
            <div class="header-content">
                <h1 class="page-title">{ui["latest_posts"]}</h1>
                <div class="header-controls">
                    <div class="sort-control">
                        <span class="sort-label">{ui["sort_by"]}</span>
                        <button id="order-toggle" class="order-toggle" data-order="created" data-label-updated="{ui["last_updated"]}" data-label-created="{ui["published_at"]}" aria-label="{ui["toggle_sort_order"]}">
                            <span class="order-toggle-text">{ui["published_at"]}</span>
                        </button>
                    </div>
                    <button id="filter-toggle" class="filter-toggle" aria-label="{ui["toggle_filters"]}">
                        <span class="filter-toggle-text">{ui["filter"]}</span>
                        <svg class="filter-toggle-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="6 9 12 15 18 9"></polyline>
                        </svg>
                    </button>
                </div>
            </div>
        </header>

        <div class="filters" id="filters-panel" style="view-transition-name: blog-filters;">
            <div class="filter-row">
                <div class="custom-select" id="year-filter-wrapper">
                    <div class="select-trigger" data-value="">
                        <span class="select-label">{ui["all_years"]}</span>
                    </div>
                    <div class="select-options">
                        {year_options}
                    </div>
                </div>
                <div class="custom-select" id="month-filter-wrapper">
                    <div class="select-trigger" data-value="">
                        <span class="select-label">{ui["all_months"]}</span>
                    </div>
                    <div class="select-options">
                        {month_options}
                    </div>
                </div>
                <button id="clear-filters" class="filter-clear">{ui["clear_filters"]}</button>
            </div>
            <div class="filter-tags">
                {tag_pills_html}
            </div>
        </div>

        <div class="posts-grid">
{posts_html}
        </div>
    </main>

    {footer}
</body>
</html>"""


def generate_about_html(lang="en", translated_about=None):
    """Generate About page with translated content.

    Creates about.html page with author bio content from config,
    translated for the specified language.

    Args:
        lang (str): Language code ('en' or 'pt').

    Returns:
        str: Complete HTML document for the About page.
    """
    lang_toggle_html = generate_lang_toggle_html(lang, "about.html")
    if lang == "pt" and translated_about:
        about = translated_about
    else:
        about = LANGUAGES[lang]["about"]

    # SEO info
    other_lang = get_alternate_lang(lang)
    current_url = f"{SITE_URL}/{lang}/about.html"
    other_url = f"{SITE_URL}/{other_lang}/about.html"
    meta_description = LANGUAGES[lang]["ui"]["meta_about"]

    # JSON-LD: ProfilePage + Person
    about_name_tpl = LANGUAGES[lang]["ui"].get("about_jsonld_name", "About {author}")
    about_bio = LANGUAGES[lang]["ui"].get("author_bio", AUTHOR_BIO)
    jsonld = render_jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "ProfilePage",
            "name": about_name_tpl.format(author=AUTHOR),
            "url": current_url,
            "mainEntity": {
                **render_person_jsonld(),
                "description": about_bio,
            },
        }
    )

    # Open Graph meta
    esc_meta_desc = _html.escape(meta_description)
    extra_meta = f"""<!-- Open Graph / Social -->
    <meta property="og:type" content="profile">
    <meta property="og:url" content="{current_url}">
    <meta property="og:title" content="{_html.escape(about["title"])} – {_html.escape(AUTHOR)}">
    <meta property="og:description" content="{esc_meta_desc}">
    <meta property="og:site_name" content="{_html.escape(SITE_NAME)}">
    <meta property="og:locale" content="{get_og_locale(lang)}">
    <meta property="profile:first_name" content="Daniel">
    <meta property="profile:last_name" content="Cavalli">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{_html.escape(about["title"])} – {_html.escape(AUTHOR)}">
    <meta name="twitter:description" content="{esc_meta_desc}">
    
    {jsonld}"""

    head = render_head(
        title=f"{about['title']} – {AUTHOR} | {SITE_NAME}",
        description=meta_description,
        lang=lang,
        current_url=current_url,
        other_lang=other_lang,
        other_url=other_url,
        extra_meta=extra_meta,
        stylesheets=[f"{BASE_PATH}/static/css/styles.css", f"{BASE_PATH}/static/css/post.css"],
    )

    nav = render_nav(lang, "about", lang_toggle_html)
    footer = render_footer(lang)
    skip_link = render_skip_link(lang)

    # Build about paragraphs dynamically
    _strikethrough_re = _re.compile(r"\{\{STRIKETHROUGH:(.+?)\}\}")
    paragraph_keys = sorted(k for k in about if k.startswith("p") and k[1:].isdigit())
    paragraphs_html = []
    for key in paragraph_keys:
        escaped = _html.escape(about[key])
        escaped = _strikethrough_re.sub(r'<s>\1</s>', escaped)
        paragraphs_html.append(f"                <p>{escaped}</p>")
    paragraphs_block = "\n\n".join(paragraphs_html)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
{head}
<body>
    {skip_link}
    {nav}

    <main id="main-content" class="container">
        <article class="post" style="view-transition-name: about-content;">
            <header class="post-header">
                <h1 class="post-title-large" style="view-transition-name: about-title;">{_html.escape(about["title"])}</h1>
            </header>

            <div class="post-body" style="view-transition-name: about-body;">
{paragraphs_block}

                <img src="{BASE_PATH}/static/images/Logo.png" alt="Moana Surfworks" loading="lazy" class="about-image">
            </div>
        </article>
    </main>

    {footer}
</body>
</html>"""


def generate_cv_html(lang="en", translated_cv=None):
    """Generate CV page with professional experience and skills.

    Reads CV data from cv_data.yaml (single source of truth) and generates
    HTML. For Portuguese, uses pre-translated content.

    Args:
        lang (str): Language code ('en' or 'pt').
        translated_cv (Dict, optional): Pre-translated CV data for Portuguese.

    Returns:
        str: Complete HTML document for the CV page.
    """
    lang_toggle_html = generate_lang_toggle_html(lang, "cv.html")
    ui = LANGUAGES[lang]["ui"]

    # Use translated data for Portuguese, otherwise load from YAML
    if lang == "pt" and translated_cv:
        cv_data = translated_cv
    else:
        cv_data = load_cv_data()
        if not cv_data:
            print("Error: Could not load cv_data.yaml")
            return ""

    cv = {
        "title": cv_data["name"].upper(),
        "tagline": cv_data["tagline"],
        "location": cv_data["location"],
        "summary": cv_data["summary"],
        "contact": cv_data["contact"],
        "skills": cv_data["skills"],
        "languages_spoken": cv_data["languages_spoken"],
        "experience": cv_data["experience"],
        "education": cv_data["education"],
    }

    # Build experience HTML with achievements
    experience_html = ""
    for exp in cv["experience"]:
        # Build achievements list if present
        achievements_html = ""
        if exp.get("achievements"):
            achievements_items = "".join(
                f"<li>{_html.escape(ach)}</li>" for ach in exp["achievements"]
            )
            achievements_html = f'<ul class="cv-achievements">{achievements_items}</ul>'

        experience_html += f"""
                <div class="cv-experience-item">
                    <div class="cv-period">{_html.escape(exp["period"])}</div>
                    <div class="cv-details">
                        <h3 class="cv-title">{_html.escape(exp["title"])}</h3>
                        <div class="cv-company">{_html.escape(exp["company"])} · {_html.escape(exp["location"])}</div>
                        <p class="cv-description">{_html.escape(exp["description"])}</p>
                        {achievements_html}
                    </div>
                </div>"""

    # Build skills HTML - simple list format
    skills_list = " · ".join(_html.escape(s) for s in cv["skills"])
    skills_html = f'<p class="cv-skills-inline">{skills_list}</p>'

    # Build education HTML
    education_html = ""
    for edu in cv["education"]:
        education_html += f"""
                    <div class="cv-education-item">
                        <div class="cv-education-degree">{_html.escape(edu["degree"])}</div>
                        <div class="cv-education-school">{_html.escape(edu["school"])}</div>
                        <div class="cv-education-year">{_html.escape(edu["period"])}</div>
                    </div>"""

    # Build languages spoken HTML
    languages_html = ""
    if cv.get("languages_spoken"):
        languages_list = " · ".join(_html.escape(language) for language in cv["languages_spoken"])
        languages_html = f"""
                <section class="cv-section cv-section-compact">
                    <h2 class="cv-section-title">{ui["cv_languages"]}</h2>
                    <p class="cv-languages">{languages_list}</p>
                </section>"""

    # SEO info
    other_lang = get_alternate_lang(lang)
    current_url = f"{SITE_URL}/{lang}/cv.html"
    other_url = f"{SITE_URL}/{other_lang}/cv.html"
    meta_description = LANGUAGES[lang]["ui"]["meta_cv"]

    # JSON-LD: Person (full CV entity)
    jsonld = render_jsonld_script(
        {
            "@context": "https://schema.org",
            "@type": "ProfilePage",
            "name": f"{AUTHOR} – CV",
            "url": current_url,
            "mainEntity": {
                **render_person_jsonld(),
                "description": meta_description,
            },
        }
    )

    # Open Graph meta
    esc_meta_desc = _html.escape(meta_description)
    extra_meta = f"""<!-- Open Graph / Social -->
    <meta property="og:type" content="profile">
    <meta property="og:url" content="{current_url}">
    <meta property="og:title" content="{_html.escape(AUTHOR)} | CV">
    <meta property="og:description" content="{esc_meta_desc}">
    <meta property="og:site_name" content="{_html.escape(SITE_NAME)}">
    <meta property="og:locale" content="{get_og_locale(lang)}">
    <meta property="profile:first_name" content="Daniel">
    <meta property="profile:last_name" content="Cavalli">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{_html.escape(AUTHOR)} | CV">
    <meta name="twitter:description" content="{esc_meta_desc}">
    
    {jsonld}"""

    head = render_head(
        title=f"{AUTHOR} | CV – {SITE_NAME}",
        description=meta_description,
        lang=lang,
        current_url=current_url,
        other_lang=other_lang,
        other_url=other_url,
        extra_meta=extra_meta,
        stylesheets=[
            f"{BASE_PATH}/static/css/styles.css",
            f"{BASE_PATH}/static/css/post.css",
            f"{BASE_PATH}/static/css/cv.css",
        ],
    )

    nav = render_nav(lang, "cv", lang_toggle_html)
    footer = render_footer(lang)
    skip_link = render_skip_link(lang)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
{head}
<body>
    {skip_link}
    {nav}

    <main id="main-content" class="container">
        <article class="post cv-container" style="view-transition-name: cv-content;">
            <header class="post-header cv-header">
                <h1 class="post-title-large" style="view-transition-name: cv-title;">{_html.escape(cv["title"])}</h1>
                <p class="cv-tagline">{_html.escape(cv["tagline"])}</p>
                <p class="cv-location">{_html.escape(cv["location"])}</p>
            </header>

            <div class="post-body cv-body" style="view-transition-name: cv-body;">
                <!-- Contact Section - Prominent for recruiters -->
                <section class="cv-section cv-section-highlight">
                    <h2 class="cv-section-title">{ui["cv_contact"]}</h2>
                    <div class="cv-contact">
                        <div class="cv-contact-item">
                            <span class="cv-contact-label">Email</span>
                            <a href="mailto:{_html.escape(cv["contact"].get("email", ""))}">{_html.escape(cv["contact"].get("email", ""))}</a>
                        </div>
                        <div class="cv-contact-item">
                            <span class="cv-contact-label">LinkedIn</span>
                            <a href="https://linkedin.com/in/{_html.escape(cv["contact"].get("linkedin", ""))}" target="_blank" rel="noopener">linkedin.com/in/{_html.escape(cv["contact"].get("linkedin", ""))}</a>
                        </div>
                        <div class="cv-contact-item">
                            <span class="cv-contact-label">GitHub</span>
                            <a href="https://github.com/{_html.escape(cv["contact"].get("github", ""))}" target="_blank" rel="noopener">github.com/{_html.escape(cv["contact"].get("github", ""))}</a>
                        </div>
                    </div>
                </section>

                <!-- Summary Section -->
                <section class="cv-section">
                    <h2 class="cv-section-title">{ui["cv_summary"]}</h2>
                    <p class="cv-summary">{_html.escape(cv["summary"])}</p>
                </section>

                <!-- Experience Section -->
                <section class="cv-section">
                    <h2 class="cv-section-title">{ui["cv_experience"]}</h2>
                    <div class="cv-experience-list">{experience_html}
                    </div>
                </section>

                <!-- Skills Section -->
                <section class="cv-section cv-section-compact">
                    <h2 class="cv-section-title">{ui["cv_skills"]}</h2>
                    {skills_html}
                </section>

                <!-- Education Section -->
                <section class="cv-section">
                    <h2 class="cv-section-title">{ui["cv_education"]}</h2>
                    <div class="cv-education-list">{education_html}
                    </div>
                </section>
                {languages_html}
            </div>
        </article>
    </main>

    {footer}
</body>
</html>"""


def generate_root_index():
    """Generate root index.html as the landing page.

    The landing page is served directly at dan.rio/ for:
    - Better SEO (no redirect overhead)
    - AI/bot accessibility (content visible without JS)
    - Cleaner URL structure

    Features morphing transition to blog pages via View Transitions API.
    Includes WebSite + Person JSON-LD for entity disambiguation.
    """
    # JSON-LD: WebSite + Person (entity home)
    ui = LANGUAGES["en"]["ui"]
    jsonld = render_jsonld_script(
        [
            {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": SITE_NAME,
                "alternateName": [f"{AUTHOR} Blog", f"{AUTHOR}"],
                "url": f"{SITE_URL}/",
                "description": SITE_DESCRIPTION,
                "inLanguage": get_language_codes(),
                "author": render_person_jsonld(),
                "publisher": render_person_jsonld(),
            },
            {
                "@context": "https://schema.org",
                **render_person_jsonld(),
                "description": AUTHOR_BIO,
                "mainEntityOfPage": f"{SITE_URL}/",
            },
        ]
    )

    # Build hreflang alternate links from config
    _hreflang_links = [f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}/">']
    for _code in get_language_codes():
        _lang_dir = LANGUAGES[_code]["dir"]
        _hreflang_links.append(
            f'<link rel="alternate" hreflang="{_code}" href="{SITE_URL}/{_lang_dir}/index.html">'
        )
    _hreflang_html = "\n    ".join(_hreflang_links)

    head = render_head(
        title=f"{AUTHOR} – {SITE_NAME}",
        description=SITE_DESCRIPTION,
        lang="en",
        current_url=f"{SITE_URL}/",
        extra_meta=f"""<!-- Language alternates -->
    {_hreflang_html}
    
    <!-- Open Graph / Social -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{SITE_URL}/">
    <meta property="og:title" content="{_html.escape(AUTHOR)} – {_html.escape(SITE_NAME)}">
    <meta property="og:description" content="{_html.escape(SITE_DESCRIPTION)}">
    <meta property="og:site_name" content="{_html.escape(SITE_NAME)}">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{_html.escape(AUTHOR)} – {_html.escape(SITE_NAME)}">
    <meta name="twitter:description" content="{_html.escape(SITE_DESCRIPTION)}">
    
    {jsonld}""",
        stylesheets=[
            f"{BASE_PATH}/static/css/styles.css",
            f"{BASE_PATH}/static/css/landing.css",
        ],
        scripts_head=[f"{BASE_PATH}/static/js/theme.js"],
        scripts_defer=[],
    )

    return f"""<!DOCTYPE html>
<html lang="en">
{head}
<body>
    <!-- Theme toggle (minimal, top-right corner) -->
    <button id="theme-toggle" class="theme-toggle-minimal" aria-label="{_html.escape(ui["toggle_theme"])}" style="view-transition-name: theme-toggle;">
        {render_theme_toggle_svg()}
    </button>

    <!-- Landing surface -->
    <div class="landing-surface">
        <div class="landing-center">
            <h1 class="landing-title" style="view-transition-name: landing-title;">{SITE_NAME}</h1>
            <nav class="landing-nav">
                <a href="{get_lang_path(DEFAULT_LANGUAGE, "index.html")}" class="landing-link" style="view-transition-name: nav-blog;">{ui["landing_blog"]}</a>
                <a href="{get_lang_path(DEFAULT_LANGUAGE, "about.html")}" class="landing-link" style="view-transition-name: nav-about;">{ui["landing_about"]}</a>
                <a href="{get_lang_path(DEFAULT_LANGUAGE, "cv.html")}" class="landing-link" style="view-transition-name: nav-cv;">{ui["landing_cv"]}</a>
            </nav>
        </div>
    </div>

    <script src="{BASE_PATH}/static/js/landing.js?v={_asset_hash(f"{BASE_PATH}/static/js/landing.js")}"></script>
</body>
</html>"""
