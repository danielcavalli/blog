// A document through the old engine's localization process, to the text of the file to write.
//
//   1. source analysis      the author's voice, rhetoric and intent             translation model
//   2. terminology policy   which terms stay in English, which are localized    translation model
//   3. translate            the draft, given the analysis and the policy        translation model
//      (the owner's revision: revise, given both, the translation and his comments, instead)
//   4. up to MAX_REVISION_PASSES passes of
//        critique           the critic's findings                                critic model
//        revise             only when the critique says it needs refinement      translation model
//        final review       accept and publish_ready, or the residual issues     critic model
//
// The document is done at the first final review that accepts it. If the last pass still rejects it,
// it fails: nothing is written, and the reviewer's residual issues are what the run reports.
//
// Every answer is validated against its stage's contract (contracts.ts), and a draft or a revision
// also against the deterministic checks (checks.ts). An answer that fails is sent back once with the
// exact findings; if the second answer fails too, the document fails and nothing is written.

import fs from "node:fs";
import path from "node:path";

import { checkCv, checkProse } from "./checks.ts";
import type { ProseAnswer, Verdict } from "./checks.ts";
import { markAddressed, openComments } from "./comments.ts";
import type { Comment } from "./comments.ts";
import {
  schemaFor,
  validateCritique,
  validateCvRevision,
  validateFinalReview,
  validateRevision,
  validateTerminologyPolicy,
  validateTranslation,
  validateVoiceIntent,
} from "./contracts.ts";
import type { CVRevisionOutput, FinalReviewOutput, RevisionOutput, Schema, Stage, Validated } from "./contracts.ts";
import { linkMapper, readMarkdown, readText, stateOf, toYaml } from "./documents.ts";
import type { CvDocument, MarkdownFile, ProseDocument, SourceDocument } from "./documents.ts";
import { ask } from "./hub.ts";
import type { Answer, HubOptions, Message, Question, Usage } from "./hub.ts";
import { lf } from "./markdown.ts";
import { repairPrompt, systemPrompt, userPrompt } from "./prompt.ts";
import type { StageInputs } from "./prompt.ts";
import { DocumentRun } from "./runs.ts";
import type { StageRecord } from "./runs.ts";

/** How many passes of critique, revision and final review a document gets: the old engine's `_max_revision_passes`. */
export const MAX_REVISION_PASSES = 2;

export interface Settings {
  /** The model that analyses, drafts and revises, and its reasoning effort. */
  model: string;
  effort: string;
  /** The model that critiques and gives the final review, and its reasoning effort. */
  criticModel: string;
  criticEffort: string;
  maxTokens: number;
  /** The day to record as `translated_at`: YYYY-MM-DD. */
  today: string;
  hub?: HubOptions;
  /** The call to the model. Tests put their own here. */
  ask?: (question: Question, options?: HubOptions) => Promise<Answer>;
  /** Told what happens along the way: a repair, a retry. */
  log?: (line: string) => void;
  /** A file to append every question and answer to, one JSON object per line. */
  trace?: string;
}

/** An answer that failed its checks twice. */
export class CheckError extends Error {
  findings: string[];
  /** What the two calls cost. */
  usages: Usage[];
  /** The conversation, the refused answers included. */
  messages: Message[];
  constructor(findings: string[], usages: Usage[], messages: Message[] = []) {
    super(`The translation failed its checks after one repair:\n${findings.map((finding) => `  - ${finding}`).join("\n")}`);
    this.name = "CheckError";
    this.findings = findings;
    this.usages = usages;
    this.messages = messages;
  }
}

/** A document the final review still rejected after the last pass. */
export class RejectedError extends Error {
  review: FinalReviewOutput;
  passes: number;
  constructor(review: FinalReviewOutput, passes: number) {
    const issues = review.residual_issues.length ? review.residual_issues : ["(the reviewer listed none, and did not accept)"];
    super(
      `The final review rejected the translation after ${passes} of ${MAX_REVISION_PASSES} passes; its residual issues:\n` +
        issues.map((issue) => `  - ${issue}`).join("\n"),
    );
    this.name = "RejectedError";
    this.review = review;
    this.passes = passes;
  }
}

