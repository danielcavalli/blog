// The site's content, read from the Markdown files as they are in the repository.
//
// A post is `posts/<slug>.md`, in the language it was written in; `posts/<slug>.<locale>.md` is its
// translation and names it in `translation_of`. What a reader gets is a file's front matter and its
// body: the reef trailer (the document's marker and any conversation) is never part of a page.

import fs from "node:fs";
import path from "node:path";
import { parse as parseYaml } from "yaml";

import { split } from "../../tools/git/conversations.mjs";

export const LANGS = { en: "en-us", pt: "pt-br" } as const;
export type Lang = keyof typeof LANGS;
export type Locale = (typeof LANGS)[Lang];

export const langOf = (locale: string): Lang => (locale.toLowerCase().startsWith("pt") ? "pt" : "en");
export const otherLang = (lang: Lang): Lang => (lang === "en" ? "pt" : "en");

export interface Document {
  /** The file, from the repository's root. */
  file: string;
  lang: Lang;
  title: string;
  excerpt: string;
  tags: string[];
  body: string;
  meta: Record<string, unknown>;
}

export interface Post {
  slug: string;
  /** ISO date the post was published. */
  date: string;
  updated?: string;
  kind: "post" | "presentation";
  /** The language it was written in. */
  written: Lang;
  in: Partial<Record<Lang, Document>>;
}

const ROOT = process.cwd();
const FRONT_MATTER = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?/;

export function readDocument(file: string): Document {
  const raw = fs.readFileSync(path.join(ROOT, file), "utf8");
  const front = FRONT_MATTER.exec(raw);
  const meta = (front ? parseYaml(front[1]) : {}) as Record<string, unknown>;
  const text = (key: string) => (meta[key] == null ? "" : String(meta[key]));
  return {
    file,
    lang: langOf(text("lang") || "en-us"),
    title: text("title"),
    excerpt: text("excerpt"),
    tags: Array.isArray(meta.tags) ? meta.tags.map(String) : [],
    body: split(front ? raw.slice(front[0].length) : raw).body.trim(),
    meta,
  };
}

let cached: Post[] | undefined;

/** Every post, newest first. */
export function posts(): Post[] {
  if (cached) return cached;
  const files = fs.readdirSync(path.join(ROOT, "posts")).filter((name) => name.endsWith(".md")).sort();
  const documents = files.map((name) => readDocument(`posts/${name}`));
  const sources = documents.filter((document) => !document.meta.translation_of);
  const all = sources.map((source): Post => {
    const name = path.basename(source.file);
    const slug = String(source.meta.slug ?? name.replace(/\.md$/, ""));
    const post: Post = {
      slug,
      date: String(source.meta.date ?? ""),
      updated: source.meta.updated ? String(source.meta.updated) : undefined,
      kind: source.meta.content_type === "presentation" ? "presentation" : "post",
      written: source.lang,
      in: { [source.lang]: source },
    };
    for (const translation of documents.filter((document) => document.meta.translation_of === name)) {
      post.in[translation.lang] = translation;
    }
    return post;
  });
  all.sort((a, b) => b.date.localeCompare(a.date) || a.slug.localeCompare(b.slug));
  cached = all;
  return all;
}

/** The post a Markdown file belongs to, for links between posts. */
export function postOfFile(name: string): Post | undefined {
  return posts().find((post) => Object.values(post.in).some((document) => path.basename(document!.file) === name));
}

// ---------- words about a post ----------

const MONTHS = {
  en: ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
  pt: ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
};

export function formatDate(iso: string, lang: Lang): string {
  const [year, month, day] = iso.split("-");
  if (!year || !month || !day) return iso;
  const name = MONTHS[lang][Number(month) - 1];
  return lang === "pt" ? `${day} de ${name} de ${year}` : `${name} ${day}, ${year}`;
}

export function readingTime(document: Document): string {
  const minutes = Math.max(1, Math.round(document.body.split(/\s+/).length / 200));
  return document.lang === "pt" ? `${minutes} min de leitura` : `${minutes} min read`;
}

export const postUrl = (post: Post, lang: Lang) => `/${lang}/blog/${post.slug}`;
