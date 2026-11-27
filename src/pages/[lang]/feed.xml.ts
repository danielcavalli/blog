// A feed of every post in one language, whole: /en/feed.xml and /pt/feed.xml (Atom).
import type { APIRoute } from "astro";

import { posts, postUrl } from "../../content/documents";
import { htmlOf } from "../../site/publish";
import { absolute } from "../../site/seo";
import { WORDS, type Lang } from "../../site/words";

export const getStaticPaths = () => [{ params: { lang: "en" } }, { params: { lang: "pt" } }];

const escape = (text: string) => text.replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const moment = (date: string) => `${date}T12:00:00Z`;

export const GET: APIRoute = ({ params }) => {
  const lang = params.lang as Lang;
  const here = posts().filter((post) => post.in[lang]);
  const newest = here.map((post) => post.updated ?? post.date).sort().at(-1) ?? "1970-01-01";
  const entries = here.map((post) => {
    const document = post.in[lang]!;
    const url = absolute(postUrl(post, lang));
    return `  <entry>
    <id>${url}</id>
    <title>${escape(document.title)}</title>
    <link rel="alternate" type="text/html" href="${url}"/>
    <published>${moment(post.date)}</published>
    <updated>${moment(post.updated ?? post.date)}</updated>
    <summary>${escape(document.excerpt)}</summary>
${document.tags.map((tag) => `    <category term="${escape(tag)}"/>`).join("\n")}
    <content type="html">${escape(htmlOf(post, lang))}</content>
  </entry>`;
  });
  const xml = `<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="${lang === "pt" ? "pt-BR" : "en"}">
  <id>${absolute(`/${lang}/`)}</id>
  <title>dan.rio</title>
  <subtitle>${escape(WORDS[lang].description)}</subtitle>
  <link rel="self" type="application/atom+xml" href="${absolute(`/${lang}/feed.xml`)}"/>
  <link rel="alternate" type="text/html" href="${absolute(`/${lang}/blog/`)}"/>
  <updated>${moment(newest)}</updated>
  <author><name>Daniel Cavalli</name><uri>${absolute(`/${lang}/about`)}</uri></author>
  <rights>CC BY 4.0</rights>
${entries.join("\n")}
</feed>
`;
  return new Response(xml, { headers: { "Content-Type": "application/atom+xml; charset=utf-8" } });
};
