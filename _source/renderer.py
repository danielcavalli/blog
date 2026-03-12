"""HTML rendering functions for all site pages.

Generates complete HTML documents for blog posts, index, about, CV,
and root landing pages. Each function returns a full HTML string.
"""

import html as _html

from config import BASE_PATH, SITE_URL, SITE_NAME, SITE_DESCRIPTION, AUTHOR, AUTHOR_BIO, LANGUAGES, SOCIAL_LINKS, DEFAULT_LANGUAGE, get_language_codes, get_og_locale
from helpers import (
    _asset_hash, CURRENT_YEAR, tag_to_slug, format_date, format_reading_time,
    get_lang_path, get_alternate_lang,
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


def render_skip_link(lang='en'):
    """Render skip-to-content accessibility link.

    Args:
        lang (str): Language code ('en' or 'pt').

    Returns:
        str: HTML for skip navigation link.
    """
    label = LANGUAGES[lang]['ui']['skip_to_content']
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
    ui = LANGUAGES[lang]['ui']

    blog_class = ' class="active"' if active_page == 'blog' else ''
    about_class = ' class="active"' if active_page == 'about' else ''
    cv_class = ' class="active"' if active_page == 'cv' else ''

    return f"""<nav class="nav" style="view-transition-name: site-nav;">
        <div class="nav-container">
            <a href="{get_lang_path(lang, 'index.html')}" class="logo" style="view-transition-name: landing-title;">dan.rio</a>
            <div class="nav-right">
                <ul class="nav-links">
                    <li><a href="{get_lang_path(lang, 'index.html')}"{blog_class} style="view-transition-name: nav-blog;">{ui['blog']}</a></li>
                    <li><a href="{get_lang_path(lang, 'about.html')}"{about_class} style="view-transition-name: nav-about;">{ui['about']}</a></li>
                    <li><a href="{get_lang_path(lang, 'cv.html')}"{cv_class} style="view-transition-name: nav-cv;">{ui['cv']}</a></li>
                </ul>
                <div style="view-transition-name: lang-toggle;">{lang_toggle_html}</div>
                <button id="theme-toggle" class="theme-toggle" aria-label="{_html.escape(ui['toggle_theme'])}" style="view-transition-name: theme-toggle;">
                    {render_theme_toggle_svg()}
                </button>
            </div>
        </div>
    </nav>"""


def render_footer(lang='en'):
    """Render the site footer shared across all pages.

    Uses SOCIAL_LINKS from config, dynamic CURRENT_YEAR for copyright,
    and locale-aware "All Rights Reserved" text.

    Args:
        lang (str): Language code ('en' or 'pt').

    Returns:
        str: Complete <footer> HTML element.
    """
    ui = LANGUAGES[lang]['ui']
    return f"""<footer class="footer" style="view-transition-name: site-footer;">
        <div class="footer-container">
            <div class="social-links">
                <a href="{SOCIAL_LINKS['twitter']}" target="_blank" rel="noopener" aria-label="Twitter">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                </a>
                <a href="{SOCIAL_LINKS['github']}" target="_blank" rel="noopener" aria-label="GitHub">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                </a>
                <a href="{SOCIAL_LINKS['linkedin']}" target="_blank" rel="noopener" aria-label="LinkedIn">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                </a>
            </div>
            <p class="copyright">&copy; {CURRENT_YEAR} {ui['all_rights_reserved']}.</p>
        </div>
    </footer>"""


def render_head(title, description, lang, current_url, other_lang=None, other_url=None,
                extra_meta='', stylesheets=None, scripts_head=None, scripts_defer=None):
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
        stylesheets = [f'{BASE_PATH}/static/css/styles.css']
    if scripts_head is None:
        scripts_head = [f'{BASE_PATH}/static/js/theme.js']
    if scripts_defer is None:
        scripts_defer = [f'{BASE_PATH}/static/js/transitions.js']

    # Build versioned stylesheet links (content-hash per file)
    css_links = '\n    '.join(
        f'<link rel="stylesheet" href="{css}?v={_asset_hash(css)}">'
        for css in stylesheets
    )

    # Build script tags (head scripts get preloaded + loaded, defer scripts get deferred)
    head_script_tags = '\n    '.join(
        f'<link rel="preload" href="{js}?v={_asset_hash(js)}" as="script">\n    <script src="{js}?v={_asset_hash(js)}"></script>'
        for js in scripts_head
    )

    defer_script_tags = '\n    '.join(
        f'<script src="{js}?v={_asset_hash(js)}" defer></script>'
        for js in scripts_defer
    )

    # Language alternate links (includes x-default for language-neutral fallback)
    lang_alternates = ''
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
        label = LANGUAGES[code]['label']
        active = ' active' if code == current_lang else ''
        lang_spans.append(f'<span class="lang-{code}{active}">{label}</span>')
    lang_labels_html = '\n            <span class="lang-sep">/</span>\n            '.join(lang_spans)

    # Accessibility label (locale-aware)
    current_name = LANGUAGES[current_lang]['name']
    target_name = LANGUAGES[other_lang]['name']
    switch_tpl = LANGUAGES[current_lang]['ui'].get('switch_language', 'Switch to {target} (currently {current})')
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


def generate_post_html(post, post_number, lang='en'):
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
    # Generate language-specific paths
    current_page = f"blog/{post['slug']}.html"
    lang_toggle_html = generate_lang_toggle_html(lang, current_page)
    ui = LANGUAGES[lang]['ui']

    # Generate tags HTML for post page
    tags_html = ''
    if post.get('tags'):
        tag_pills = ''.join(f'<span class="tag-pill">{_html.escape(tag)}</span>' for tag in post['tags'])
        tags_html = f'<div class="post-tags">{tag_pills}</div>'

    # Format last updated date -- only show if frontmatter 'updated' exists
    # and differs from 'date'. Uses editorial dates, not build timestamps.
    updated_fm = post.get('updated_fm_date', '')
    published_fm = post.get('published_date', post.get('date', ''))

    last_updated_html = ''
    if updated_fm and updated_fm != published_fm:
        last_updated_html = f'<div class="last-updated">{ui["last_updated_label"]}: {format_date(updated_fm, lang)}</div>'

    # Published date for display: use frontmatter 'date' (stable, author-controlled)
    published_date_display = format_date(post.get('published_date', post.get('date', '')), lang)

    # Reading time label (locale-aware)
    reading_time_raw = post.get('reading_time', 1)
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
    meta_description = _html.escape(post['excerpt'][:160])
    # Raw (unescaped) description for JSON-LD -- json.dumps handles its own escaping
    raw_description = post['excerpt'][:160]

    # JSON-LD: BlogPosting
    # datePublished: frontmatter 'date' (editorial publication date)
    # dateModified: frontmatter 'updated' if present, else 'date'
    jsonld_date_published = post.get('published_date', post.get('date', ''))
    jsonld_date_modified = post.get('updated_fm_date') or jsonld_date_published
    post_jsonld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post['title'],
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
    if post.get('tags'):
        post_jsonld["keywords"] = ', '.join(post['tags'])
    jsonld = render_jsonld_script(post_jsonld)

    # Open Graph meta
    extra_meta = f"""<!-- Open Graph / Social -->
    <meta property="og:type" content="article">
    <meta property="og:url" content="{current_url}">
    <meta property="og:title" content="{_html.escape(post['title'])}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:site_name" content="{_html.escape(SITE_NAME)}">
    <meta property="og:locale" content="{get_og_locale(lang)}">
    <meta property="og:locale:alternate" content="{get_og_locale(other_lang)}">
    <meta property="article:published_time" content="{jsonld_date_published}">
    <meta property="article:modified_time" content="{jsonld_date_modified}">
    <meta property="article:author" content="{_html.escape(AUTHOR)}">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{_html.escape(post['title'])}">
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
        stylesheets=[f'{BASE_PATH}/static/css/styles.css', f'{BASE_PATH}/static/css/post.css'],
    )

    nav = render_nav(lang, 'blog', lang_toggle_html)
    footer = render_footer(lang)
    skip_link = render_skip_link(lang)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
{head}
<body>
    {skip_link}
    {nav}

    <main id="main-content" class="container">
        <article class="post" style="view-transition-name: post-container-{post_number};">
            <header class="post-header">
                <a href="{get_lang_path(lang, 'index.html')}" class="back-link">{ui['back_to_blog']}</a>
                {last_updated_html}
                <h1 class="post-title-large" style="view-transition-name: post-title-{post_number};">{_html.escape(post['title'].upper())}</h1>
                <div class="post-meta">
                    <time class="post-date" style="view-transition-name: post-date-{post_number};">{published_date_display}</time>
                    <span class="post-separator">•</span>
                    <span class="post-reading-time">{reading_time_display}</span>
                </div>
                {tags_html}
            </header>

            <div class="post-body">
                <p class="lead" style="view-transition-name: post-excerpt-{post_number};">
                    {_html.escape(post['excerpt'])}
                </p>
                {post['content']}
            </div>
        </article>
    </main>

    {footer}
</body>
</html>"""


def generate_post_card(post, post_number, lang='en'):
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
    tags_html = ''
    if post.get('tags'):
        tag_pills = ''.join(f'<span class="tag-pill">{_html.escape(tag)}</span>' for tag in post['tags'])
        tags_html = f'<div class="post-tags">{tag_pills}</div>'

    # Create data attributes for filtering and sorting
    tags_attr = _html.escape(','.join(post.get('tags', [])))
    # Canonical EN slugs for stable cross-language filter-state restoration
    tag_keys_attr = ','.join(tag_to_slug(t) for t in post.get('en_tags', post.get('tags', [])))
    # Use frontmatter-derived dates for client-side sort (stable, author-controlled)
    created_timestamp = post.get('published_date', post.get('date', ''))
    updated_timestamp = post.get('updated_fm_date') or post.get('published_date', post.get('date', ''))

    # Generate language-specific blog post link
    post_url = get_lang_path(lang, f"blog/{post['slug']}.html")

    return f"""            <article class="post-card" 
                     data-year="{post['year']}" 
                     data-month="{post['month']}" 
                     data-tags="{tags_attr}"
                     data-tag-keys="{tag_keys_attr}"
                     data-created="{created_timestamp}"
                     data-updated="{updated_timestamp}"
                     style="view-transition-name: post-container-{post_number};">
                <a href="{post_url}" class="post-link">
                    <div class="post-content">
                        <h2 class="post-title" style="view-transition-name: post-title-{post_number};">{_html.escape(post['title'].upper())}</h2>
                        <time class="post-date" style="view-transition-name: post-date-{post_number};">{format_date(post.get('published_date', post.get('date', '')), lang)}</time>
                        {tags_html}
                        <p class="post-excerpt" style="view-transition-name: post-excerpt-{post_number};">
                            {_html.escape(post['excerpt'])}
                        </p>
                    </div>
                </a>
            </article>"""


def generate_index_html(posts, lang='en'):
    """Generate main blog index page with filtering.

    Creates index.html with post cards, filter controls (year/month/tag),
    sort controls (newest/oldest/updated), and bilingual navigation.

    Args:
        posts (List[Dict]): List of all posts to display.
        lang (str): Language code ('en' or 'pt').

    Returns:
        str: Complete HTML document for the index page.
    """
    lang_toggle_html = generate_lang_toggle_html(lang, 'index.html')
    ui = LANGUAGES[lang]['ui']
    posts_html = '\n\n'.join(generate_post_card(post, i + 1, lang) for i, post in enumerate(posts))

    # Collect all unique years, months, and tags for filters (only from existing posts)
    years = sorted(set(post['year'] for post in posts), reverse=True)

    # Collect only months that have posts
    months_with_posts = sorted(set(post['month'] for post in posts),
                                key=lambda m: ["January", "February", "March", "April", "May", "June",
                                              "July", "August", "September", "October", "November", "December"].index(m))

    all_tags = sorted(set(tag for post in posts for tag in post.get('tags', [])))

    # Build display-tag -> canonical-EN-slug mapping for data-tag-key attributes.
    # For EN posts, en_tags == tags, so tag_to_slug(en_tag) is used directly.
    # For PT posts, en_tags holds the original EN tags at the same index as the
    # translated PT tags, so we can recover the EN slug for each display tag.
    tag_key_map: dict = {}
    for post in posts:
        pt_tags = post.get('tags', [])
        en_tags_list = post.get('en_tags', pt_tags)
        for pt_tag, en_tag in zip(pt_tags, en_tags_list):
            tag_key_map.setdefault(pt_tag, tag_to_slug(en_tag))

    # Generate year options
    year_options = f'<div class="select-option" data-value="">{ui["all_years"]}</div>' + ''.join(
        f'<div class="select-option" data-value="{year}">{year}</div>' for year in years
    )

    # Get month translations
    months_dict = LANGUAGES[lang].get('months', {})

    # Generate month options (only months with posts)
    month_options = f'<div class="select-option" data-value="">{ui["all_months"]}</div>' + ''.join(
        f'<div class="select-option" data-value="{month}">{months_dict.get(month, month)}</div>' for month in months_with_posts
    )

    # Generate tag pills for filter
    tag_pills_html = ''.join(
        f'<button class="filter-tag" data-tag="{_html.escape(tag)}" data-tag-key="{tag_key_map.get(tag, tag_to_slug(tag))}">{_html.escape(tag)}</button>'
        for tag in all_tags
    )

    # Generate language-specific SEO info
    other_lang = get_alternate_lang(lang)
    current_url = f"{SITE_URL}/{lang}/index.html"
    other_url = f"{SITE_URL}/{other_lang}/index.html"
    meta_description = LANGUAGES[lang]['ui']['meta_index']

    # JSON-LD: Blog with author
    jsonld = render_jsonld_script({
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": f"{AUTHOR} | Blog",
        "url": current_url,
        "description": meta_description,
        "inLanguage": lang,
        "author": render_person_jsonld(),
        "publisher": render_person_jsonld(),
    })

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
        stylesheets=[f'{BASE_PATH}/static/css/styles.css'],
        scripts_defer=[f'{BASE_PATH}/static/js/transitions.js', f'{BASE_PATH}/static/js/filter.js'],
    )

    nav = render_nav(lang, 'blog', lang_toggle_html)
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
                <h1 class="page-title">{ui['latest_posts']}</h1>
                <div class="header-controls">
                    <div class="sort-control">
                        <span class="sort-label">{ui['sort_by']}</span>
                        <button id="order-toggle" class="order-toggle" data-order="created" data-label-updated="{ui['last_updated']}" data-label-created="{ui['published_at']}" aria-label="{ui['toggle_sort_order']}">
                            <span class="order-toggle-text">{ui['published_at']}</span>
                        </button>
                    </div>
                    <button id="filter-toggle" class="filter-toggle" aria-label="{ui['toggle_filters']}">
                        <span class="filter-toggle-text">{ui['filter']}</span>
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
                        <span class="select-label">{ui['all_years']}</span>
                    </div>
                    <div class="select-options">
                        {year_options}
                    </div>
                </div>
                <div class="custom-select" id="month-filter-wrapper">
                    <div class="select-trigger" data-value="">
                        <span class="select-label">{ui['all_months']}</span>
                    </div>
                    <div class="select-options">
                        {month_options}
                    </div>
                </div>
                <button id="clear-filters" class="filter-clear">{ui['clear_filters']}</button>
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


