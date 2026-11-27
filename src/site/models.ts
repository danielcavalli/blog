// What each page is given: plain data, worked out at build time from the Markdown files, that the
// server draws into the page and the browser draws again. Server only.

import fs from "node:fs";
import path from "node:path";
import { parse as parseYaml } from "yaml";

import { formatDate, postOfFile, posts, postUrl, readDocument, readingTime, type Post } from "../content/documents";
import { readDeck, type DeckSlide } from "../reef/deck";
import { renderDocument } from "../reef/render";
import type { Heading, Note, TreeNode } from "../reef/tree";
import { WORDS, type Alternates, type Lang } from "./words";

export interface PostModel {
  lang: Lang;
  slug: string;
  title: string;
  dek: string;
  facts: string[];
  tags: string[];
  headings: Heading[];
  notes: Note[];
  body: TreeNode[];
  alternates: Alternates;
}

export interface DeckModel {
  lang: Lang;
  slug: string;
  title: string;
  dek: string;
  tags: string[];
  facts: string[];
  slides: DeckSlide[];
  alternates: Alternates;
}

export interface EntryModel {
  slug: string;
  href: string;
  title: string;
  excerpt: string;
  tags: string[];
  /** As it is read. */
  date: string;
  /** ISO, to order by. */
  created: string;
  updated: string;
  year: string;
}

export interface IndexModel {
  lang: Lang;
  posts: EntryModel[];
  alternates: Alternates;
}

export interface LandingModel {
  lang: Lang;
  count: number;
  latest: string;
  alternates: Alternates;
}

export interface PlainModel {
  lang: Lang;
  which: "about" | "cv";
  title: string;
  fact: string;
  dek?: string;
  description: string;
  body: TreeNode[];
  alternates: Alternates;
}

const LANGS: Lang[] = ["en", "pt"];
const both = (to: (lang: Lang) => string): Alternates => Object.fromEntries(LANGS.map((lang) => [lang, to(lang)]));

/** A link between posts is written as a link to the file beside it; on the site it is that post's page. */
function linkIn(lang: Lang) {
  return (href: string) => {
    const match = /^(?:\.\/)?([^/#?]+\.md)(#.*)?$/.exec(href);
    const post = match && postOfFile(match[1]);
    return post ? postUrl(post, post.in[lang] ? lang : post.written) + (match[2] ?? "") : href;
  };
}

export function postModel(post: Post, lang: Lang): PostModel {
  const document = post.in[lang]!;
  // A translation's sections keep the ids of the text it translates.
  const source = post.in[post.written]!;
  const headingIds = document === source ? undefined : renderDocument(source.body).headings.map((heading) => heading.id);
  const { body, headings, notes } = renderDocument(document.body, { link: linkIn(lang), headingIds, file: document.file });
  return {
    lang,
    slug: post.slug,
    title: document.title,
    dek: document.excerpt,
    facts: [formatDate(post.date, lang), readingTime(document)],
    tags: document.tags,
    headings,
    notes,
    body,
    alternates: Object.fromEntries((Object.keys(post.in) as Lang[]).map((code) => [code, postUrl(post, code)])),
  };
}

export function deckModel(post: Post, lang: Lang): DeckModel {
  const document = post.in[lang]!;
  return {
    lang,
    slug: post.slug,
    title: document.title,
    dek: document.excerpt,
    tags: document.tags,
    facts: [formatDate(post.date, lang), readingTime(document)],
    slides: readDeck(document.body, { link: linkIn(lang), file: document.file }),
    alternates: Object.fromEntries((Object.keys(post.in) as Lang[]).map((code) => [code, postUrl(post, code)])),
  };
}

export function indexModel(lang: Lang): IndexModel {
  return {
    lang,
    posts: posts()
      .filter((post) => post.in[lang])
      .map((post) => {
        const document = post.in[lang]!;
        return {
          slug: post.slug,
          href: postUrl(post, lang),
          title: document.title,
          excerpt: document.excerpt,
          tags: document.tags,
          date: formatDate(post.date, lang),
          created: post.date,
          updated: post.updated ?? post.date,
          year: post.date.slice(0, 4),
        };
      }),
    alternates: both((code) => `/${code}/blog/`),
  };
}

export function landingModel(lang: Lang): LandingModel {
  const here = posts().filter((post) => post.in[lang]);
  return { lang, count: here.length, latest: here[0] ? formatDate(here[0].date, lang) : "", alternates: both((code) => `/${code}/`) };
}

export function aboutModel(lang: Lang): PlainModel {
  const document = readDocument(lang === "pt" ? "pages/about.pt-br.md" : "pages/about.md");
  return {
    lang,
    which: "about",
    title: document.title || WORDS[lang].about.title,
    fact: WORDS[lang].about.fact,
    description: WORDS[lang].description,
    body: renderDocument(document.body, { link: linkIn(lang), file: document.file }).body,
    alternates: both((code) => `/${code}/about`),
  };
}

interface Cv {
  name: string;
  tagline: string;
  location: string;
  contact: { email: string; phone?: string; linkedin?: string; github?: string };
  skills: string[];
  languages_spoken: string[];
  summary: string;
  experience: { title: string; company: string; location?: string; period: string; description?: string; achievements?: string[] }[];
  education: { degree: string; school: string; period: string }[];
}

/** The CV, kept as data, written out as the document it is read as. */
function cvMarkdown(cv: Cv, lang: Lang): string {
  const names = WORDS[lang].cv;
  const contact = [
    `[${cv.contact.email}](mailto:${cv.contact.email})`,
    cv.contact.linkedin && `[linkedin.com/in/${cv.contact.linkedin}](https://www.linkedin.com/in/${cv.contact.linkedin}/)`,
    cv.contact.github && `[github.com/${cv.contact.github}](https://github.com/${cv.contact.github})`,
    cv.location,
  ].filter(Boolean);
  const lines = [`## ${names.contact}`, contact.join(" · "), `## ${names.summary}`, cv.summary.trim(), `## ${names.experience}`];
  for (const role of cv.experience) {
    lines.push(`### ${role.title}`, [role.company, role.period, role.location].filter(Boolean).join(" · "));
    if (role.description) lines.push(role.description.trim());
    if (role.achievements?.length) lines.push(role.achievements.map((line) => `- ${line.trim()}`).join("\n"));
  }
  lines.push(`## ${names.skills}`, cv.skills.join(" · "), `## ${names.education}`);
  for (const study of cv.education) lines.push(`### ${study.degree}`, `${study.school} · ${study.period}`);
  lines.push(`## ${names.languages}`, cv.languages_spoken.map((line) => `- ${line}`).join("\n"));
  return lines.join("\n\n");
}

export function cvModel(lang: Lang): PlainModel {
  const file = lang === "pt" ? "cv_data.pt-br.yaml" : "cv_data.yaml";
  const cv = parseYaml(fs.readFileSync(path.join(process.cwd(), file), "utf8")) as Cv;
  return {
    lang,
    which: "cv",
    title: cv.name,
    fact: WORDS[lang].cv.fact,
    dek: cv.tagline,
    description: cv.tagline,
    body: renderDocument(cvMarkdown(cv, lang)).body,
    alternates: both((code) => `/${code}/cv`),
  };
}
