// What the model is told: the guidance as the system message, the document as the user message,
// and the shape its answer must have.
//
// The guidance is the author's and lives in Markdown, which this file reads and never rewords:
//
//   guides/<locale>_localization_brief.md   how the target language should read
//   guides/<from>_to_<to>.md                the rules, glossary and protected names of a direction
//   guides/cv.md                            the names a CV keeps
//   .agents/skills/…/references/*.md        how the author writes (read in place: one copy)
//
// `prompts/` holds what the old engine wrapped around that guidance (`prompts/v2/*.md` and the text
// in `providers/opencode.py`), with `{{placeholders}}` where the guidance goes.

import fs from "node:fs";
import path from "node:path";

import type { Comment } from "./comments.ts";
import type { ProseAnswer } from "./checks.ts";
import type { SourceDocument } from "./documents.ts";
import { destinations } from "./markdown.ts";

const HERE = import.meta.dirname;
const REPOSITORY = path.resolve(HERE, "../..");

// The author's writing references, in the order and under the labels the old engine gave them.
const WRITING_REFERENCES: [string, string][] = [
  ["Blog composition", ".agents/skills/editorial-line/references/blog-composition.md"],
  ["Prose", ".agents/skills/prose-style/references/prose-contract.md"],
  ["Author voice", ".agents/skills/writing-style/references/WRITING_STYLE.md"],
];

// Guidance that is missing or empty must stop the run, not quietly weaken the translation.
function read(file: string): string {
  const content = fs.readFileSync(file, "utf8").trim();
  if (!content) throw new Error(`Empty guidance: ${file}`);
  return content;
}