def generate_about_html(lang='en'):
    """Generate About page with translated content.

    Creates about.html page with author bio content from config,
    translated for the specified language.

    Args:
        lang (str): Language code ('en' or 'pt').

    Returns:
        str: Complete HTML document for the About page.
    """
    lang_toggle_html = generate_lang_toggle_html(lang, 'about.html')
    about = LANGUAGES[lang]['about']

    # SEO info
    other_lang = get_alternate_lang(lang)
    current_url = f"{SITE_URL}/{lang}/about.html"
    other_url = f"{SITE_URL}/{other_lang}/about.html"
    meta_description = LANGUAGES[lang]['ui']['meta_about']

    # JSON-LD: ProfilePage + Person
    about_name_tpl = LANGUAGES[lang]['ui'].get('about_jsonld_name', 'About {author}')
    about_bio = LANGUAGES[lang]['ui'].get('author_bio', AUTHOR_BIO)
    jsonld = render_jsonld_script({
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "name": about_name_tpl.format(author=AUTHOR),
        "url": current_url,
        "mainEntity": {
            **render_person_jsonld(),
            "description": about_bio,
        },
    })

    # Open Graph meta
    esc_meta_desc = _html.escape(meta_description)
    extra_meta = f"""<!-- Open Graph / Social -->
    <meta property="og:type" content="profile">
    <meta property="og:url" content="{current_url}">
    <meta property="og:title" content="{_html.escape(about['title'])} – {_html.escape(AUTHOR)}">
    <meta property="og:description" content="{esc_meta_desc}">
    <meta property="og:site_name" content="{_html.escape(SITE_NAME)}">
    <meta property="og:locale" content="{get_og_locale(lang)}">
    <meta property="profile:first_name" content="Daniel">
    <meta property="profile:last_name" content="Cavalli">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{_html.escape(about['title'])} – {_html.escape(AUTHOR)}">
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
        stylesheets=[f'{BASE_PATH}/static/css/styles.css', f'{BASE_PATH}/static/css/post.css'],
    )

    nav = render_nav(lang, 'about', lang_toggle_html)
    footer = render_footer(lang)
    skip_link = render_skip_link(lang)

    return f"""<!DOCTYPE html>
