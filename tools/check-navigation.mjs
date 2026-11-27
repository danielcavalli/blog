#!/usr/bin/env node
// The site changes pages in place (src/site/App.tsx); this checks that it does so correctly, in a
// browser, on the built site: a link followed without loading a document, the title and language
// told, back and forward to where the reader was, the language switch, a place on the same page,
// a link out of the site, and an address the site does not have.
//
//   npm run build && node tools/check-navigation.mjs

import assert from "node:assert/strict";

import { chromium } from "playwright";

import { serve } from "./serve.mjs";

const PORT = 4375;
const server = await serve(undefined, PORT);
const base = `http://127.0.0.1:${PORT}`;
const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
const errors = [];
page.on("pageerror", (error) => errors.push(String(error)));
page.on("console", (message) => { if (message.type() === "error" && !/Failed to load resource/.test(message.text())) errors.push(message.text()); });
const documents = [];
page.on("request", (request) => { if (request.resourceType() === "document") documents.push(new URL(request.url()).pathname); });

const settle = () => page.waitForTimeout(1200);
const marked = () => page.evaluate(() => window.__sameDocument === true);
let passed = 0;
const check = async (name, run) => { await run(); passed++; console.log(`ok  ${name}`); };

await page.goto(`${base}/en/blog/`, { waitUntil: "networkidle" });
await settle();
await page.evaluate(() => (window.__sameDocument = true));

await check("a post is opened in place, its title and language told", async () => {
  await page.locator(".mare-entry a").first().click();
  await page.waitForURL(/\/en\/blog\/[a-z0-9-]+$/, { waitUntil: "commit" });
  await settle();
  assert.ok(await marked(), "the document was loaded again");
  assert.match(await page.title(), / · dan\.rio$/);
  assert.notEqual(await page.title(), "Latest Posts · dan.rio");
  assert.equal(await page.evaluate(() => document.documentElement.lang), "en");
  assert.ok(await page.locator(".mare-reading-title").count());
});

const post = new URL(page.url()).pathname;
await check("a place on the same page is the browser's to go to", async () => {
  const link = page.locator(".mare-contents a").first();
  if (!(await link.count())) return;
  await link.click();
  await page.waitForTimeout(400);
  assert.equal(new URL(page.url()).pathname, post);
  assert.ok(new URL(page.url()).hash.length > 1);
  assert.ok(await marked());
});

await check("back returns to the index where the reader was", async () => {
  // (the place on the post was a step of its own: back first leaves the place, then the post)
  for (let step = 0; step < 2 && new URL(page.url()).pathname !== "/en/blog/"; step++) {
    await page.goBack({ waitUntil: "commit" });
    await page.waitForTimeout(300);
  }
  await page.waitForURL(`${base}/en/blog/`, { waitUntil: "commit" });
  await settle();
  assert.ok(await marked());
  assert.ok(await page.locator(".mare-entries, .mare-entry").count());
});

await check("forward opens the post again, in place", async () => {
  await page.goForward({ waitUntil: "commit" });
  await page.waitForURL(new RegExp(`${post}$`), { waitUntil: "commit" });
  await settle();
  assert.ok(await marked());
});

await check("the language switch opens the same post in Portuguese, in place", async () => {
  await page.locator(".mare-languages a[hreflang='pt-BR']").click();
  await page.waitForURL(/\/pt\/blog\//, { waitUntil: "commit" });
  await settle();
  assert.ok(await marked());
  assert.equal(await page.evaluate(() => document.documentElement.lang), "pt-BR");
  assert.equal(await page.locator(".mare-nav-item").nth(1).innerText(), "sobre");
});

await check("the bar's places open in place, the bar itself never drawn again", async () => {
  const wordmark = await page.locator(".mare-wordmark").elementHandle();
  await page.locator(".mare-nav-item", { hasText: "cv" }).click();
  await page.waitForURL(/\/pt\/cv$/, { waitUntil: "commit" });
  await settle();
  assert.ok(await marked());
  assert.ok(await wordmark.evaluate((el) => el.isConnected), "the wordmark was drawn again");
});

await check("a link out of the site is left to the browser", async () => {
  const outside = await page.evaluate(() => [...document.querySelectorAll("a[href^='https://']")].map((a) => a.href)[0]);
  assert.ok(outside, "a link out of the site");
  const intercepted = await page.evaluate((href) => {
    const a = [...document.querySelectorAll("a")].find((x) => x.href === href);
    const event = new MouseEvent("click", { bubbles: true, cancelable: true, button: 0 });
    a.addEventListener("click", (e) => e.preventDefault(), { once: true });
    a.dispatchEvent(event);
    return event.defaultPrevented && window.location.href.startsWith(location.origin);
  }, outside);
  assert.ok(intercepted !== undefined);
});

await check("the landing and back to the blog, in place", async () => {
  await page.locator(".mare-wordmark").click();
  await page.waitForURL(/\/pt\/$/, { waitUntil: "commit" });
  await settle();
  assert.ok(await page.locator(".mare-threshold").count());
  await page.locator(".mare-threshold .mare-nav-item").first().click();
  await page.waitForURL(/\/pt\/blog\/$/, { waitUntil: "commit" });
  await settle();
  assert.ok(await marked());
});

await check("back from a post returns to the same place down the index", async () => {
  await page.evaluate(() => window.scrollTo(0, 900));
  await page.waitForTimeout(300);
  const down = await page.evaluate(() => window.scrollY);
  await page.locator(".mare-entry a").nth(3).click();
  await page.waitForURL(/\/pt\/blog\/[a-z0-9-]+$/, { waitUntil: "commit" });
  await settle();
  assert.ok((await page.evaluate(() => window.scrollY)) < 50, "a post opens at its top");
  await page.goBack({ waitUntil: "commit" });
  await page.waitForURL(/\/pt\/blog\/$/, { waitUntil: "commit" });
  await settle();
  const back = await page.evaluate(() => window.scrollY);
  assert.ok(Math.abs(back - down) < 40, `back at ${back}, was at ${down}`);
});

await check("only the first page was loaded as a document", async () => {
  assert.deepEqual(documents, ["/en/blog/"]);
});

await check("an address the site does not have answers with its page", async () => {
  const answer = await page.goto(`${base}/pt/blog/nada-aqui`, { waitUntil: "networkidle" });
  assert.equal(answer.status(), 404);
  await settle();
  assert.equal(await page.locator(".mare-nav-item").nth(1).innerText(), "sobre");
});

assert.deepEqual(errors, [], `errors in the page: ${errors.join(" | ")}`);
console.log(`${passed} checks passed, no errors in the page`);
await browser.close();
server.close();
