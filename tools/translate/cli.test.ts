import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { after, before, test } from "node:test";
import { parse as parseYaml } from "yaml";

import { costLine, main } from "./cli.ts";
import { discover, readMarkdown, stateOf } from "./documents.ts";
import { json } from "./prompt.ts";
import { fakeHub, repository } from "./testing.ts";
import type { FakeHub, Reply } from "./testing.ts";

// The whole tool, from its command line to the files it writes, against a Hub that is a local
// server. Each test works in a small repository of its own.

let hub: FakeHub;
before(async () => {
  hub = await fakeHub();
});
after(() => hub.close());

const TIDE = `---
title: The tide
date: 2026-11-01
lang: en-us
excerpt: Why the tide matters (a little).
tags:
- sea
---

The tide comes in twice a day (more or less), as [the moon post](lua.en-us.md) explains, and [waves](wave.md#big) too.

![A beach at low tide.](tide.assets/low.jpg "Low tide, in the morning.")
`;

const post = (lang: string, body: string, extra = "") => `---\ntitle: T\nlang: ${lang}\nexcerpt: E\ntags:\n- x\n${extra}---\n\n${body}\n`;

const GOOD = {
  title: "A maré",
  excerpt: "Por que a maré importa (um pouco).",
  tags: ["mar"],
  content:
    "A maré sobe duas vezes por dia (mais ou menos), como [o post da lua](lua.md) explica, e [as ondas](wave.pt-br.md#big) também.\n\n" +
    '![Uma praia na maré baixa.](tide.assets/low.jpg "Maré baixa, de manhã.")',
};
// The same, with the aside's parentheses turned into dashes: it fails one check.
const DASHED = { ...GOOD, content: GOOD.content.replace("(mais ou menos)", "— mais ou menos —") };

const COMMENTS =
  "<!-- reef document k3x9f2 · revision 2 · note first draft -->\n" +
  "<!-- reef comment 1 · open · Daniel Cavalli · 2026-11-27T02:49Z · line 1 · before A maré · after duas vezes por dia\n> sobe\nPrefiro \"enche\".\n-->\n" +
  "<!-- reef comment 2 · open · Daniel Cavalli · 2026-11-27T02:50Z · line 3\n> Maré baixa\nIsso está certo?\n-->\n" +
  "<!-- reef comment 3 · resolved · Daniel Cavalli · 2026-11-20T10:00Z · line 1\n> lua\nResolvido.\n-->\n";

interface World {
  root: string;
  lines: string[];
  errors: string[];
  run: (...argv: string[]) => Promise<number>;
  read: (file: string) => string;
  exists: (file: string) => boolean;
}

function world(files: Record<string, string> = {}, trace?: string): World {
  const root = repository({
    "posts/tide.md": TIDE,
    "posts/wave.md": post("en-us", "Waves."),
    "posts/lua.md": post("pt-br", "A lua."),
    ...files,
  });
  hub.asked.length = 0;
  hub.replies.length = 0;
  const lines: string[] = [];
  const errors: string[] = [];
  return {
    root,
    lines,
    errors,
    run: (...argv) =>
      main(argv, {
        root,
        cwd: root,
        out: (line) => lines.push(line),
        err: (line) => errors.push(line),
        hub: { baseUrl: hub.baseUrl, backoffMs: () => 1 },
        today: "2026-11-26",
        trace: trace ?? "",
        runId: RUN,
      }),
    read: (file) => fs.readFileSync(path.join(root, file), "utf8"),
    exists: (file) => fs.existsSync(path.join(root, file)),
  };
}

const reply = (...replies: Reply[]) => hub.replies.push(...replies);

// What the other stages answer. The fake Hub reports every call as 1,000 tokens in, 200 out, $0.01.
const RUN = "20261126T120000Z";
const ANALYSIS = {
  author_voice_summary: "Dry, first person.",
  tone: "wry",
  register: "technical-editorial",
  sentence_rhythm: ["short"],
  connective_tissue: ["as"],
  rhetorical_moves: ["aside"],
  humor_signals: ["understatement"],
  stance_markers: [],
  must_preserve: ["(more or less)"],
};
const POLICY = { keep_english: [], localize: ["tide"], context_sensitive: [], do_not_translate: [], resolved_decisions: [], consistency_rules: [], rationale_notes: [] };
const critique = (needs: boolean) => ({
  score: needs ? 78.5 : 96,
  feedback: needs ? "One calque." : "No material defect.",
  needs_refinement: needs,
  dimension_scores: { accuracy_completeness: 95, terminology_entities: 95, markdown_code_link_fidelity: 100, locale_naturalness: 80, borrowing_consistency: 95, rhetorical_structure: 90 },
  critical_errors: 0,
  major_core_errors: needs ? 1 : 0,
  confidence: 0.8,
  findings: needs ? [{ id: "finding-1", severity: "major", dimension: "locale_naturalness", source_span: "comes in", target_span: "sobe", description: "Calque.", fix_hint: "Use enche." }] : [],
});
const review = (accept: boolean) => ({
  accept,
  publish_ready: accept,
  confidence: 0.9,
  residual_issues: accept ? [] : [{ passage: "duas vezes por dia", violates: "Review checks: flag literal calques", failure: '"sobe" is still the dictionary verb for the tide' }],
  voice_score: 90.5,
  terminology_score: 92,
  locale_naturalness_score: accept ? 88 : 61,
});
// A revision whose report applies these critique findings.
const revised = (content: string, applied: string[] = []) => ({
  ...GOOD,
  content,
  applied_feedback: applied.map((finding_id) => ({ finding_id, status: "applied", rationale: "used enche" })),
  declined_feedback: [],
  rewrite_summary: [],
  unresolved_risks: [],
});
// An answer with an empty revision report: a revision that keeps the text as it was.
const kept = (answer: unknown) => ({ ...(answer as object), applied_feedback: [], declined_feedback: [], rewrite_summary: [], unresolved_risks: [] });

