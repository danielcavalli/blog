// What a run leaves for the author to read, as the old engine's run artifacts did: every stage's
// answer, what it was asked, and a summary, in a folder git ignores.
//
//   .translate-runs/<run id>/<document>/01-source_analysis.json       the answer, validated, and its cost
//   .translate-runs/<run id>/<document>/01-source_analysis.prompt.md  the messages it answered
//   .translate-runs/<run id>/<document>/05-pass-1-critique.json       …one pair per stage, in order
//   .translate-runs/<run id>/<document>/summary.json                  passes, verdict, cost per stage
//
// `<document>` is the source's path without its extension: `posts/<slug>`, `pages/about`, `cv_data`.
// Nothing here is ever part of a published file.

import fs from "node:fs";
import path from "node:path";

import type { Stage } from "./contracts.ts";
import type { Message, Usage } from "./hub.ts";

export const RUNS_FOLDER = ".translate-runs";

/** One stage, as it ran. */
export interface StageRecord {
  stage: Stage;
  /** The revision pass, from 1; null for the stages before the passes. */
  pass: number | null;
  /** The revise stage that applies the owner's comments. */
  owner?: boolean;
  model: string;
  effort: string;
  /** Each call: the answer, and the repair when there was one. */
  usages: Usage[];
  /** The findings that sent the first answer back for its one repair. Empty when it passed. */
  repaired: string[];
  warnings: string[];
  /** The answer, as its contract normalized it. */
  output?: unknown;
  /** Why the stage failed, when it did. */
  error?: string;
  findings?: string[];
}

/** A stage's name in the run: `source_analysis`, `pass-1-critique`, `revise-owner`. */
export const stageName = (record: Pick<StageRecord, "stage" | "pass" | "owner">): string =>
  [record.pass === null ? null : `pass-${record.pass}`, record.stage, record.owner ? "owner" : null].filter(Boolean).join("-");

/** A run's id: when it started, to the second, in UTC. */
export const runId = (now = new Date()): string => now.toISOString().replace(/\.\d+Z$/, "Z").replace(/[-:]/g, "");

const write = (file: string, text: string): void => {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, text, "utf8");
};

/** The stages of one document's run, kept as they finish, and written under `dir` when there is one. */
export class DocumentRun {
  readonly stages: StageRecord[] = [];
  readonly dir: string | null;
  private readonly onStage: ((record: StageRecord) => void) | undefined;

  constructor(dir: string | null = null, onStage?: (record: StageRecord) => void) {
    this.dir = dir;
    this.onStage = onStage;
  }

  add(record: StageRecord, messages: Message[]): void {
    this.stages.push(record);
    if (this.dir) {
      const name = `${String(this.stages.length).padStart(2, "0")}-${stageName(record)}`;
      write(path.join(this.dir, `${name}.json`), `${JSON.stringify(record, null, 2)}\n`);
      write(path.join(this.dir, `${name}.prompt.md`), messages.map(({ role, content }) => `## ${role}\n\n${content.trim()}\n`).join("\n"));
    }
    this.onStage?.(record);
  }

  /** Every call of the run, in order. */
  get usages(): Usage[] {
    return this.stages.flatMap((record) => record.usages);
  }

  /** The summary at the end: what the caller says, and the cost of each stage. */
  finish(summary: Record<string, unknown>): void {
    if (!this.dir) return;
    const stages = this.stages.map((record) => {
      const sum = (key: string) => record.usages.reduce((total, usage) => total + (typeof usage[key] === "number" ? (usage[key] as number) : 0), 0);
      return {
        stage: stageName(record),
        model: `${record.model} (${record.effort})`,
        calls: record.usages.length,
        prompt_tokens: sum("prompt_tokens"),
        completion_tokens: sum("completion_tokens"),
        cost_usd: record.usages.length && record.usages.every((usage) => typeof usage.cost_usd === "number") ? sum("cost_usd") : null,
        ...(record.error ? { error: record.error } : {}),
      };
    });
    write(path.join(this.dir, "summary.json"), `${JSON.stringify({ ...summary, stages }, null, 2)}\n`);
  }
}
