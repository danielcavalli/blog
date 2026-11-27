// A document through the model and its checks, to the text of the file to write.
//
// The model answers once. If the answer fails a check it is asked once more, with the exact
// findings; if that answer fails too, the document fails and nothing is written.

import fs from "node:fs";
import path from "node:path";

import { checkCv, checkProse } from "./checks.ts";
import type { ProseAnswer, Verdict } from "./checks.ts";
import { markAddressed, openComments } from "./comments.ts";
import type { Comment } from "./comments.ts";
import { linkMapper, readMarkdown, readText, stateOf, toYaml } from "./documents.ts";
import type { CvDocument, MarkdownFile, ProseDocument, SourceDocument } from "./documents.ts";
import { ask } from "./hub.ts";
import type { Answer, HubOptions, Message, Question, Usage } from "./hub.ts";
import { lf } from "./markdown.ts";
import { repairPrompt, schemaFor, systemPrompt, userPrompt } from "./prompt.ts";
import type { Schema } from "./prompt.ts";

export interface Settings {
  model: string;
  effort: string;
  maxTokens: number;
  /** The day to record as `translated_at`: YYYY-MM-DD. */
  today: string;
  hub?: HubOptions;
  /** The call to the model. Tests put their own here. */
  ask?: (question: Question, options?: HubOptions) => Promise<Answer>;
  /** Told what happens along the way: a repair, a retry. */
  log?: (line: string) => void;
}

/** An answer that failed its checks twice. */
export class CheckError extends Error {
  findings: string[];
  /** What the two calls cost. */
  usages: Usage[];
  constructor(findings: string[], usages: Usage[]) {
    super(`The translation failed its checks after one repair:\n${findings.map((finding) => `  - ${finding}`).join("\n")}`);
    this.name = "CheckError";
    this.findings = findings;
    this.usages = usages;
  }
}

export interface Outcome {
  answer: unknown;
  /** What each call cost, in order. */
  usages: Usage[];
  warnings: string[];
}

// The answer as a value. Some models wrap the JSON in a code fence whatever they are told.
function parse(content: string): { value: unknown } | { error: string } {
  const unfenced = content.trim().replace(/^```(?:json)?\s*\n([\s\S]*?)\n```$/, "$1");
  try {
    return { value: JSON.parse(unfenced) as unknown };
  } catch (error) {
    return { error: `The answer is not valid JSON: ${(error as Error).message}` };
  }
}

/** Ask, check, and once ask again with the findings. Throws `CheckError` when the second answer fails too. */
export async function converse(
  job: { system: string; user: string; schema: Schema; check: (answer: unknown) => Verdict },
  settings: Settings,
): Promise<Outcome> {
  const messages: Message[] = [
    { role: "system", content: job.system },
    { role: "user", content: job.user },
  ];
  const usages: Usage[] = [];
  for (let attempt = 0; ; attempt++) {
    const answer = await (settings.ask ?? ask)(
      { model: settings.model, effort: settings.effort, maxTokens: settings.maxTokens, messages, schema: job.schema },
      { ...settings.hub, onRetry: (reason, wait) => settings.log?.(`${reason}; again in ${Math.round(wait / 1000)}s`) },
    );
    usages.push(answer.usage);
    const parsed = parse(answer.content);
    const verdict = "error" in parsed ? { findings: [parsed.error], warnings: [] } : job.check(parsed.value);
    if (!verdict.findings.length && "value" in parsed) return { answer: parsed.value, usages, warnings: verdict.warnings };
    if (attempt > 0) throw new CheckError(verdict.findings, usages);
    settings.log?.(`failed ${verdict.findings.length} check(s), asking for a repair:`);
    for (const finding of verdict.findings) settings.log?.(`  - ${finding}`);
    messages.push({ role: "assistant", content: answer.content }, { role: "user", content: repairPrompt(verdict.findings) });
  }
}

// ---------- the file to write ----------

const stamp = (settings: Settings) => ({
  translated_by: `${settings.model} (${settings.effort}), via mare-hub`,
  translated_at: settings.today,
});

// The fields this tool owns in a translation's front matter. Anything else found there is kept.
const OWNED = new Set(["title", "excerpt", "tags", "lang", "translation_of", "source_digest", "translated_by", "translated_at"]);

/** A translated post or page as a file: its front matter, its body, and the trailer it already had. */
export function renderProse(
  source: ProseDocument,
  answer: ProseAnswer,
  previous: Pick<MarkdownFile, "meta" | "trailer"> | null,
  settings: Settings,
): string {
  const front: Record<string, unknown> = { title: answer.title };
  if ("excerpt" in source.meta) front.excerpt = answer.excerpt;
  if ("tags" in source.meta) front.tags = answer.tags;
  Object.assign(front, {
    lang: source.target,
    translation_of: path.posix.basename(source.file),
    source_digest: source.digest,
    ...stamp(settings),
  });
  for (const [key, value] of Object.entries(previous?.meta ?? {})) if (!OWNED.has(key)) front[key] = value;
  const text = `---\n${toYaml(front)}---\n\n${lf(answer.content).trim()}\n`;
  return previous?.trailer ? `${text}\n${previous.trailer}` : text;
}

// A translated value with its keys in the source's order, whatever order the model used.
function ordered(source: unknown, translated: unknown): unknown {
  if (Array.isArray(source) && Array.isArray(translated)) return translated.map((item, index) => ordered(source[index], item));
  if (typeof source !== "object" || source === null || typeof translated !== "object" || translated === null) return translated;
  const [from, to] = [source as Record<string, unknown>, translated as Record<string, unknown>];
  return Object.fromEntries(Object.keys(from).map((key) => [key, ordered(from[key], to[key])]));
}

