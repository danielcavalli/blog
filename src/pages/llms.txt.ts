// The site, said to a language model: what it is and where each post is as Markdown.
import type { APIRoute } from "astro";

import { posts, postUrl, type Lang } from "../content/documents";
import { absolute } from "../site/seo";
import { WORDS } from "../site/words";

const listed = (lang: Lang) =>
  posts()
    .filter((post) => post.in[lang])
    .map((post) => `- [${post.in[lang]!.title}](${absolute(`${postUrl(post, lang)}.md`)}): ${post.in[lang]!.excerpt}`)
    .join("\n");

export const GET: APIRoute = () =>
  new Response(
    `# dan.rio

> ${WORDS.en.description} Written by Daniel Cavalli in English and Brazilian Portuguese. The writing is under CC BY 4.0.

Every post is also served as Markdown: add \`.md\` to its address. Feeds: ${absolute("/en/feed.xml")} and ${absolute("/pt/feed.xml")}.

## Posts in English

${listed("en")}

## Posts em português

${listed("pt")}

## About

- [About Daniel Cavalli](${absolute("/en/about")})
- [CV](${absolute("/en/cv")})
`,
    { headers: { "Content-Type": "text/plain; charset=utf-8" } },
  );
