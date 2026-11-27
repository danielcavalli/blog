// The documents that are translated, and where each one's translation stands.
//
//   posts/<slug>.md, pages/<name>.md    a source, in the language its front matter names (`lang`)
//   posts/<slug>.<locale>.md            its translation, which names it in `translation_of`
//   cv_data.yaml, cv_data.pt-br.yaml    the CV and its translation
//
// A Markdown file is its front matter, its body, and an optional reef trailer (the document's marker
// and the conversation about it), which is never part of what is translated and never rewritten.

import fs from "node:fs";
import path from "node:path";
import { parse as parseYaml, stringify as stringifyYaml } from "yaml";

import { split } from "../git/conversations.mjs";

import { cvDigest, sourceDigest } from "./digest.ts";

export type Locale = "en-us" | "pt-br";
export const LOCALES: readonly Locale[] = ["en-us", "pt-br"];

export const localeOf = (lang: unknown): Locale => (String(lang ?? "").toLowerCase().startsWith("pt") ? "pt-br" : "en-us");
export const otherLocale = (locale: Locale): Locale => (locale === "en-us" ? "pt-br" : "en-us");

// ---------- files ----------

/** A file's text. Anything that is not UTF-8 is refused: it could not be written back byte for byte. */
export function readText(file: string): string {
  const bytes = fs.readFileSync(file);
  const text = bytes.toString("utf8");
  if (!Buffer.from(text, "utf8").equals(bytes)) throw new Error(`${file} is not valid UTF-8`);
  return text;
}

export function writeText(file: string, text: string): void {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const partial = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(partial, text, "utf8");
  fs.renameSync(partial, file);
}

export interface MarkdownFile {
  meta: Record<string, unknown>;
  /** After the front matter, before the trailer, CRLF read as LF, trimmed. */
  body: string;
  /** The reef trailer exactly as the file has it, from its first block to the file's end. Empty when there is none. */
  trailer: string;
}

const FRONT_MATTER = /^﻿?---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/;

/** A Markdown file as its front matter, its body and its trailer. */
export function readMarkdown(text: string): MarkdownFile {
  const head: string = split(text).body;
  const front = FRONT_MATTER.exec(head);
  const meta = front ? (parseYaml(front[1]!) as unknown) : {};
  return {
    meta: typeof meta === "object" && meta !== null && !Array.isArray(meta) ? (meta as Record<string, unknown>) : {},
    body: (front ? head.slice(front[0].length) : head).replace(/\r\n?/g, "\n").trim(),
    trailer: text.slice(head.length),
  };
}

const text = (value: unknown): string => (value == null ? "" : String(value));
const list = (value: unknown): string[] => (Array.isArray(value) ? value.map(String) : []);

// Laid out as the translations already in the repository are (they were written by PyYAML): one
// line per value, lists flush with their key, single quotes where quotes are needed, and a string
// quoted when YAML 1.1 would read it as something else (a date, `no`).
const YAML_STYLE = { version: "1.1", lineWidth: 0, indentSeq: false, singleQuote: true } as const;

export const toYaml = (value: unknown): string => stringifyYaml(value, YAML_STYLE);

// ---------- sources ----------

interface Source {
  /** The file, from the repository's root, with forward slashes. */
  file: string;
  /** The language it was written in. */
  lang: Locale;
  /** The language it is translated into. */
  target: Locale;
  /** Where its translation is, or would be. */
  translation: string;
  digest: string;
}

export interface ProseDocument extends Source {
  kind: "post" | "presentation" | "about";
  title: string;
  excerpt: string;
  tags: string[];
  body: string;
  meta: Record<string, unknown>;
}

export interface CvDocument extends Source {
  kind: "cv";
  data: unknown;
}

export type SourceDocument = ProseDocument | CvDocument;

export const CV_SOURCE = "cv_data.yaml";

function proseSource(root: string, file: string): ProseDocument | null {
  const { meta, body } = readMarkdown(readText(path.join(root, file)));
  if (meta.translation_of != null) return null;
  const lang = localeOf(meta.lang);
  const target = otherLocale(lang);
  const fields = { title: text(meta.title), excerpt: text(meta.excerpt), tags: list(meta.tags), body };
  return {
    kind: meta.content_type === "presentation" ? "presentation" : file === "pages/about.md" ? "about" : "post",
    file,
    lang,
    target,
    translation: file.replace(/\.md$/, `.${target}.md`),
    digest: sourceDigest(fields),
    meta,
    ...fields,
  };
}

