#!/usr/bin/env node
// Pictures of the built site, for looking at: every page asked for, at a desk and on a phone, under
// the sun, dusk and the moon. Paint is laid by a shader, so the pages are opened in a real browser
// and given time for the strokes to come up.
//
//   npm run build && node tools/shots.mjs [out-dir] [path ...]

import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

import { chromium } from "playwright";

const [out = "/tmp/blog-shots", ...asked] = process.argv.slice(2);
const pages = asked.length ? asked : ["/en/", "/en/blog/", "/en/blog/mare-rio-and-mare-hub", "/en/about", "/en/cv"];
const frames = { desk: { width: 1440, height: 1000 }, phone: { width: 402, height: 874 } };
const lights = (process.env.LIGHTS ?? "day,dusk,night").split(",");
const port = 4399;

fs.mkdirSync(out, { recursive: true });
const server = spawn("npx", ["astro", "preview", "--port", String(port), "--host", "127.0.0.1"], { stdio: "ignore", detached: true });
const stop = () => { try { process.kill(-server.pid); } catch {} };
process.on("exit", stop);

for (let tries = 0; tries < 60; tries++) {
  try {
    if ((await fetch(`http://127.0.0.1:${port}/en/`)).ok) break;
  } catch {}
  await new Promise((done) => setTimeout(done, 250));
}

// Software rendering: the pictures never touch the machine's graphics card.
const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
for (const [frame, viewport] of Object.entries(frames)) {
  for (const light of lights) {
    const context = await browser.newContext({ viewport, deviceScaleFactor: 1, reducedMotion: process.env.MOTION ? "no-preference" : "reduce" });
    await context.addInitScript((kept) => localStorage.setItem("mare-theme", kept), light);
    const page = await context.newPage();
    const said = [];
    page.on("console", (message) => { if (message.type() === "error") said.push(message.text()); });
    page.on("pageerror", (error) => said.push(String(error)));
    for (const to of pages) {
      await page.goto(`http://127.0.0.1:${port}${to}`, { waitUntil: "networkidle" });
      await page.evaluate(() => document.fonts.ready);
      await page.waitForTimeout(Number(process.env.WAIT ?? 2500));
      // AT=<selector>: the page scrolled until the first such thing is in the middle of the screen.
      if (process.env.AT) {
        await page.evaluate((selector) => document.querySelector(selector)?.scrollIntoView({ block: "center" }), process.env.AT);
        await page.waitForTimeout(600);
      }
      const name = `${to.replace(/^\/|\/$/g, "").replaceAll("/", "_") || "root"}--${frame}--${light}.png`;
      await page.screenshot({ path: path.join(out, name), fullPage: process.env.FULL === "1" });
      console.log(name, said.length ? `· ${said.length} errors: ${said.slice(0, 2).join(" | ").slice(0, 300)}` : "");
      said.length = 0;
    }
    await context.close();
  }
}
await browser.close();
stop();
