// Every page of the site, each with the same page in the other language beside it.
import type { APIRoute } from "astro";

import { posts, postUrl, type Lang } from "../content/documents";
import { absolute } from "../site/seo";

const LANGS: Lang[] = ["en", "pt"];
const hreflang = (lang: Lang) => (lang === "pt" ? "pt-BR" : "en");

export const GET: APIRoute = () => {
  const newest = posts().map((post) => post.updated ?? post.date).sort().at(-1);
  const pages: { in: Partial<Record<Lang, string>>; changed?: string }[] = [
    { in: { en: "/en/", pt: "/pt/" }, changed: newest },
    { in: { en: "/en/blog/", pt: "/pt/blog/" }, changed: newest },
    { in: { en: "/en/about", pt: "/pt/about" } },
    { in: { en: "/en/cv", pt: "/pt/cv" } },
    ...posts().map((post) => ({ in: Object.fromEntries(LANGS.filter((lang) => post.in[lang]).map((lang) => [lang, postUrl(post, lang)])), changed: post.updated ?? post.date })),
  ];
  const urls = pages.flatMap((page) =>
    (Object.keys(page.in) as Lang[]).map(
      (lang) => `  <url>
    <loc>${absolute(page.in[lang]!)}</loc>
${(Object.keys(page.in) as Lang[]).map((other) => `    <xhtml:link rel="alternate" hreflang="${hreflang(other)}" href="${absolute(page.in[other]!)}"/>`).join("\n")}
    <xhtml:link rel="alternate" hreflang="x-default" href="${absolute(page.in.en ?? page.in[lang]!)}"/>${page.changed ? `\n    <lastmod>${page.changed}</lastmod>` : ""}
  </url>`,
    ),
  );
  const xml = `<?xml version="1.0" encoding="utf-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">
${urls.join("\n")}
</urlset>
`;
  return new Response(xml, { headers: { "Content-Type": "application/xml; charset=utf-8" } });
};
