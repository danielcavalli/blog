"""SEO helpers: JSON-LD structured data and sitemap generation.

All functions here produce serialized output (JSON-LD script tags,
sitemap XML) and depend only on config constants.
"""

import json
from datetime import datetime

from config import SITE_URL, AUTHOR, SOCIAL_LINKS, LANGUAGES, get_language_codes


def render_person_jsonld():
    """Return a reusable Person JSON-LD dict for the site author.

    Used as the author reference in BlogPosting, WebSite, and standalone
    Person schema. Links social profiles via sameAs for entity disambiguation.

    Returns:
        dict: JSON-LD Person object.
    """
    return {
        "@type": "Person",
        "name": AUTHOR,
        "alternateName": ["Dan Cavalli", "Dan Rio", "Daniel Rio"],
        "url": f"{SITE_URL}/",
        "jobTitle": "Machine Learning Engineer",
        "worksFor": {
            "@type": "Organization",
            "name": "Nubank"
        },
        "sameAs": [
            SOCIAL_LINKS.get("github", ""),
            SOCIAL_LINKS.get("linkedin", ""),
            SOCIAL_LINKS.get("twitter", ""),
        ],
        "knowsAbout": [
            "Machine Learning", "Artificial Intelligence", "CUDA",
            "Distributed Training", "MLOps", "Software Engineering",
            "Deep Learning", "Python"
        ]
    }


def render_jsonld_script(data):
    """Serialize a JSON-LD object into a <script> tag.

    Uses json.dumps for proper JSON escaping.  The serialized string is
    further hardened by replacing ``</`` with ``<\\/`` to prevent
    premature closing of the ``<script>`` element if any value contains
    ``</script>`` or similar sequences.

    Args:
        data: dict or list of dicts to serialize.

    Returns:
        str: <script type="application/ld+json"> HTML element.
    """
    payload = json.dumps(data, ensure_ascii=False).replace('</','<\\/')
    return f'<script type="application/ld+json">{payload}</script>'


def _sitemap_hreflang_links(page_path: str) -> str:
    """Build xhtml:link hreflang elements for a sitemap <url> entry.

    Generates x-default plus one link per configured language.

    Args:
        page_path: Path relative to the language dir (e.g. 'index.html',
                   'blog/my-post.html').  Pass '' for the root landing page.
    """
    lines = [f'<xhtml:link rel="alternate" hreflang="x-default" href="{SITE_URL}/"/>']
    for code in get_language_codes():
        lang_dir = LANGUAGES[code]['dir']
        href = f"{SITE_URL}/{lang_dir}/{page_path}" if page_path else f"{SITE_URL}/"
        lines.append(f'<xhtml:link rel="alternate" hreflang="{code}" href="{href}"/>')
    return '\n        '.join(lines)


def generate_sitemap(posts_en, posts_pt):
    """Generate sitemap.xml with correct hreflang annotations.

    Produces a sitemap with:
    - Root landing page as x-default
    - All language page pairs with reciprocal hreflang links
    - lastmod dates derived from actual post metadata

    Args:
        posts_en (list): English post dictionaries with 'slug', 'published_date', 'updated_fm_date'.
        posts_pt (list): Portuguese post dictionaries (same structure).

    Returns:
        str: Complete sitemap.xml content.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    lang_codes = get_language_codes()

    urls = []

    # Root landing page (x-default)
    urls.append(f"""    <url>
        <loc>{SITE_URL}/</loc>
        {_sitemap_hreflang_links('index.html')}
        <lastmod>{today}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>1.0</priority>
    </url>""")

    # Static pages: index, about, cv
    for page, priority, freq in [('index.html', '0.9', 'weekly'), ('about.html', '0.7', 'monthly'), ('cv.html', '0.8', 'monthly')]:
        for lang in lang_codes:
            lang_dir = LANGUAGES[lang]['dir']
            urls.append(f"""    <url>
        <loc>{SITE_URL}/{lang_dir}/{page}</loc>
        {_sitemap_hreflang_links(page)}
        <lastmod>{today}</lastmod>
        <changefreq>{freq}</changefreq>
        <priority>{priority}</priority>
    </url>""")

    # Blog posts
    for post in posts_en:
        slug = post['slug']
        # lastmod: prefer frontmatter 'updated' field (author-controlled),
        # fall back to frontmatter 'date', then today as last resort.
        lastmod = (
            post.get('updated_fm_date')
            or post.get('published_date')
            or post.get('date')
            or today
        )
        # Normalize to YYYY-MM-DD (strip time component if present)
        if 'T' in str(lastmod):
            lastmod = str(lastmod).split('T')[0]
        lastmod = str(lastmod)

        blog_page = f'blog/{slug}.html'
        for lang in lang_codes:
            lang_dir = LANGUAGES[lang]['dir']
            urls.append(f"""    <url>
        <loc>{SITE_URL}/{lang_dir}/blog/{slug}.html</loc>
        {_sitemap_hreflang_links(blog_page)}
        <lastmod>{lastmod}</lastmod>
        <changefreq>monthly</changefreq>
        <priority>0.8</priority>
    </url>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
    
{chr(10).join(urls)}
    
</urlset>
"""
