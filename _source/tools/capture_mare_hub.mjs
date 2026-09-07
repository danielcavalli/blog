// Capture the actual local Hub UI with sample data, without a live account or backend.
// Run with a local Hub dev server and Playwright available (or PLAYWRIGHT_MODULE set).
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const origin = new URL(process.argv[2] || 'http://127.0.0.1:4173');
if (!['127.0.0.1', 'localhost', '[::1]'].includes(origin.hostname)) {
  throw new Error('The screenshot fixture is restricted to a local Hub server.');
}
const root = fileURLToPath(new URL('../../', import.meta.url));
const output = resolve(root, 'static/images/mare-agent');
await mkdir(output, { recursive: true });

const account = {
  email: 'reader@example.com', tenant: 'preview', namespace: 'tenant-preview',
  user: 'reader', entitlements: [], hasTenant: true,
};
const catalog = [
  { slug: 'notes', name: 'Notes', description: 'Capture thoughts and find them again.' },
  { slug: 'finance', name: 'Finance', description: 'Understand income, spending, and savings.' },
  { slug: 'moon', name: 'Moon', description: 'Keep a watchlist and discover what to watch.' },
  { slug: 'library', name: 'Library', description: 'Develop ideas into lasting understanding.' },
].map(item => ({ ...item, entitled: true, available: true, installable: true }));
const fixtures = {
  '/verify': { ...account, token: 'local-preview-fixture' },
  '/platform/me': account,
  '/platform/catalog': { items: catalog },
  '/platform/apps': { items: catalog.map((app, i) => ({
    slug: app.slug, phase: 'Ready', url: `/${app.slug}/`, pinned: false, order: String(i),
  })) },
  '/platform/agent-auth': { codex: 'connected', opencodeGo: 'connected', deepseek: 'connected' },
};

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1060 }, deviceScaleFactor: 1,
    reducedMotion: 'reduce', colorScheme: 'light',
  });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  for (const [path, body] of Object.entries(fixtures)) {
    await page.route(`${origin.origin}${path}`, route => route.fulfill({ json: body }));
  }
  await page.routeWebSocket('**/ws', () => {});
  await page.addInitScript(() => localStorage.setItem('mare-theme', 'day'));
  await page.goto(origin.href, { waitUntil: 'networkidle' });
  await page.getByRole('link', { name: 'Moon', exact: true }).waitFor();
  await page.evaluate(() => document.fonts.ready);
  for (const theme of ['day', 'night']) {
    await page.evaluate(value => {
      localStorage.setItem('mare-theme', value);
      document.documentElement.dataset.theme = value;
    }, theme);
    await page.waitForTimeout(700);
    await page.screenshot({
      path: resolve(output, `hub-${theme}.jpg`), type: 'jpeg', quality: 92, fullPage: true,
    });
  }
  if (errors.length) throw new Error(errors.join('\n'));
  await writeFile(resolve(output, 'capture.json'), JSON.stringify({
    description: 'Actual Maré Hub frontend, locally rendered with sample account and app data.',
    sourceRevision: process.env.MARE_SOURCE_REVISION || 'unspecified',
    viewport: { width: 1440, height: 1060 },
    themes: ['day', 'night'],
    sampleApps: catalog.map(({ slug }) => slug),
    playwrightVersion: '1.62.1',
  }, null, 2) + '\n');
  console.log(`Saved Day and Night screenshots to ${output}`);
} finally {
  await browser.close();
}
