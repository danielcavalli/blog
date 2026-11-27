#!/usr/bin/env node
// What a phone's screen shows, frame by frame: a page opened cold, then a link followed, recorded
// as a film with the CPU slowed four times and a phone's network, and cut into a contact sheet of
// frames a tenth of a second apart. For judging arrival and page changes by eye.
//
//   npm run build && node tools/film.mjs [--root dist] [--network wifi|4g] [--light day] <out-dir> <path> [<selector to tap>]

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

import { chromium } from "playwright";

import { serve } from "./serve.mjs";

const args = process.argv.slice(2);
const option = (name, fallback) => (args.includes(name) ? args.splice(args.indexOf(name), 2)[1] : fallback);
const root = path.resolve(option("--root", "dist"));
const network = option("--network", "wifi");
const light = option("--light", "day");
const [out, to, tap] = args;
const NETWORKS = { wifi: { latency: 30, downloadThroughput: 3276800, uploadThroughput: 1310720 }, "4g": { latency: 150, downloadThroughput: 209715, uploadThroughput: 98304 } };

fs.mkdirSync(out, { recursive: true });
const server = await serve(root, 4382);
const browser = await chromium.launch({ args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"] });
const context = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1, isMobile: true, hasTouch: true, recordVideo: { dir: out, size: { width: 390, height: 844 } } });
await context.addInitScript((kept) => localStorage.setItem("mare-theme", kept), light);
const page = await context.newPage();
const cdp = await context.newCDPSession(page);
await cdp.send("Network.enable");
await cdp.send("Network.emulateNetworkConditions", { offline: false, ...NETWORKS[network] });
await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
const started = Date.now();
await page.goto(`http://127.0.0.1:4382${to}`, { waitUntil: "load" });
await page.waitForTimeout(3000);
let tapped = null;
if (tap) {
  tapped = (Date.now() - started) / 1000;
  await page.locator(tap).first().tap();
  await page.waitForTimeout(2500);
}
const video = page.video();
await context.close();
await browser.close();
server.close();

const film = path.join(out, "film.webm");
fs.renameSync(await video.path(), film);
// (the system's ffmpeg: the one Playwright brings records film but has no filters to cut it)
const ffmpeg = process.env.FFMPEG ?? "ffmpeg";
// Two strips: the arrival (its first 1.5 s) and the page change (the 1.5 s from the tap).
const strip = (from, name) =>
  execFileSync(ffmpeg, ["-y", "-loglevel", "error", "-ss", String(from), "-t", "1.5", "-i", film, "-vf", "fps=10,scale=195:-1,tile=15x1", "-frames:v", "1", path.join(out, name)]);
strip(0, "arrival.png");
if (tapped !== null) strip(tapped, "change.png");
console.log(`${out}: arrival.png${tapped !== null ? ", change.png" : ""} (frames 0.1 s apart), film.webm`);