// A whole run whose critic finds nothing, whose revision keeps the draft and whose reviewer accepts.
const passing = (draft: Reply, revision: Reply = { answer: kept((draft as { answer: unknown }).answer) }): Reply[] => [
  { answer: ANALYSIS },
  { answer: POLICY },
  draft,
  { answer: critique(false) },
  revision,
  { answer: review(true) },
];

// The lines a passing run prints between its first line and the one that says what it wrote.
const STAGE_LINES = (draftCost = "$0.0100") => [
  "  source analysis            1 call, 1,000 tokens in, 200 out, $0.0100",
  "  terminology policy         1 call, 1,000 tokens in, 200 out, $0.0100",
  `  translate                  1 call, 1,000 tokens in, 200 out, ${draftCost}`,
  "  pass 1 critique            1 call, 1,000 tokens in, 200 out, $0.0100; no refinement needed (score 96, 0 findings)",
  "  pass 1 revise              1 call, 1,000 tokens in, 200 out, $0.0100; 0 applied, 0 declined",
  "  pass 1 final review        1 call, 1,000 tokens in, 200 out, $0.0100; accepted: voice 90.5, terminology 92, locale naturalness 88 (confidence 0.9)",
  "  accepted in pass 1 of 2: voice 90.5, terminology 92, locale naturalness 88 (confidence 0.9)",
];

// A translation of tide.md as the tool would have written it, current unless told otherwise.
function translated(root: string, { digest, trailer = "" }: { digest?: string; trailer?: string } = {}): string {
  const tide = discover(root).find((source) => source.file === "posts/tide.md")!;
  return (
    `---\ntitle: A maré\nexcerpt: Por que a maré importa (um pouco).\ntags:\n- mar\nlang: pt-br\ntranslation_of: tide.md\n` +
    `source_digest: ${digest ?? tide.digest}\ntranslated_by: openai/gpt-5.5, via opencode\n---\n\n${GOOD.content}\n${trailer ? `\n${trailer}` : ""}`
  );
}

// ---------- status ----------

test("status lists every source with where its translation stands, and fails unless all are current", async () => {
  const w = world();
  const wave = discover(w.root).find((source) => source.file === "posts/wave.md")!;
  fs.writeFileSync(path.join(w.root, "posts/wave.pt-br.md"), post("pt-br", "Ondas.", `translation_of: wave.md\nsource_digest: ${wave.digest}\n`));
  fs.writeFileSync(path.join(w.root, "posts/lua.en-us.md"), post("en-us", "The moon.", `translation_of: lua.md\nsource_digest: ${"a".repeat(64)}\n`));
  assert.equal(await w.run("status"), 1);
  assert.deepEqual(w.lines, [
    "stale    posts/lua.md -> posts/lua.en-us.md",
    "missing  posts/tide.md -> posts/tide.pt-br.md",
    "current  posts/wave.md -> posts/wave.pt-br.md",
    "1 current, 1 stale, 1 missing",
  ]);
  assert.equal(hub.asked.length, 0, "status asks no model");

  w.lines.length = 0;
  assert.equal(await w.run("status", "--json"), 1);
  const rows = JSON.parse(w.lines.join("\n")) as Record<string, unknown>[];
  assert.deepEqual(rows[0], {
    source: "posts/lua.md",
    translation: "posts/lua.en-us.md",
    kind: "post",
    from: "pt-br",
    to: "en-us",
    status: "stale",
    source_digest: discover(w.root)[0]!.digest,
    recorded_digest: "a".repeat(64),
  });
  assert.deepEqual(rows.map((row) => row.status), ["stale", "missing", "current"]);
});

test("status passes when every translation is current", async () => {
  const w = world();
  for (const source of discover(w.root)) {
    fs.writeFileSync(path.join(w.root, source.translation), post(source.target, "x", `translation_of: ${path.basename(source.file)}\nsource_digest: ${source.digest}\n`));
  }
  assert.equal(await w.run("status"), 0);
  assert.equal(w.lines.at(-1), "3 current, 0 stale, 0 missing");
});

test("this repository's own translations are all current", async () => {
  const lines: string[] = [];
  const code = await main(["status"], { out: (line) => lines.push(line), err: (line) => lines.push(line) });
  assert.equal(code, 0, lines.join("\n"));
  assert.match(lines.at(-1)!, /^\d+ current, 0 stale, 0 missing$/);
});

// ---------- translate ----------

