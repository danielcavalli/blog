import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { after, before, test } from "node:test";
import { parse as parseYaml } from "yaml";

import { costLine, main } from "./cli.ts";
import { discover, readMarkdown, stateOf } from "./documents.ts";
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
      }),
    read: (file) => fs.readFileSync(path.join(root, file), "utf8"),
    exists: (file) => fs.existsSync(path.join(root, file)),
  };
}

const reply = (...replies: Reply[]) => hub.replies.push(...replies);

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

test("a missing translation is translated and written with its front matter", async () => {
  const w = world();
  reply({ answer: GOOD, cost: 0.0421 });
  assert.equal(await w.run("posts/tide.md"), 0, w.errors.join("\n"));

  assert.equal(
    w.read("posts/tide.pt-br.md"),
    "---\ntitle: A maré\nexcerpt: Por que a maré importa (um pouco).\ntags:\n- mar\nlang: pt-br\ntranslation_of: tide.md\n" +
      `source_digest: ${discover(w.root)[1]!.digest}\ntranslated_by: gpt-5.6-sol (high), via mare-hub\ntranslated_at: '2026-11-26'\n---\n\n${GOOD.content}\n`,
  );
  assert.equal(stateOf(w.root, discover(w.root)[1]!).status, "current");
  assert.deepEqual(w.lines, [
    "missing  posts/tide.md: translating with gpt-5.6-sol (high)…",
    "  wrote posts/tide.pt-br.md: 1 call, 1,000 tokens in, 200 out, $0.0421",
  ]);

  const [asked] = hub.asked;
  assert.equal(hub.asked.length, 1);
  assert.equal(asked!.model, "gpt-5.6-sol");
  assert.equal(asked!.reasoning_effort, "high");
  assert.equal(asked!.max_tokens, 64_000);
  assert.equal(asked!.response_format.json_schema.name, "translation");
  assert.deepEqual(asked!.messages.map((message) => message.role), ["system", "user"]);
  assert.match(asked!.messages[0]!.content, /^UNATTENDED LOCALIZATION AGENT\n/);
  assert.ok(asked!.messages[1]!.content.includes("- `lua.en-us.md` is written `lua.md`\n- `wave.md#big` is written `wave.pt-br.md#big`"));
  assert.ok(asked!.messages[1]!.content.includes("The tide comes in twice a day (more or less)"));
});

test("--model, --effort and --max-tokens choose the model, and the translation says which it was", async () => {
  const w = world();
  reply({ answer: GOOD });
  assert.equal(await w.run("posts/tide.md", "--model", "claude-opus-5", "--effort", "medium", "--max-tokens", "32000"), 0);
  assert.deepEqual([hub.asked[0]!.model, hub.asked[0]!.reasoning_effort, hub.asked[0]!.max_tokens], ["claude-opus-5", "medium", 32_000]);
  assert.equal(readMarkdown(w.read("posts/tide.pt-br.md")).meta.translated_by, "claude-opus-5 (medium), via mare-hub");
});

test("a translation that is current is left alone, unless --force", async () => {
  const w = world();
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), translated(w.root));
  assert.equal(await w.run("posts/tide.md"), 0);
  assert.equal(hub.asked.length, 0);
  assert.deepEqual(w.lines, ["current  posts/tide.md -> posts/tide.pt-br.md: nothing to do (--force translates it again)"]);
  assert.equal(w.read("posts/tide.pt-br.md"), translated(w.root));

  reply({ answer: { ...GOOD, title: "A maré, de novo" } });
  assert.equal(await w.run("posts/tide.pt-br.md", "--force"), 0, "a translation's own path names its source");
  assert.equal(hub.asked.length, 1);
  assert.equal(readMarkdown(w.read("posts/tide.pt-br.md")).meta.title, "A maré, de novo");
});

