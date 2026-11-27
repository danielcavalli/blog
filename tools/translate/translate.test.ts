import assert from "node:assert/strict";
import { test } from "node:test";
import { parse as parseYaml } from "yaml";

import { cvHeader, readMarkdown } from "./documents.ts";
import type { CvDocument, ProseDocument } from "./documents.ts";
import type { Answer, Question } from "./hub.ts";
import { CheckError, converse, renderCv, renderProse } from "./translate.ts";
import type { Settings } from "./translate.ts";

const settings = (over: Partial<Settings> = {}): Settings => ({
  model: "gpt-5.6-sol",
  effort: "high",
  maxTokens: 64_000,
  today: "2026-11-26",
  ...over,
});

const source = (over: Partial<ProseDocument> = {}): ProseDocument => ({
  kind: "post",
  file: "posts/tide.md",
  lang: "en-us",
  target: "pt-br",
  translation: "posts/tide.pt-br.md",
  digest: "d".repeat(64),
  title: "The tide: a note",
  excerpt: "Why it matters.",
  tags: ["sea", "moon"],
  body: "The tide.",
  meta: { title: "The tide: a note", date: "2026-11-01", lang: "en-us", excerpt: "Why it matters.", tags: ["sea", "moon"], slug: "tide" },
  ...over,
});

const answer = { title: "A maré: uma nota", excerpt: "Por que importa.", tags: ["mar", "lua"], content: "\nA maré.\n\nSegundo parágrafo.\n\n" };

const TRAILER =
  "<!-- reef document k3x9f2 · revision 3 · note the method comes before the results -->\n" +
  "<!-- reef comment 4 · open · Daniel Cavalli · 2026-10-05T14:02Z · line 3\n> a reader sees\nSay who the reader is.\n-->\n\n" +
  "<!-- reef reply 4 · Claude · 2026-10-05T14:20Z\nIn section 2.\n-->";

// ---------- the file ----------

test("a translation is written with its front matter, in order, and its body", () => {
  assert.equal(
    renderProse(source(), answer, null, settings()),
    [
      "---",
      "title: 'A maré: uma nota'",
      "excerpt: Por que importa.",
      "tags:",
      "- mar",
      "- lua",
      "lang: pt-br",
      "translation_of: tide.md",
      `source_digest: ${"d".repeat(64)}`,
      "translated_by: gpt-5.6-sol (high), via mare-hub",
      "translated_at: '2026-11-26'",
      "---",
      "",
      "A maré.",
      "",
      "Segundo parágrafo.",
      "",
    ].join("\n"),
  );
});

test("what is written reads back as what was written", () => {
  const { meta, body, trailer } = readMarkdown(renderProse(source(), answer, null, settings({ model: "claude-opus-5", effort: "medium" })));
  assert.deepEqual(meta, {
    title: "A maré: uma nota",
    excerpt: "Por que importa.",
    tags: ["mar", "lua"],
    lang: "pt-br",
    translation_of: "tide.md",
    source_digest: "d".repeat(64),
    translated_by: "claude-opus-5 (medium), via mare-hub",
    translated_at: "2026-11-26",
  });
  assert.equal(body, "A maré.\n\nSegundo parágrafo.");
  assert.equal(trailer, "");
});

test("a page without excerpt or tags gets neither", () => {
  const about = source({ kind: "about", file: "pages/about.md", meta: { title: "About", lang: "en-us" } });
  const text = renderProse(about, { title: "Sobre", excerpt: "", tags: [], content: "Eu." }, null, settings());
  assert.deepEqual(Object.keys(readMarkdown(text).meta), ["title", "lang", "translation_of", "source_digest", "translated_by", "translated_at"]);
  assert.equal(readMarkdown(text).meta.translation_of, "about.md");
});

test("the trailer an existing translation ends with is kept byte for byte", () => {
  for (const trailer of [TRAILER, `${TRAILER}\n`, `${TRAILER}\n\n\n`, TRAILER.replaceAll("\n", "\r\n")]) {
    const before = `---\ntitle: Velho\nlang: pt-br\ntranslation_of: tide.md\nsource_digest: old\n---\n\nTexto antigo.\n\n${trailer}`;
    const previous = readMarkdown(before);
    assert.equal(previous.trailer, trailer);
    const after = renderProse(source(), answer, previous, settings());
    assert.ok(after.endsWith(`\nSegundo parágrafo.\n\n${trailer}`), "the new body, a blank line, then the trailer as it was");
    assert.equal(readMarkdown(after).trailer, trailer);
    assert.equal(readMarkdown(after).body, "A maré.\n\nSegundo parágrafo.");
    assert.ok(!after.includes("Texto antigo"));
    assert.equal(readMarkdown(after).meta.source_digest, "d".repeat(64));
  }
});

test("front matter someone added to a translation by hand is kept", () => {
  const previous = { meta: { title: "Velho", lang: "pt-br", source_digest: "old", translated_by: "x", reviewed: true, note: "keep: me" }, trailer: "" };
  const { meta } = readMarkdown(renderProse(source(), answer, previous, settings()));
  assert.equal(meta.title, "A maré: uma nota");
  assert.equal(meta.translated_by, "gpt-5.6-sol (high), via mare-hub");
  assert.equal(meta.reviewed, true);
  assert.equal(meta.note, "keep: me");
  assert.deepEqual(Object.keys(meta).slice(-2), ["reviewed", "note"]);
});