test("a missing translation goes through every stage and is written with its front matter", async () => {
  const w = world();
  reply(...passing({ answer: GOOD, cost: 0.0421 }));
  assert.equal(await w.run("posts/tide.md"), 0, w.errors.join("\n"));

  assert.equal(
    w.read("posts/tide.pt-br.md"),
    "---\ntitle: A maré\nexcerpt: Por que a maré importa (um pouco).\ntags:\n- mar\nlang: pt-br\ntranslation_of: tide.md\n" +
      `source_digest: ${discover(w.root)[1]!.digest}\ntranslated_by: gpt-5.6-sol (high), via mare-hub\ntranslated_at: '2026-11-26'\n---\n\n${GOOD.content}\n`,
  );
  assert.equal(stateOf(w.root, discover(w.root)[1]!).status, "current");
  assert.deepEqual(w.lines, [
    "missing  posts/tide.md: translating with gpt-5.6-sol (high), critic claude-opus-5-5 (medium)…",
    ...STAGE_LINES("$0.0421"),
    "  wrote posts/tide.pt-br.md: 6 calls, 6,000 tokens in, 1,200 out, $0.0921",
    `  stage outputs: .translate-runs/${RUN}/posts/tide`,
  ]);

  assert.equal(hub.asked.length, 6);
  assert.deepEqual(
    hub.asked.map((asked) => [asked.response_format.json_schema.name, asked.model, asked.reasoning_effort, asked.max_tokens]),
    [
      ["source_analysis", "gpt-5.6-sol", "high", 64_000],
      ["terminology_policy", "gpt-5.6-sol", "high", 64_000],
      ["translation", "gpt-5.6-sol", "high", 64_000],
      ["critique", "claude-opus-5-5", "medium", 64_000],
      ["revision", "gpt-5.6-sol", "high", 64_000],
      ["final_review", "claude-opus-5-5", "medium", 64_000],
    ],
  );
  const draft = hub.asked[2]!;
  assert.deepEqual(draft.messages.map((message) => message.role), ["system", "user"]);
  assert.match(draft.messages[0]!.content, /^LOCALIZATION AUTHORITY\n[\s\S]*\nTRANSLATE\n/);
  assert.ok(draft.messages[1]!.content.includes("- `lua.en-us.md` is written `lua.md`\n- `wave.md#big` is written `wave.pt-br.md#big`"));
  assert.ok(draft.messages[1]!.content.includes(`SOURCE ANALYSIS JSON (MODEL ADVICE)\n${json(ANALYSIS)}`));
  assert.ok(draft.messages[1]!.content.includes("TERMINOLOGY POLICY JSON (MODEL PROPOSAL)\n{"));
  assert.ok(draft.messages[1]!.content.includes("The tide comes in twice a day (more or less)"));
  assert.ok(hub.asked[5]!.messages[1]!.content.includes(`LOCALIZED CANDIDATE JSON\n${json(GOOD)}`), "the final review reads what is written");
});

test("--model, --effort, --critic-model, --critic-effort and --max-tokens choose the models, and the translation says which wrote it", async () => {
  const w = world();
  reply(...passing({ answer: GOOD }));
  assert.equal(
    await w.run("posts/tide.md", "--model", "claude-opus-5", "--effort", "medium", "--critic-model", "gpt-5.6-sol", "--critic-effort", "low", "--max-tokens", "32000"),
    0,
    w.errors.join("\n"),
  );
  assert.deepEqual(
    hub.asked.map((asked) => [asked.model, asked.reasoning_effort, asked.max_tokens]),
    [
      ["claude-opus-5", "medium", 32_000],
      ["claude-opus-5", "medium", 32_000],
      ["claude-opus-5", "medium", 32_000],
      ["gpt-5.6-sol", "low", 32_000],
      ["claude-opus-5", "medium", 32_000],
      ["gpt-5.6-sol", "low", 32_000],
    ],
  );
  assert.equal(readMarkdown(w.read("posts/tide.pt-br.md")).meta.translated_by, "claude-opus-5 (medium), via mare-hub");
  assert.equal(w.lines[0], "missing  posts/tide.md: translating with claude-opus-5 (medium), critic gpt-5.6-sol (low)…");
});

test("a translation that is current is left alone, unless --force", async () => {
  const w = world();
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), translated(w.root));
  assert.equal(await w.run("posts/tide.md"), 0);
  assert.equal(hub.asked.length, 0);
  assert.deepEqual(w.lines, ["current  posts/tide.md -> posts/tide.pt-br.md: nothing to do (--force translates it again)"]);
  assert.equal(w.read("posts/tide.pt-br.md"), translated(w.root));

  reply(...passing({ answer: { ...GOOD, title: "A maré, de novo" } }));
  assert.equal(await w.run("posts/tide.pt-br.md", "--force"), 0, "a translation's own path names its source");
  assert.equal(hub.asked.length, 6);
  assert.equal(readMarkdown(w.read("posts/tide.pt-br.md")).meta.title, "A maré, de novo");
});

test("a stale translation is translated again, and the trailer at its end is kept byte for byte", async () => {
  const w = world();
  const stale = translated(w.root, { digest: "b".repeat(64), trailer: COMMENTS });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), stale.replace("lang: pt-br\n", "lang: pt-br\nreviewed_by: Daniel\n"));
  reply(...passing({ answer: { ...GOOD, content: GOOD.content.replace("sobe", "enche") } }));
  assert.equal(await w.run("posts/tide.md"), 0, w.errors.join("\n"));
  const after = w.read("posts/tide.pt-br.md");
  assert.ok(after.endsWith(`\n\n${COMMENTS}`));
  assert.equal(readMarkdown(after).trailer, COMMENTS);
  assert.ok(after.includes("A maré enche duas vezes"));
  assert.equal(readMarkdown(after).meta.reviewed_by, "Daniel");
  assert.equal(stateOf(w.root, discover(w.root)[1]!).status, "current");
  assert.equal(w.lines[0], "stale    posts/tide.md: translating with gpt-5.6-sol (high), critic claude-opus-5-5 (medium)…");
});

test("the revision after the critique is what is written", async () => {
  const w = world();
  const better = revised(GOOD.content.replace("sobe", "enche"), ["finding-1"]);
  reply({ answer: ANALYSIS }, { answer: POLICY }, { answer: GOOD }, { answer: critique(true) }, { answer: better }, { answer: review(true) });
  assert.equal(await w.run("posts/tide.md"), 0, w.errors.join("\n"));
  assert.deepEqual(hub.asked.map((asked) => asked.response_format.json_schema.name), ["source_analysis", "terminology_policy", "translation", "critique", "revision", "final_review"]);
  const revision = hub.asked[4]!;
  assert.equal(revision.model, "gpt-5.6-sol");
  assert.ok(revision.messages[1]!.content.includes(`TRANSLATED CANDIDATE JSON\n${json(GOOD)}`));
  assert.ok(revision.messages[1]!.content.includes('CRITIQUE JSON\n{\n  "confidence": 0.8,'));
  assert.ok(w.read("posts/tide.pt-br.md").includes("A maré enche duas vezes"));
  assert.ok(w.lines.includes("  pass 1 critique            1 call, 1,000 tokens in, 200 out, $0.0100; needs refinement (score 78.5, 1 finding)"));
  assert.ok(w.lines.includes("  pass 1 revise              1 call, 1,000 tokens in, 200 out, $0.0100; 1 applied, 0 declined"));
});

