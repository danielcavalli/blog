#!/usr/bin/env node
// Translates the blog's documents into its other language, through the Maré Hub.
//
//   npm run translate -- status [--json]            where every translation stands; exit 1 unless all are current
//   npm run translate -- <file>… | --all            translate what is missing or stale (--force: a current one too)
//   npm run translate -- revise <translation file>  revise a translation by the open comments in its margin
//
//   --model <id>           the model that analyses, drafts and revises (default gpt-5.6-sol)
//   --effort <level>       its reasoning effort (default high)
//   --critic-model <id>    the model that critiques and gives the final review (default claude-opus-5-5)
//   --critic-effort <level> its reasoning effort (default medium)
//   --max-tokens <n>       the most a call may answer with, thinking included (default 64000)
//   --dry-run              say what would be done, call nothing, write nothing
//   --out <dir>            write under <dir> instead of the repository (for trials)
//
// A document is a post, a page or the CV: `posts/<slug>.md`, `pages/about.md`, `cv_data.yaml`. Each
// goes through the old engine's process (translate.ts): source analysis, terminology policy, draft,
// then up to two passes of critique, revision and final review. What every stage said is written
// under `.translate-runs/<run id>/` (runs.ts), which git ignores. What a translation was made from is
// recorded in it as `source_digest` (see digest.ts).
//
// MARE_HUB names another Hub than the one on the tailnet. TRANSLATE_TRACE=<file> appends every
// question and the model's whole answer to that file, one JSON object per line: the way to see what
// a model was told and what it said, above all when its answer was refused.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

import { openComments } from "./comments.ts";
import type { CVRevisionOutput, CritiqueOutput, FinalReviewOutput, RevisionOutput } from "./contracts.ts";
import { discover, readMarkdown, readText, stateOf, writeText } from "./documents.ts";
import type { SourceDocument } from "./documents.ts";
import { DEFAULT_CRITIC_EFFORT, DEFAULT_CRITIC_MODEL, DEFAULT_EFFORT, DEFAULT_MAX_TOKENS, DEFAULT_MODEL } from "./hub.ts";
import type { HubOptions, Usage } from "./hub.ts";
import { DocumentRun, RUNS_FOLDER, runId } from "./runs.ts";
import type { StageRecord } from "./runs.ts";
import { MAX_REVISION_PASSES, RejectedError, accepted, revise, translate } from "./translate.ts";
import type { Localized, Settings } from "./translate.ts";

export interface Io {
  /** The repository whose documents are translated. */
  root: string;
  /** Where file arguments are relative to. */
  cwd: string;
  out: (line: string) => void;
  err: (line: string) => void;
  hub?: HubOptions;
  ask?: Settings["ask"];
  today?: string;
  trace?: string;
  /** The run's folder name under `.translate-runs/`. Default: when it started. */
  runId?: string;
}

const USAGE = `usage: npm run translate -- status [--json]
       npm run translate -- <file>… | --all [--force] [options]
       npm run translate -- revise <translation file> [options]
       npm run translate -- stamp <file>…

options: --model <id>  --effort <level>  --critic-model <id>  --critic-effort <level>
         --max-tokens <n>  --dry-run  --out <dir>`;

class UsageError extends Error {}