test("a stale translation is translated again, and the trailer at its end is kept byte for byte", async () => {
  const w = world();
  const stale = translated(w.root, { digest: "b".repeat(64), trailer: COMMENTS });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), stale.replace("lang: pt-br\n", "lang: pt-br\nreviewed_by: Daniel\n"));
  reply({ answer: { ...GOOD, content: GOOD.content.replace("sobe", "enche") } });
  assert.equal(await w.run("posts/tide.md"), 0, w.errors.join("\n"));
  const after = w.read("posts/tide.pt-br.md");
  assert.ok(after.endsWith(`\n\n${COMMENTS}`));
  assert.equal(readMarkdown(after).trailer, COMMENTS);
  assert.ok(after.includes("A maré enche duas vezes"));
  assert.equal(readMarkdown(after).meta.reviewed_by, "Daniel");
  assert.equal(stateOf(w.root, discover(w.root)[1]!).status, "current");
  assert.equal(w.lines[0], "stale    posts/tide.md: translating with gpt-5.6-sol (high)…");
});

test("--all translates what is missing or stale, and nothing else", async () => {
  const w = world();
  const wave = discover(w.root).find((source) => source.file === "posts/wave.md")!;
  fs.writeFileSync(path.join(w.root, "posts/wave.pt-br.md"), post("pt-br", "Ondas.", `translation_of: wave.md\nsource_digest: ${wave.digest}\n`));
  reply({ answer: { title: "T", excerpt: "E", tags: ["x"], content: "The moon." } }, { answer: GOOD });
  assert.equal(await w.run("--all"), 0, w.errors.join("\n"));
  assert.equal(hub.asked.length, 2);
  assert.ok(hub.asked[0]!.messages[1]!.content.startsWith("DOCUMENT\nposts/lua.md (post), pt-br to en-us"));
  assert.ok(hub.asked[0]!.messages[0]!.content.includes("Target: publishable US English technical-editorial prose."));
  assert.equal(readMarkdown(w.read("posts/lua.en-us.md")).meta.lang, "en-us");
  assert.equal(await w.run("status"), 0);
});

test("an answer that fails a check is repaired once, with the exact finding", async () => {
  const w = world();
  reply({ answer: DASHED, cost: 0.03 }, { answer: GOOD, cost: 0.02 });
  assert.equal(await w.run("posts/tide.md"), 0, w.errors.join("\n"));
  assert.equal(hub.asked.length, 2);
  const messages = hub.asked[1]!.messages;
  assert.deepEqual(messages.map((message) => message.role), ["system", "user", "assistant", "user"]);
  assert.equal(messages[2]!.content, JSON.stringify(DASHED));
  assert.match(messages[3]!.content, /^DETERMINISTIC VALIDATION FINDINGS\n/);
  assert.match(messages[3]!.content, /- Translation changed parenthetical asides: preserve parentheses around the same thoughts.*The source has 1 and the translation 0\. The source's, in order: 1\. "\(more or less\)"/);
  assert.equal(readMarkdown(w.read("posts/tide.pt-br.md")).body, GOOD.content);
  assert.equal(w.lines.at(-1), "  wrote posts/tide.pt-br.md: 2 calls, 2,000 tokens in, 400 out, $0.0500");
  assert.ok(w.errors.some((line) => line.includes("failed 1 check(s), asking for a repair")));
});

test("an answer that still fails after the repair is never written", async () => {
  const w = world();
  const stale = translated(w.root, { digest: "b".repeat(64), trailer: COMMENTS });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), stale);
  reply({ answer: DASHED }, { answer: { ...DASHED, content: DASHED.content.replace("lua.md", "lua.en-us.md") } }, { answer: GOOD });
  assert.equal(await w.run("posts/tide.md"), 1);
  assert.equal(hub.asked.length, 2, "one repair, not two");
  assert.equal(w.read("posts/tide.pt-br.md"), stale, "the file is as it was");
  const said = w.errors.join("\n");
  assert.match(said, /posts\/tide\.md: The translation failed its checks after one repair:/);
  assert.match(said, /- Translation changed protected link destinations: missing link `lua\.md`; not in the source link `lua\.en-us\.md`/);
  assert.match(said, /- Translation changed parenthetical asides/);
  assert.match(said, /2 calls, 2,000 tokens in, 400 out, \$0\.0200; nothing was written/);

  const fresh = world();
  reply({ answer: "not json at all" }, { answer: { title: "only a title" } });
  assert.equal(await fresh.run("posts/tide.md"), 1);
  assert.ok(!fresh.exists("posts/tide.pt-br.md"), "no file appears for a translation that failed");
  assert.match(fresh.errors.join("\n"), /Missing required field "content"/);
});