test("--all translates what is missing or stale, and nothing else", async () => {
  const w = world();
  const wave = discover(w.root).find((source) => source.file === "posts/wave.md")!;
  fs.writeFileSync(path.join(w.root, "posts/wave.pt-br.md"), post("pt-br", "Ondas.", `translation_of: wave.md\nsource_digest: ${wave.digest}\n`));
  reply(...passing({ answer: { title: "T", excerpt: "E", tags: ["x"], content: "The moon." } }), ...passing({ answer: GOOD }));
  assert.equal(await w.run("--all"), 0, w.errors.join("\n"));
  assert.equal(hub.asked.length, 12);
  assert.ok(hub.asked[0]!.messages[1]!.content.startsWith("DOCUMENT\nposts/lua.md (post), pt-br to en-us"));
  assert.ok(hub.asked[0]!.messages[0]!.content.includes("Target: publishable US English technical-editorial prose."));
  assert.equal(readMarkdown(w.read("posts/lua.en-us.md")).meta.lang, "en-us");
  assert.equal(await w.run("status"), 0);
});

test("an answer that fails a check is repaired once, with the exact finding", async () => {
  const w = world();
  reply({ answer: ANALYSIS }, { answer: POLICY }, { answer: DASHED, cost: 0.03 }, { answer: GOOD, cost: 0.02 }, { answer: critique(false) }, { answer: kept(GOOD) }, { answer: review(true) });
  assert.equal(await w.run("posts/tide.md"), 0, w.errors.join("\n"));
  assert.equal(hub.asked.length, 7);
  const messages = hub.asked[3]!.messages;
  assert.deepEqual(messages.map((message) => message.role), ["system", "user", "assistant", "user"]);
  assert.equal(messages[2]!.content, JSON.stringify(DASHED));
  assert.match(messages[3]!.content, /^DETERMINISTIC VALIDATION FINDINGS\n/);
  assert.match(messages[3]!.content, /- Translation changed parenthetical asides: preserve parentheses around the same thoughts.*The source has 1 and the translation 0\. The source's, in order: 1\. "\(more or less\)"/);
  assert.equal(readMarkdown(w.read("posts/tide.pt-br.md")).body, GOOD.content);
  assert.ok(w.lines.includes("  translate                  2 calls, 2,000 tokens in, 400 out, $0.0500 after one repair"));
  assert.equal(w.lines.at(-2), "  wrote posts/tide.pt-br.md: 7 calls, 7,000 tokens in, 1,400 out, $0.1000");
  assert.ok(w.errors.some((line) => line.includes("failed 1 check(s), asking for a repair")));
});

test("an answer that still fails after the repair is never written", async () => {
  const w = world();
  const stale = translated(w.root, { digest: "b".repeat(64), trailer: COMMENTS });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), stale);
  reply({ answer: ANALYSIS }, { answer: POLICY }, { answer: DASHED }, { answer: { ...DASHED, content: DASHED.content.replace("lua.md", "lua.en-us.md") } }, { answer: GOOD });
  assert.equal(await w.run("posts/tide.md"), 1);
  assert.equal(hub.asked.length, 4, "one repair, not two, and no stage after the failed one");
  assert.equal(w.read("posts/tide.pt-br.md"), stale, "the file is as it was");
  const said = w.errors.join("\n");
  assert.match(said, /posts\/tide\.md: The translation failed its checks after one repair:/);
  assert.match(said, /- Translation changed protected link destinations: missing link `lua\.md`; not in the source link `lua\.en-us\.md`/);
  assert.match(said, /- Translation changed parenthetical asides/);
  assert.match(said, /4 calls, 4,000 tokens in, 800 out, \$0\.0400; nothing was written/);

  const fresh = world();
  reply({ answer: ANALYSIS }, { answer: POLICY }, { answer: "not json at all" }, { answer: { title: "only a title" } });
  assert.equal(await fresh.run("posts/tide.md"), 1);
  assert.ok(!fresh.exists("posts/tide.pt-br.md"), "no file appears for a translation that failed");
  assert.match(fresh.errors.join("\n"), /Missing required field "excerpt"/);
});

