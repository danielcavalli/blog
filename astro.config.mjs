// @ts-check
import react from "@astrojs/react";
import { defineConfig } from "astro/config";

// Every page is built ahead of time. `preserve` writes en/blog/<slug>.html and en/blog/index.html,
// which a static host serves as /en/blog/<slug> and /en/blog/.
export default defineConfig({
  site: "https://dan.rio",
  integrations: [react()],
  build: { format: "preserve" },
  trailingSlash: "ignore",
});