test("the translated CV is YAML in the source's order, with what it translates at its head", () => {
  const cv: CvDocument = {
    kind: "cv",
    file: "cv_data.yaml",
    lang: "en-us",
    target: "pt-br",
    translation: "cv_data.pt-br.yaml",
    digest: "c".repeat(64),
    data: { name: "Daniel", tagline: "Engineer: ML", contact: { email: "d@example.com", github: "d" }, skills: ["A", "B"] },
  };
  const text = renderCv(cv, { skills: ["A", "bê"], contact: { github: "d", email: "d@example.com" }, tagline: "Engenheiro: ML", name: "Daniel" }, settings());
  assert.deepEqual(cvHeader(text), {
    translation_of: "cv_data.yaml",
    source_digest: "c".repeat(64),
    translated_by: "gpt-5.6-sol (high), via mare-hub",
    translated_at: "2026-11-26",
  });
  assert.ok(text.endsWith("\n\nname: Daniel\ntagline: 'Engenheiro: ML'\ncontact:\n  email: d@example.com\n  github: d\nskills:\n- A\n- bê\n"));
  assert.deepEqual(parseYaml(text), { name: "Daniel", tagline: "Engenheiro: ML", contact: { email: "d@example.com", github: "d" }, skills: ["A", "bê"] });
});

// ---------- asking, checking, repairing ----------

// A model that gives these answers in turn, and remembers what it was asked.
function model(...contents: string[]) {
  const asked: Question[] = [];
  const ask = async (question: Question): Promise<Answer> => {
    asked.push(structuredClone(question));
    return { content: contents[asked.length - 1] ?? "{}", model: question.model, usage: { prompt_tokens: 10, completion_tokens: 5, cost_usd: 0.5 } };
  };
  return { asked, ask };
}

const job = {
  system: "guidance",
  user: "document",
  schema: { name: "translation", schema: {} },
  check: (value: unknown) => ({
    findings: (value as { ok?: boolean }).ok ? [] : ["Translation changed protected fenced code: fenced block 1", "Cannot accept an empty translation"],
    warnings: (value as { short?: boolean }).short ? ["suspiciously short"] : [],
  }),
};

test("an answer that passes its checks is accepted in one call", async () => {
  const { asked, ask } = model('{"ok":true,"short":true}');
  const outcome = await converse(job, settings({ ask }));
  assert.deepEqual(outcome.answer, { ok: true, short: true });
  assert.deepEqual(outcome.warnings, ["suspiciously short"]);
  assert.equal(outcome.usages.length, 1);
  assert.equal(asked.length, 1);
  assert.deepEqual(asked[0], {
    model: "gpt-5.6-sol",
    effort: "high",
    maxTokens: 64_000,
    messages: [
      { role: "system", content: "guidance" },
      { role: "user", content: "document" },
    ],
    schema: job.schema,
  });
});

test("an answer that fails a check gets one repair call, with the exact findings", async () => {
  const log: string[] = [];
  const { asked, ask } = model('{"ok":false}', '{"ok":true}');
  const outcome = await converse(job, settings({ ask, log: (line) => log.push(line) }));
  assert.deepEqual(outcome.answer, { ok: true });
  assert.equal(outcome.usages.length, 2);
  assert.equal(asked.length, 2);
  const [, , previous, repair] = asked[1]!.messages;
  assert.deepEqual(asked[1]!.messages.slice(0, 2), asked[0]!.messages, "the same guidance and document");
  assert.deepEqual(previous, { role: "assistant", content: '{"ok":false}' });
  assert.equal(repair!.role, "user");
  assert.match(repair!.content, /^DETERMINISTIC VALIDATION FINDINGS\n/);
  assert.ok(repair!.content.includes("- Translation changed protected fenced code: fenced block 1\n- Cannot accept an empty translation\n"));
  assert.ok(log.some((line) => line.includes("Translation changed protected fenced code")), "the findings are shown");
});

test("an answer that fails again after the repair is an error, loudly", async () => {
  const { asked, ask } = model('{"ok":false}', '{"ok":false}', '{"ok":true}');
  await assert.rejects(converse(job, settings({ ask })), (error: unknown) => {
    assert.ok(error instanceof CheckError);
    assert.deepEqual(error.findings, ["Translation changed protected fenced code: fenced block 1", "Cannot accept an empty translation"]);
    assert.match(error.message, /failed its checks after one repair:\n {2}- Translation changed protected fenced code/);
    assert.equal(error.usages.length, 2);
    return true;
  });
  assert.equal(asked.length, 2, "one repair, never a second");
});

test("an answer that is not JSON is a finding like any other", async () => {
  const { asked, ask } = model("Here is the translation: …", '```json\n{"ok":true}\n```');
  const outcome = await converse(job, settings({ ask }));
  assert.deepEqual(outcome.answer, { ok: true }, "a code fence around the JSON is not held against the model");
  assert.match(asked[1]!.messages[3]!.content, /- The answer is not valid JSON: /);
});