test("a translation the final review still rejects after the last pass is never written, and the reviewer's issues are said", async () => {
  const w = world();
  const stale = translated(w.root, { digest: "b".repeat(64), trailer: COMMENTS });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), stale);
  const better = revised(GOOD.content.replace("sobe", "enche"), ["finding-1"]);
  reply(
    { answer: ANALYSIS },
    { answer: POLICY },
    { answer: GOOD },
    { answer: critique(true) },
    { answer: better },
    { answer: review(false) },
    { answer: critique(false) },
    { answer: kept(better) },
    { answer: review(false) },
    { answer: review(true) },
  );
  assert.equal(await w.run("posts/tide.md"), 1);
  assert.equal(hub.asked.length, 9, "two passes, not three");
  assert.ok(hub.asked[6]!.messages[1]!.content.includes("PREVIOUS FINAL REVIEW RESIDUAL ISSUES"), "pass 2's critic is told why pass 1 was rejected");
  assert.ok(!hub.asked[8]!.messages[1]!.content.includes("PREVIOUS FINAL REVIEW"), "pass 2's final review is not");
  assert.equal(w.read("posts/tide.pt-br.md"), stale, "the file is as it was");
  assert.ok(w.lines.includes("  pass 2 final review        1 call, 1,000 tokens in, 200 out, $0.0100; not accepted: voice 90.5, terminology 92, locale naturalness 61 (confidence 0.9), 1 residual issue"));
  assert.deepEqual(w.errors.join("\n").split("\n"), [
    "posts/tide.md: The final review rejected the translation after 2 of 2 passes; its residual issues:",
    '  - "duas vezes por dia": "sobe" is still the dictionary verb for the tide (violates: Review checks: flag literal calques)',
    "  9 calls, 9,000 tokens in, 1,800 out, $0.0900; nothing was written",
  ]);
  const summary = JSON.parse(w.read(`.translate-runs/${RUN}/posts/tide/summary.json`)) as Record<string, unknown>;
  assert.equal(summary.accepted, false);
  assert.equal(summary.passes, 2);
  assert.deepEqual((summary.final_review as { residual_issues: unknown[] }).residual_issues, review(false).residual_issues);
});

test("every stage's answer is kept under .translate-runs for the author to read, and none of it is published", async () => {
  const w = world();
  const better = revised(GOOD.content.replace("sobe", "enche"), ["finding-1"]);
  reply({ answer: ANALYSIS }, { answer: POLICY }, { answer: DASHED }, { answer: GOOD }, { answer: critique(true) }, { answer: better }, { answer: review(true) });
  assert.equal(await w.run("posts/tide.md"), 0, w.errors.join("\n"));
  const dir = `.translate-runs/${RUN}/posts/tide`;
  assert.deepEqual(fs.readdirSync(path.join(w.root, dir)).sort(), [
    "01-source_analysis.json",
    "01-source_analysis.prompt.md",
    "02-terminology_policy.json",
    "02-terminology_policy.prompt.md",
    "03-translate.json",
    "03-translate.prompt.md",
    "04-pass-1-critique.json",
    "04-pass-1-critique.prompt.md",
    "05-pass-1-revise.json",
    "05-pass-1-revise.prompt.md",
    "06-pass-1-final_review.json",
    "06-pass-1-final_review.prompt.md",
    "summary.json",
  ]);
  const stage = (name: string) => JSON.parse(w.read(`${dir}/${name}.json`)) as Record<string, unknown>;
  assert.deepEqual(stage("01-source_analysis").output, ANALYSIS);
  assert.deepEqual((stage("02-terminology_policy").output as Record<string, unknown>).education_degree_localization_policy, null);
  const draft = stage("03-translate");
  assert.equal(draft.model, "gpt-5.6-sol");
  assert.equal((draft.usages as unknown[]).length, 2, "the repair is part of the stage");
  assert.equal((draft.repaired as string[]).length, 1);
  assert.deepEqual(draft.output, GOOD);
  assert.equal((stage("04-pass-1-critique").output as { needs_refinement: boolean }).needs_refinement, true);
  assert.equal(stage("04-pass-1-critique").effort, "medium");
  assert.deepEqual((stage("05-pass-1-revise").output as { applied_feedback: unknown[] }).applied_feedback, [{ finding_id: "finding-1", status: "applied", rationale: "used enche" }]);
  assert.deepEqual(stage("06-pass-1-final_review").output, review(true));
  const prompt = w.read(`${dir}/04-pass-1-critique.prompt.md`);
  assert.match(prompt, /^## system\n\nLOCALIZATION AUTHORITY\n[\s\S]*\n## user\n\nDOCUMENT\n[\s\S]*\n## assistant\n\n\{/);
  const summary = JSON.parse(w.read(`${dir}/summary.json`)) as { accepted: boolean; passes: number; stages: Record<string, unknown>[] };
  assert.equal(summary.accepted, true);
  assert.equal(summary.passes, 1);
  assert.deepEqual(summary.stages[2], { stage: "translate", model: "gpt-5.6-sol (high)", calls: 2, prompt_tokens: 2000, completion_tokens: 400, cost_usd: 0.02 });
  assert.equal(summary.stages[3]!.model, "claude-opus-5-5 (medium)");

  const published = w.read("posts/tide.pt-br.md");
  for (const word of ["SOURCE ANALYSIS", "critique", "residual_issues", "voice_score", ".translate-runs"]) assert.ok(!published.includes(word), `${word} is not in the translation`);
  assert.match(fs.readFileSync(path.resolve(import.meta.dirname, "../../.gitignore"), "utf8"), /^\.translate-runs\/$/m, "git ignores the runs");
});

test("a trace keeps every question and the whole answer, the refused one too", async () => {
  const trace = path.join(repository({}), "trace.jsonl");
  const w = world({}, trace);
  reply({ answer: ANALYSIS }, { answer: POLICY }, { answer: DASHED }, { answer: GOOD }, { answer: critique(false) }, { answer: kept(GOOD) }, { answer: review(true) });
  assert.equal(await w.run("posts/tide.md"), 0, w.errors.join("\n"));
  const entries = fs.readFileSync(trace, "utf8").trim().split("\n").map((line) => JSON.parse(line) as { question: { messages: unknown[] }; answer: { content: string; usage: { cost_usd: number } } });
  assert.equal(entries.length, 7);
  assert.deepEqual(entries.map((entry) => entry.question.messages.length), [2, 2, 2, 4, 2, 2, 2]);
  assert.equal(entries[2]!.answer.content, JSON.stringify(DASHED));
  assert.equal(entries[3]!.answer.usage.cost_usd, 0.01);
});

test("one document failing does not stop the others, and the run still fails", async () => {
  const w = world();
  reply({ status: 400, message: "unknown model 'gpt-9'" }, ...passing({ answer: GOOD }), ...passing({ answer: { title: "T", excerpt: "E", tags: ["x"], content: "Ondas." } }));
  assert.equal(await w.run("--all", "--model", "gpt-9"), 1);
  assert.match(w.errors.join("\n"), /posts\/lua\.md: The Hub answered 400: unknown model 'gpt-9'/);
  assert.ok(!w.exists("posts/lua.en-us.md"));
  assert.ok(w.exists("posts/tide.pt-br.md") && w.exists("posts/wave.pt-br.md"));
});

test("--out writes under another folder and leaves the repository as it was", async () => {
  const w = world();
  const existing = translated(w.root, { digest: "b".repeat(64), trailer: COMMENTS });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), existing);
  const out = repository({});
  reply(...passing({ answer: GOOD }));
  assert.equal(await w.run("posts/tide.md", "--out", out), 0, w.errors.join("\n"));
  assert.equal(w.read("posts/tide.pt-br.md"), existing);
  const written = fs.readFileSync(path.join(out, "posts/tide.pt-br.md"), "utf8");
  assert.equal(readMarkdown(written).meta.translated_by, "gpt-5.6-sol (high), via mare-hub");
  assert.equal(readMarkdown(written).trailer, COMMENTS, "it is the file that would have been written");
  assert.deepEqual(fs.readdirSync(out).sort(), [".translate-runs", "posts"], "the stages' answers go with it");
  assert.ok(!w.exists(".translate-runs"));
});

