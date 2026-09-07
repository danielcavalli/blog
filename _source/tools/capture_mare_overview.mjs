// Actual local Maré frontends with sample API data; no production account required.
// Start Vite for Platform, Notes, and Moon on 4173, 4174, and 4175, respectively.
// PLAYWRIGHT_MODULE may point to an installed Playwright index.mjs.
import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';

const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const root = fileURLToPath(new URL('../../', import.meta.url));
const output = resolve(root, 'static/images/mare-rio');
const repos = process.env.MARE_REPOS || '/home/dan/mare-rio';
await mkdir(output, { recursive: true });

const account = {
  email: 'reader@example.com', tenant: 'preview', namespace: 'tenant-preview',
  user: 'reader', entitlements: ['notes', 'finance', 'moon', 'library'], hasTenant: true,
};
const catalog = [
  { slug: 'notes', name: 'Notes', description: 'Capture thoughts and find them again.' },
  { slug: 'finance', name: 'Finance', description: 'Understand income, spending, and savings.' },
  { slug: 'moon', name: 'Moon', description: 'Keep a watchlist and discover what to watch.' },
  { slug: 'library', name: 'Library', description: 'Develop ideas into lasting understanding.' },
].map(app => ({ ...app, entitled: true, available: true, installable: true }));
const hub = {
  '/verify': { ...account, token: 'local-preview-fixture' },
  '/platform/me': account,
  '/platform/catalog': { items: catalog },
  '/platform/apps': { items: catalog.map((app, i) => ({
    slug: app.slug, phase: 'Ready', url: `/${app.slug}/`, pinned: false, order: String(i),
  })) },
  '/platform/agent-auth': { codex: 'connected', opencodeGo: 'connected', deepseek: 'connected' },
};

const notes = [
  ['A place to think', 'A note can begin before I know where it belongs.\n\nCapture the observation first. Give it a title when there is a useful one.\n\n## To return to\n\n- Keep the original source close to the thought.\n- Link related notes when the connection becomes clear.\n- Leave room to change my mind.', ['writing', 'ideas']],
  ['Reading notes', 'Keep the passage and my reaction separate. One is evidence of what the author said; the other is something I still need to examine.', ['reading']],
  ['An idea for the watchlist', 'Try recommendations that explain a connection to something I have already watched.', ['ideas']],
  ['September', 'Loose ends, books to return to, and things worth trying.', []],
].map(([title, body, tags], i) => ({
  id: i + 1, title, body, tags, snippet: body.split('\n')[0], folder_id: null,
  pinned: i === 0, rev: 1, updated_at: '2026-09-06T12:00:00Z',
  created_at: '2026-09-06T12:00:00Z', trashed_at: null, properties: {}, backlinks: [],
}));

// Real catalog titles used only as sample watchlist entries, not the author's history.
const titles = [
  ['tt0944947', 'Game of Thrones', '2011', 'series', ['Drama', 'Fantasy']],
  ['tt0903747', 'Breaking Bad', '2008', 'series', ['Drama', 'Crime']],
  ['tt4574334', 'Stranger Things', '2016', 'series', ['Drama', 'Sci-Fi']],
  ['tt0816692', 'Interstellar', '2014', 'movie', ['Drama', 'Sci-Fi']],
  ['tt2543164', 'Arrival', '2016', 'movie', ['Drama', 'Sci-Fi']],
  ['tt1856101', 'Blade Runner 2049', '2017', 'movie', ['Drama', 'Sci-Fi']],
  ['tt0185906', 'Band of Brothers', '2001', 'series', ['Drama', 'History']],
  ['tt7366338', 'Chernobyl', '2019', 'series', ['Drama', 'History']],
].map(([imdb_id, title, year, media_type, genres]) => ({
  imdb_id, external_id: imdb_id, title, year, media_type, genres, premiered: '',
  image_url: imdb_id === 'tt0185906'
    ? 'https://static.tvmaze.com/uploads/images/medium_portrait/80/201679.jpg'
    : `https://images.metahub.space/poster/medium/${imdb_id}/img`,
  imdb_score: 0, imdb_votes: 0, best_quality: '', estimated_bytes: 0,
}));
const items = titles.slice(0, 4).map((title, i) => ({
  ...title, id: i + 1, target_season: 1, target_episode: 1,
  cache_end_season: 1, cache_end_episode: 12, pinned_seasons: [],
  episodes_cached: title.media_type === 'movie' ? 1 : 12, episodes_total: 12, catalog_total_episodes: 12,
  watched_season_episodes: 0, season_total_episodes: 12, cached_bytes: 0,
  watched_episodes: 0, next_watch_season: 1, next_watch_episode: 1,
  storage_used_bytes: 0, storage_total_bytes: 0, rating: 0, marked_watched: false,
  needs_decision: '', source_label: '', status: 'ready', status_detail: '',
}));
const pageResult = items => ({ items, nextCursor: null });

