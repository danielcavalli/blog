// What each page is, said the way search engines read it (schema.org). Server only.

import type { Post } from "../content/documents";
import type { Lang } from "./words";

export const SITE = "https://dan.rio";
export const absolute = (path: string) => new URL(path, SITE).href;

const AUTHOR = {
  "@type": "Person",
  name: "Daniel Cavalli",
  url: `${SITE}/en/about`,
  sameAs: ["https://x.com/dancavlli", "https://github.com/danielcavalli", "https://www.linkedin.com/in/cavallidaniel/"],
};
const inLanguage = (lang: Lang) => (lang === "pt" ? "pt-BR" : "en");

export function postData(post: Post, lang: Lang, path: string) {
  const document = post.in[lang]!;
  return {
    "@context": "https://schema.org",
    "@type": "BlogPosting",
    headline: document.title,
    description: document.excerpt,
    datePublished: post.date,
    dateModified: post.updated ?? post.date,
    inLanguage: inLanguage(lang),
    keywords: document.tags.join(", "),
    author: AUTHOR,
    publisher: AUTHOR,
    mainEntityOfPage: absolute(path),
    url: absolute(path),
    license: "https://creativecommons.org/licenses/by/4.0/",
    ...(post.written !== lang ? { translationOfWork: { "@type": "BlogPosting", url: absolute(`/${post.written}/blog/${post.slug}`) } } : {}),
  };
}

export function siteData(lang: Lang, description: string) {
  return { "@context": "https://schema.org", "@type": "WebSite", name: "dan.rio", url: absolute(`/${lang}/`), inLanguage: inLanguage(lang), description, author: AUTHOR };
}

export function blogData(lang: Lang, description: string) {
  return { "@context": "https://schema.org", "@type": "Blog", name: "dan.rio", url: absolute(`/${lang}/blog/`), inLanguage: inLanguage(lang), description, author: AUTHOR };
}

export function personData(lang: Lang, path: string, description: string) {
  return { "@context": "https://schema.org", "@type": "ProfilePage", url: absolute(path), inLanguage: inLanguage(lang), mainEntity: { ...AUTHOR, description, jobTitle: "Machine Learning Engineer" } };
}