test("--dry-run says what would be done, asks no model and writes nothing", async () => {
  const w = world();
  assert.equal(await w.run("--all", "--dry-run"), 0);
  assert.equal(hub.asked.length, 0);
  assert.equal(w.lines.length, 3);
  assert.equal(
    w.lines[1],
    "missing  posts/tide.md: would translate into posts/tide.pt-br.md with gpt-5.6-sol (high), critic claude-opus-5-5 (medium); " +
      "6 to 9 calls: source analysis, terminology policy, draft, then up to 2 passes of critique, revision and final review",
  );
  assert.deepEqual(fs.readdirSync(path.join(w.root, "posts")).sort(), ["lua.md", "tide.md", "wave.md"]);
  assert.ok(!w.exists(".translate-runs"));
});

test("the CV is translated to YAML that says what it translates, through its own stage prompts", async () => {
  const cv = "# The CV.\nname: Daniel\ntagline: Engineer\ncontact:\n  email: d@example.com\nskills:\n- Distributed Systems\n";
  const w = world({ "cv_data.yaml": cv });
  reply({ answer: ANALYSIS }, { answer: { ...POLICY, education_degree_localization_policy: { decision: "localize_equivalent", apply_consistently: true, rule: "r", exceptions: [] } } });
  reply({ answer: { name: "Daniel", tagline: "Engenheiro", contact: { email: "d@exemplo.com" }, skills: ["sistemas distribuídos"] } });
  reply({ answer: { tagline: "Engenheiro", name: "Daniel", skills: ["sistemas distribuídos"], contact: { email: "d@example.com" } } });
  const report = { applied_findings: [], declined_findings: [], protected_field_exceptions: [] };
  reply({ answer: critique(false) }, { answer: { revised_cv: { name: "Daniel", tagline: "Engenheiro", contact: { email: "d@example.com" }, skills: ["sistemas distribuídos"] }, revision_report: report } }, { answer: review(true) });
  assert.equal(await w.run("cv_data.yaml"), 0, w.errors.join("\n"));
  assert.deepEqual(hub.asked.map((asked) => asked.response_format.json_schema.name), ["source_analysis", "terminology_policy", "cv_translation", "cv_translation", "critique", "cv_revision", "final_review"]);
  assert.match(hub.asked[0]!.messages[0]!.content, /structured CV artifact/);
  assert.match(hub.asked[2]!.messages[0]!.content, /Produce a localized CV draft/);
  assert.match(hub.asked[3]!.messages[3]!.content, /- CV translation changed contact details/);
  assert.match(hub.asked[5]!.messages[0]!.content, /Rewrite the translated CV candidate/);
  assert.match(hub.asked[6]!.messages[0]!.content, /Review the localized CV directly/);
  const text = w.read("cv_data.pt-br.yaml");
  assert.deepEqual(parseYaml(text), { name: "Daniel", tagline: "Engenheiro", contact: { email: "d@example.com" }, skills: ["sistemas distribuídos"] });
  assert.ok(text.includes("# translation_of: cv_data.yaml\n# source_digest: "));
  assert.equal(stateOf(w.root, discover(w.root).at(-1)!).status, "current");
  assert.equal(w.read("cv_data.yaml"), cv);
});

// ---------- revise ----------

const revision = (comments: unknown[], content = GOOD.content.replace("sobe", "enche")) => ({ ...revised(content), comments });

// The translation `translated()` writes, as a candidate.
const CURRENT = { title: "A maré", excerpt: "Por que a maré importa (um pouco).", tags: ["mar"], content: GOOD.content };

