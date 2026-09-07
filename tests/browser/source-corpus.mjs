/* Review every current source post without writing source or publication files. */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { mkdir, writeFile } from 'node:fs/promises';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = fileURLToPath(new URL('../../', import.meta.url));
const base = process.env.BLOG_URL || 'http://127.0.0.1:8000';
const articles = JSON.parse(execFileSync(process.env.BLOG_PYTHON || `${root}/.venv/bin/python`, ['-c', `
from collections import Counter
from pathlib import Path
import hashlib, json, re
import html5lib, markdown
from build import _prepare_presentation_post, _sorted_posts
from content_loader import parse_markdown_post
from renderer import generate_post_html, generate_presentation_html
from reading_layout import compile_reading_layout

posts = [parse_markdown_post(path) for path in sorted(Path('_source/posts').glob('*.md'))]
articles = []
for number, post in enumerate(_sorted_posts(posts), 1):
    language = 'pt' if post['lang'].startswith('pt') else 'en'
    presentation = post['content_type'] == 'presentation'
    render = generate_presentation_html if presentation else generate_post_html
    html = render(_prepare_presentation_post(post), number, lang=language)
    parser = html5lib.HTMLParser(namespaceHTMLElements=False)
    document = parser.parse(html)
    assert not parser.errors, (post['slug'], parser.errors)
    ids = [e.get('id') for e in document.iter() if e.get('id')]
    assert len(ids) == len(set(ids)), (post['slug'], 'duplicate IDs')
    for a in document.iter('a'):
        href = a.get('href', '')
        assert not href.startswith('#') or href[1:] in ids, (post['slug'], href)
    if not presentation:
        original = html5lib.parseFragment(markdown.markdown(post['raw_content'], extensions=[
            'fenced_code', 'tables', 'nl2br', 'attr_list', 'footnotes']), namespaceHTMLElements=False)
        layout = compile_reading_layout(post['content'], lang=language)
        rendered = html5lib.parseFragment(layout.content + layout.notes, namespaceHTMLElements=False)
        code = lambda tree: Counter(''.join(e.itertext()) for e in tree.iter('code'))
        assert code(original) == code(rendered), (post['slug'], 'changed code')
    articles.append({'slug': post['slug'], 'language': language, 'presentation': presentation,
        'source_sha256': hashlib.sha256(post['raw_content'].encode()).hexdigest(), 'html': html})
print(json.dumps(articles))
`], { cwd: root, env: { ...process.env, PYTHONPATH: `${root}/_source` }, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 }));

const browser = await chromium.launch({ headless: true, executablePath: process.env.PLAYWRIGHT_CHROMIUM });
const results = [];
try {
    const context = await browser.newContext({ reducedMotion: 'reduce' });
    for (const article of articles) {
        await context.route(`**/${article.language}/blog/${article.slug}.html*`, route => route.fulfill({ contentType: 'text/html', body: article.html }));
    }
    const page = await context.newPage();
    for (const article of articles) {
        for (const width of [1500, 390, 320]) {
            await page.setViewportSize({ width, height: 1000 });
            await page.goto(`${base}/${article.language}/blog/${article.slug}.html`, { waitUntil: 'domcontentloaded' });
            if (!article.presentation) await page.waitForSelector('.post--reading[data-reading-mode]');
            await page.evaluate(() => document.fonts.ready);
            const measurements = await page.evaluate(() => {
                const body = document.querySelector('.post-body');
                return {
                    overflow: document.documentElement.scrollWidth > innerWidth + 1,
                    headings: [...(body?.querySelectorAll('h1,h2,h3,h4,h5,h6') || [])].filter(e => !e.closest('.sidenote')).length,
                    outline: document.querySelectorAll('.article-outline a').length,
                    notes: document.querySelectorAll('.sidenote').length,
                    returns: document.querySelectorAll('.sidenote [role="doc-backlink"], .sidenote .footnote-backref').length,
                };
            });
            assert.equal(measurements.overflow, false, `${article.slug} overflows at ${width}px`);
            if (!article.presentation) {
                assert.equal(measurements.outline, measurements.headings, `${article.slug}: missing outline headings`);
                assert.equal(measurements.returns, 0, `${article.slug}: return links remain`);
                if (width < 1280 && measurements.notes) {
                    await page.locator('.note-reference').first().click();
                    await assert.doesNotReject(() => page.locator('.sidenote:not([hidden])').first().waitFor({ state: 'visible' }));
                    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
                }
            }
            results.push({ slug: article.slug, language: article.language, width, ...measurements });
            if (process.env.BLOG_REVIEW_DIR && article.slug === 'semiconductors-and-sovereignty') {
                await mkdir(process.env.BLOG_REVIEW_DIR, { recursive: true });
                await page.screenshot({ path: `${process.env.BLOG_REVIEW_DIR}/semiconductors-${width}.png` });
            }
        }
    }
} finally {
    await browser.close();
}
if (process.env.BLOG_REVIEW_DIR) {
    await mkdir(process.env.BLOG_REVIEW_DIR, { recursive: true });
    await writeFile(`${process.env.BLOG_REVIEW_DIR}/corpus.json`, JSON.stringify({
        sources: articles.map(({ html, ...source }) => source), results,
    }, null, 2));
}
console.log(JSON.stringify({ posts: articles.length, viewports: [1500, 390, 320], checks: results }, null, 2));
