#!/usr/bin/env node
// A post's pictures and files live beside it, in posts/<slug>.assets/, where Reef finds them. The
// site serves them from /media/<slug>/. This copies them into public/media/ before a build or the
// development server starts (public/media/ is not kept in git: posts/ is where they live), and
// writes each picture again as WebP at the widths a reader's screen may want (720 and 1440 px), so
// a phone is not sent a picture made for a desk. The page offers them by width (src/reef/Tree.tsx);
// the original stays, for a browser that can take nothing else.

import fs from "node:fs";
import path from "node:path";

import sharp from "sharp";

// (the widths are the renderer's too: src/reef/render.ts offers the same files)
const WIDTHS = JSON.parse(fs.readFileSync(new URL("../src/reef/picture-widths.json", import.meta.url), "utf8"));

const root = process.cwd();
const from = path.join(root, "posts");
const to = path.join(root, "public", "media");

fs.rmSync(to, { recursive: true, force: true });
let files = 0;
let written = 0;
for (const entry of fs.readdirSync(from, { withFileTypes: true })) {
  if (!entry.isDirectory() || !entry.name.endsWith(".assets")) continue;
  const slug = entry.name.slice(0, -".assets".length);
  const into = path.join(to, slug);
  fs.cpSync(path.join(from, entry.name), into, { recursive: true });
  for (const name of fs.readdirSync(into)) {
    files++;
    if (!/\.(jpe?g|png)$/i.test(name)) continue;
    const picture = sharp(path.join(into, name));
    const { width = 0 } = await picture.metadata();
    for (const target of WIDTHS) {
      if (width < target * 0.9 && target !== WIDTHS[0]) continue;
      await sharp(path.join(into, name))
        .resize({ width: Math.min(target, width), withoutEnlargement: true })
        .webp({ quality: 80, effort: 5 })
        .toFile(path.join(into, `${name.replace(/\.[a-z]+$/i, "")}-${target}.webp`));
      written++;
    }
  }
}
console.log(`media: ${files} files from posts/*.assets, ${written} WebP copies`);