export interface Outcome {
  answer: unknown;
  /** What each call cost, in order. */
  usages: Usage[];
  warnings: string[];
  /** The findings that sent the first answer back, when it was. */
  repaired: string[];
  /** The conversation as it ended. */
  messages: Message[];
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
  settings: Pick<Settings, "model" | "effort" | "maxTokens" | "hub" | "ask" | "log" | "trace">,
): Promise<Outcome> {
  const messages: Message[] = [
    { role: "system", content: job.system },
    { role: "user", content: job.user },
  ];
  const usages: Usage[] = [];
  let repaired: string[] = [];
  for (let attempt = 0; ; attempt++) {
    const question = { model: settings.model, effort: settings.effort, maxTokens: settings.maxTokens, messages, schema: job.schema };
    const answer = await (settings.ask ?? ask)(question, {
      ...settings.hub,
      onRetry: (reason, wait) => settings.log?.(`${reason}; again in ${Math.round(wait / 1000)}s`),
    });
    if (settings.trace) {
      fs.appendFileSync(settings.trace, `${JSON.stringify({ at: new Date().toISOString(), question, answer })}\n`);
    }
    usages.push(answer.usage);
    const parsed = parse(answer.content);
    const verdict = "error" in parsed ? { findings: [parsed.error], warnings: [] } : job.check(parsed.value);
    if (!verdict.findings.length && "value" in parsed) {
      return { answer: parsed.value, usages, warnings: verdict.warnings, repaired, messages: [...messages, { role: "assistant", content: answer.content }] };
    }
    if (attempt > 0) throw new CheckError(verdict.findings, usages, [...messages, { role: "assistant", content: answer.content }]);
    settings.log?.(`failed ${verdict.findings.length} check(s), asking for a repair:`);
    for (const finding of verdict.findings) settings.log?.(`  - ${finding}`);
    repaired = verdict.findings;
    messages.push({ role: "assistant", content: answer.content }, { role: "user", content: repairPrompt(verdict.findings) });
  }
}

// ---------- the file to write ----------

