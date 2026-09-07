/* Browser contract for the reading layout. Run against `dan blog serve`.
   PLAYWRIGHT_MODULE and PLAYWRIGHT_CHROMIUM can select local installations. */
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = fileURLToPath(new URL('../../', import.meta.url));
const base = process.env.BLOG_URL || 'http://127.0.0.1:8000';
const markdown = `## First section

A passage with two adjacent notes[^one][^two].

${'A longer paragraph keeps enough reading context between the citation and the next section. '.repeat(12)}

### A subsection

The first note is useful again[^one].

#### A deeper section

${'The navigation follows the reader while every heading remains reachable. '.repeat(25)}

## Last section

A final paragraph.

[^one]: A **formatted** note with [a source](https://example.com). ${'This longer note tests collision handling and text wrapping. '.repeat(12)}

    A second paragraph belongs to the same note.

[^two]: A short adjacent note.
`;
const fixture = execFileSync(process.env.BLOG_PYTHON || `${root}/.venv/bin/python`, ['-c', `
import sys
from markdown_refs import render_markdown_with_internal_refs
from renderer import generate_post_html
print(generate_post_html({"title":"Reading layout", "slug":"reading-layout-fixture", "date":"2026-09-05",
 "excerpt":"An article with an outline and notes.", "tags":[], "content":render_markdown_with_internal_refs(sys.stdin.read())}, 1))
`], { cwd: root, env: { ...process.env, PYTHONPATH: `${root}/_source` }, input: markdown, encoding: 'utf8' });
const browser = await chromium.launch({ headless: true, executablePath: process.env.PLAYWRIGHT_CHROMIUM });
const checks = [];
try {
    const context = await browser.newContext({ viewport: { width: 1500, height: 1000 }, reducedMotion: 'reduce' });
    await context.route('**/en/blog/reading-layout-fixture.html*', route => route.fulfill({ contentType: 'text/html', body: fixture }));
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(base + '/en/blog/reading-layout-fixture.html');
    await page.waitForFunction(() => document.querySelector('.post--reading')?.dataset.readingMode === 'margin');
    assert.equal(await page.locator('.sidenote').count(), 2);
    assert.equal(await page.locator('.article-outline a').count(), 4);
    assert.equal(await page.locator('.sidenote-backlink, .footnote-backref, [role="doc-backlink"]').count(), 0);
    const bounds = await page.locator('.sidenote').evaluateAll(notes => notes.map(note => {
        const b = note.getBoundingClientRect(); return { top: b.top, bottom: b.bottom, left: b.left };
    }));
    const body = await page.locator('.post-body').boundingBox();
    assert(bounds[0].left > body.x + body.width);
    assert(bounds[1].top >= bounds[0].bottom + 18, 'Adjacent notes do not collide');
    await page.locator('.article-outline a[href="#a-subsection"]').click();
    await page.waitForFunction(() => document.querySelector('.article-outline [aria-current="location"]')?.hash === '#a-subsection');
    checks.push('Desktop margins, collision avoidance, nested outline, and active section');

    for (const width of [1100, 768, 390, 320]) {
        await page.setViewportSize({ width, height: 844 });
        await page.waitForFunction(() => document.querySelector('.post--reading').dataset.readingMode === 'inline');
        const ref = page.locator('.note-reference').first();
        await ref.scrollIntoViewIfNeeded();
        if (await ref.getAttribute('aria-expanded') !== 'true') await ref.click();
        const noteId = await ref.getAttribute('data-note-target');
        assert(await page.locator(`[id="${noteId}"]`).isVisible());
        assert.equal(await page.locator('.sidenote').count(), 2, 'Notes are moved, never duplicated');
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    }
    await page.locator('.note-reference').last().click();
    assert.equal(await page.locator('.note-reference').last().getAttribute('aria-expanded'), 'true');
    await page.locator('.note-reference').last().click();
    assert.equal(await page.locator('.note-reference').last().getAttribute('aria-expanded'), 'false');
    // Keyboard activation uses the native link activation path.
    await page.locator('.note-reference').last().focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('.note-reference').last().getAttribute('aria-expanded'), 'true');
    checks.push('Tablet/mobile expansion, repeated citations, keyboard activation, and no overflow');

    await page.goto(base + '/en/blog/reading-layout-fixture.html#fn:two');
    await page.waitForFunction(() => !document.getElementById('fn:two').closest('.sidenote').hidden);
    await page.emulateMedia({ media: 'print' });
    assert.equal(await page.locator('.sidenote:visible').count(), 2, 'Print includes every note');
    await page.emulateMedia({ media: 'screen' });
    checks.push('Direct note links and complete print output');

    await page.setViewportSize({ width: 1500, height: 1000 });
    await page.goto(base + '/en/index.html');
    await page.evaluate(() => { window.readingNavigationSentinel = true; });
    await page.locator('a[href="/en/blog/semiconductors-and-sovereignty.html"]').click();
    await page.waitForFunction(() => document.querySelector('.post--reading')?.dataset.readingMode === 'margin');
    assert(await page.evaluate(() => window.readingNavigationSentinel), 'Entered through SPA navigation');
    const ref = page.locator('.note-reference').first();
    const href = await ref.getAttribute('href');
    await ref.click();
    await page.locator('a.lang-toggle').click();
    await page.waitForURL('**/pt/blog/semiconductors-and-sovereignty.html*');
    await page.waitForFunction(() => document.querySelector('.post--reading')?.dataset.readingMode === 'margin');
    assert.equal(await page.locator('.article-outline').getAttribute('aria-label'), 'Neste artigo');
    assert.equal(new URL(page.url()).hash, href);
    await page.locator('#theme-toggle').click();
    assert.equal(await page.locator('.sidenote').count(), 32);
    await page.locator('.note-reference').first().evaluate(ref => ref.scrollIntoView({ block: 'center' }));
    await page.waitForTimeout(300);
    await page.screenshot({ path: '/tmp/blog-reading-final-desktop.png' });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForFunction(() => document.querySelector('.post--reading')?.dataset.readingMode === 'inline');
    const mobileRef = page.locator('.note-reference').first();
    if (await mobileRef.getAttribute('aria-expanded') !== 'true') await mobileRef.click();
    const mobileNote = page.locator(`[id="${await mobileRef.getAttribute('data-note-target')}"]`);
    await mobileNote.scrollIntoViewIfNeeded();
    assert(await mobileNote.isVisible());
    await page.waitForTimeout(300);
    await page.screenshot({ path: '/tmp/blog-reading-final-mobile.png' });
    assert.deepEqual(errors, []);
    checks.push('SPA initialization, language/deep-link preservation, themes, and real article references');

    for (const language of ['en', 'pt']) {
        await page.goto(`${base}/${language}/blog/semiconductors-and-sovereignty.html`);
        await page.waitForFunction(() => document.querySelector('.post--reading')?.dataset.readingMode === 'inline');
        const labels = await page.locator('.post-body > p, .post-body > h2').allTextContents();
        assert(!labels.some(text => /^(sources|fontes|references|referências)\s*:?$/i.test(text.trim())));
        assert.equal(await page.locator('.sidenote').count(), 32);
        assert.equal(await page.locator('.sidenote-returns, [role="doc-backlink"]').count(), 0);
        await page.locator('.post-body > p').last().scrollIntoViewIfNeeded();
        await page.screenshot({ path: `/tmp/blog-sources-cleanup-${language}-mobile.png` });
        await page.goto(`${base}/${language}/blog/adding-an-agent-to-a-mare-app.html`);
        await page.waitForFunction(() => document.querySelector('.post--reading')?.dataset.readingMode === 'inline');
        assert.equal(await page.locator('.sidenote a[href^="#first-use-"], [role="doc-backlink"]').count(), 0);
    }
    checks.push('No redundant return links or empty source sections in either language');

    const noJS = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 390, height: 844 } });
    await noJS.route('**/en/blog/reading-layout-fixture.html*', route => route.fulfill({ contentType: 'text/html', body: fixture }));
    const fallback = await noJS.newPage();
    await fallback.goto(base + '/en/blog/reading-layout-fixture.html');
    assert.equal(await fallback.locator('.sidenote:visible').count(), 2);
    assert.equal(await fallback.locator('.article-outline a:visible').count(), 4);
    await fallback.locator('.note-reference').first().click();
    assert.equal(new URL(fallback.url()).hash, '#fn:one');
    assert(await fallback.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await noJS.close();
    checks.push('Complete outline, notes, and native links without JavaScript');
    console.log(checks.map(check => `PASS ${check}`).join('\n'));
} finally {
    await browser.close();
}
