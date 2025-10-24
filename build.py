#!/usr/bin/env python3
"""
Blog Builder - Compiles Markdown posts to HTML
Run this whenever you add or edit a blog post.
"""

import os
import re
from pathlib import Path
from datetime import datetime
import markdown
import frontmatter

# Configuration
POSTS_DIR = Path("blog-posts")
OUTPUT_DIR = Path("blog")
INDEX_FILE = Path("index.html")

# Path configuration
# For GitHub Pages at username.github.io/blog/: BASE_PATH = "/blog"
# For local development: BASE_PATH = ""
BASE_PATH = "/blog"

# Ensure directories exist
POSTS_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


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


def generate_post_html(post, post_number):
    """Generate HTML for a single blog post"""
    return f"""<!DOCTYPE html>
<html lang="en">
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
        <article class="post" style="view-transition-name: post-content-{post_number};">
            <header class="post-header">
                <a href="{BASE_PATH}/index.html" class="back-link">← Back to Blog</a>
                <h1 class="post-title-large" style="view-transition-name: post-title-{post_number};">{post['title'].upper()}</h1>
                <div class="post-meta" style="view-transition-name: post-date-{post_number};">
                    <time class="post-date">{format_date(post['date'])}</time>
                    <span class="post-separator">•</span>
                    <span class="post-reading-time">{post['reading_time']}</span>
                </div>
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


def generate_post_card(post, post_number):
    """Generate HTML card for the index page"""
    return f"""            <article class="post-card">
                <a href="{BASE_PATH}/blog/{post['slug']}.html" class="post-link">
                    <div class="post-content" style="view-transition-name: post-content-{post_number};">
                        <h2 class="post-title" style="view-transition-name: post-title-{post_number};">{post['title'].upper()}</h2>
                        <time class="post-date" style="view-transition-name: post-date-{post_number};">{post['date']}</time>
                        <p class="post-excerpt" style="view-transition-name: post-excerpt-{post_number};">
                            {post['excerpt']}
                        </p>
                    </div>
                </a>
            </article>"""


def generate_index_html(posts):
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
    
    # Convert markdown content to HTML
    html_content = markdown.markdown(
        post.content,
        extensions=['fenced_code', 'tables', 'nl2br']
    )
    
    return {
        'title': post.get('title', 'Untitled Post'),
        'date': post.get('date', datetime.now().strftime('%Y-%m-%d')),
        'excerpt': post.get('excerpt', ''),
        'slug': post.get('slug', filename),
        'order': post.get('order', 0),
        'reading_time': post.get('readingTime') or calculate_reading_time(post.content),
        'content': html_content,
    }


def build():
    """Main build function"""
    print("🏗️  Building blog from Markdown...\n")
    
    # Run validation first
    try:
        from validate import run_validation
        if not run_validation(BASE_PATH, POSTS_DIR):
            print("❌ Build aborted due to validation failures.\n")
            return False
    except ImportError:
        print("⚠️  Skipping validation (validate.py not found)\n")
    
    # Get all markdown files
    md_files = sorted(POSTS_DIR.glob("*.md"))
    
    if not md_files:
        print("⚠️  No markdown files found in blog-posts/")
        print("💡 Create .md files in blog-posts/ to get started!\n")
        return False
    
    print(f"📝 Found {len(md_files)} markdown file(s)\n")
    
    # Parse all posts
    posts = []
    for md_file in md_files:
        try:
            post = parse_markdown_post(md_file)
            posts.append(post)
            print(f"   ✓ Parsed: {md_file.name}")
        except Exception as e:
            print(f"   ✗ Error parsing {md_file.name}: {e}")
            return False
    
    # Sort posts (by order, then by date)
    posts.sort(key=lambda p: (-p['order'], p['date']), reverse=True)
    
    print(f"\n🔨 Generating HTML files...\n")
    
    # Generate HTML for each post
    for i, post in enumerate(posts):
        try:
            html = generate_post_html(post, i + 1)
            output_file = OUTPUT_DIR / f"{post['slug']}.html"
            output_file.write_text(html, encoding='utf-8')
            print(f"   ✓ Generated: blog/{post['slug']}.html")
        except Exception as e:
            print(f"   ✗ Error generating {post['slug']}.html: {e}")
            return False
    
    # Generate index.html
    try:
        index_html = generate_index_html(posts)
        INDEX_FILE.write_text(index_html, encoding='utf-8')
        print(f"   ✓ Generated: index.html")
    except Exception as e:
        print(f"   ✗ Error generating index.html: {e}")
        return False
    
    print(f"\n🎉 Build complete! {len(posts)} post(s) compiled.\n")
    return True


if __name__ == "__main__":
    import sys
    success = build()
    sys.exit(0 if success else 1)