/** Every source document of the repository at `root`: posts, pages, then the CV. */
export function discover(root: string): SourceDocument[] {
  const sources: SourceDocument[] = [];
  for (const folder of ["posts", "pages"]) {
    if (!fs.existsSync(path.join(root, folder))) continue;
    for (const name of fs.readdirSync(path.join(root, folder)).filter((entry) => entry.endsWith(".md")).sort()) {
      const source = proseSource(root, `${folder}/${name}`);
      if (source) sources.push(source);
    }
  }
  if (fs.existsSync(path.join(root, CV_SOURCE))) {
    const data = parseYaml(readText(path.join(root, CV_SOURCE))) as unknown;
    sources.push({
      kind: "cv",
      file: CV_SOURCE,
      lang: "en-us",
      target: "pt-br",
      translation: "cv_data.pt-br.yaml",
      digest: cvDigest(data),
      data,
    });
  }
  return sources;
}

// ---------- where a translation stands ----------

export interface State {
  status: "current" | "stale" | "missing";
  /** The digest the translation records, when it records one. */
  recorded: string | null;
  /** Why it is stale, when the reason is not simply that the source changed. */
  note?: string;
}

const CV_HEADER = /^# (translation_of|source_digest|translated_by|translated_at): (.*)$/;

/** What the comment lines at the head of a translated CV say about it. */
export function cvHeader(yaml: string): Record<string, string> {
  const fields: Record<string, string> = {};
  for (const line of yaml.split(/\r?\n/)) {
    if (!line.startsWith("#")) break;
    const match = CV_HEADER.exec(line);
    if (match) fields[match[1]!] = match[2]!.trim();
  }
  return fields;
}

/** Where a source's translation stands: current, stale (it was made from another text) or missing. */
export function stateOf(root: string, source: SourceDocument): State {
  const file = path.join(root, source.translation);
  if (!fs.existsSync(file)) return { status: "missing", recorded: null };
  const content = readText(file);
  const fields = source.kind === "cv" ? cvHeader(content) : readMarkdown(content).meta;
  const recorded = fields.source_digest == null ? null : String(fields.source_digest);
  const names = fields.translation_of == null ? null : String(fields.translation_of);
  if (names !== path.posix.basename(source.file)) {
    return { status: "stale", recorded, note: names ? `it says it translates ${names}` : "it does not say what it translates" };
  }
  if (recorded === null) return { status: "stale", recorded, note: "it records no source_digest" };
  return { status: recorded === source.digest ? "current" : "stale", recorded };
}

// ---------- links between documents ----------

const SCHEME = /^[a-z][a-z0-9+.-]*:/i;
const LOCALE_SUFFIX = new RegExp(`\\.(?:${LOCALES.join("|")})$`, "i");

/**
 * How a link destination in `source` must read in its translation. A link to another document is
 * a link to that document's file in the reader's language: `other.md` where that is the language it
 * was written in, `other.<locale>.md` where it is a translation. Anything else is unchanged.
 */
export function linkMapper(source: SourceDocument, sources: SourceDocument[]): (destination: string) => string {
  const written = new Map(sources.map((other) => [other.file, other.lang]));
  const folder = path.posix.dirname(source.file);
  return (destination) => {
    if (SCHEME.test(destination) || destination.startsWith("/") || destination.startsWith("#")) return destination;
    const cut = destination.search(/[#?]/);
    const [target, rest] = cut === -1 ? [destination, ""] : [destination.slice(0, cut), destination.slice(cut)];
    if (!target.endsWith(".md")) return destination;
    const slash = target.lastIndexOf("/") + 1;
    const [prefix, name] = [target.slice(0, slash), target.slice(slash)];
    const stem = name.slice(0, -".md".length).replace(LOCALE_SUFFIX, "");
    const lang = written.get(path.posix.normalize(path.posix.join(folder, prefix, `${stem}.md`)));
    if (!lang) return destination;
    return `${prefix}${lang === source.target ? `${stem}.md` : `${stem}.${source.target}.md`}${rest}`;
  };
}
