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
from config import BASE_PATH, SITE_NAME, AUTHOR_BIO, LANGUAGES, DEFAULT_LANGUAGE
from translator import GeminiTranslator

# Configuration
POSTS_DIR = Path("blog-posts")
OUTPUT_DIR = Path("blog")
INDEX_FILE = Path("index.html")
ABOUT_FILE = Path("about.html")
METADATA_FILE = Path("post-metadata.json")

# Language-specific directories
LANG_DIRS = {
    'en': Path('en'),
    'pt': Path('pt')
}

# Ensure directories exist
POSTS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Create language-specific directories
for lang_dir in LANG_DIRS.values():
    lang_dir.mkdir(exist_ok=True)
    (lang_dir / 'blog').mkdir(exist_ok=True)


def load_metadata():
    """Load post metadata (creation and update dates)"""
    if METADATA_FILE.exists():
        try:
            with open(METADATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_metadata(metadata):
    """Save post metadata to JSON file"""
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def calculate_content_hash(content):
    """Calculate MD5 hash of content for change detection"""
    return hashlib.md5(content.encode('utf-8')).hexdigest()


def update_post_metadata(slug, output_file, content_hash):
    """Update metadata for a post (tracks creation and update dates)
    Only updates the 'updated' timestamp if content actually changed"""
    metadata = load_metadata()
    now = datetime.now().isoformat()
    
    if slug not in metadata:
        # New post - set creation date
        metadata[slug] = {
            'created': now,
            'updated': now,
            'content_hash': content_hash
        }
    else:
        # Existing post - only update timestamp if content changed
        if metadata[slug].get('content_hash') != content_hash:
            metadata[slug]['updated'] = now
            metadata[slug]['content_hash'] = content_hash
        # If content hasn't changed, keep existing timestamps
    
    save_metadata(metadata)
    return metadata[slug]


def calculate_reading_time(content):
    """Estimate reading time based on word count"""
    words = len(content.split())
    minutes = max(1, round(words / 200))
    return f"{minutes} min read"


def format_date(date_str):
    """Format date string nicely"""
    try:
        date = datetime.strptime(str(date_str), "%Y-%m-%d")
        return date.strftime("%B %d, %Y")
    except:
        return str(date_str)


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
    """Generate language toggle button HTML"""
    other_lang = get_alternate_lang(current_lang)
    other_lang_label = LANGUAGES[other_lang]['label']
    other_lang_path = get_lang_path(other_lang, current_page)
    
    return f'''<a href="{other_lang_path}" class="lang-toggle" aria-label="Switch to {LANGUAGES[other_lang]['name']}" data-lang-switch="{other_lang}">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
        </svg>
        <span class="lang-label">{other_lang_label}</span>
    </a>'''


def generate_post_html(post, post_number, lang='en'):
    """Generate HTML for a single blog post"""
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
    
    return f"""<!DOCTYPE html>>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{post['title']} - dan.rio</title>
    <link rel="stylesheet" href="{BASE_PATH}/styles.css">
    <link rel="stylesheet" href="{BASE_PATH}/post.css">
    <link rel="preload" href="{BASE_PATH}/theme.js" as="script">
    <style>
        @view-transition {{
            navigation: auto;
        }}
    </style>
    <script src="{BASE_PATH}/theme.js"></script>
    <script src="{BASE_PATH}/transitions.js" defer></script>
</head>
<body>
    <nav class="nav">
        <div class="nav-container">
            <a href="{get_lang_path(lang, 'index.html')}" class="logo">dan.rio</a>
            <div class="nav-right">
                <ul class="nav-links">
                    <li><a href="{get_lang_path(lang, 'index.html')}" class="active">BLOG</a></li>
                    <li><a href="{get_lang_path(lang, 'about.html')}">ABOUT</a></li>
                </ul>
                {lang_toggle_html}
                <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">
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
                    <time class="post-date" style="view-transition-name: post-date-{post_number};">{format_date(post['date'])}</time>
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

    <footer class="footer">
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
    """Generate HTML card for the index page"""
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
                        <time class="post-date" style="view-transition-name: post-date-{post_number};">{post['date']}</time>
                        {tags_html}
                        <p class="post-excerpt" style="view-transition-name: post-excerpt-{post_number};">
                            {post['excerpt']}
                        </p>
                    </div>
                </a>
            </article>"""


def generate_index_html(posts, lang='en'):
    """Generate the main index.html page"""
    lang_toggle_html = generate_lang_toggle_html(lang, 'index.html')
    posts_html = '\n\n'.join(generate_post_card(post, i + 1, lang) for i, post in enumerate(posts))
    
    # Collect all unique years, months, and tags for filters (only from existing posts)
    years = sorted(set(post['year'] for post in posts), reverse=True)
    
    # Collect only months that have posts
    months_with_posts = sorted(set(post['month'] for post in posts), 
                                key=lambda m: ["January", "February", "March", "April", "May", "June", 
                                              "July", "August", "September", "October", "November", "December"].index(m))
    
    all_tags = sorted(set(tag for post in posts for tag in post.get('tags', [])))
    
    # Generate year options
    year_options = '<div class="select-option" data-value="">All Years</div>' + ''.join(
        f'<div class="select-option" data-value="{year}">{year}</div>' for year in years
    )
    
    # Generate month options (only months with posts)
    month_options = '<div class="select-option" data-value="">All Months</div>' + ''.join(
        f'<div class="select-option" data-value="{month}">{month}</div>' for month in months_with_posts
    )
    
    # Generate tag pills for filter
    tag_pills_html = ''.join(
        f'<button class="filter-tag" data-tag="{tag}">{tag}</button>' for tag in all_tags
    )
    
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>dan.rio - Blog</title>
    <meta name="description" content="Personal blog by Daniel Cavalli on machine learning, CUDA, distributed training, and engineering.">
    <link rel="stylesheet" href="{BASE_PATH}/styles.css">
    <link rel="preload" href="{BASE_PATH}/theme.js" as="script">
    <style>
        /* View Transitions API support */
        @view-transition {{
            navigation: auto;
        }}
    </style>
    <script src="{BASE_PATH}/theme.js"></script>
    <script src="{BASE_PATH}/transitions.js" defer></script>
    <script src="{BASE_PATH}/filter.js" defer></script>
</head>
<body>
    <nav class="nav">
        <div class="nav-container">
            <a href="{get_lang_path(lang, 'index.html')}" class="logo">dan.rio</a>
            <div class="nav-right">
                <ul class="nav-links">
                    <li><a href="{get_lang_path(lang, 'index.html')}" class="active">BLOG</a></li>
                    <li><a href="{get_lang_path(lang, 'about.html')}">ABOUT</a></li>
                </ul>
                {lang_toggle_html}
                <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">
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
                <h1 class="page-title">Latest Posts</h1>
                <div class="header-controls">
                    <button id="order-toggle" class="order-toggle" data-order="updated" aria-label="Toggle sort order">
                        <span class="order-toggle-text">Updated</span>
                    </button>
                    <button id="filter-toggle" class="filter-toggle" aria-label="Toggle filters">
                        <span class="filter-toggle-text">Filter</span>
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
                        <span class="select-label">All Years</span>
                    </div>
                    <div class="select-options">
                        {year_options}
                    </div>
                </div>
                <div class="custom-select" id="month-filter-wrapper">
                    <div class="select-trigger" data-value="">
                        <span class="select-label">All Months</span>
                    </div>
                    <div class="select-options">
                        {month_options}
                    </div>
                </div>
                <button id="clear-filters" class="filter-clear">Clear Filters</button>
            </div>
            <div class="filter-tags">
                {tag_pills_html}
            </div>
        </div>

        <div class="posts-grid">
{posts_html}
        </div>
    </main>

    <footer class="footer">
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
    """Generate the about.html page"""
    lang_toggle_html = generate_lang_toggle_html(lang, 'about.html')
    
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>About - dan.rio</title>
    <meta name="description" content="{AUTHOR_BIO}">
    <link rel="stylesheet" href="{BASE_PATH}/styles.css">
    <link rel="stylesheet" href="{BASE_PATH}/post.css">
    <link rel="preload" href="{BASE_PATH}/theme.js" as="script">
    <style>
        @view-transition {{
            navigation: auto;
        }}
    </style>
    <script src="{BASE_PATH}/theme.js"></script>
    <script src="{BASE_PATH}/transitions.js" defer></script>
</head>
<body>
    <nav class="nav">
        <div class="nav-container">
            <a href="{get_lang_path(lang, 'index.html')}" class="logo">dan.rio</a>
            <div class="nav-right">
                <ul class="nav-links">
                    <li><a href="{get_lang_path(lang, 'index.html')}">BLOG</a></li>
                    <li><a href="{get_lang_path(lang, 'about.html')}" class="active">ABOUT</a></li>
                </ul>
                {lang_toggle_html}
                <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">
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
                <h1 class="post-title-large">ABOUT</h1>
            </header>

            <div class="post-body">
                <p>I'm Daniel Cavalli. I like understanding how things work by taking them apart. It doesn't matter if it's a CUDA kernel, a surfboard, or a bike crankset. The process is the same: break it open, study the pieces, build it better.</p>

                <p>I work as a Machine Learning Engineer at Nubank, where I care about efficiency. I like when systems are clean and do what they should without noise. My work is an extension of that mindset, finding simpler paths that make everything move faster and with less friction.</p>

                <p>Writing helps me think. It forces precision and makes me see where my ideas actually hold.</p>

                <p>Outside of work I stay close to the ocean. I surf, bike, build things with my hands, and spend time with Moana, my dog. I live in Copacabana, where the sea is part of the background of everything.</p>

                <img src="{BASE_PATH}/Logo.png" alt="Moana Surfworks" loading="lazy" class="about-image">
            </div>
        </article>
    </main>

    <footer class="footer">
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
    """Generate the main index.html page"""
    posts_html = '\n\n'.join(generate_post_card(post, i + 1) for i, post in enumerate(posts))
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>dan.rio - Blog</title>
    <meta name="description" content="Personal blog by Daniel Cavalli on machine learning, CUDA, distributed training, and engineering.">
    <link rel="stylesheet" href="{BASE_PATH}/styles.css">
    <link rel="preload" href="{BASE_PATH}/theme.js" as="script">
    <style>
        /* View Transitions API support */
        @view-transition {{
            navigation: auto;
        }}
    </style>
    <script src="{BASE_PATH}/theme.js"></script>
    <script src="{BASE_PATH}/transitions.js" defer></script>
</head>
<body>
    <nav class="nav">
        <div class="nav-container">
            <a href="{BASE_PATH}/index.html" class="logo">dan.rio</a>
            <div class="nav-right">
                <ul class="nav-links">
                    <li><a href="{BASE_PATH}/index.html" class="active">BLOG</a></li>
                    <li><a href="{BASE_PATH}/about.html">ABOUT</a></li>
                </ul>
                <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">
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
        <header class="page-header">
            <h1 class="page-title">Latest Posts</h1>
        </header>

        <div class="posts-grid">
{posts_html}
        </div>
    </main>

    <footer class="footer">
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
</html>
"""


def parse_markdown_post(filepath):
    """Parse a markdown file with frontmatter"""
    post = frontmatter.load(filepath)
    
    # Get filename without extension
    filename = filepath.stem
    slug = post.get('slug', filename)
    
    # Calculate content hash for change detection
    content_hash = calculate_content_hash(post.content)
    
    # Check if HTML output exists to determine if this is an update
    output_file = OUTPUT_DIR / f"{slug}.html"
    metadata = load_metadata()
    
    # Determine creation and update dates based on content hash
    if slug in metadata:
        created_date = metadata[slug]['created']
        # Check if content actually changed
        if metadata[slug].get('content_hash') == content_hash:
            # Content unchanged - use existing updated date
            updated_date = metadata[slug]['updated']
        else:
            # Content changed - set new updated date
            updated_date = datetime.now().isoformat()
    else:
        # New post
        created_date = datetime.now().isoformat()
        updated_date = created_date
    
    # Convert markdown content to HTML
    html_content = markdown.markdown(
        post.content,
        extensions=['fenced_code', 'tables', 'nl2br']
    )
    
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
        'created_date': created_date,
        'updated_date': updated_date,
        'content_hash': content_hash,
    }


def build():
    """Main build function with bilingual support"""
    print("🏗️  Building bilingual blog from Markdown...\n")
    
    # Run validation first
    try:
        from validate import run_validation
        if not run_validation(BASE_PATH, POSTS_DIR):
            print("❌ Build aborted due to validation failures.\n")
            return False
    except ImportError:
        print("⚠️  Skipping validation (validate.py not found)\n")
    
    # Initialize translator
    try:
        translator = GeminiTranslator()
        print("🌐 Translation system initialized\n")
    except Exception as e:
        print(f"⚠️  Translation system unavailable: {e}")
        print("   Continuing with English-only build\n")
        translator = None
    
    # Get all markdown files
    md_files = sorted(POSTS_DIR.glob("*.md"))
    
    if not md_files:
        print("⚠️  No markdown files found in blog-posts/")
        print("💡 Create .md files in blog-posts/ to get started!\n")
        return False
    
    print(f"📝 Found {len(md_files)} markdown file(s)\n")
    
    # Parse all posts (English versions)
    posts_en = []
    posts_pt = []
    
    for md_file in md_files:
        try:
            # Parse English version
            post_en = parse_markdown_post(md_file)
            posts_en.append(post_en)
            print(f"   ✓ Parsed: {md_file.name} (EN)")
            
            # Translate to Portuguese if translator available
            if translator:
                try:
                    post_pt = translator.translate_if_needed(post_en, 'pt')
                    posts_pt.append(post_pt)
                    print(f"   ✓ Translated: {md_file.name} (PT)")
                except Exception as e:
                    print(f"   ⚠️  Translation failed for {md_file.name}: {e}")
                    # Use English version as fallback
                    posts_pt.append(post_en)
        except Exception as e:
            print(f"   ✗ Error parsing {md_file.name}: {e}")
            return False
    
    # Sort posts (by order, then by updated date)
    posts_en.sort(key=lambda p: (-p['order'], p['updated_date']), reverse=True)
    posts_pt.sort(key=lambda p: (-p['order'], p['updated_date']), reverse=True)
    
    print(f"\n🔨 Generating HTML files...\n")
    
    # Generate English site
    print("   📄 English version:")
    for i, post in enumerate(posts_en):
        try:
            html = generate_post_html(post, i + 1, lang='en')
            output_file = LANG_DIRS['en'] / 'blog' / f"{post['slug']}.html"
            output_file.write_text(html, encoding='utf-8')
            
            # Update metadata
            update_post_metadata(post['slug'], output_file, post['content_hash'])
            
            print(f"      ✓ blog/{post['slug']}.html")
        except Exception as e:
            print(f"      ✗ Error generating {post['slug']}.html: {e}")
            return False
    
    # Generate English index
    try:
        index_html = generate_index_html(posts_en, lang='en')
        index_file = LANG_DIRS['en'] / 'index.html'
        index_file.write_text(index_html, encoding='utf-8')
        print(f"      ✓ index.html")
    except Exception as e:
        print(f"      ✗ Error generating index.html: {e}")
        return False
    
    # Generate English about
    try:
        about_html = generate_about_html(lang='en')
        about_file = LANG_DIRS['en'] / 'about.html'
        about_file.write_text(about_html, encoding='utf-8')
        print(f"      ✓ about.html")
    except Exception as e:
        print(f"      ✗ Error generating about.html: {e}")
        return False
    
    # Generate Portuguese site (if translations available)
    if posts_pt:
        print("\n   📄 Portuguese version:")
        for i, post in enumerate(posts_pt):
            try:
                html = generate_post_html(post, i + 1, lang='pt')
                output_file = LANG_DIRS['pt'] / 'blog' / f"{post['slug']}.html"
                output_file.write_text(html, encoding='utf-8')
                print(f"      ✓ blog/{post['slug']}.html")
            except Exception as e:
                print(f"      ✗ Error generating {post['slug']}.html: {e}")
                return False
        
        # Generate Portuguese index
        try:
            index_html = generate_index_html(posts_pt, lang='pt')
            index_file = LANG_DIRS['pt'] / 'index.html'
            index_file.write_text(index_html, encoding='utf-8')
            print(f"      ✓ index.html")
        except Exception as e:
            print(f"      ✗ Error generating index.html: {e}")
            return False
        
        # Generate Portuguese about
        try:
            about_html = generate_about_html(lang='pt')
            about_file = LANG_DIRS['pt'] / 'about.html'
            about_file.write_text(about_html, encoding='utf-8')
            print(f"      ✓ about.html")
        except Exception as e:
            print(f"      ✗ Error generating about.html: {e}")
            return False
    
    lang_count = 2 if posts_pt else 1
    print(f"\n🎉 Build complete! {len(posts_en)} post(s) in {lang_count} language(s).\n")
    return True


if __name__ == "__main__":
    import sys
    success = build()
    sys.exit(0 if success else 1)
