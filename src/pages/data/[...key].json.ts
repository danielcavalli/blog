// Each page's value (site/pages.ts) as JSON, for the site to change to that page in place:
// /data/en/blog/<slug>.json, /data/en/blog.json, /data/en.json, /data/index.json for the root.
import type { APIRoute } from "astro";

import { routeAt, routes } from "../../site/routes";

export function getStaticPaths() {
  return routes().map((route) => ({ params: { key: route.path.replace(/^\/+|\/+$/g, "") || "index" }, props: { path: route.path } }));
}

export const GET: APIRoute = ({ props }) =>
  new Response(JSON.stringify(routeAt(props.path as string)), { headers: { "Content-Type": "application/json; charset=utf-8" } });
