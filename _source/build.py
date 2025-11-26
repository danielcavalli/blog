#!/usr/bin/env python3
"""
Blog Builder - Compiles Markdown posts to HTML with bilingual support
Run this whenever you add or edit a blog post.
"""

import os
import re
import json
import hashlib
from pathlib import Path
from datetime import datetime
import markdown
import frontmatter
from config import BASE_PATH, SITE_NAME, SITE_DESCRIPTION, AUTHOR_BIO, LANGUAGES, DEFAULT_LANGUAGE
from translator import MultiAgentTranslator

# Project structure paths
PROJECT_ROOT = Path(__file__).parent.parent  # Go up from _source to project root
POSTS_DIR = Path(__file__).parent / "posts"   # _source/posts/
CACHE_DIR = PROJECT_ROOT / "_cache"           # _cache/
STATIC_DIR = PROJECT_ROOT / "static"          # static/

# Output directories (at project root for GitHub Pages)
LANG_DIRS = {
    'en': PROJECT_ROOT / 'en',
    'pt': PROJECT_ROOT / 'pt'
}

# Cache files
METADATA_FILE = CACHE_DIR / "post-metadata.json"
TRANSLATION_CACHE = CACHE_DIR / "translation-cache.json"

# Ensure directories exist
POSTS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Create language-specific directories
for lang_dir in LANG_DIRS.values():
    lang_dir.mkdir(parents=True, exist_ok=True)
    (lang_dir / 'blog').mkdir(parents=True, exist_ok=True)


def calculate_content_hash(content):
    """Calculate MD5 hash of content for change detection.
    
    Used to determine if post content has changed since last build,
    enabling incremental rebuilds and cache invalidation.
    
    Args:
        content (str): Post content to hash.
    
    Returns:
        str: MD5 hexadecimal digest string.
    """
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def calculate_reading_time(content):
    """Estimate reading time based on word count.
    
    Assumes average reading speed of 200 words per minute.
    Minimum reading time is 1 minute.
    
    Args:
        content (str): Post content to analyze.
    
    Returns:
        str: Reading time estimate (e.g., "5 min read").
    """
    words = len(content.split())
    minutes = max(1, round(words / 200))
    return f"{minutes} min read"


def format_date(date_str):
    """Format date string to readable format.
    
    Converts YYYY-MM-DD format to full month name format.
    Falls back to original string if parsing fails.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format.
    
    Returns:
        str: Formatted date (e.g., "January 15, 2024").
    """
    try:
        date = datetime.strptime(str(date_str), "%Y-%m-%d")
        return date.strftime("%B %d, %Y")
    except:
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
    except:
        return str(iso_str)


def get_lang_path(lang: str, path: str = '') -> str:
    """Generate language-specific path"""
    if lang == DEFAULT_LANGUAGE:
        # English version at /en/
        return f"{BASE_PATH}/en/{path}" if path else f"{BASE_PATH}/en"
    else:
        # Portuguese at /pt/
        return f"{BASE_PATH}/pt/{path}" if path else f"{BASE_PATH}/pt"


def get_alternate_lang(current_lang: str) -> str:
    """Get the alternate language code"""
    return 'pt' if current_lang == 'en' else 'en'