const browser = await chromium.launch({ headless: true });
const captures = [];
const failures = [];
try {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1060 }, deviceScaleFactor: 1,
    reducedMotion: 'reduce', colorScheme: 'light', serviceWorkers: 'block',
  });
  await context.addInitScript(() => localStorage.setItem('mare-theme', 'day'));
  await context.routeWebSocket('**/ws', () => {});
  const page = await context.newPage();
  page.on('pageerror', error => failures.push(error.message));
  await page.route('**/*', async route => {
    const url = new URL(route.request().url());
    const path = url.pathname;
    if (['images.metahub.space', 'static.tvmaze.com'].includes(url.hostname)) return route.continue();
    if (url.hostname !== '127.0.0.1') return route.abort();
    if (hub[path]) return route.fulfill({ json: hub[path] });
    if (path.startsWith('/notes/api/')) {
      const endpoint = path.slice('/notes/api'.length);
      let body;
      if (endpoint === '/hub/me') body = account;
      else if (endpoint === '/folders') body = [];
      else if (endpoint === '/tags') body = ['writing', 'ideas', 'reading'].map(tag => ({ tag, count: notes.filter(n => n.tags.includes(tag)).length }));
      else if (endpoint === '/titles') body = notes.map(({ id, title }) => ({ id, title }));
      else if (endpoint === '/usage') body = { attachment_bytes: 0, quota_bytes: 1000000000, note_count: notes.length, trash_count: 0 };
      else if (/^\/notes\/\d+$/.test(endpoint)) body = notes.find(n => n.id === Number(endpoint.split('/').pop()));
      else if (endpoint === '/notes') body = { items: notes, next_cursor: null };
      else { failures.push(`Unexpected Notes endpoint: ${endpoint}`); body = {}; }
      return route.fulfill({ json: body });
    }
    if (path.startsWith('/moon/api/')) {
      const endpoint = path.slice('/moon/api'.length);
      let body;
      if (endpoint === '/items') body = pageResult(items);
      else if (endpoint === '/config') body = { jellyfin_web_url: '' };
      else if (endpoint === '/hub/me') body = account;
      else if (endpoint === '/settings/opensubtitles') body = { configured: false, mode: '', username: '', phase: 'absent', detail: '' };
      else if (endpoint === '/profile') body = {};
      else if (endpoint.startsWith('/recommendations/')) {
        const kind = endpoint.endsWith('/shows') ? 'series' : 'movie';
        body = pageResult(titles.filter(t => t.media_type === kind).map((t, i) => ({ ...t, match: 92 - i * 4, reason: 'Sample recommendation for this screenshot.' })));
      } else if (endpoint === '/catalog') body = pageResult(titles.filter(t => t.media_type === route.request().postDataJSON().media_type));
      else { failures.push(`Unexpected Moon endpoint: ${endpoint}`); body = {}; }
      return route.fulfill({ json: body });
    }
    return route.continue();
  });

  async function capture(name, url, ready, prepare = async () => {}) {
    await page.goto(url, { waitUntil: 'networkidle' });
    await ready();
    await prepare();
    await page.evaluate(() => document.fonts.ready);
    // Load image elements before the capture, including ones initially below the fold.
    await page.evaluate(async () => {
      await Promise.all([...document.images].map(img => {
        img.loading = 'eager';
        return img.decode().catch(() => {});
      }));
    });
    const broken = await page.evaluate(() => [...document.images].filter(img => !img.naturalWidth).map(img => img.src));
    assert.deepEqual(broken, [], `${name}: failed images`);
    for (const theme of ['day', 'night']) {
      await page.evaluate(value => {
        localStorage.setItem('mare-theme', value);
        document.documentElement.dataset.theme = value;
      }, theme);
      await page.waitForTimeout(500);
      const filename = `${name}-${theme}.jpg`;
      await page.screenshot({ path: resolve(output, filename), type: 'jpeg', quality: 92, fullPage: true });
      captures.push({ filename, url, theme });
    }
  }
  await capture('hub', 'http://127.0.0.1:4173/', () => page.getByRole('link', { name: 'Moon', exact: true }).waitFor());
  await capture('settings', 'http://127.0.0.1:4173/settings', () => page.getByRole('heading', { name: 'Agent providers' }).waitFor());
  await capture('notes', 'http://127.0.0.1:4174/notes/', () => page.getByRole('region', { name: 'Notes', exact: true }).waitFor(), async () => {
    await page.getByRole('button', { name: /^Pinned A place to think/ }).click();
    await page.getByRole('textbox', { name: 'Title', exact: true }).waitFor();
  });
  await capture('moon', 'http://127.0.0.1:4175/moon/', () => page.getByRole('heading', { name: 'Watchlist', exact: true }).waitFor());
  assert.deepEqual(failures, []);
  await writeFile(resolve(output, 'capture.json'), JSON.stringify({
    description: 'Actual local Maré frontends with sample account, notes, catalog, and provider status. No production data or live agent output.',
    capturedAt: new Date().toISOString(), viewport: { width: 1440, height: 1060 },
    sources: Object.fromEntries(['mare-platform', 'notes', 'moon'].map(repo => [repo, {
      revision: execFileSync('git', ['-C', resolve(repos, repo), 'rev-parse', 'HEAD'], { encoding: 'utf8' }).trim(),
      frontendChanges: execFileSync('git', ['-C', resolve(repos, repo), 'status', '--short', '--', 'web'], { encoding: 'utf8' }).trim(),
    }])),
    posterSources: titles.map(({ title, image_url }) => ({ title, url: image_url })), captures,
  }, null, 2) + '\n');
  console.log(`Saved ${captures.length} screenshots to ${output}`);
} finally {
  await browser.close();
}