const stamp = (settings: Pick<Settings, "model" | "effort" | "today">) => ({
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
  settings: Pick<Settings, "model" | "effort" | "today">,
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
export function renderCv(source: CvDocument, answer: unknown, settings: Pick<Settings, "model" | "effort" | "today">): string {
  const head = { translation_of: source.file, source_digest: source.digest, ...stamp(settings) };
  const lines = Object.entries(head).map(([key, value]) => `# ${key}: ${value}`);
  const note = `# The CV in ${source.target}: a translation of ${source.file}. \`npm run translate\` writes this file; edit the source.`;
  return `${note}\n${lines.join("\n")}\n\n${toYaml(ordered(source.data, answer))}`;
}

// ---------- the stages ----------

/** The translation under work: a post's title, excerpt, tags and body, or the CV. */
export type Candidate = ProseAnswer | Record<string, unknown>;

/** The owner's revision: his translation as it stands, and his open comments on it. */
export interface OwnerRevision {
  current: ProseAnswer;
  comments: Comment[];
}

interface Context {
  source: SourceDocument;
  map: (destination: string) => string;
  settings: Settings;
  run: DocumentRun;
  /** The owner's comments: every stage of his revision sees them, as the old engine's did. */
  comments?: Comment[];
}

type Checked<T> = Verdict & { value?: T };

// A contract, and then what else the value must pass.
function contract<T>(validate: (answer: unknown) => Validated<T>, then?: (value: T) => Verdict): (answer: unknown) => Checked<T> {
  return (answer) => {
    const validated = validate(answer);
    if ("finding" in validated) return { findings: [validated.finding], warnings: [] };
    const more = then?.(validated.value) ?? { findings: [], warnings: [] };
    return { ...more, value: validated.value };
  };
}

// One stage: its prompt, its call (and one repair), its record in the run.
async function step<T>(
  ctx: Context,
  stage: Stage,
  pass: number | null,
  inputs: StageInputs,
  check: (answer: unknown) => Checked<T>,
  { critic = false, owner = false } = {},
): Promise<{ value: T; warnings: string[] }> {
  const [model, effort] = critic ? [ctx.settings.criticModel, ctx.settings.criticEffort] : [ctx.settings.model, ctx.settings.effort];
  const record: StageRecord = { stage, pass, ...(owner ? { owner } : {}), model, effort, usages: [], repaired: [], warnings: [] };
  const system = systemPrompt(ctx.source, stage, { owner });
  const user = userPrompt(ctx.source, ctx.map, { ...inputs, comments: ctx.comments });
  try {
    const outcome = await converse({ system, user, schema: schemaFor(stage, ctx.source, { owner }), check }, { ...ctx.settings, model, effort });
    const { value } = check(outcome.answer);
    Object.assign(record, { usages: outcome.usages, repaired: outcome.repaired, warnings: outcome.warnings, output: value });
    ctx.run.add(record, outcome.messages);
    return { value: value as T, warnings: outcome.warnings };
  } catch (error) {
    record.error = error instanceof Error ? error.message : String(error);
    if (error instanceof CheckError) Object.assign(record, { usages: error.usages, findings: error.findings });
    ctx.run.add(record, error instanceof CheckError ? error.messages : [{ role: "system", content: system }, { role: "user", content: user }]);
    throw error;
  }
}

/** Whether a final review lets the document be written: it accepts, says publish-ready, and leaves no residual issue. */
export const accepted = (review: FinalReviewOutput): boolean => review.accept && review.publish_ready && review.residual_issues.length === 0;

export interface Localized {
  candidate: Candidate;
  /** The checks' warnings about the accepted text. */
  warnings: string[];
  /** The pass whose final review accepted it. */
  passes: number;
  review: FinalReviewOutput;
  /** Each comment of the owner's, as his revision left it. */
  handled: Handled[];
  /** What each call cost, in order. */
  usages: Usage[];
}

export interface Handled {
  comment: Comment;
  /** Whether the text now does what the comment asks. If not, the comment stays open. */
  addressed: boolean;
  note: string;
}

interface OwnerAnswer extends RevisionOutput {
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

const prose = ({ title, excerpt, tags, content }: ProseAnswer): ProseAnswer => ({ title, excerpt, tags, content });

/**
 * The whole process for one document. Returns the accepted text; throws `RejectedError` when the
 * last pass's final review still rejects it, and `CheckError` or `HubError` when a stage fails.
 */
export async function localize(
  source: SourceDocument,
  sources: SourceDocument[],
  settings: Settings,
  { owner, run = new DocumentRun() }: { owner?: OwnerRevision; run?: DocumentRun } = {},
): Promise<Localized> {
  if (owner && source.kind === "cv") throw new Error("the owner's revision works on a Markdown translation");
  const map = linkMapper(source, sources);
  const ctx: Context = { source, map, settings, run, comments: owner?.comments };
  const checkProduced = (value: unknown): Verdict =>
    source.kind === "cv" ? checkCv(source.data, value) : checkProse({ ...source, mapLink: map }, value);

  const analysis = (await step(ctx, "source_analysis", null, {}, contract(validateVoiceIntent))).value;
  const policy = (await step(ctx, "terminology_policy", null, { analysis }, contract(validateTerminologyPolicy))).value;

  let current: Candidate;
  let warnings: string[];
  let handled: Handled[] = [];
  if (owner) {
    const validateOwner = (answer: unknown): Validated<OwnerAnswer> => {
      const validated = validateRevision(answer);
      return "finding" in validated ? validated : { value: { ...validated.value, comments: (answer as OwnerAnswer).comments } };
    };
    const check = contract(validateOwner, (value) => {
      const verdict = checkProduced(value);
      return verdict.findings.length ? verdict : { findings: accounted(value, owner.comments, owner.current), warnings: verdict.warnings };
    });
    const inputs = { analysis, policy, candidate: owner.current };
    const revised = await step(ctx, "revise", null, inputs, check, { owner: true });
    handled = owner.comments.map((comment): Handled => {
      const entry = revised.value.comments.find((candidate) => candidate.id === comment.id)!;
      return { comment, addressed: entry.addressed, note: entry.note };
    });
    [current, warnings] = [prose(revised.value), revised.warnings];
  } else if (source.kind === "cv") {
    const draft = await step(ctx, "translate", null, { analysis, policy }, (answer) => ({ ...checkProduced(answer), value: answer as Candidate }));
    [current, warnings] = [draft.value, draft.warnings];
  } else {
    const draft = await step(ctx, "translate", null, { analysis, policy }, contract(validateTranslation, checkProduced));
    [current, warnings] = [draft.value, draft.warnings];
  }

  let review: FinalReviewOutput | undefined;
  for (let pass = 1; pass <= MAX_REVISION_PASSES; pass++) {
    const critique = (await step(ctx, "critique", pass, { analysis, policy, candidate: current }, contract(validateCritique), { critic: true })).value;
    let revised = current;
    if (critique.needs_refinement) {
      const inputs = { analysis, policy, candidate: current, critique };
      if (source.kind === "cv") {
        const result = await step(ctx, "revise", pass, inputs, contract(validateCvRevision, (value: CVRevisionOutput) => checkProduced(value.revised_cv)));
        [revised, warnings] = [result.value.revised_cv, result.warnings];
      } else {
        const result = await step(ctx, "revise", pass, inputs, contract(validateRevision, checkProduced));
        [revised, warnings] = [prose(result.value), result.warnings];
      }
    }
    const inputs: StageInputs = { candidate: revised, candidateLabel: "LOCALIZED CANDIDATE JSON" };
    review = (await step(ctx, "final_review", pass, inputs, contract(validateFinalReview), { critic: true })).value;
    if (accepted(review)) return { candidate: revised, warnings, passes: pass, review, handled, usages: run.usages };
    current = revised;
  }
  throw new RejectedError(review!, MAX_REVISION_PASSES);
}

// ---------- the two jobs ----------

export interface Translated extends Localized {
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
  run?: DocumentRun,
): Promise<Translated> {
  const result = await localize(source, sources, settings, { run });
  if (source.kind === "cv") return { ...result, text: renderCv(source, result.candidate, settings) };
  const before = existing(root, source);
  const text = renderProse(source, result.candidate as ProseAnswer, before === null ? null : readMarkdown(before), settings);
  return { ...result, text };
}

/** The open comments in a translation's margin, and the translation as it stands. Refuses one that is missing or stale. */
export function ownerRevision(root: string, source: ProseDocument): { previous: MarkdownFile; revision: OwnerRevision } {
  const state = stateOf(root, source);
  if (state.status === "missing") throw new Error(`${source.translation} does not exist: translate ${source.file} first`);
  if (state.status === "stale") {
    throw new Error(
      `${source.translation} is stale (${state.note ?? `${source.file} changed since it was translated`}): ` +
        "translate it first; the comments stay in its margin",
    );
  }
  const previous = readMarkdown(existing(root, source)!);
  const current: ProseAnswer = {
    title: previous.meta.title == null ? "" : String(previous.meta.title),
    excerpt: previous.meta.excerpt == null ? "" : String(previous.meta.excerpt),
    tags: Array.isArray(previous.meta.tags) ? previous.meta.tags.map(String) : [],
    content: previous.body,
  };
  return { previous, revision: { current, comments: openComments(previous.trailer) } };
}

export interface Revised extends Translated {
  handled: Handled[];
}

/**
 * Revise a translation by the open comments in its margin, through the whole process. Returns null
 * when there are none. The comments the revision says it addressed go from `open` to `addressed`;
 * the rest of the trailer is kept.
 */
export async function revise(
  root: string,
  source: ProseDocument,
  sources: SourceDocument[],
  settings: Settings,
  run?: DocumentRun,
): Promise<Revised | null> {
  const { previous, revision } = ownerRevision(root, source);
  if (!revision.comments.length) return null;
  const result = await localize(source, sources, settings, { owner: revision, run });
  const trailer = markAddressed(
    previous.trailer,
    result.handled.filter((entry) => entry.addressed).map((entry) => entry.comment.id),
  );
  return { ...result, text: renderProse(source, result.candidate as ProseAnswer, { meta: previous.meta, trailer }, settings) };
}
