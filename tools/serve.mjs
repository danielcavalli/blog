#!/usr/bin/env node
// The built site, served the way the static host serves it: /en/blog/x is en/blog/x.html, /en/blog/
// is en/blog/index.html, and an address that is not there gets 404.html. For looking at dist/ and
// for the checks that open it in a browser.
//
//   node tools/serve.mjs [port]

import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8", ".xml": "application/xml; charset=utf-8", ".md": "text/markdown; charset=utf-8",
  ".txt": "text/plain; charset=utf-8", ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".woff2": "font/woff2",
};

export function serve(root = path.join(process.cwd(), "dist"), port = 4321) {
  const server = http.createServer((request, response) => {
    const asked = decodeURIComponent(new URL(request.url ?? "/", "http://x").pathname);
    const candidates = asked.endsWith("/") ? [`${asked}index.html`] : [asked, `${asked}.html`, `${asked}/index.html`];
    const found = candidates.map((name) => path.join(root, name)).find((file) => file.startsWith(root) && fs.existsSync(file) && fs.statSync(file).isFile());
    const file = found ?? path.join(root, "404.html");
    response.writeHead(found ? 200 : 404, { "Content-Type": TYPES[path.extname(file)] ?? "application/octet-stream" });
    fs.createReadStream(file).pipe(response);
  });
  return new Promise((ready) => server.listen(port, "127.0.0.1", () => ready(server)));
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === fs.realpathSync(fileURLToPath(import.meta.url))) {
  const port = Number(process.argv[2] ?? 4321);
  await serve(undefined, port);
  console.log(`dist/ at http://127.0.0.1:${port}/`);
}
