#!/usr/bin/env node
// The built site, served the way the static host serves it: /en/blog/x is en/blog/x.html, /en/blog/
// is en/blog/index.html, an address that is not there gets 404.html, text is compressed and the
// files named by their content are kept by the browser. For looking at dist/ (from a phone too) and
// for the checks that open it in a browser.
//
//   node tools/serve.mjs [port] [--host 0.0.0.0] [--root dist]

import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import zlib from "node:zlib";

const TYPES = {
  ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8", ".xml": "application/xml; charset=utf-8", ".md": "text/markdown; charset=utf-8",
  ".txt": "text/plain; charset=utf-8", ".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp", ".avif": "image/avif",
  ".svg": "image/svg+xml", ".woff2": "font/woff2",
};
const COMPRESSED = new Set([".html", ".css", ".js", ".json", ".xml", ".md", ".txt", ".svg"]);

export function serve(root = path.join(process.cwd(), "dist"), port = 4321, host = "127.0.0.1") {
  const server = http.createServer((request, response) => {
    const asked = decodeURIComponent(new URL(request.url ?? "/", "http://x").pathname);
    const candidates = asked.endsWith("/") ? [`${asked}index.html`] : [asked, `${asked}.html`, `${asked}/index.html`];
    const found = candidates.map((name) => path.join(root, name)).find((file) => file.startsWith(root) && fs.existsSync(file) && fs.statSync(file).isFile());
    const file = found ?? path.join(root, "404.html");
    const type = path.extname(file);
    const headers = { "Content-Type": TYPES[type] ?? "application/octet-stream", Vary: "Accept-Encoding" };
    headers["Cache-Control"] = /\/_astro\//.test(file) ? "public, max-age=31536000, immutable" : "public, max-age=0, must-revalidate";
    const accepts = String(request.headers["accept-encoding"] ?? "");
    let body = fs.createReadStream(file);
    if (COMPRESSED.has(type) && /\bbr\b/.test(accepts)) {
      headers["Content-Encoding"] = "br";
      body = body.pipe(zlib.createBrotliCompress({ params: { [zlib.constants.BROTLI_PARAM_QUALITY]: 5 } }));
    } else if (COMPRESSED.has(type) && /\bgzip\b/.test(accepts)) {
      headers["Content-Encoding"] = "gzip";
      body = body.pipe(zlib.createGzip());
    }
    response.writeHead(found ? 200 : 404, headers);
    body.pipe(response);
  });
  return new Promise((ready) => server.listen(port, host, () => ready(server)));
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === fs.realpathSync(fileURLToPath(import.meta.url))) {
  const args = process.argv.slice(2);
  const option = (name, fallback) => (args.includes(name) ? args[args.indexOf(name) + 1] : fallback);
  const port = Number(args.find((arg) => /^\d+$/.test(arg)) ?? 4321);
  const host = option("--host", "127.0.0.1");
  const root = path.resolve(option("--root", "dist"));
  await serve(root, port, host);
  console.log(`${path.relative(process.cwd(), root) || root} at http://${host}:${port}/`);
}
