// @ts-check
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@astrojs/react";
import { defineConfig } from "astro/config";

// The site before this one kept every page at an address ending in .html, and a post's pictures
// under /static/. Each old address answers with a permanent redirect to where the thing is now, so
// links and search results made before the rebuild still arrive. Written after the build, from the
// pages it made.
const redirects = {
  name: "dan.rio:redirects",
  hooks: {
    /** @param {{ dir: URL }} built */
    "astro:build:done": ({ dir }) => {
      const out = fileURLToPath(dir);
      const lines = ["/index.html / 301"];
      for (const lang of ["en", "pt"]) {
        lines.push(`/${lang}/index.html /${lang}/blog/ 301`, `/${lang}/about.html /${lang}/about 301`, `/${lang}/cv.html /${lang}/cv 301`);
        for (const file of fs.readdirSync(path.join(out, lang, "blog")).sort()) {
          const slug = file.endsWith(".html") && file !== "index.html" ? file.slice(0, -".html".length) : undefined;
          if (slug) lines.push(`/${lang}/blog/${slug}.html /${lang}/blog/${slug} 301`);
        }
      }
      lines.push(
        "/static/images/mare-rio/* /media/mare-rio-and-mare-hub/:splat 301",
        "/static/images/mare-agent/* /media/adding-an-agent-to-a-mare-app/:splat 301",
        "/static/images/presentations/how-i-use-ai-agents/* /media/how-i-use-ai-agents/:splat 301",
        "/static/examples/mare-agent/* /media/adding-an-agent-to-a-mare-app/:splat 301",
        "/static/images/Logo.png /logo.png 301",
      );
      fs.writeFileSync(path.join(out, "_redirects"), `${lines.join("\n")}\n`);
    },
  },
};

// Every page is built ahead of time. `preserve` writes en/blog/<slug>.html and en/blog/index.html,
// which a static host serves as /en/blog/<slug> and /en/blog/.
export default defineConfig({
  site: "https://dan.rio",
  integrations: [react(), redirects],
  build: { format: "preserve" },
  trailingSlash: "ignore",
});
