// How Cloudflare serves the built site (dist/): as static files, nothing running per request.
// `npm run deploy` builds and uploads it; README.md says how.
import { defineConfig } from "cf/config";

export default defineConfig({
  worker: {
    name: "dan-rio",
    compatibilityDate: "2026-11-23",
    // The site's own name. (www.dan.rio is sent here by a redirect rule on the zone.)
    domains: ["dan.rio"],
    assets: {
      // /en/blog/x is en/blog/x.html, /en/blog/ is en/blog/index.html.
      htmlHandling: "auto-trailing-slash",
      // An address that is not there is answered with 404.html.
      notFoundHandling: "404-page",
    },
  },
});
