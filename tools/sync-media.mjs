#!/usr/bin/env node
// A post's pictures and files live beside it, in posts/<slug>.assets/, where Reef finds them. The
// site serves them from /media/<slug>/. This copies them into public/media/ before a build or the
// development server starts (public/media/ is not kept in git: posts/ is where they live).

import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const from = path.join(root, "posts");
const to = path.join(root, "public", "media");

fs.rmSync(to, { recursive: true, force: true });
let files = 0;
for (const entry of fs.readdirSync(from, { withFileTypes: true })) {
  if (!entry.isDirectory() || !entry.name.endsWith(".assets")) continue;
  const slug = entry.name.slice(0, -".assets".length);
  fs.cpSync(path.join(from, entry.name), path.join(to, slug), { recursive: true });
  files += fs.readdirSync(path.join(to, slug), { recursive: true }).length;
}
console.log(`media: ${files} files from posts/*.assets`);