/** A guide's `## Sections`, by heading. */
export function sections(markdown: string): Map<string, string> {
  const found = new Map<string, string>();
  const parts = markdown.split(/^## +(.+)$/m);
  for (let index = 1; index < parts.length; index += 2) found.set(parts[index]!.trim(), parts[index + 1]!.trim());
  return found;
}

/** A template with its `{{placeholders}}` filled. A placeholder with nothing to fill it is an error. */
export function render(template: string, values: Record<string, string>): string {
  return template.replace(/\{\{\s*([a-z_][a-z0-9_]*)\s*\}\}/g, (_, key: string) => {
    if (!(key in values)) throw new Error(`Missing prompt placeholder: ${key}`);
    return values[key]!;
  });
}

const prompt = (name: string): string => read(path.join(HERE, "prompts", name));

function section(guide: Map<string, string>, heading: string, file: string): string {
  const body = guide.get(heading);
  if (body === undefined) throw new Error(`${file} has no "## ${heading}" section`);
  return body || "- none";
}

// One list after another, without repeating an item (compared without regard to case).
function merged(...lists: string[]): string {
  const seen = new Set<string>();
  const lines = lists
    .flatMap((items) => items.split("\n"))
    .map((line) => line.trim())
    .filter((line) => line && line !== "- none" && !seen.has(line.toLowerCase()) && seen.add(line.toLowerCase()));
  return lines.length ? lines.join("\n") : "- none";
}

function writingStyleBrief(): string {
  return WRITING_REFERENCES.map(([name, file]) => `## ${name}\n\n${read(path.join(REPOSITORY, file))}`).join("\n\n");
}

const TEMPLATES = {
  post: "translate.md",
  about: "translate.md",
  presentation: "presentation_translate.md",
  cv: "cv_translate.md",
} as const;

/** The guidance for translating `source`: the system message. */
export function systemPrompt(source: SourceDocument, { revise = false } = {}): string {
  const rules = path.join(HERE, "guides", `${source.lang}_to_${source.target}.md`);
  const guide = sections(read(rules));
  const brief = path.join(HERE, "guides", `${source.target.replace("-", "_")}_localization_brief.md`);
  const cv = path.join(HERE, "guides", "cv.md");
  const kept = section(guide, "Do not translate", rules);
  const body = render(prompt(TEMPLATES[source.kind]), {
    source_locale: source.lang,
    target_locale: source.target,
    localization_brief: read(brief),
    style_constraints: section(guide, "Style constraints", rules),
    borrowing_conventions: section(guide, "Borrowing conventions", rules),
    punctuation_conventions: section(guide, "Punctuation conventions", rules),
    discourse_conventions: section(guide, "Discourse conventions", rules),
    register_conventions: section(guide, "Register conventions", rules),
    review_checks: section(guide, "Review checks", rules),
    glossary_entries: section(guide, "Glossary", rules),
    do_not_translate_entities:
      source.kind === "cv" ? merged(kept, section(sections(read(cv)), "Do not translate", cv)) : merged(kept),
    writing_style_brief: writingStyleBrief(),
  });
  const parts = [prompt("agent.md"), body, prompt("boundary.md")];
  if (revise) parts.push(prompt("revise.md"));
  const text = source.kind === "cv" ? JSON.stringify(source.data) : source.body;
  if (text.includes("mermaid")) parts.push(prompt("mermaid.md"));
  return `${parts.join("\n\n")}\n`;
}

const json = (value: unknown): string => JSON.stringify(value, null, 2);

const block = (name: string, content: string): string => `<${name}>\n${content}\n</${name}>`;

function commentText(comment: Comment): string {
  const where = [`Comment ${comment.id}`, comment.line === null ? null : `line ${comment.line}`].filter(Boolean);
  const lines = [where.join(", ")];
  if (comment.quote) lines.push("Quoted passage:", comment.quote.replace(/^/gm, "> "));
  if (comment.before !== null || comment.after !== null) {
    lines.push(`Around it: …${comment.before ?? ""} [the passage] ${comment.after ?? ""}…`);
  }
  lines.push(`${comment.author} wrote:`, comment.text);
  for (const reply of comment.replies) lines.push(`${reply.author} replied:`, reply.text);
  return lines.join("\n");
}

export interface Revision {
  /** The translation as it stands. */
  current: ProseAnswer;
  /** The owner's open comments on it. */
  comments: Comment[];
}

/** The document to translate: the user message. */
export function userPrompt(source: SourceDocument, map: (destination: string) => string, revision?: Revision): string {
  const parts = [`DOCUMENT\n${source.file} (${source.kind}), ${source.lang} to ${source.target}`];
  if (source.kind === "cv") {
    parts.push(`SOURCE CV JSON\n${block("source_cv", json(source.data))}`);
    return `${parts.join("\n\n")}\n`;
  }
  parts.push(`SOURCE FRONT MATTER\n${json({ title: source.title, excerpt: source.excerpt, tags: source.tags })}`);
  const moved = new Map<string, string>();
  for (const { kind, destination } of destinations(source.body)) {
    if (kind === "link" && map(destination) !== destination) moved.set(destination, map(destination));
  }
  const links = [...moved].map(([from, to]) => `- \`${from}\` is written \`${to}\``);
  parts.push(`LINKS TO OTHER DOCUMENTS\n${links.length ? links.join("\n") : "- none"}`);
  parts.push(`SOURCE MARKDOWN\n${block("source_markdown", source.body)}`);
  if (revision) {
    const { content, ...front } = revision.current;
    parts.push(`CURRENT TRANSLATION\nFront matter:\n${json(front)}\n${block("current_translation", content)}`);
    parts.push(`OWNER REVISION INSTRUCTIONS\n${revision.comments.map(commentText).join("\n\n")}`);
  }
  return `${parts.join("\n\n")}\n`;
}

/** What follows an answer that failed its checks: the exact findings, and a request to resolve them. */
export function repairPrompt(findings: string[]): string {
  return `${render(prompt("repair.md"), { findings: findings.map((finding) => `- ${finding}`).join("\n") })}\n`;
}

// ---------- the answer's shape ----------

export interface Schema {
  name: string;
  schema: Record<string, unknown>;
}

const object = (properties: Record<string, unknown>): Record<string, unknown> => ({
  type: "object",
  properties,
  required: Object.keys(properties),
  additionalProperties: false,
});

const STRING = { type: "string" };
const PROSE = { title: STRING, excerpt: STRING, tags: { type: "array", items: STRING }, content: STRING };

// The shape of a value, as JSON Schema: the CV's translation has the shape of the CV.
function shapeOf(value: unknown): Record<string, unknown> {
  if (Array.isArray(value)) return { type: "array", items: value.length ? entryShape(value) : STRING };
  if (typeof value === "object" && value !== null) {
    return object(Object.fromEntries(Object.entries(value).map(([key, child]) => [key, shapeOf(child)])));
  }
  return { type: value === null ? "null" : typeof value };
}

// The entries of a list as one shape: every key any entry has, required where every entry has it.
function entryShape(entries: unknown[]): Record<string, unknown> {
  const records = entries.filter(
    (entry): entry is Record<string, unknown> => typeof entry === "object" && entry !== null && !Array.isArray(entry),
  );
  if (records.length !== entries.length) return shapeOf(entries[0]);
  const properties: Record<string, unknown> = {};
  for (const record of records) for (const [key, child] of Object.entries(record)) properties[key] ??= shapeOf(child);
  const required = Object.keys(properties).filter((key) => records.every((record) => key in record));
  return { ...object(properties), required };
}

/** The structured output asked of the model. */
export function schemaFor(source: SourceDocument, { revise = false } = {}): Schema {
  if (source.kind === "cv") return { name: "cv_translation", schema: shapeOf(source.data) };
  if (!revise) return { name: "translation", schema: object(PROSE) };
  const comment = object({ id: { type: "integer" }, addressed: { type: "boolean" }, note: STRING });
  return { name: "revision", schema: object({ ...PROSE, comments: { type: "array", items: comment } }) };
}