<html lang="{lang}">
{head}
<body>
    {skip_link}
    {nav}

    <main id="main-content" class="container">
        <article class="post" style="view-transition-name: about-content;">
            <header class="post-header">
                <h1 class="post-title-large" style="view-transition-name: about-title;">{_html.escape(about['title'])}</h1>
            </header>

            <div class="post-body" style="view-transition-name: about-body;">
                <p>{_html.escape(about['p1'])}</p>

                <p>{_html.escape(about['p2'])}</p>

                <p>{_html.escape(about['p3'])}</p>

                <p>{_html.escape(about['p4'])}</p>

                <img src="{BASE_PATH}/static/images/Logo.png" alt="Moana Surfworks" loading="lazy" class="about-image">
            </div>
        </article>
    </main>

    {footer}
</body>
</html>"""


def generate_cv_html(lang='en', translated_cv=None):
    """Generate CV page with professional experience and skills.

    Reads CV data from cv_data.yaml (single source of truth) and generates
    HTML. For Portuguese, uses pre-translated content.

    Args:
        lang (str): Language code ('en' or 'pt').
        translated_cv (Dict, optional): Pre-translated CV data for Portuguese.

    Returns:
        str: Complete HTML document for the CV page.
    """
    lang_toggle_html = generate_lang_toggle_html(lang, 'cv.html')
    ui = LANGUAGES[lang]['ui']

    # Use translated data for Portuguese, otherwise load from YAML
    if lang == 'pt' and translated_cv:
        cv_data = translated_cv
    else:
        cv_data = load_cv_data()
        if not cv_data:
            print("Error: Could not load cv_data.yaml")
            return ""

    cv = {
        'title': cv_data['name'].upper(),
        'tagline': cv_data['tagline'],
        'location': cv_data['location'],
        'summary': cv_data['summary'],
        'contact': cv_data['contact'],
        'skills': cv_data['skills'],
        'languages_spoken': cv_data['languages_spoken'],
        'experience': cv_data['experience'],
        'education': cv_data['education']
    }

    # Build experience HTML with achievements
    experience_html = ''
    for exp in cv['experience']:
        # Build achievements list if present
        achievements_html = ''
        if exp.get('achievements'):
            achievements_items = ''.join(f'<li>{_html.escape(ach)}</li>' for ach in exp['achievements'])
            achievements_html = f'<ul class="cv-achievements">{achievements_items}</ul>'

        experience_html += f"""
                <div class="cv-experience-item">
                    <div class="cv-period">{_html.escape(exp['period'])}</div>
                    <div class="cv-details">
                        <h3 class="cv-title">{_html.escape(exp['title'])}</h3>
                        <div class="cv-company">{_html.escape(exp['company'])} · {_html.escape(exp['location'])}</div>
                        <p class="cv-description">{_html.escape(exp['description'])}</p>
                        {achievements_html}
                    </div>
                </div>"""

    # Build skills HTML - simple list format
    skills_list = ' · '.join(_html.escape(s) for s in cv['skills'])
    skills_html = f'<p class="cv-skills-inline">{skills_list}</p>'

    # Build education HTML
    education_html = ''
    for edu in cv['education']:
        education_html += f"""
                    <div class="cv-education-item">
                        <div class="cv-education-degree">{_html.escape(edu['degree'])}</div>
                        <div class="cv-education-school">{_html.escape(edu['school'])}</div>
                        <div class="cv-education-year">{_html.escape(edu['period'])}</div>
                    </div>"""

    # Build languages spoken HTML
    languages_html = ''
    if cv.get('languages_spoken'):
        languages_list = ' · '.join(_html.escape(l) for l in cv['languages_spoken'])
        languages_html = f"""
                <section class="cv-section cv-section-compact">
                    <h2 class="cv-section-title">{ui['cv_languages']}</h2>
                    <p class="cv-languages">{languages_list}</p>
                </section>"""

    # SEO info
    other_lang = get_alternate_lang(lang)
    current_url = f"{SITE_URL}/{lang}/cv.html"
    other_url = f"{SITE_URL}/{other_lang}/cv.html"
    meta_description = LANGUAGES[lang]['ui']['meta_cv']

    # JSON-LD: Person (full CV entity)
    jsonld = render_jsonld_script({
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "name": f"{AUTHOR} – CV",
        "url": current_url,
        "mainEntity": {
            **render_person_jsonld(),
            "description": meta_description,
        },
    })

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
            f'{BASE_PATH}/static/css/styles.css',
            f'{BASE_PATH}/static/css/post.css',
            f'{BASE_PATH}/static/css/cv.css',
        ],
    )

    nav = render_nav(lang, 'cv', lang_toggle_html)
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
                <h1 class="post-title-large" style="view-transition-name: cv-title;">{_html.escape(cv['title'])}</h1>
                <p class="cv-tagline">{_html.escape(cv['tagline'])}</p>
                <p class="cv-location">{_html.escape(cv['location'])}</p>
            </header>

            <div class="post-body cv-body" style="view-transition-name: cv-body;">
                <!-- Contact Section - Prominent for recruiters -->
                <section class="cv-section cv-section-highlight">
                    <h2 class="cv-section-title">{ui['cv_contact']}</h2>
                    <div class="cv-contact">
                        <div class="cv-contact-item">
                            <span class="cv-contact-label">Email</span>
                            <a href="mailto:{_html.escape(cv['contact'].get('email', ''))}">{_html.escape(cv['contact'].get('email', ''))}</a>
                        </div>
                        <div class="cv-contact-item">
                            <span class="cv-contact-label">LinkedIn</span>
                            <a href="https://linkedin.com/in/{_html.escape(cv['contact'].get('linkedin', ''))}" target="_blank" rel="noopener">linkedin.com/in/{_html.escape(cv['contact'].get('linkedin', ''))}</a>
                        </div>
                        <div class="cv-contact-item">
                            <span class="cv-contact-label">GitHub</span>
                            <a href="https://github.com/{_html.escape(cv['contact'].get('github', ''))}" target="_blank" rel="noopener">github.com/{_html.escape(cv['contact'].get('github', ''))}</a>
                        </div>
                    </div>
                </section>

                <!-- Summary Section -->
                <section class="cv-section">
                    <h2 class="cv-section-title">{ui['cv_summary']}</h2>
                    <p class="cv-summary">{_html.escape(cv['summary'])}</p>
                </section>

                <!-- Experience Section -->
                <section class="cv-section">
                    <h2 class="cv-section-title">{ui['cv_experience']}</h2>
                    <div class="cv-experience-list">{experience_html}
                    </div>
                </section>

                <!-- Skills Section -->
                <section class="cv-section cv-section-compact">
                    <h2 class="cv-section-title">{ui['cv_skills']}</h2>
                    {skills_html}
                </section>

                <!-- Education Section -->
                <section class="cv-section">
                    <h2 class="cv-section-title">{ui['cv_education']}</h2>
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
    ui = LANGUAGES['en']['ui']
    jsonld = render_jsonld_script([
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
        }
    ])

    # Build hreflang alternate links from config
    _hreflang_links = [f'<link rel="alternate" hreflang="x-default" href="{SITE_URL}/">']
    for _code in get_language_codes():
        _lang_dir = LANGUAGES[_code]['dir']
        _hreflang_links.append(f'<link rel="alternate" hreflang="{_code}" href="{SITE_URL}/{_lang_dir}/index.html">')
    _hreflang_html = '\n    '.join(_hreflang_links)

    head = render_head(
        title=f"{AUTHOR} – {SITE_NAME}",
        description=SITE_DESCRIPTION,
        lang='en',
        current_url=f'{SITE_URL}/',
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
            f'{BASE_PATH}/static/css/styles.css',
            f'{BASE_PATH}/static/css/landing.css',
        ],
        scripts_head=[f'{BASE_PATH}/static/js/theme.js'],
        scripts_defer=[],
    )

    return f"""<!DOCTYPE html>