/** The translated CV as a file. What it translates and from which text is in the comments at its head. */
export function renderCv(source: CvDocument, answer: unknown, settings: Settings): string {
  const head = { translation_of: source.file, source_digest: source.digest, ...stamp(settings) };
  const lines = Object.entries(head).map(([key, value]) => `# ${key}: ${value}`);
  const note = `# The CV in ${source.target}: a translation of ${source.file}. \`npm run translate\` writes this file; edit the source.`;
  return `${note}\n${lines.join("\n")}\n\n${toYaml(ordered(source.data, answer))}`;
}

// ---------- the two jobs ----------

export interface Translated extends Outcome {
  /** The whole file to write at the translation's path. */
  text: string;
}

const existing = (root: string, source: SourceDocument): string | null => {
  const file = path.join(root, source.translation);
  return fs.existsSync(file) ? readText(file) : null;
};

/** Translate a source from scratch. An existing translation gives only its trailer and its own front matter fields. */
export async function translate(
  root: string,
  source: SourceDocument,
  sources: SourceDocument[],
  settings: Settings,
): Promise<Translated> {
  const map = linkMapper(source, sources);
  const outcome = await converse(
    {
      system: systemPrompt(source),
      user: userPrompt(source, map),
      schema: schemaFor(source),
      check: (answer) =>
        source.kind === "cv" ? checkCv(source.data, answer) : checkProse({ ...source, mapLink: map }, answer),
    },
    settings,
  );
  if (source.kind === "cv") return { ...outcome, text: renderCv(source, outcome.answer, settings) };
  const before = existing(root, source);
  const text = renderProse(source, outcome.answer as ProseAnswer, before === null ? null : readMarkdown(before), settings);
  return { ...outcome, text };
}

export interface Handled {
  comment: Comment;
  /** Whether the text now does what the comment asks. If not, the comment stays open. */
  addressed: boolean;
  note: string;
}

export interface Revised extends Translated {
  handled: Handled[];
}

interface RevisionAnswer extends ProseAnswer {
  comments: { id: number; addressed: boolean; note: string }[];
}

// Every open comment answered once, and a change in the text if any is said to be addressed.
function accounted(answer: unknown, comments: Comment[], current: ProseAnswer): string[] {
  const entries = (answer as { comments?: unknown }).comments;
  if (!Array.isArray(entries)) return ['Field "comments" must be a list with one entry per comment'];
  const findings: string[] = [];
  const seen = new Map<number, number>();
  for (const entry of entries as Record<string, unknown>[]) {
    if (typeof entry?.id !== "number" || typeof entry.addressed !== "boolean" || typeof entry.note !== "string") {
      return ['Every entry of "comments" must have an integer `id`, a boolean `addressed` and a string `note`'];
    }
    seen.set(entry.id, (seen.get(entry.id) ?? 0) + 1);
  }
  for (const { id } of comments) {
    if (seen.get(id) !== 1) findings.push(`"comments" must have exactly one entry for comment ${id}, and has ${seen.get(id) ?? 0}`);
    seen.delete(id);
  }
  for (const id of seen.keys()) findings.push(`"comments" has an entry for comment ${id}, which is not one of the open comments`);
  const { title, excerpt, tags, content } = answer as ProseAnswer;
  const unchanged =
    title === current.title &&
    excerpt === current.excerpt &&
    JSON.stringify(tags) === JSON.stringify(current.tags) &&
    lf(content).trim() === current.content;
  if (unchanged && (entries as { addressed: boolean }[]).some((entry) => entry.addressed)) {
    findings.push("The answer says comments are addressed and changes nothing in the translation");
  }
  return findings;
}

/**
 * Revise a translation by the open comments in its margin. Returns null when there are none.
 * The comments the model says it addressed go from `open` to `addressed`; the rest of the trailer is kept.
 */
export async function revise(
  root: string,
  source: ProseDocument,
  sources: SourceDocument[],
  settings: Settings,
): Promise<Revised | null> {
  const state = stateOf(root, source);
  if (state.status === "missing") throw new Error(`${source.translation} does not exist: translate ${source.file} first`);
  if (state.status === "stale") {
    throw new Error(
      `${source.translation} is stale (${state.note ?? `${source.file} changed since it was translated`}): ` +
        "translate it first; the comments stay in its margin",
    );
  }
  const previous = readMarkdown(existing(root, source)!);
  const comments = openComments(previous.trailer);
  if (!comments.length) return null;
  const current: ProseAnswer = {
    title: previous.meta.title == null ? "" : String(previous.meta.title),
    excerpt: previous.meta.excerpt == null ? "" : String(previous.meta.excerpt),
    tags: Array.isArray(previous.meta.tags) ? previous.meta.tags.map(String) : [],
    content: previous.body,
  };
  const map = linkMapper(source, sources);
  const outcome = await converse(
    {
      system: systemPrompt(source, { revise: true }),
      user: userPrompt(source, map, { current, comments }),
      schema: schemaFor(source, { revise: true }),
      check: (answer) => {
        const verdict = checkProse({ ...source, mapLink: map }, answer);
        if (verdict.findings.length) return verdict;
        return { findings: accounted(answer, comments, current), warnings: verdict.warnings };
      },
    },
    settings,
  );
  const answer = outcome.answer as RevisionAnswer;
  const handled = comments.map((comment): Handled => {
    const entry = answer.comments.find((candidate) => candidate.id === comment.id)!;
    return { comment, addressed: entry.addressed, note: entry.note };
  });
  const trailer = markAddressed(
    previous.trailer,
    handled.filter((entry) => entry.addressed).map((entry) => entry.comment.id),
  );
  return { ...outcome, handled, text: renderProse(source, answer, { meta: previous.meta, trailer }, settings) };
}