const today = (): string => {
  const now = new Date();
  const two = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${two(now.getMonth() + 1)}-${two(now.getDate())}`;
};

const number = (n: unknown): string => (typeof n === "number" ? n.toLocaleString("en-US") : "?");

/**
 * What calls cost, in one line. The Hub prices metered models; for one it serves from a subscription
 * (the default, `gpt-5.6-sol`, is one) its answer carries tokens and no `cost_usd`.
 */
export function costLine(usages: Usage[]): string {
  const sum = (key: string) => usages.reduce((total, usage) => total + (typeof usage[key] === "number" ? (usage[key] as number) : 0), 0);
  const priced = usages.every((usage) => typeof usage.cost_usd === "number");
  const calls = usages.length === 1 ? "1 call" : `${usages.length} calls`;
  return `${calls}, ${number(sum("prompt_tokens"))} tokens in, ${number(sum("completion_tokens"))} out, ${priced ? `$${sum("cost_usd").toFixed(4)}` : "no cost reported by the Hub"}`;
}

const LABELS: Record<StageRecord["stage"], string> = {
  source_analysis: "source analysis",
  terminology_policy: "terminology policy",
  translate: "translate",
  critique: "critique",
  revise: "revise",
  final_review: "final review",
};

const plural = (n: number, word: string): string => `${n} ${word}${n === 1 ? "" : "s"}`;

/** A final review's scores, as the summary says them. */
export const scores = (review: FinalReviewOutput): string =>
  `voice ${review.voice_score}, terminology ${review.terminology_score}, locale naturalness ${review.locale_naturalness_score} (confidence ${review.confidence})`;

// What a stage's answer comes to, in a few words.
function verdict(record: StageRecord): string {
  if (record.error !== undefined) return "failed";
  if (record.stage === "critique") {
    const critique = record.output as CritiqueOutput;
    return `${critique.needs_refinement ? "needs refinement" : "no refinement needed"} (score ${critique.score}, ${plural(critique.findings.length, "finding")})`;
  }
  if (record.stage === "final_review") {
    const review = record.output as FinalReviewOutput;
    const issues = review.residual_issues.length ? `, ${plural(review.residual_issues.length, "residual issue")}` : "";
    return `${accepted(review) ? "accepted" : "not accepted"}: ${scores(review)}${issues}`;
  }
  if (record.stage === "revise" && !record.owner) {
    const output = record.output as RevisionOutput | CVRevisionOutput;
    const [applied, declined] =
      "revision_report" in output
        ? [output.revision_report.applied_findings.length, output.revision_report.declined_findings.length]
        : [output.applied_feedback.length, output.declined_feedback.length];
    return `${applied} applied, ${declined} declined`;
  }
  return "";
}

/** One stage, as the run prints it when it finishes. */
export function stageLine(record: StageRecord): string {
  const label = `${record.pass === null ? "" : `pass ${record.pass} `}${LABELS[record.stage]}${record.owner ? " (owner's comments)" : ""}`;
  const said = verdict(record);
  const cost = record.usages.length ? `${costLine(record.usages)}${record.repaired.length ? " after one repair" : ""}` : "";
  return `  ${label.padEnd(26)} ${[cost, said].filter(Boolean).join("; ")}`;
}

// The source a file argument names: the source itself, or its translation.
function find(io: Io, sources: SourceDocument[], argument: string): SourceDocument {
  for (const base of [io.cwd, io.root]) {
    const file = path.relative(io.root, path.resolve(base, argument)).split(path.sep).join("/");
    const source = sources.find((candidate) => candidate.file === file || candidate.translation === file);
    if (source) return source;
  }
  throw new UsageError(`${argument} is not a document of this repository (posts/*.md, pages/*.md, cv_data.yaml)`);
}

function status(io: Io, sources: SourceDocument[], asJson: boolean): number {
  const rows = sources.map((source) => ({ source, state: stateOf(io.root, source) }));
  if (asJson) {
    io.out(
      JSON.stringify(
        rows.map(({ source, state }) => ({
          source: source.file,
          translation: source.translation,
          kind: source.kind,
          from: source.lang,
          to: source.target,
          status: state.status,
          source_digest: source.digest,
          recorded_digest: state.recorded,
          ...(state.note ? { note: state.note } : {}),
        })),
        null,
        2,
      ),
    );
  } else {
    for (const { source, state } of rows) {
      io.out(`${state.status.padEnd(8)} ${source.file} -> ${source.translation}${state.note ? ` (${state.note})` : ""}`);
    }
    const count = (name: string) => rows.filter(({ state }) => state.status === name).length;
    io.out(`${count("current")} current, ${count("stale")} stale, ${count("missing")} missing`);
  }
  return rows.every(({ state }) => state.status === "current") ? 0 : 1;
}

interface Flags {
  settings: Settings;
  dryRun: boolean;
  out: string | null;
  runId: string;
}

// Where a translation is written: the repository, or the same path under --out.
const destination = (io: Io, flags: Flags, source: SourceDocument): string =>
  path.join(flags.out ?? io.root, source.translation);

// A path as the reader would type it: from where they are, when it is under there.
const shown = (io: Io, file: string): string => {
  const relative = path.relative(io.cwd, file);
  return relative && !relative.startsWith("..") && !path.isAbsolute(relative) ? relative : file;
};

// A document's run: its stages printed as they finish, and kept under .translate-runs/.
function documentRun(io: Io, flags: Flags, source: SourceDocument): DocumentRun {
  const dir = path.join(flags.out ?? io.root, RUNS_FOLDER, flags.runId, source.file.replace(/\.[^./]+$/, ""));
  return new DocumentRun(dir, (record) => io.out(stageLine(record)));
}

const models = (settings: Settings): string =>
  `${settings.model} (${settings.effort}), critic ${settings.criticModel} (${settings.criticEffort})`;

// The calls a document takes: analysis, policy and draft, then 2 or 3 a pass.
const PLAN =
  `${3 + 2} to ${3 + 3 * MAX_REVISION_PASSES} calls: source analysis, terminology policy, draft, then up to ${MAX_REVISION_PASSES} passes ` +
  "of critique, revision (when the critique asks) and final review";

// How a document's run ended, in its summary and on the terminal.
function finished(io: Io, run: DocumentRun, result: Localized | null, error: unknown, what: string): void {
  const review = result?.review ?? (error instanceof RejectedError ? error.review : null);
  if (run.stages.length) {
    run.finish({
      document: what,
      accepted: result !== null,
      passes: result?.passes ?? (error instanceof RejectedError ? error.passes : null),
      max_passes: MAX_REVISION_PASSES,
      final_review: review,
      ...(result?.handled.length ? { comments: result.handled.map(({ comment, addressed, note }) => ({ id: comment.id, addressed, note })) } : {}),
      ...(error === null ? {} : { error: error instanceof Error ? error.message : String(error) }),
    });
  }
  if (result) {
    io.out(`  accepted in pass ${result.passes} of ${MAX_REVISION_PASSES}: ${scores(result.review)}`);
    return;
  }
  io.err(`${what}: ${error instanceof Error ? error.message : String(error)}`);
  if (run.usages.length) io.err(`  ${costLine(run.usages)}; nothing was written`);
  outputs(io, run);
}

// Where the stages' answers are.
const outputs = (io: Io, run: DocumentRun): void => {
  if (run.dir && fs.existsSync(run.dir)) io.out(`  stage outputs: ${shown(io, run.dir)}`);
};

async function translateAll(io: Io, sources: SourceDocument[], chosen: SourceDocument[], force: boolean, flags: Flags): Promise<number> {
  let failed = 0;
  for (const source of chosen) {
    const state = stateOf(io.root, source);
    if (state.status === "current" && !force) {
      io.out(`current  ${source.file} -> ${source.translation}: nothing to do (--force translates it again)`);
      continue;
    }
    const to = destination(io, flags, source);
    if (flags.dryRun) {
      io.out(`${state.status.padEnd(8)} ${source.file}: would translate into ${shown(io, to)} with ${models(flags.settings)}; ${PLAN}`);
      continue;
    }
    io.out(`${state.status.padEnd(8)} ${source.file}: translating with ${models(flags.settings)}…`);
    const run = documentRun(io, flags, source);
    try {
      const result = await translate(io.root, source, sources, flags.settings, run);
      writeText(to, result.text);
      finished(io, run, result, null, source.file);
      for (const warning of result.warnings) io.err(`  warning: ${warning}`);
      io.out(`  wrote ${shown(io, to)}: ${costLine(result.usages)}`);
      outputs(io, run);
    } catch (error) {
      failed++;
      finished(io, run, null, error, source.file);
    }
  }
  return failed ? 1 : 0;
}

async function reviseOne(io: Io, sources: SourceDocument[], argument: string, flags: Flags): Promise<number> {
  const source = find(io, sources, argument);
  if (source.kind === "cv") throw new UsageError("revise works on a Markdown translation; the CV's comments are not read yet");
  const to = destination(io, flags, source);
  if (flags.dryRun) {
    const file = path.join(io.root, source.translation);
    const comments = fs.existsSync(file) ? openComments(readMarkdown(readText(file)).trailer) : [];
    io.out(`${source.translation}: ${comments.length} open comment(s) would go to ${models(flags.settings)}; ${PLAN.replace("draft", "revision by the comments")}`);
    for (const comment of comments) io.out(`  #${comment.id} ${comment.author}: ${comment.text.split("\n")[0]}`);
    return 0;
  }
  const run = documentRun(io, flags, source);
  try {
    const result = await revise(io.root, source, sources, flags.settings, run);
    if (!result) {
      io.out(`${source.translation}: no open comments, nothing to revise`);
      return 0;
    }
    writeText(to, result.text);
    finished(io, run, result, null, source.translation);
    for (const warning of result.warnings) io.err(`  warning: ${warning}`);
    io.out(`revised ${shown(io, to)}: ${costLine(result.usages)}`);
    for (const { comment, addressed, note } of result.handled) {
      io.out(`  #${comment.id} ${addressed ? "addressed" : "left open"}: ${note}`);
    }
    outputs(io, run);
    return 0;
  } catch (error) {
    finished(io, run, null, error, source.translation);
    return 1;
  }
}

/**
 * Record on a translation the digest its source has now, without asking a model: for when the same
 * change was made by hand to both (a file moved, a marker renamed), so the two still say the same.
 */
function stamp(io: Io, chosen: SourceDocument[]): number {
  let failed = 0;
  for (const source of chosen) {
    const file = path.join(io.root, source.translation);
    if (!fs.existsSync(file)) {
      io.err(`${source.translation} is not there: translate ${source.file} first`);
      failed++;
      continue;
    }
    const before = readText(file);
    const line = source.kind === "cv" ? /^(# source_digest: ).*$/m : /^(source_digest: ).*$/m;
    if (!line.test(before)) {
      io.err(`${source.translation} records no source_digest to replace`);
      failed++;
      continue;
    }
    const after = before.replace(line, `$1${source.digest}`);
    if (after !== before) writeText(file, after);
    io.out(`${after === before ? "current " : "stamped "} ${source.file} -> ${source.translation}`);
  }
  return failed ? 1 : 0;
}

/** Run the tool. Returns its exit code: 0 done, 1 something is not current or failed, 2 it was called wrongly. */
export async function main(argv: string[], given: Partial<Io> = {}): Promise<number> {
  const io: Io = {
    root: path.resolve(import.meta.dirname, "../.."),
    cwd: process.env.INIT_CWD ?? process.cwd(),
    out: (line) => console.log(line),
    err: (line) => console.error(line),
    ...given,
  };
  try {
    const { values, positionals } = parseArgs({
      args: argv,
      allowPositionals: true,
      options: {
        all: { type: "boolean" },
        force: { type: "boolean" },
        json: { type: "boolean" },
        "dry-run": { type: "boolean" },
        model: { type: "string" },
        effort: { type: "string" },
        "critic-model": { type: "string" },
        "critic-effort": { type: "string" },
        "max-tokens": { type: "string" },
        out: { type: "string" },
        help: { type: "boolean", short: "h" },
      },
    });
    if (values.help) {
      io.out(USAGE);
      return 0;
    }
    const maxTokens = values["max-tokens"] === undefined ? DEFAULT_MAX_TOKENS : Number(values["max-tokens"]);
    if (!Number.isInteger(maxTokens) || maxTokens <= 0) throw new UsageError("--max-tokens takes a whole number");
    const flags: Flags = {
      settings: {
        model: values.model ?? DEFAULT_MODEL,
        effort: values.effort ?? DEFAULT_EFFORT,
        criticModel: values["critic-model"] ?? DEFAULT_CRITIC_MODEL,
        criticEffort: values["critic-effort"] ?? DEFAULT_CRITIC_EFFORT,
        maxTokens,
        today: io.today ?? today(),
        hub: io.hub,
        ask: io.ask,
        trace: io.trace ?? process.env.TRANSLATE_TRACE,
        log: (line) => io.err(`  ${line}`),
      },
      dryRun: values["dry-run"] ?? false,
      out: values.out === undefined ? null : path.resolve(io.cwd, values.out),
      runId: io.runId ?? runId(),
    };
    const sources = discover(io.root);
    const [command, ...rest] = positionals;
    if (command === "status") {
      if (rest.length) throw new UsageError("status takes no file");
      return status(io, sources, values.json ?? false);
    }
    if (command === "revise") {
      if (rest.length !== 1) throw new UsageError("revise takes one translation file");
      return await reviseOne(io, sources, rest[0]!, flags);
    }
    if (command === "stamp") {
      if (!rest.length) throw new UsageError("name the files whose translations to stamp");
      return stamp(io, [...new Set(rest.map((argument) => find(io, sources, argument)))]);
    }
    if (values.all ? positionals.length > 0 : positionals.length === 0) {
      throw new UsageError(values.all ? "--all takes no file" : "name the files to translate, or pass --all");
    }
    const chosen = values.all ? sources : [...new Set(positionals.map((argument) => find(io, sources, argument)))];
    return await translateAll(io, sources, chosen, values.force ?? false, flags);
  } catch (error) {
    if (error instanceof UsageError || (error as { code?: string }).code?.startsWith("ERR_PARSE_ARGS")) {
      io.err(`${(error as Error).message}\n\n${USAGE}`);
      return 2;
    }
    io.err(error instanceof Error ? error.message : String(error));
    return 1;
  }
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === fs.realpathSync(fileURLToPath(import.meta.url))) {
  process.exitCode = await main(process.argv.slice(2));
}