<html lang="en">
{head}
<body>
    <!-- Theme toggle (minimal, top-right corner) -->
    <button id="theme-toggle" class="theme-toggle-minimal" aria-label="{_html.escape(ui['toggle_theme'])}" style="view-transition-name: theme-toggle;">
        {render_theme_toggle_svg()}
    </button>

    <!-- Landing surface -->
    <div class="landing-surface">
        <div class="landing-center">
            <h1 class="landing-title" style="view-transition-name: landing-title;">{SITE_NAME}</h1>
            <nav class="landing-nav">
                <a href="{get_lang_path(DEFAULT_LANGUAGE, 'index.html')}" class="landing-link" style="view-transition-name: nav-blog;">{ui['landing_blog']}</a>
                <a href="{get_lang_path(DEFAULT_LANGUAGE, 'about.html')}" class="landing-link" style="view-transition-name: nav-about;">{ui['landing_about']}</a>
                <a href="{get_lang_path(DEFAULT_LANGUAGE, 'cv.html')}" class="landing-link" style="view-transition-name: nav-cv;">{ui['landing_cv']}</a>
            </nav>
        </div>
    </div>

    <script src="{BASE_PATH}/static/js/landing.js?v={_asset_hash(f'{BASE_PATH}/static/js/landing.js')}"></script>
</body>
</html>"""