test("revise sends the open comments to the revise stage as the owner's instructions, then critique and final review, and marks the handled ones addressed", async () => {
  const w = world();
  const before = translated(w.root, { trailer: COMMENTS });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), before);
  reply(
    ...passing({
      answer: revision([
        { id: 1, addressed: true, note: '"sobe" virou "enche".' },
        { id: 2, addressed: false, note: "É uma pergunta: sim, a legenda corresponde à fonte." },
      ]),
    }),
  );
  assert.equal(await w.run("revise", "posts/tide.pt-br.md"), 0, w.errors.join("\n"));

  assert.deepEqual(hub.asked.map((asked) => asked.response_format.json_schema.name), ["source_analysis", "terminology_policy", "owner_revision", "critique", "revision", "final_review"]);
  const asked = hub.asked[2]!;
  assert.equal(asked.model, "gpt-5.6-sol");
  assert.match(asked.messages[0]!.content, /\nREVISE\nRewrite the translated candidate[\s\S]*\nOWNER REVISION\n/);
  const user = asked.messages[1]!.content;
  assert.ok(user.includes(`TRANSLATED CANDIDATE JSON\n${json(CURRENT)}`), "the translation as it stands");
  assert.ok(user.includes(`SOURCE ANALYSIS JSON (MODEL ADVICE)\n${json(ANALYSIS)}`));
  assert.ok(user.includes('Comment 1, line 1\nQuoted passage:\n> sobe\nAround it: …A maré [the passage] duas vezes por dia…\nDaniel Cavalli wrote:\nPrefiro "enche".'));
  assert.ok(user.includes("Comment 2, line 3\nQuoted passage:\n> Maré baixa\nDaniel Cavalli wrote:\nIsso está certo?"));
  assert.ok(!user.includes("Resolvido."), "a comment that is not open is not an instruction");
  assert.ok(user.includes("The tide comes in twice a day"), "the source goes too");
  for (const other of hub.asked) assert.ok(other.messages[1]!.content.includes("OWNER REVISION INSTRUCTIONS\nComment 1, line 1"), "every stage holds the owner's instructions");
  assert.ok(hub.asked[3]!.messages[1]!.content.includes(`TRANSLATED CANDIDATE JSON\n${json({ ...CURRENT, content: GOOD.content.replace("sobe", "enche") })}`), "the critic reads the revision");

  const after = w.read("posts/tide.pt-br.md");
  const written = readMarkdown(after);
  assert.equal(written.body, GOOD.content.replace("sobe", "enche"));
  assert.equal(written.trailer, COMMENTS.replace("<!-- reef comment 1 · open · ", "<!-- reef comment 1 · addressed · "), "one word of the trailer changed");
  assert.equal(written.meta.translated_by, "gpt-5.6-sol (high), via mare-hub");
  assert.equal(stateOf(w.root, discover(w.root)[1]!).status, "current");
  assert.deepEqual(w.lines, [
    "  source analysis            1 call, 1,000 tokens in, 200 out, $0.0100",
    "  terminology policy         1 call, 1,000 tokens in, 200 out, $0.0100",
    "  revise (owner's comments)  1 call, 1,000 tokens in, 200 out, $0.0100",
    ...STAGE_LINES().slice(3),
    "revised posts/tide.pt-br.md: 6 calls, 6,000 tokens in, 1,200 out, $0.0600",
    '  #1 addressed: "sobe" virou "enche".',
    "  #2 left open: É uma pergunta: sim, a legenda corresponde à fonte.",
    `  stage outputs: .translate-runs/${RUN}/posts/tide`,
  ]);
  const summary = JSON.parse(w.read(`.translate-runs/${RUN}/posts/tide/summary.json`)) as { comments: unknown[] };
  assert.deepEqual(summary.comments, [
    { id: 1, addressed: true, note: '"sobe" virou "enche".' },
    { id: 2, addressed: false, note: "É uma pergunta: sim, a legenda corresponde à fonte." },
  ]);
  assert.ok(fs.existsSync(path.join(w.root, `.translate-runs/${RUN}/posts/tide/03-revise-owner.json`)));
});

test("an owner's revision the final review rejects is not written, and no comment is marked", async () => {
  const w = world();
  const before = translated(w.root, { trailer: COMMENTS });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), before);
  const answered = revision([{ id: 1, addressed: true, note: "feito" }, { id: 2, addressed: false, note: "pergunta" }]);
  reply(
    { answer: ANALYSIS },
    { answer: POLICY },
    { answer: answered },
    { answer: critique(false) },
    { answer: kept(answered) },
    { answer: review(false) },
    { answer: critique(false) },
    { answer: kept(answered) },
    { answer: review(false) },
  );
  assert.equal(await w.run("revise", "posts/tide.pt-br.md"), 1);
  assert.equal(w.read("posts/tide.pt-br.md"), before);
  assert.match(w.errors.join("\n"), /posts\/tide\.pt-br\.md: The final review rejected the translation after 2 of 2 passes/);
});

test("revise with no open comment does nothing", async () => {
  const w = world();
  const before = translated(w.root, { trailer: COMMENTS.replaceAll(" · open · ", " · addressed · ") });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), before);
  assert.equal(await w.run("revise", "posts/tide.pt-br.md"), 0);
  assert.equal(hub.asked.length, 0);
  assert.equal(w.read("posts/tide.pt-br.md"), before);
  assert.deepEqual(w.lines, ["posts/tide.pt-br.md: no open comments, nothing to revise"]);
  assert.ok(!w.exists(".translate-runs"));
});

test("a revision must pass the same checks, account for every comment, and change something", async () => {
  const w = world();
  const before = translated(w.root, { trailer: COMMENTS });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), before);
  reply(
    { answer: ANALYSIS },
    { answer: POLICY },
    { answer: revision([{ id: 1, addressed: true, note: "feito" }]) },
    { answer: revision([{ id: 1, addressed: true, note: "feito" }, { id: 2, addressed: true, note: "feito" }], GOOD.content) },
  );
  assert.equal(await w.run("revise", "posts/tide.pt-br.md"), 1);
  assert.equal(hub.asked.length, 4);
  assert.match(hub.asked[3]!.messages[3]!.content, /- "comments" must have exactly one entry for comment 2, and has 0/);
  assert.match(w.errors.join("\n"), /The answer says comments are addressed and changes nothing in the translation/);
  assert.equal(w.read("posts/tide.pt-br.md"), before, "nothing was written, and no comment was marked");

  reply(
    { answer: ANALYSIS },
    { answer: POLICY },
    { answer: revision([{ id: 1, addressed: true, note: "feito" }, { id: 2, addressed: true, note: "feito" }], DASHED.content) },
    { answer: DASHED },
  );
  assert.equal(await w.run("revise", "posts/tide.pt-br.md"), 1);
  assert.match(w.errors.join("\n"), /Translation changed parenthetical asides/);
  assert.equal(w.read("posts/tide.pt-br.md"), before);
});

