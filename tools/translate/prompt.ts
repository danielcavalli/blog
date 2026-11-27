// What each stage is told: the guidance as the system message, the document and what the earlier
// stages said about it as the user message.
//
// The guidance is the author's and lives in Markdown, which this file reads and never rewords:
//
//   guides/<locale>_localization_brief.md   how the target language should read
//   guides/<from>_to_<to>.md                the rules, glossary and protected names of a direction
//   guides/cv.md                            the names a CV keeps
//   .agents/skills/…/references/*.md        how the author writes (read in place: one copy)
//
// `prompts/` holds the old engine's stage prompts (`prompts/v2/*.md`), with `{{placeholders}}` where
// the guidance goes. A stage's prompt is `<kind>_<stage>.md` where there is one (the CV has all six,
// a presentation its own translate and revise) and `<stage>.md` otherwise, as the old registry chose.
// Around it, every stage gets the same LOCALIZATION AUTHORITY before and LOCALIZATION BOUNDARY after.
//
// The old prompts carried the document and the earlier stages' answers inline. Here those sections
// are the user message, in the order the old prompts had them, so the system message is guidance only.

import fs from "node:fs";
import path from "node:path";

import type { Comment } from "./comments.ts";
import type { Stage } from "./contracts.ts";
import { sorted } from "./digest.ts";
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

/** The file of a stage's prompt for a kind of document: its own where it has one, the shared one otherwise. */
export function templateFor(kind: SourceDocument["kind"], stage: Stage): string {
  const own = `${kind}_${stage}.md`;
  return fs.existsSync(path.join(HERE, "prompts", own)) ? own : `${stage}.md`;
}

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

// What fills the placeholders: the same for every stage of a document.
function guidance(source: SourceDocument): Record<string, string> {
  const rules = path.join(HERE, "guides", `${source.lang}_to_${source.target}.md`);
  const guide = sections(read(rules));
  const brief = path.join(HERE, "guides", `${source.target.replace("-", "_")}_localization_brief.md`);
  const cv = path.join(HERE, "guides", "cv.md");
  const kept = section(guide, "Do not translate", rules);
  return {
    source_locale: source.lang,
    target_locale: source.target,
    locale_direction: `${source.lang}->${source.target}`,
    localization_brief: read(brief),
    style_constraints: section(guide, "Style constraints", rules),
    borrowing_conventions: section(guide, "Borrowing conventions", rules),
    punctuation_conventions: section(guide, "Punctuation conventions", rules),
    discourse_conventions: section(guide, "Discourse conventions", rules),
    register_conventions: section(guide, "Register conventions", rules),
    review_checks: section(guide, "Review checks", rules),
    glossary_entries: section(guide, "Glossary", rules),
    // The human list only: a policy's proposed names are not added to it (ADR 017).
    do_not_translate_entities: source.kind === "cv" ? merged(kept, section(sections(read(cv)), "Do not translate", cv)) : merged(kept),
    writing_style_brief: writingStyleBrief(),
  };
}

/** The guidance for one stage of `source`: the system message. `owner`: the stage is the owner's revision. */
export function systemPrompt(source: SourceDocument, stage: Stage = "translate", { owner = false } = {}): string {
  const parts = [prompt("authority.md"), render(prompt(templateFor(source.kind, stage)), guidance(source)), prompt("boundary.md")];
  if (owner) parts.push(prompt("owner_revision.md"));
  const text = source.kind === "cv" ? JSON.stringify(source.data) : source.body;
  if (text.includes("mermaid")) parts.push(prompt("mermaid.md"));
  return `${parts.join("\n\n")}\n`;
}

/** A value as the old engine showed it to a stage: JSON with its keys in order, two spaces deep. */
export const json = (value: unknown): string => JSON.stringify(sorted(value), null, 2);

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

/** What a stage is given besides the source: the earlier stages' answers, and the owner's comments. */
export interface StageInputs {
  analysis?: unknown;
  policy?: unknown;
  /** The translation under work: a draft, a revision, or the owner's translation as it stands. */
  candidate?: unknown;
  /** Its heading: the critique and the revision see a translated candidate, the final review a localized one. */
  candidateLabel?: "TRANSLATED CANDIDATE JSON" | "LOCALIZED CANDIDATE JSON";
  critique?: unknown;
  /** The owner's open comments, when the run is his revision. */
  comments?: Comment[];
}

/** The document and what the stage is given about it: the user message. */
export function userPrompt(source: SourceDocument, map: (destination: string) => string, inputs: StageInputs = {}): string {
  const parts = [`DOCUMENT\n${source.file} (${source.kind}), ${source.lang} to ${source.target}`];
  if (source.kind !== "cv") {
    parts.push(`SOURCE FRONT MATTER\n${JSON.stringify({ title: source.title, excerpt: source.excerpt, tags: source.tags }, null, 2)}`);
    const moved = new Map<string, string>();
    for (const { kind, destination } of destinations(source.body)) {
      if (kind === "link" && map(destination) !== destination) moved.set(destination, map(destination));
    }
    const links = [...moved].map(([from, to]) => `- \`${from}\` is written \`${to}\``);
    parts.push(`LINKS TO OTHER DOCUMENTS\n${links.length ? links.join("\n") : "- none"}`);
  }
  if (inputs.analysis !== undefined) parts.push(`SOURCE ANALYSIS JSON (MODEL ADVICE)\n${json(inputs.analysis)}`);
  if (inputs.policy !== undefined) parts.push(`TERMINOLOGY POLICY JSON (MODEL PROPOSAL)\n${json(inputs.policy)}`);
  parts.push(
    source.kind === "cv"
      ? `SOURCE CV JSON\n${block("source_cv", JSON.stringify(source.data, null, 2))}`
      : `SOURCE MARKDOWN\n${block("source_markdown", source.body)}`,
  );
  if (inputs.candidate !== undefined) parts.push(`${inputs.candidateLabel ?? "TRANSLATED CANDIDATE JSON"}\n${json(inputs.candidate)}`);
  if (inputs.critique !== undefined) parts.push(`CRITIQUE JSON\n${json(inputs.critique)}`);
  if (inputs.comments?.length) parts.push(`OWNER REVISION INSTRUCTIONS\n${inputs.comments.map(commentText).join("\n\n")}`);
  return `${parts.join("\n\n")}\n`;
}

/** What follows an answer that failed its checks: the exact findings, and a request to resolve them. */
export function repairPrompt(findings: string[]): string {
  return `${render(prompt("repair.md"), { findings: findings.map((finding) => `- ${finding}`).join("\n") })}\n`;
}