test("a trace keeps every question and the whole answer, the refused one too", async () => {
  const trace = path.join(repository({}), "trace.jsonl");
  const w = world({}, trace);
  reply({ answer: DASHED }, { answer: GOOD });
  assert.equal(await w.run("posts/tide.md"), 0, w.errors.join("\n"));
  const entries = fs.readFileSync(trace, "utf8").trim().split("\n").map((line) => JSON.parse(line) as { question: { messages: unknown[] }; answer: { content: string; usage: { cost_usd: number } } });
  assert.equal(entries.length, 2);
  assert.deepEqual(entries.map((entry) => entry.question.messages.length), [2, 4]);
  assert.equal(entries[0]!.answer.content, JSON.stringify(DASHED));
  assert.equal(entries[1]!.answer.usage.cost_usd, 0.01);
});

test("one document failing does not stop the others, and the run still fails", async () => {
  const w = world();
  reply({ status: 400, message: "unknown model 'gpt-9'" }, { answer: GOOD }, { answer: { title: "T", excerpt: "E", tags: ["x"], content: "Ondas." } });
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
  reply({ answer: GOOD });
  assert.equal(await w.run("posts/tide.md", "--out", out), 0, w.errors.join("\n"));
  assert.equal(w.read("posts/tide.pt-br.md"), existing);
  const written = fs.readFileSync(path.join(out, "posts/tide.pt-br.md"), "utf8");
  assert.equal(readMarkdown(written).meta.translated_by, "gpt-5.6-sol (high), via mare-hub");
  assert.equal(readMarkdown(written).trailer, COMMENTS, "it is the file that would have been written");
  assert.deepEqual(fs.readdirSync(out), ["posts"]);
});

test("--dry-run says what would be done, asks no model and writes nothing", async () => {
  const w = world();
  assert.equal(await w.run("--all", "--dry-run"), 0);
  assert.equal(hub.asked.length, 0);
  assert.equal(w.lines.length, 3);
  assert.match(w.lines[1]!, /^missing {2}posts\/tide\.md: would translate into posts\/tide\.pt-br\.md with gpt-5\.6-sol \(high\); [\d,]+ characters of guidance, [\d,]+ of document$/);
  assert.deepEqual(fs.readdirSync(path.join(w.root, "posts")).sort(), ["lua.md", "tide.md", "wave.md"]);
});

test("the CV is translated to YAML that says what it translates", async () => {
  const cv = "# The CV.\nname: Daniel\ntagline: Engineer\ncontact:\n  email: d@example.com\nskills:\n- Distributed Systems\n";
  const w = world({ "cv_data.yaml": cv });
  reply({ answer: { name: "Daniel", tagline: "Engenheiro", contact: { email: "d@exemplo.com" }, skills: ["sistemas distribuídos"] } });
  reply({ answer: { tagline: "Engenheiro", name: "Daniel", skills: ["sistemas distribuídos"], contact: { email: "d@example.com" } } });
  assert.equal(await w.run("cv_data.yaml"), 0, w.errors.join("\n"));
  assert.equal(hub.asked[0]!.response_format.json_schema.name, "cv_translation");
  assert.match(hub.asked[0]!.messages[0]!.content, /Produce a localized CV draft/);
  assert.match(hub.asked[1]!.messages[3]!.content, /- CV translation changed contact details/);
  const text = w.read("cv_data.pt-br.yaml");
  assert.deepEqual(parseYaml(text), { name: "Daniel", tagline: "Engenheiro", contact: { email: "d@example.com" }, skills: ["sistemas distribuídos"] });
  assert.ok(text.includes("# translation_of: cv_data.yaml\n# source_digest: "));
  assert.equal(stateOf(w.root, discover(w.root).at(-1)!).status, "current");
  assert.equal(w.read("cv_data.yaml"), cv);
});

// ---------- revise ----------

const revision = (comments: unknown[], content = GOOD.content.replace("sobe", "enche")) => ({ ...GOOD, content, comments });

