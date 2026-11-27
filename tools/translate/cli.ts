#!/usr/bin/env node
// Translates the blog's documents into its other language, through the Maré Hub.
//
//   npm run translate -- status [--json]            where every translation stands; exit 1 unless all are current
//   npm run translate -- <file>… | --all            translate what is missing or stale (--force: a current one too)
//   npm run translate -- revise <translation file>  revise a translation by the open comments in its margin
//
//   --model <id>        the model that translates (default gpt-5.6-sol)
//   --effort <level>    its reasoning effort (default high)
//   --max-tokens <n>    the most it may answer with, thinking included (default 64000)
//   --dry-run           say what would be done, call nothing, write nothing
//   --out <dir>         write under <dir> instead of the repository (for trials)
//
// A document is a post, a page or the CV: `posts/<slug>.md`, `pages/about.md`, `cv_data.yaml`.
// What a translation was made from is recorded in it as `source_digest` (see digest.ts).

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { parseArgs } from "node:util";

import { openComments } from "./comments.ts";
import { discover, linkMapper, readMarkdown, readText, stateOf, writeText } from "./documents.ts";
import type { SourceDocument } from "./documents.ts";
import { DEFAULT_EFFORT, DEFAULT_MAX_TOKENS, DEFAULT_MODEL } from "./hub.ts";
import type { HubOptions, Usage } from "./hub.ts";
import { systemPrompt, userPrompt } from "./prompt.ts";
import { CheckError, revise, translate } from "./translate.ts";
import type { Settings } from "./translate.ts";

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
}

const USAGE = `usage: npm run translate -- status [--json]
       npm run translate -- <file>… | --all [--force] [--model <id>] [--effort <level>] [--dry-run] [--out <dir>]
       npm run translate -- revise <translation file> [--model <id>] [--effort <level>] [--dry-run] [--out <dir>]`;

class UsageError extends Error {}

const today = (): string => {
  const now = new Date();
  const two = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${two(now.getMonth() + 1)}-${two(now.getDate())}`;
};

const number = (n: unknown): string => (typeof n === "number" ? n.toLocaleString("en-US") : "?");

/** What a document's calls cost, in one line. */
export function costLine(usages: Usage[]): string {
  const sum = (key: string) => usages.reduce((total, usage) => total + (typeof usage[key] === "number" ? (usage[key] as number) : 0), 0);
  const priced = usages.every((usage) => typeof usage.cost_usd === "number");
  const calls = usages.length === 1 ? "1 call" : `${usages.length} calls`;
  return `${calls}, ${number(sum("prompt_tokens"))} tokens in, ${number(sum("completion_tokens"))} out, ${priced ? `$${sum("cost_usd").toFixed(4)}` : "cost not reported"}`;
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
}

// Where a translation is written: the repository, or the same path under --out.
const destination = (io: Io, flags: Flags, source: SourceDocument): string =>
  path.join(flags.out ?? io.root, source.translation);

const shown = (io: Io, file: string): string => path.relative(io.cwd, file) || file;

function report(io: Io, error: unknown, what: string): void {
  io.err(`${what}: ${error instanceof Error ? error.message : String(error)}`);
  if (error instanceof CheckError) io.err(`  ${costLine(error.usages)}; nothing was written`);
}

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
      const sizes = [systemPrompt(source), userPrompt(source, linkMapper(source, sources))].map((text) => number(text.length));
      io.out(
        `${state.status.padEnd(8)} ${source.file}: would translate into ${shown(io, to)} with ${flags.settings.model} (${flags.settings.effort}); ` +
          `${sizes[0]} characters of guidance, ${sizes[1]} of document`,
      );
      continue;
    }
    io.out(`${state.status.padEnd(8)} ${source.file}: translating with ${flags.settings.model} (${flags.settings.effort})…`);
    try {
      const result = await translate(io.root, source, sources, flags.settings);
      writeText(to, result.text);
      for (const warning of result.warnings) io.err(`  warning: ${warning}`);
      io.out(`  wrote ${shown(io, to)}: ${costLine(result.usages)}`);
    } catch (error) {
      failed++;
      report(io, error, source.file);
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
    io.out(`${source.translation}: ${comments.length} open comment(s) would go to ${flags.settings.model} (${flags.settings.effort})`);
    for (const comment of comments) io.out(`  #${comment.id} ${comment.author}: ${comment.text.split("\n")[0]}`);
    return 0;
  }
  try {
    const result = await revise(io.root, source, sources, flags.settings);
    if (!result) {
      io.out(`${source.translation}: no open comments, nothing to revise`);
      return 0;
    }
    writeText(to, result.text);
    for (const warning of result.warnings) io.err(`  warning: ${warning}`);
    io.out(`revised ${shown(io, to)}: ${costLine(result.usages)}`);
    for (const { comment, addressed, note } of result.handled) {
      io.out(`  #${comment.id} ${addressed ? "addressed" : "left open"}: ${note}`);
    }
    return 0;
  } catch (error) {
    report(io, error, source.translation);
    return 1;
  }
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
        maxTokens,
        today: io.today ?? today(),
        hub: io.hub,
        ask: io.ask,
        log: (line) => io.err(`  ${line}`),
      },
      dryRun: values["dry-run"] ?? false,
      out: values.out === undefined ? null : path.resolve(io.cwd, values.out),
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
