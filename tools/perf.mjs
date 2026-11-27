#!/usr/bin/env node
// How the site behaves on a phone: pages opened and links followed in Chromium with the CPU slowed
// four times and a phone's network, measured from the browser's own clocks.
//
// For a page opened cold: when the first words are painted, when the largest thing is, when the
// fonts are in, when the page comes alive (its components hydrated), when the first wash is painted
// and when it is fully up. For a link followed: from the tap to the next page's words, and to its
// wash. And what was sent, by kind.
//
//   npm run build && node tools/perf.mjs [--root dist] [--network wifi|4g] [--runs 3] [path ...]
//
// A dist/ of the old site can be measured the same way with --root.

import path from "node:path";

import { chromium } from "playwright";

import { serve } from "./serve.mjs";

const args = process.argv.slice(2);
const option = (name, fallback) => (args.includes(name) ? args.splice(args.indexOf(name), 2)[1] : fallback);
const root = path.resolve(option("--root", "dist"));
const network = option("--network", "wifi");
const runs = Number(option("--runs", "3"));
const follow = option("--follow", "");
const pages = args.length ? args : ["/en/blog/", "/en/blog/dont-outsource-the-thinking", "/en/"];

// A phone: four times slower than this machine, on home Wi-Fi or on a mobile network.
const NETWORKS = {
  wifi: { latency: 30, downloadThroughput: (25 * 1024 * 1024) / 8, uploadThroughput: (10 * 1024 * 1024) / 8 },
  "4g": { latency: 150, downloadThroughput: (1.6 * 1024 * 1024) / 8, uploadThroughput: (0.75 * 1024 * 1024) / 8 },
};
const PORT = 4385;
const server = await serve(root, PORT);
const base = `http://127.0.0.1:${PORT}`;
const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });

async function phone() {
  const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true });
  const page = await context.newPage();
  const cdp = await context.newCDPSession(page);
  await cdp.send("Network.enable");
  await cdp.send("Network.emulateNetworkConditions", { offline: false, ...NETWORKS[network] });
  await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
  const sent = {};
  cdp.on("Network.loadingFinished", (event) => {
    const kind = byId.get(event.requestId) ?? "other";
    sent[kind] = (sent[kind] ?? 0) + event.encodedDataLength;
  });
  const byId = new Map();
  cdp.on("Network.responseReceived", (event) => byId.set(event.requestId, kindOf(event.response)));
  return { context, page, sent };
}

function kindOf(response) {
  const type = response.mimeType ?? "";
  if (type.includes("html")) return "html";
  if (type.includes("css")) return "css";
  if (type.includes("javascript")) return "js";
  if (type.includes("font")) return "font";
  if (type.startsWith("image/")) return "image";
  return "other";
}

// Watches set up before the page's own scripts run: everything is read off performance.now().
const WATCH = () => {
  const at = (window.__perf = { marks: {} });
  const mark = (name) => { if (at.marks[name] === undefined) at.marks[name] = performance.now(); };
  new PerformanceObserver((list) => { for (const e of list.getEntries()) if (e.name === "first-contentful-paint") at.marks.fcp = e.startTime; }).observe({ type: "paint", buffered: true });
  new PerformanceObserver((list) => { const e = list.getEntries().at(-1); if (e) at.marks.lcp = e.startTime; }).observe({ type: "largest-contentful-paint", buffered: true });
  const look = () => {
    if (!document.documentElement.classList.contains("dan-arriving") && document.querySelector(".mare-page")) mark("shown");
    if (document.querySelector("astro-island") && !document.querySelector("astro-island[ssr]")) mark("alive");
    const wash = document.querySelector(".mare-wash[data-painted]");
    if (wash) {
      mark("painted");
      if (getComputedStyle(wash).opacity === "1") mark("up");
    }
  };
  new MutationObserver(look).observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ["data-painted", "ssr", "style", "class"] });
  const frame = () => { look(); if (at.marks.up === undefined) requestAnimationFrame(frame); };
  requestAnimationFrame(frame);
};

const median = (values) => {
  const known = values.filter((value) => typeof value === "number").sort((a, b) => a - b);
  return known.length ? known[Math.floor(known.length / 2)] : undefined;
};
const ms = (value) => (value === undefined ? "    -" : `${Math.round(value)}`.padStart(5));

