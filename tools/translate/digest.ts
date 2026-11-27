// Which text a translation was made from.
//
// Source digest, version 1 (defined in `tools/migrate/export_translations.py`, which wrote the
// first ones): the SHA-256, in hex, of the UTF-8 bytes of
//
//     title: <title>\n
//     excerpt: <excerpt>\n
//     tags: <tag>, <tag>, ...\n
//     \n
//     <body>
//
// where `<body>` is the source file after its front matter and before its reef trailer, with CRLF
// read as LF and whitespace trimmed at both ends. A missing field is the empty string. Dates, slugs
// and other front matter do not count: a translation is stale only when words a reader sees have
// changed.
//
// The CV has no body and no front matter, so it has a digest of its own, version 1: the SHA-256, in
// hex, of the UTF-8 bytes of the CV's data as JSON, with every object's keys sorted and no space
// between tokens. Comments, key order and how the YAML is laid out do not count, for the same reason.

import { createHash } from "node:crypto";

const sha256 = (text: string): string => createHash("sha256").update(text, "utf8").digest("hex");

export interface Digested {
  title: string;
  excerpt: string;
  tags: string[];
  /** After the front matter, before the trailer, CRLF read as LF, trimmed. */
  body: string;
}

/** The source digest of a post or a page. */
export function sourceDigest({ title, excerpt, tags, body }: Digested): string {
  return sha256(`title: ${title}\nexcerpt: ${excerpt}\ntags: ${tags.join(", ")}\n\n${body}`);
}

/** A value with every object's keys in order. */
export function sorted(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sorted);
  if (typeof value !== "object" || value === null) return value;
  const record = value as Record<string, unknown>;
  return Object.fromEntries(
    Object.keys(record)
      .sort()
      .map((key) => [key, sorted(record[key])]),
  );
}

/** The source digest of the CV. */
export function cvDigest(cv: unknown): string {
  return sha256(JSON.stringify(sorted(cv)));
}