test("revise refuses a translation that is stale or missing, and the CV", async () => {
  const w = world({ "cv_data.yaml": "name: D\n" });
  assert.equal(await w.run("revise", "posts/tide.pt-br.md"), 1);
  assert.match(w.errors.at(-1)!, /posts\/tide\.pt-br\.md does not exist: translate posts\/tide\.md first/);
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), translated(w.root, { digest: "b".repeat(64), trailer: COMMENTS }));
  assert.equal(await w.run("revise", "posts/tide.pt-br.md"), 1);
  assert.match(w.errors.at(-1)!, /posts\/tide\.pt-br\.md is stale \(posts\/tide\.md changed since it was translated\): translate it first; the comments stay in its margin/);
  assert.equal(await w.run("revise", "cv_data.pt-br.yaml"), 2);
  assert.equal(hub.asked.length, 0);
});

test("revise --dry-run lists the comments that would be sent; --out leaves the repository alone", async () => {
  const w = world();
  const before = translated(w.root, { trailer: COMMENTS });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), before);
  assert.equal(await w.run("revise", "posts/tide.pt-br.md", "--dry-run"), 0);
  assert.deepEqual(w.lines, [
    "posts/tide.pt-br.md: 2 open comment(s) would go to gpt-5.6-sol (high), critic claude-opus-5-5 (medium); " +
      "6 to 9 calls: source analysis, terminology policy, revision by the comments, then up to 2 passes of critique, revision and final review",
    '  #1 Daniel Cavalli: Prefiro "enche".',
    "  #2 Daniel Cavalli: Isso está certo?",
  ]);
  assert.equal(hub.asked.length, 0);

  const out = repository({});
  reply(...passing({ answer: revision([{ id: 1, addressed: true, note: "feito" }, { id: 2, addressed: true, note: "feito" }]) }));
  assert.equal(await w.run("revise", "posts/tide.pt-br.md", "--out", out), 0, w.errors.join("\n"));
  assert.equal(w.read("posts/tide.pt-br.md"), before);
  assert.equal(readMarkdown(fs.readFileSync(path.join(out, "posts/tide.pt-br.md"), "utf8")).trailer, COMMENTS.replaceAll(" · open · ", " · addressed · "));
});

// ---------- the command line ----------

test("a command line that makes no sense is refused with the usage", async () => {
  for (const argv of [[], ["--all", "posts/tide.md"], ["posts/nothing.md"], ["status", "extra"], ["revise"], ["--unknown"], ["--all", "--max-tokens", "many"]]) {
    const w = world();
    assert.equal(await w.run(...argv), 2, argv.join(" "));
    assert.match(w.errors.join("\n"), /usage: npm run translate -- status/);
    assert.equal(hub.asked.length, 0);
  }
  const w = world();
  assert.equal(await w.run("--help"), 0);
  assert.match(w.lines.join("\n"), /usage: npm run translate/);
});

test("the cost of a document is its calls added up", () => {
  assert.equal(costLine([{ prompt_tokens: 12_345, completion_tokens: 678, cost_usd: 0.1234 }]), "1 call, 12,345 tokens in, 678 out, $0.1234");
  // What the Hub's answer for a subscription model carries: tokens, and no cost.
  const unpriced = { cache_write_tokens: 0, cached_tokens: 0, completion_tokens: 5580, prompt_tokens: 13_498, total_tokens: 19_078 };
  assert.equal(costLine([unpriced]), "1 call, 13,498 tokens in, 5,580 out, no cost reported by the Hub");
  assert.equal(costLine([{ prompt_tokens: 1, completion_tokens: 2 }, { prompt_tokens: 3, completion_tokens: 4, cost_usd: 1 }]), "2 calls, 4 tokens in, 6 out, no cost reported by the Hub");
});

test("stamp records the source's digest on its translation without asking a model", async () => {
  const translated = "---\ntitle: T\nlang: pt-br\nexcerpt: E\ntags:\n- x\ntranslation_of: wave.md\nsource_digest: 0000\ntranslated_by: someone\n---\n\nUma onda.\n";
  const root = repository({ "posts/wave.md": post("en-us", "A wave."), "posts/wave.pt-br.md": translated });
  const said: string[] = [];
  const io = { root, cwd: root, out: (line: string) => said.push(line), err: (line: string) => said.push(line) };
  const wave = discover(root).find((source) => source.file === "posts/wave.md")!;
  assert.equal(stateOf(root, wave).status, "stale");
  const asked = hub.asked.length;

  assert.equal(await main(["stamp", "posts/wave.md"], io), 0, said.join("\n"));
  assert.equal(hub.asked.length, asked, "no model is asked");
  assert.match(said.join("\n"), /^stamped /m);
  assert.equal(stateOf(root, wave).status, "current");
  const written = fs.readFileSync(path.join(root, "posts/wave.pt-br.md"), "utf8");
  assert.equal(written, translated.replace("source_digest: 0000", `source_digest: ${wave.digest}`), "nothing else in the file changes");

  assert.equal(await main(["stamp", "posts/wave.md"], io), 0);
  assert.match(said.at(-1)!, /^current /);
  assert.equal(await main(["stamp"], io), 2, "it needs a file");
});