console.log(`phone: CPU ×4, ${network} (${NETWORKS[network].latency} ms, ${Math.round((NETWORKS[network].downloadThroughput * 8) / 1024 / 1024 * 10) / 10} Mbit/s) · ${path.relative(process.cwd(), root) || root} · median of ${runs}`);
console.log(`${"page".padEnd(46)}  words  large  fonts  alive  paint     up  shown    sent (KB: html css js font image)`);
for (const to of pages) {
  const results = [];
  for (let run = 0; run < runs; run++) {
    const { context, page, sent } = await phone();
    await page.addInitScript(WATCH);
    await page.goto(base + to, { waitUntil: "load" });
    await page.waitForFunction(() => window.__perf?.marks.up !== undefined || performance.now() > 9000, null, { timeout: 15000 }).catch(() => {});
    await page.waitForTimeout(300);
    results.push({
      marks: await page.evaluate(() => ({
        ...window.__perf.marks,
        // the fonts are in when the last font file has arrived
        fonts: Math.max(0, ...performance.getEntriesByType("resource").filter((e) => /\.woff2/.test(e.name)).map((e) => e.responseEnd)) || undefined,
      })),
      sent: { ...sent },
    });
    await context.close();
  }
  const m = (name) => median(results.map((r) => r.marks[name]));
  const s = (kind) => Math.round((results[0].sent[kind] ?? 0) / 1024);
  console.log(`${to.padEnd(46)}  ${ms(m("fcp"))}  ${ms(m("lcp"))}  ${ms(m("fonts"))}  ${ms(m("alive"))}  ${ms(m("painted"))}  ${ms(m("up"))}  ${ms(m("shown"))}    ${s("html")} ${s("css")} ${s("js")} ${s("font")} ${s("image")}`);
}

// A link followed: from the index, the first post's entry, after the index has settled.
if (follow) {
  const [from, selector] = follow.split(" ");
  const times = [];
  for (let run = 0; run < runs; run++) {
    const { context, page } = await phone();
    await page.addInitScript(WATCH);
    await page.goto(base + from, { waitUntil: "load" });
    await page.waitForTimeout(2500);
    const before = page.url();
    // the phases of the change: the transition asked for, the new page drawn, the crossing begun and ended
    await page.evaluate(() => {
      const at = (window.__turn = {});
      const now = () => performance.timeOrigin + performance.now();
      const start = document.startViewTransition?.bind(document);
      if (!start) return;
      document.startViewTransition = (run) => {
        at.asked = now();
        const t = start(async () => { at.drawing = now(); await run(); at.drawn = now(); });
        t.ready.then(() => (at.crossing = now()), () => {});
        t.finished.then(() => (at.crossed = now()), () => {});
        return t;
      };
    });
    const started = await page.evaluate(() => performance.timeOrigin + performance.now());
    await page.locator(selector).first().tap();
    await page.waitForFunction((url) => location.href !== url, before, { timeout: 15000 });
    // the next page's words: its title is on screen; its wash: painted and fully up
    const words = await page.waitForFunction(() => {
      const title = document.querySelector(".mare-reading-title, h1");
      return title && title.getBoundingClientRect().height > 0 ? performance.timeOrigin + performance.now() : false;
    }, null, { timeout: 15000 }).then((h) => h.jsonValue());
    const up = await page.waitForFunction(() => {
      const wash = document.querySelector(".mare-reading-head .mare-wash[data-painted]");
      return wash && getComputedStyle(wash).opacity === "1" ? performance.timeOrigin + performance.now() : false;
    }, null, { timeout: 15000, polling: "raf" }).then((h) => h.jsonValue()).catch(() => undefined);
    await page.waitForTimeout(1200);
    const turn = await page.evaluate(() => window.__turn);
    const rel = (key) => (turn?.[key] === undefined ? undefined : turn[key] - started);
    times.push({ words: words - started, up: up === undefined ? undefined : up - started, asked: rel("asked"), drawn: rel("drawn"), crossing: rel("crossing"), crossed: rel("crossed") });
    await context.close();
  }
  const t = (key) => ms(median(times.map((x) => x[key])));
  console.log(`\nfollowing "${selector}" from ${from}, ms after the tap: asked ${t("asked")} · new page drawn ${t("drawn")} · crossing begins ${t("crossing")} · ends ${t("crossed")} · words ${t("words")} · wash up ${t("up")}`);
}

await browser.close();
server.close();
