// What the index's search looks through: every post in one language, as plain words. Fetched when a
// reader starts to search.
import type { APIRoute } from "astro";

import { posts, postUrl, formatDate } from "../../content/documents";
import { postModel } from "../../site/models";
import { wordsOf } from "../../site/publish";
import type { Lang } from "../../site/words";

export const getStaticPaths = () => [{ params: { lang: "en" } }, { params: { lang: "pt" } }];

export const GET: APIRoute = ({ params }) => {
  const lang = params.lang as Lang;
  const entries = posts()
    .filter((post) => post.in[lang])
    .map((post) => {
      const model = postModel(post, lang);
      return { slug: post.slug, href: postUrl(post, lang), title: model.title, excerpt: model.dek, tags: model.tags, date: formatDate(post.date, lang), text: wordsOf(model.body) };
    });
  return new Response(JSON.stringify(entries), { headers: { "Content-Type": "application/json; charset=utf-8" } });
};
