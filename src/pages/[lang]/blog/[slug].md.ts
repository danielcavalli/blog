// Each post as Markdown, beside its page: /en/blog/<slug>.md. For agents and anything else that
// reads text better than pages.
import type { APIRoute } from "astro";

import { posts, type Lang, type Post } from "../../../content/documents";
import { markdownOf } from "../../../site/publish";

export function getStaticPaths() {
  return posts().flatMap((post) => (Object.keys(post.in) as Lang[]).map((lang) => ({ params: { lang, slug: post.slug }, props: { post, lang } })));
}

export const GET: APIRoute = ({ props }) =>
  new Response(markdownOf(props.post as Post, props.lang as Lang), { headers: { "Content-Type": "text/markdown; charset=utf-8" } });
