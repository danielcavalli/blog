/* Run against the local blog server. PLAYWRIGHT_MODULE can point to an existing
   Playwright installation; BLOG_URL defaults to http://127.0.0.1:8000. */
import assert from 'node:assert/strict';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.BLOG_URL || 'http://127.0.0.1:8000';
const article = '/en/blog/adding-an-agent-to-a-mare-app.html';
const browser = await chromium.launch({ headless: true, executablePath: process.env.PLAYWRIGHT_CHROMIUM });
const checks = [];
try {
    const context = await browser.newContext({
        viewport: { width: 1200, height: 1050 }, colorScheme: 'dark', reducedMotion: 'reduce',
    });
    const page = await context.newPage();
    const errors = [];
    const downloads = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('request', request => {
        if (request.url().includes('cdn.jsdelivr.net/npm/mermaid@')) downloads.push(request.url());
    });
    async function checkTheme(theme) {
        await page.waitForFunction(expected => {
            const diagrams = [...document.querySelectorAll('.mermaid-diagram')];
            return diagrams.length === 1 && diagrams.every(d => d.dataset.mermaidTheme === expected);
        }, theme);
        assert.equal(await page.locator('.theme-media').getByRole('img').count(), 1);
        assert(await page.locator(`.theme-media [data-theme-variant="${theme}"]`).isVisible());
        for (const svg of await page.locator('.mermaid-diagram > svg').all()) {
            assert(await svg.locator('title').textContent());
            assert(await svg.locator('desc').textContent());
            const colors = await svg.evaluate(s => ({
                text: getComputedStyle(s.querySelector('text')).fill,
                expected: getComputedStyle(document.body).color,
            }));
            assert.equal(colors.text, colors.expected, 'Diagram text follows blog palette');
            const fits = await svg.evaluate(s => {
                const bounds = s.getBBox();
                const view = s.viewBox.baseVal;
                return bounds.x >= view.x - 1 && bounds.y >= view.y - 1 &&
                    bounds.x + bounds.width <= view.x + view.width + 1 &&
                    bounds.y + bounds.height <= view.y + view.height + 1;
            });
            assert(fits, 'The whole diagram fits its SVG viewBox after rendering');
        }
    }
    // Enter through another page: the lazy runtime must be available before the
    // first diagram page is reached through the site's DOM-swapping navigation.
    await page.goto(base + '/en/index.html');
    assert.equal(downloads.length, 0, 'No Mermaid download on a page without diagrams');
    await page.evaluate(path => {
        window.diagramNavigationSentinel = true;
        const link = document.createElement('a');
        link.href = path;
        link.id = 'diagram-test-link';
        link.textContent = 'Open article';
        document.querySelector('main').prepend(link);
    }, article);
    await page.locator('#diagram-test-link').click();
    await page.waitForURL('**' + article);
    await checkTheme('dark');
    assert(await page.evaluate(() => window.diagramNavigationSentinel), 'Navigation used the SPA');
    assert(downloads.length > 0);
    checks.push('Lazy loading and first SPA entry');

    await page.emulateMedia({ colorScheme: 'light' });
    await checkTheme('light');
    await page.locator('#theme-toggle').click();
    await checkTheme('dark');
    await page.reload();
    await checkTheme('dark');
    await page.emulateMedia({ colorScheme: 'dark' });
    await page.locator('#theme-toggle').click();
    await checkTheme('light');
    checks.push('System preference, manual overrides, and persisted theme');

    await page.locator('.back-link').click();
    await page.waitForURL('**/en/index.html');
    await page.goBack();
    await page.waitForURL('**' + article);
    await checkTheme('light');
    checks.push('Diagrams render again after history navigation');

    for (const width of [1200, 390, 320]) {
        await page.setViewportSize({ width, height: 1050 });
        assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
        const clipped = await page.locator('.mermaid-diagram .node').evaluateAll(nodes => nodes.flatMap(node => {
            const box = node.querySelector('rect.label-container').getBoundingClientRect();
            const label = node.querySelector('.label').getBoundingClientRect();
            return label.left < box.left || label.right > box.right || label.top < box.top || label.bottom > box.bottom
                ? [node.textContent] : [];
        }));
        assert.deepEqual(clipped, [], 'Labels fit inside their nodes');
        assert.equal(await page.locator('.mermaid-diagram foreignObject').count(), 0,
            'SVG labels avoid inheriting article paragraph sizes and clipping text');
    }
    checks.push('Desktop and mobile layout, label bounds, and no horizontal overflow');
    await page.locator('#theme-toggle').click();
    await checkTheme('dark');
    await page.emulateMedia({ media: 'print' });
    assert(await page.locator('.theme-media [data-theme-variant="light"]').isVisible());
    assert(!(await page.locator('.theme-media [data-theme-variant="dark"]').isVisible()));
    checks.push('Print uses the Day screenshot');
    assert.deepEqual(errors, []);
    await context.close();

    const noJS = await browser.newContext({ javaScriptEnabled: false, colorScheme: 'dark' });
    const fallback = await noJS.newPage();
    await fallback.goto(base + article);
    assert.equal(await fallback.locator('code.language-mermaid').count(), 1);
    assert(await fallback.locator('.theme-media [data-theme-variant="dark"]').isVisible());
    await noJS.close();
    const offline = await browser.newContext();
    await offline.route('https://cdn.jsdelivr.net/**', route => route.abort());
    const offlinePage = await offline.newPage();
    await offlinePage.goto(base + article, { waitUntil: 'networkidle' });
    assert.equal(await offlinePage.locator('code.language-mermaid').count(), 1);
    assert.equal(await offlinePage.locator('.mermaid-diagram').count(), 0);
    await offline.close();
    checks.push('Readable source fallback without JavaScript or CDN access');
    console.log(checks.map(check => `PASS ${check}`).join('\n'));
} finally {
    await browser.close();
}