def generate_lang_toggle_html(current_lang: str, current_page: str) -> str:
    """Generate language toggle button HTML as a single unified control
    
    Creates a single button showing a globe icon and both languages (EN / PT) with
    the active language highlighted by a soft ambient glow. Clicking the button
    switches to the opposite language.
    
    Design Philosophy:
        - Single unified button (not separate clickable areas)
        - Globe icon + "EN / PT" on same baseline
        - Active language: soft ambient glow effect
        - Inactive language: dimmed appearance
        - Smooth glow transition when switching
        - Typographic design, not boxed or decorated
        - Minimal and elegant
    
    Args:
        current_lang (str): Current page language code ('en' or 'pt')
        current_page (str): Relative page path (e.g., "index.html" or "blog/post-slug.html")
    
    Returns:
        str: HTML string for language toggle button
    
    Accessibility:
        - Single button element with clear aria-label
        - Announces current and target language for screen readers
        - Keyboard navigable via Tab key
        - Focus states with outline for keyboard users
    
    Example Output:
        <a href="/pt/index.html" class="lang-toggle" aria-label="Switch to Português (currently English)">
            <svg>...</svg>
            <span class="lang-text">
                <span class="lang-en active">EN</span>
                <span class="lang-sep">/</span>
                <span class="lang-pt">PT</span>
            </span>
        </a>
    """
    other_lang = get_alternate_lang(current_lang)
    other_lang_path = get_lang_path(other_lang, current_page)
    
    # Determine which language is active for CSS classes
    en_class = 'lang-en active' if current_lang == 'en' else 'lang-en'
    pt_class = 'lang-pt active' if current_lang == 'pt' else 'lang-pt'
    
    # Accessibility label
    current_name = LANGUAGES[current_lang]['name']
    target_name = LANGUAGES[other_lang]['name']
    aria_label = f"Switch to {target_name} (currently {current_name})"
    
    return f'''<a href="{other_lang_path}" class="lang-toggle" aria-label="{aria_label}" data-current-lang="{current_lang}">
        <svg class="lang-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10"/>
            <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
        <span class="lang-text">
            <span class="{en_class}">EN</span>
            <span class="lang-sep">/</span>
            <span class="{pt_class}">PT</span>
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
    lang_dir = LANGUAGES[lang]['dir']
    current_page = f"blog/{post['slug']}.html"
    lang_toggle_html = generate_lang_toggle_html(lang, current_page)
    
    # Generate tags HTML for post page
    tags_html = ''
    if post.get('tags'):
        tag_pills = ''.join(f'<span class="tag-pill">{tag}</span>' for tag in post['tags'])
        tags_html = f'<div class="post-tags">{tag_pills}</div>'
    
    # Format last updated date (only show if different from creation)
    created_date = post.get('created_date', '')
    updated_date = post.get('updated_date', '')
    
    last_updated_html = ''
    if updated_date and created_date and updated_date != created_date:
        # Parse the ISO datetime and format with date and time
        updated_dt = datetime.fromisoformat(updated_date)
        updated_formatted = updated_dt.strftime('%B %d, %Y at %I:%M %p')
        last_updated_html = f'<div class="last-updated">Last updated: {updated_formatted}</div>'
    
    # Get alternate language info for hreflang
    other_lang = get_alternate_lang(lang)
    other_lang_path = f"https://dan.rio/{other_lang}/blog/{post['slug']}.html"
    current_url = f"https://dan.rio/{lang}/blog/{post['slug']}.html"
    
    # Generate excerpt for meta description (strip HTML, limit length)
    meta_description = post['excerpt'][:160].replace('"', '&quot;')
    
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post['title']} - dan.rio</title>
    <meta name="description" content="{meta_description}">
    
    <!-- Canonical URL -->
    <link rel="canonical" href="{current_url}">
    
    <!-- Open Graph / Social -->
    <meta property="og:type" content="article">
    <meta property="og:url" content="{current_url}">
    <meta property="og:title" content="{post['title']}">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:site_name" content="dan.rio">
    <meta property="og:locale" content="{'en_US' if lang == 'en' else 'pt_BR'}">
    <meta property="og:locale:alternate" content="{'pt_BR' if lang == 'en' else 'en_US'}">
    <meta property="article:published_time" content="{post.get('created_date', '')}">
    <meta property="article:author" content="Daniel Cavalli">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{post['title']}">
    <meta name="twitter:description" content="{meta_description}">
    
    <!-- Additional SEO -->
    <meta name="author" content="Daniel Cavalli">
    <meta name="robots" content="index, follow">
    
    <!-- Language alternates -->
    <link rel="alternate" hreflang="{lang}" href="{current_url}">
    <link rel="alternate" hreflang="{other_lang}" href="{other_lang_path}">
    
    <link rel="stylesheet" href="{BASE_PATH}/static/css/styles.css">
    <link rel="stylesheet" href="{BASE_PATH}/static/css/post.css">
    <link rel="preload" href="{BASE_PATH}/static/js/theme.js" as="script">
    <script src="{BASE_PATH}/static/js/theme.js"></script>
    <script src="{BASE_PATH}/static/js/transitions.js" defer></script>
</head>
<body>
    <nav class="nav" style="view-transition-name: site-nav;">
        <div class="nav-container">
            <a href="{get_lang_path(lang, 'index.html')}" class="logo" style="view-transition-name: landing-title;">dan.rio</a>
            <div class="nav-right">
                <ul class="nav-links">
                    <li><a href="{get_lang_path(lang, 'index.html')}" class="active" style="view-transition-name: nav-blog;">BLOG</a></li>
                    <li><a href="{get_lang_path(lang, 'about.html')}" style="view-transition-name: nav-about;">ABOUT</a></li>
                    <li><a href="{get_lang_path(lang, 'cv.html')}" style="view-transition-name: nav-cv;">CV</a></li>
                </ul>
                <div style="view-transition-name: lang-toggle;">{lang_toggle_html}</div>
                <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme" style="view-transition-name: theme-toggle;">
                    <svg class="sun-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
                    </svg>
                </button>
            </div>
        </div>
    </nav>

    <main class="container">
        <article class="post" style="view-transition-name: post-container-{post_number};">
            <header class="post-header">
                <a href="{get_lang_path(lang, 'index.html')}" class="back-link">← Back to Blog</a>
                {last_updated_html}
                <h1 class="post-title-large" style="view-transition-name: post-title-{post_number};">{post['title'].upper()}</h1>
                <div class="post-meta">
                    <time class="post-date" style="view-transition-name: post-date-{post_number};">{format_iso_date(post['created_date'])}</time>
                    <span class="post-separator">•</span>
                    <span class="post-reading-time">{post['reading_time']}</span>
                </div>
                {tags_html}
            </header>

            <div class="post-body">
                <p class="lead" style="view-transition-name: post-excerpt-{post_number};">
                    {post['excerpt']}
                </p>
                {post['content']}
            </div>
        </article>
    </main>

    <footer class="footer" style="view-transition-name: site-footer;">
        <div class="footer-container">
            <div class="social-links">
                <a href="https://x.com/dancavlli" target="_blank" rel="noopener" aria-label="Twitter">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                </a>
                <a href="https://github.com/danielcavalli" target="_blank" rel="noopener" aria-label="GitHub">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                </a>
                <a href="https://www.linkedin.com/in/cavallidaniel/" target="_blank" rel="noopener" aria-label="LinkedIn">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                </a>
            </div>
            <p class="copyright">© 2025 All Rights Reserved.</p>
        </div>
    </footer>
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
        tag_pills = ''.join(f'<span class="tag-pill">{tag}</span>' for tag in post['tags'])
        tags_html = f'<div class="post-tags">{tag_pills}</div>'
    
    # Create data attributes for filtering and sorting
    tags_attr = ','.join(post.get('tags', []))
    created_timestamp = post.get('created_date', '')
    updated_timestamp = post.get('updated_date', '')
    
    # Generate language-specific blog post link
    post_url = get_lang_path(lang, f"blog/{post['slug']}.html")
    
    return f"""            <article class="post-card" 
                     data-year="{post['year']}" 
                     data-month="{post['month']}" 
                     data-tags="{tags_attr}"
                     data-created="{created_timestamp}"
                     data-updated="{updated_timestamp}"
                     style="view-transition-name: post-container-{post_number};">
                <a href="{post_url}" class="post-link">
                    <div class="post-content">
                        <h2 class="post-title" style="view-transition-name: post-title-{post_number};">{post['title'].upper()}</h2>
                        <time class="post-date" style="view-transition-name: post-date-{post_number};">{format_iso_date(post['created_date'])}</time>
                        {tags_html}
                        <p class="post-excerpt" style="view-transition-name: post-excerpt-{post_number};">
                            {post['excerpt']}
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
        f'<button class="filter-tag" data-tag="{tag}">{tag}</button>' for tag in all_tags
    )
    
    # Generate language-specific SEO info
    other_lang = get_alternate_lang(lang)
    current_url = f"https://dan.rio/{lang}/index.html"
    other_url = f"https://dan.rio/{other_lang}/index.html"
    meta_description = f"Daniel Cavalli - Machine Learning Engineer. Blog on MLOps, distributed systems, CUDA optimization, and AI infrastructure."
    
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daniel Cavalli | Blog - dan.rio</title>
    <meta name="description" content="{meta_description}">
    
    <!-- Canonical URL -->
    <link rel="canonical" href="{current_url}">
    
    <!-- Open Graph / Social -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="{current_url}">
    <meta property="og:title" content="Daniel Cavalli | Blog">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:site_name" content="dan.rio">
    <meta property="og:locale" content="{'en_US' if lang == 'en' else 'pt_BR'}">
    <meta property="og:locale:alternate" content="{'pt_BR' if lang == 'en' else 'en_US'}">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="Daniel Cavalli | Blog">
    <meta name="twitter:description" content="{meta_description}">
    
    <!-- Additional SEO -->
    <meta name="author" content="Daniel Cavalli">
    <meta name="robots" content="index, follow">
    
    <!-- Language alternates -->
    <link rel="alternate" hreflang="{lang}" href="{current_url}">
    <link rel="alternate" hreflang="{other_lang}" href="{other_url}">
    <link rel="alternate" hreflang="x-default" href="https://dan.rio/">
    
    <link rel="stylesheet" href="{BASE_PATH}/static/css/styles.css?v=20251108103307">
    <link rel="preload" href="{BASE_PATH}/static/js/theme.js?v=20251108103307" as="script">
    <script src="{BASE_PATH}/static/js/theme.js?v=20251108103307"></script>
    <script src="{BASE_PATH}/static/js/transitions.js?v=20251108103307" defer></script>
    <script src="{BASE_PATH}/static/js/filter.js?v=20251108103307" defer></script>
</head>
<body>
    <nav class="nav" style="view-transition-name: site-nav;">
        <div class="nav-container">
            <a href="{get_lang_path(lang, 'index.html')}" class="logo" style="view-transition-name: landing-title;">dan.rio</a>
            <div class="nav-right">
                <ul class="nav-links">
                    <li><a href="{get_lang_path(lang, 'index.html')}" class="active" style="view-transition-name: nav-blog;">{ui['blog']}</a></li>
                    <li><a href="{get_lang_path(lang, 'about.html')}" style="view-transition-name: nav-about;">{ui['about']}</a></li>
                    <li><a href="{get_lang_path(lang, 'cv.html')}" style="view-transition-name: nav-cv;">{ui['cv']}</a></li>
                </ul>
                <div style="view-transition-name: lang-toggle;">{lang_toggle_html}</div>
                <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme" style="view-transition-name: theme-toggle;">
                    <svg class="sun-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
                    </svg>
                </button>
            </div>
        </div>
    </nav>

    <main class="container">
        <header class="page-header" style="view-transition-name: blog-header;">
            <div class="header-content">
                <h1 class="page-title">{ui['latest_posts']}</h1>
                <div class="header-controls">
                    <div class="sort-control">
                        <span class="sort-label">{ui['sort_by']}</span>
                        <button id="order-toggle" class="order-toggle" data-order="created" data-label-updated="{ui['last_updated']}" data-label-created="{ui['published_at']}" aria-label="Toggle sort order">
                            <span class="order-toggle-text">{ui['published_at']}</span>
                        </button>
                    </div>
                    <button id="filter-toggle" class="filter-toggle" aria-label="Toggle filters">
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

    <footer class="footer" style="view-transition-name: site-footer;">
        <div class="footer-container">
            <div class="social-links">
                <a href="https://x.com/dancavlli" target="_blank" rel="noopener" aria-label="Twitter">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                </a>
                <a href="https://github.com/danielcavalli" target="_blank" rel="noopener" aria-label="GitHub">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                </a>
                <a href="https://www.linkedin.com/in/cavallidaniel/" target="_blank" rel="noopener" aria-label="LinkedIn">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                </a>
            </div>
            <p class="copyright">© 2025 All Rights Reserved.</p>
        </div>
    </footer>
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
    ui = LANGUAGES[lang]['ui']
    about = LANGUAGES[lang]['about']
    
    # SEO info
    other_lang = get_alternate_lang(lang)
    current_url = f"https://dan.rio/{lang}/about.html"
    other_url = f"https://dan.rio/{other_lang}/about.html"
    meta_description = "Daniel Cavalli - Machine Learning Engineer at Nubank. Background in MLOps, distributed systems, and AI infrastructure."
    
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{about['title']} - dan.rio</title>
    <meta name="description" content="{meta_description}">
    
    <!-- Canonical URL -->
    <link rel="canonical" href="{current_url}">
    
    <!-- Open Graph / Social -->
    <meta property="og:type" content="profile">
    <meta property="og:url" content="{current_url}">
    <meta property="og:title" content="{about['title']} - Daniel Cavalli">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:site_name" content="dan.rio">
    <meta property="og:locale" content="{'en_US' if lang == 'en' else 'pt_BR'}">
    <meta property="profile:first_name" content="Daniel">
    <meta property="profile:last_name" content="Cavalli">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="{about['title']} - Daniel Cavalli">
    <meta name="twitter:description" content="{meta_description}">
    
    <!-- Additional SEO -->
    <meta name="author" content="Daniel Cavalli">
    <meta name="robots" content="index, follow">
    
    <!-- Language alternates -->
    <link rel="alternate" hreflang="{lang}" href="{current_url}">
    <link rel="alternate" hreflang="{other_lang}" href="{other_url}">
    
    <link rel="stylesheet" href="{BASE_PATH}/static/css/styles.css">
    <link rel="stylesheet" href="{BASE_PATH}/static/css/post.css">
    <link rel="preload" href="{BASE_PATH}/static/js/theme.js" as="script">
    <script src="{BASE_PATH}/static/js/theme.js"></script>
    <script src="{BASE_PATH}/static/js/transitions.js" defer></script>
</head>
<body>
    <nav class="nav" style="view-transition-name: site-nav;">
        <div class="nav-container">
            <a href="{get_lang_path(lang, 'index.html')}" class="logo" style="view-transition-name: landing-title;">dan.rio</a>
            <div class="nav-right">
                <ul class="nav-links">
                    <li><a href="{get_lang_path(lang, 'index.html')}" style="view-transition-name: nav-blog;">{ui['blog']}</a></li>
                    <li><a href="{get_lang_path(lang, 'about.html')}" class="active" style="view-transition-name: nav-about;">{ui['about']}</a></li>
                    <li><a href="{get_lang_path(lang, 'cv.html')}" style="view-transition-name: nav-cv;">{ui['cv']}</a></li>
                </ul>
                <div style="view-transition-name: lang-toggle;">{lang_toggle_html}</div>
                <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme" style="view-transition-name: theme-toggle;">
                    <svg class="sun-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
                    </svg>
                </button>
            </div>
        </div>
    </nav>

    <main class="container">
        <article class="post">
            <header class="post-header">
                <h1 class="post-title-large">{about['title']}</h1>
            </header>

            <div class="post-body">
                <p>{about['p1']}</p>

                <p>{about['p2']}</p>

                <p>{about['p3']}</p>

                <p>{about['p4']}</p>

                <img src="{BASE_PATH}/static/images/Logo.png" alt="Moana Surfworks" loading="lazy" class="about-image">
            </div>
        </article>
    </main>

    <footer class="footer" style="view-transition-name: site-footer;">
        <div class="footer-container">
            <div class="social-links">
                <a href="https://x.com/dancavlli" target="_blank" rel="noopener" aria-label="Twitter">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                </a>
                <a href="https://github.com/danielcavalli" target="_blank" rel="noopener" aria-label="GitHub">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                </a>
                <a href="https://www.linkedin.com/in/cavallidaniel/" target="_blank" rel="noopener" aria-label="LinkedIn">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                </a>
            </div>
            <p class="copyright">© 2025 All Rights Reserved.</p>
        </div>
    </footer>
</body>
</html>"""


def generate_cv_html(lang='en'):
    """Generate CV page with professional experience and skills.
    
    Creates cv.html page with career information, following the blog's
    design philosophy of calm continuity and subtle morphing transitions.
    
    Args:
        lang (str): Language code ('en' or 'pt').
    
    Returns:
        str: Complete HTML document for the CV page.
    """
    lang_toggle_html = generate_lang_toggle_html(lang, 'cv.html')
    ui = LANGUAGES[lang]['ui']
    cv = LANGUAGES[lang]['cv']
    
    # Build experience HTML
    experience_html = ''
    for exp in cv['experience']:
        experience_html += f"""
                <div class="cv-experience-item">
                    <div class="cv-period">{exp['period']}</div>
                    <div class="cv-details">
                        <h3 class="cv-title">{exp['title']}</h3>
                        <div class="cv-company">{exp['company']} · {exp['location']}</div>
                        <p class="cv-description">{exp['description']}</p>
                    </div>
                </div>"""
    
    # Build skills HTML
    skills_html = ''
    for category, skills in cv['skills'].items():
        skills_list = ', '.join(skills)
        skills_html += f"""
                <div class="cv-skill-category">
                    <span class="cv-skill-label">{category.capitalize()}</span>
                    <span class="cv-skill-items">{skills_list}</span>
                </div>"""
    
    # SEO info
    other_lang = get_alternate_lang(lang)
    current_url = f"https://dan.rio/{lang}/cv.html"
    other_url = f"https://dan.rio/{other_lang}/cv.html"
    meta_description = "Daniel Cavalli - Machine Learning Engineer at Nubank. Experience in MLOps, distributed systems, CUDA optimization, and AI infrastructure."
    
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daniel Cavalli | CV - dan.rio</title>
    <meta name="description" content="{meta_description}">
    
    <!-- Canonical URL -->
    <link rel="canonical" href="{current_url}">
    
    <!-- Open Graph / Social -->
    <meta property="og:type" content="profile">
    <meta property="og:url" content="{current_url}">
    <meta property="og:title" content="Daniel Cavalli | CV">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:site_name" content="dan.rio">
    <meta property="og:locale" content="{'en_US' if lang == 'en' else 'pt_BR'}">
    <meta property="profile:first_name" content="Daniel">
    <meta property="profile:last_name" content="Cavalli">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary">
    <meta name="twitter:title" content="Daniel Cavalli | CV">
    <meta name="twitter:description" content="{meta_description}">
    
    <!-- Additional SEO -->
    <meta name="author" content="Daniel Cavalli">
    <meta name="robots" content="index, follow">
    
    <!-- Language alternates -->
    <link rel="alternate" hreflang="{lang}" href="{current_url}">
    <link rel="alternate" hreflang="{other_lang}" href="{other_url}">
    
    <link rel="stylesheet" href="{BASE_PATH}/static/css/styles.css">
    <link rel="stylesheet" href="{BASE_PATH}/static/css/post.css">
    <link rel="stylesheet" href="{BASE_PATH}/static/css/cv.css">
    <link rel="preload" href="{BASE_PATH}/static/js/theme.js" as="script">
    <script src="{BASE_PATH}/static/js/theme.js"></script>
    <script src="{BASE_PATH}/static/js/transitions.js" defer></script>
</head>
<body>
    <nav class="nav" style="view-transition-name: site-nav;">
        <div class="nav-container">
            <a href="{get_lang_path(lang, 'index.html')}" class="logo" style="view-transition-name: landing-title;">dan.rio</a>
            <div class="nav-right">
                <ul class="nav-links">
                    <li><a href="{get_lang_path(lang, 'index.html')}" style="view-transition-name: nav-blog;">{ui['blog']}</a></li>
                    <li><a href="{get_lang_path(lang, 'about.html')}" style="view-transition-name: nav-about;">{ui['about']}</a></li>
                    <li><a href="{get_lang_path(lang, 'cv.html')}" class="active" style="view-transition-name: nav-cv;">{ui['cv']}</a></li>
                </ul>
                <div style="view-transition-name: lang-toggle;">{lang_toggle_html}</div>
                <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme" style="view-transition-name: theme-toggle;">
                    <svg class="sun-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
                    </svg>
                </button>
            </div>
        </div>
    </nav>

    <main class="container">
        <article class="post cv-container">
            <header class="post-header cv-header">
                <h1 class="post-title-large">{cv['title']}</h1>
                <p class="cv-tagline">{cv['tagline']}</p>
            </header>

            <div class="post-body cv-body">
                <section class="cv-section">
                    <h2 class="cv-section-title">Experience</h2>
                    <div class="cv-experience-list">{experience_html}
                    </div>
                </section>

                <section class="cv-section">
                    <h2 class="cv-section-title">Skills</h2>
                    <div class="cv-skills-list">{skills_html}
                    </div>
                </section>

                <section class="cv-section cv-section-compact">
                    <h2 class="cv-section-title">Education</h2>
                    <p class="cv-education">{cv['education']}</p>
                </section>

                <section class="cv-section cv-section-compact">
                    <h2 class="cv-section-title">Contact</h2>
                    <div class="cv-contact">
                        <div class="cv-contact-item">
                            <span class="cv-contact-label">GitHub</span>
                            <a href="https://github.com/{cv['contact']['github']}" target="_blank" rel="noopener">@{cv['contact']['github']}</a>
                        </div>
                        <div class="cv-contact-item">
                            <span class="cv-contact-label">LinkedIn</span>
                            <a href="https://linkedin.com/in/{cv['contact']['linkedin']}" target="_blank" rel="noopener">/{cv['contact']['linkedin']}</a>
                        </div>
                    </div>
                </section>
            </div>
        </article>
    </main>

    <footer class="footer" style="view-transition-name: site-footer;">
        <div class="footer-container">
            <div class="social-links">
                <a href="https://x.com/dancavlli" target="_blank" rel="noopener" aria-label="Twitter">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                    </svg>
                </a>
                <a href="https://github.com/danielcavalli" target="_blank" rel="noopener" aria-label="GitHub">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                    </svg>
                </a>
                <a href="https://www.linkedin.com/in/cavallidaniel/" target="_blank" rel="noopener" aria-label="LinkedIn">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                    </svg>
                </a>
            </div>
            <p class="copyright">© 2025 All Rights Reserved.</p>
        </div>
    </footer>
</body>
</html>"""


def parse_markdown_post(filepath):
    """Parse Markdown file with YAML frontmatter.
    
    Extracts metadata and content from post, updates creation/modification
    timestamps in frontmatter if needed, and generates HTML from Markdown.
    
    Automatically writes back to file if timestamps are added or updated.
    
    Args:
        filepath (Path): Path to Markdown file to parse.
    
    Returns:
        Dict: Post data with title, excerpt, tags, dates, content, etc.
              Returns None if file doesn't exist or fails to parse.
    """
    post = frontmatter.load(filepath)
    
    # Get filename without extension
    filename = filepath.stem
    slug = post.get('slug', filename)
    
    # Calculate content hash for change detection
    content_hash = calculate_content_hash(post.content)
    
    # Get or create metadata directly in frontmatter
    created_at = post.get('created_at')
    updated_at = post.get('updated_at')
    stored_hash = post.get('content_hash')
    
    now = datetime.now().isoformat()
    needs_update = False
    
    if not created_at:
        # New post - set creation date
        created_at = now
        updated_at = now
        post['created_at'] = created_at
        post['updated_at'] = updated_at
        post['content_hash'] = content_hash
        needs_update = True
    elif stored_hash != content_hash:
        # Content changed - update timestamp and hash
        updated_at = now
        post['updated_at'] = updated_at
        post['content_hash'] = content_hash
        needs_update = True
    else:
        # Content unchanged - keep existing timestamps
        pass
    
    # Write updated frontmatter back to file if needed
    if needs_update:
        with open(filepath, 'wb') as f:
            frontmatter.dump(post, f)
    
    # Convert markdown content to HTML
    html_content = markdown.markdown(
        post.content,
        extensions=['fenced_code', 'tables', 'nl2br']
    )
    
    # Keep raw markdown for translation
    raw_markdown = post.content
    
    # Parse date and extract year/month
    date_str = post.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        post_date = datetime.strptime(str(date_str), "%Y-%m-%d")
        year = post_date.year
        month = post_date.strftime("%B")  # Full month name
    except:
        year = datetime.now().year
        month = datetime.now().strftime("%B")
    
    # Get tags (default to empty list if not provided)
    tags = post.get('tags', [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(',')]
    
    return {
        'title': post.get('title', 'Untitled Post'),
        'date': date_str,
        'year': year,
        'month': month,
        'excerpt': post.get('excerpt', ''),
        'slug': slug,
        'order': post.get('order', 0),
        'tags': tags,
        'reading_time': post.get('readingTime') or calculate_reading_time(post.content),
        'content': html_content,
        'raw_content': raw_markdown,  # Keep raw markdown for translation
        'created_date': created_at,
        'updated_date': updated_at,
        'content_hash': content_hash,
    }


def generate_landing_html():
    """Generate landing page with morphing transition to blog"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{SITE_NAME}</title>
    <meta name="description" content="{SITE_DESCRIPTION}">
    <link rel="stylesheet" href="{BASE_PATH}/static/css/styles.css">
    <link rel="stylesheet" href="{BASE_PATH}/static/css/landing.css">
    <script src="{BASE_PATH}/static/js/theme.js"></script>
</head>
<body>
    <!-- Theme toggle (minimal, top-right corner) -->
    <button id="theme-toggle" class="theme-toggle-minimal" aria-label="Toggle theme" style="view-transition-name: theme-toggle;">
        <svg class="sun-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
        </svg>
    </button>

    <!-- Landing surface -->
    <div class="landing-surface">
        <div class="landing-center">
            <h1 class="landing-title" style="view-transition-name: landing-title;">{SITE_NAME}</h1>
            <nav class="landing-nav">
                <a href="{BASE_PATH}/en/index.html" class="landing-link" style="view-transition-name: nav-blog;">Blog</a>
                <a href="{BASE_PATH}/en/about.html" class="landing-link" style="view-transition-name: nav-about;">About Me</a>
                <a href="{BASE_PATH}/en/cv.html" class="landing-link" style="view-transition-name: nav-cv;">CV</a>
            </nav>
        </div>
    </div>

    <script src="{BASE_PATH}/static/js/landing.js"></script>
</body>
</html>"""


def generate_root_index():
    """Generate root index.html that redirects to landing page"""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{SITE_NAME}</title>
    <meta name="description" content="{SITE_DESCRIPTION}">
    <script>
        // Redirect to landing page
        window.location.href = '{BASE_PATH}/landing.html';
    </script>
    <noscript>
        <meta http-equiv="refresh" content="0; url={BASE_PATH}/landing.html">
    </noscript>
</head>
<body>
    <div style="display: flex; align-items: center; justify-content: center; height: 100vh; font-family: system-ui, -apple-system, sans-serif;">
        <p>Loading...</p>
    </div>
</body>
</html>"""


def build():
    """Main build function orchestrating entire site generation.
    
    Workflow:
        1. Validate post structure and metadata
        2. Parse all Markdown posts
        3. Translate posts to Portuguese (with caching)
        4. Translate About page (with caching)
        5. Generate HTML files for both languages
        6. Generate root index and landing pages
    
    Returns:
        bool: True if build succeeds, False if validation or translation fails.
    """
    print("Building bilingual blog from Markdown...\n")
    
    # Run validation first
    try:
        from validate import run_validation
        if not run_validation(BASE_PATH, POSTS_DIR):
            print("Build aborted due to validation failures.\n")
            return False
    except ImportError:
        print("Skipping validation (validate.py not found)\n")
    
    # Initialize translator
    try:
        translator = MultiAgentTranslator(enable_critique=False)  # Disabled for faster builds
        print("Translation system initialized\n")
        
        # Translate About page content
        about_en = LANGUAGES['en']['about']
        about_pt_translated = translator.translate_about(about_en, force=False)
        
        # Must have translation
        if not about_pt_translated:
            raise Exception("About page translation failed")
        
        LANGUAGES['pt']['about'] = about_pt_translated
        
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
    
    # Parse all posts (English versions)
    posts_en = []
    posts_pt = []
    
    for md_file in md_files:
        try:
            # Parse English version
            post_en = parse_markdown_post(md_file)
            posts_en.append(post_en)
            print(f"   Parsed: {md_file.name} (EN)")
            
            # Translate to Portuguese if translator available
            if translator:
                post_pt = translator.translate_if_needed(post_en, 'pt')
                if not post_pt:
                    raise Exception(f"Translation failed for {md_file.name}")
                posts_pt.append(post_pt)
                print(f"   Translated: {md_file.name} (PT)")
        except Exception as e:
            print(f"   Error: {e}")
            return False
    
    # Sort posts by created date (newest first) - ignore custom order field
    posts_en.sort(key=lambda p: p['created_date'], reverse=True)
    posts_pt.sort(key=lambda p: p['created_date'], reverse=True)
    
    print(f"\nGenerating HTML files...\n")
    
    # Generate English site
    print("   English version:")
    for i, post in enumerate(posts_en):
        try:
            html = generate_post_html(post, i + 1, lang='en')
            output_file = LANG_DIRS['en'] / 'blog' / f"{post['slug']}.html"
            output_file.write_text(html, encoding='utf-8')
            
            print(f"      blog/{post['slug']}.html")
        except Exception as e:
            print(f"      Error generating {post['slug']}.html: {e}")
            return False
    
    # Generate English index
    try:
        index_html = generate_index_html(posts_en, lang='en')
        index_file = LANG_DIRS['en'] / 'index.html'
        index_file.write_text(index_html, encoding='utf-8')
        print(f"      index.html")
    except Exception as e:
        print(f"      Error generating index.html: {e}")
        return False
    
    # Generate English about
    try:
        about_html = generate_about_html(lang='en')
        about_file = LANG_DIRS['en'] / 'about.html'
        about_file.write_text(about_html, encoding='utf-8')
        print(f"      about.html")
    except Exception as e:
        print(f"      Error generating about.html: {e}")
        return False
    
    # Generate English CV
    try:
        cv_html = generate_cv_html(lang='en')
        cv_file = LANG_DIRS['en'] / 'cv.html'
        cv_file.write_text(cv_html, encoding='utf-8')
        print(f"      cv.html")
    except Exception as e:
        print(f"      Error generating cv.html: {e}")
        return False
    
    # Generate Portuguese site (if translations available)
    if posts_pt:
        print("\n   Portuguese version:")
        for i, post in enumerate(posts_pt):
            try:
                html = generate_post_html(post, i + 1, lang='pt')
                output_file = LANG_DIRS['pt'] / 'blog' / f"{post['slug']}.html"
                output_file.write_text(html, encoding='utf-8')
                print(f"      blog/{post['slug']}.html")
            except Exception as e:
                print(f"      Error generating {post['slug']}.html: {e}")
                return False
        
        # Generate Portuguese index
        try:
            index_html = generate_index_html(posts_pt, lang='pt')
            index_file = LANG_DIRS['pt'] / 'index.html'
            index_file.write_text(index_html, encoding='utf-8')
            print(f"      index.html")
        except Exception as e:
            print(f"      Error generating index.html: {e}")
            return False
        
        # Generate Portuguese about
        try:
            about_html = generate_about_html(lang='pt')
            about_file = LANG_DIRS['pt'] / 'about.html'
            about_file.write_text(about_html, encoding='utf-8')
            print(f"      about.html")
        except Exception as e:
            print(f"      Error generating about.html: {e}")
            return False
        
        # Generate Portuguese CV
        try:
            cv_html = generate_cv_html(lang='pt')
            cv_file = LANG_DIRS['pt'] / 'cv.html'
            cv_file.write_text(cv_html, encoding='utf-8')
            print(f"      cv.html")
        except Exception as e:
            print(f"      Error generating cv.html: {e}")
            return False
    
    # Generate landing page
    print("\n   Landing page:")
    try:
        landing_html = generate_landing_html()
        landing_file = Path("landing.html")
        landing_file.write_text(landing_html, encoding='utf-8')
        print(f"      landing.html")
    except Exception as e:
        print(f"      Error generating landing.html: {e}")
        return False
    
    # Generate root index.html with redirect to landing
    print("\n   Root redirect:")
    try:
        root_html = generate_root_index()
        root_index = Path("index.html")
        root_index.write_text(root_html, encoding='utf-8')
        print(f"      index.html (redirect)")
    except Exception as e:
        print(f"      Error generating root index.html: {e}")
        return False
    
    lang_count = 2 if posts_pt else 1
    print(f"\nBuild complete! {len(posts_en)} post(s) in {lang_count} language(s).\n")
    return True


if __name__ == "__main__":
    import sys
    success = build()
    sys.exit(0 if success else 1)