test("revise sends the open comments as the owner's instructions and marks the handled ones addressed", async () => {
  const w = world();
  const before = translated(w.root, { trailer: COMMENTS });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), before);
  reply({
    answer: revision([
      { id: 1, addressed: true, note: '"sobe" virou "enche".' },
      { id: 2, addressed: false, note: "É uma pergunta: sim, a legenda corresponde à fonte." },
    ]),
  });
  assert.equal(await w.run("revise", "posts/tide.pt-br.md"), 0, w.errors.join("\n"));

  const [asked] = hub.asked;
  assert.equal(hub.asked.length, 1);
  assert.equal(asked!.response_format.json_schema.name, "revision");
  assert.match(asked!.messages[0]!.content, /\nOWNER REVISION\n/);
  const user = asked!.messages[1]!.content;
  assert.ok(user.includes(`<current_translation>\n${GOOD.content}\n</current_translation>`));
  assert.ok(user.includes('Comment 1, line 1\nQuoted passage:\n> sobe\nAround it: …A maré [the passage] duas vezes por dia…\nDaniel Cavalli wrote:\nPrefiro "enche".'));
  assert.ok(user.includes("Comment 2, line 3\nQuoted passage:\n> Maré baixa\nDaniel Cavalli wrote:\nIsso está certo?"));
  assert.ok(!user.includes("Resolvido."), "a comment that is not open is not an instruction");
  assert.ok(user.includes("The tide comes in twice a day"), "the source goes too");

  const after = w.read("posts/tide.pt-br.md");
  const written = readMarkdown(after);
  assert.equal(written.body, GOOD.content.replace("sobe", "enche"));
  assert.equal(written.trailer, COMMENTS.replace("<!-- reef comment 1 · open · ", "<!-- reef comment 1 · addressed · "), "one word of the trailer changed");
  assert.equal(written.meta.translated_by, "gpt-5.6-sol (high), via mare-hub");
  assert.equal(stateOf(w.root, discover(w.root)[1]!).status, "current");
  assert.deepEqual(w.lines, [
    "revised posts/tide.pt-br.md: 1 call, 1,000 tokens in, 200 out, $0.0100",
    '  #1 addressed: "sobe" virou "enche".',
    "  #2 left open: É uma pergunta: sim, a legenda corresponde à fonte.",
  ]);
});

test("revise with no open comment does nothing", async () => {
  const w = world();
  const before = translated(w.root, { trailer: COMMENTS.replaceAll(" · open · ", " · addressed · ") });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), before);
  assert.equal(await w.run("revise", "posts/tide.pt-br.md"), 0);
  assert.equal(hub.asked.length, 0);
  assert.equal(w.read("posts/tide.pt-br.md"), before);
  assert.deepEqual(w.lines, ["posts/tide.pt-br.md: no open comments, nothing to revise"]);
});

test("a revision must pass the same checks, account for every comment, and change something", async () => {
  const w = world();
  const before = translated(w.root, { trailer: COMMENTS });
  fs.writeFileSync(path.join(w.root, "posts/tide.pt-br.md"), before);
  reply(
    { answer: revision([{ id: 1, addressed: true, note: "feito" }]) },
    { answer: revision([{ id: 1, addressed: true, note: "feito" }, { id: 2, addressed: true, note: "feito" }], GOOD.content) },
  );
  assert.equal(await w.run("revise", "posts/tide.pt-br.md"), 1);
  assert.equal(hub.asked.length, 2);
  assert.match(hub.asked[1]!.messages[3]!.content, /- "comments" must have exactly one entry for comment 2, and has 0/);
  assert.match(w.errors.join("\n"), /The answer says comments are addressed and changes nothing in the translation/);
  assert.equal(w.read("posts/tide.pt-br.md"), before, "nothing was written, and no comment was marked");

  reply({ answer: revision([{ id: 1, addressed: true, note: "feito" }, { id: 2, addressed: true, note: "feito" }], DASHED.content) }, { answer: DASHED });
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
    "posts/tide.pt-br.md: 2 open comment(s) would go to gpt-5.6-sol (high)",
    '  #1 Daniel Cavalli: Prefiro "enche".',
    "  #2 Daniel Cavalli: Isso está certo?",
  ]);
  assert.equal(hub.asked.length, 0);

  const out = repository({});
  reply({ answer: revision([{ id: 1, addressed: true, note: "feito" }, { id: 2, addressed: true, note: "feito" }]) });
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
