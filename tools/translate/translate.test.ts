import assert from "node:assert/strict";
import { test } from "node:test";
import { parse as parseYaml } from "yaml";

import { readComments } from "./comments.ts";
import { cvHeader, readMarkdown } from "./documents.ts";
import type { CvDocument, ProseDocument } from "./documents.ts";
import type { Answer, Question } from "./hub.ts";
import { json } from "./prompt.ts";
import { DocumentRun, stageName } from "./runs.ts";
import { CheckError, MAX_REVISION_PASSES, RejectedError, accepted, converse, localize, renderCv, renderProse } from "./translate.ts";
import type { Settings } from "./translate.ts";

const settings = (over: Partial<Settings> = {}): Settings => ({
  model: "gpt-5.6-sol",
  effort: "high",
  criticModel: "claude-opus-5-5",
  criticEffort: "medium",
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

// ---------- the process ----------

const TIDE = source({ body: "The tide comes in twice a day (more or less).\n\nIt should sound familiar.", digest: "e".repeat(64) });

const ANALYSIS = {
  author_voice_summary: "Dry, first person.",
  tone: "wry",
  register: "technical-editorial",
  sentence_rhythm: ["short"],
  connective_tissue: ["but"],
  rhetorical_moves: ["analogy"],
  humor_signals: ["understatement"],
  stance_markers: ["I think"],
  must_preserve: ["the aside"],
};
const POLICY = {
  keep_english: ["prompt"],
  localize: ["tide"],
  context_sensitive: [],
  do_not_translate: ["Claude Code"],
  resolved_decisions: [{ source_term: "tide", approved_rendering: "maré", decision: "localize", scope: "artifact-wide", applies_to: ["body"], notes: "plain word" }],
  consistency_rules: [],
  rationale_notes: [],
};
const DRAFT = { title: "A maré: uma nota", excerpt: "Por que importa.", tags: ["mar", "lua"], content: "A maré sobe duas vezes por dia (mais ou menos).\n\nDeveria soar familiar." };
const SCORES = { accuracy_completeness: 90, terminology_entities: 90, markdown_code_link_fidelity: 99, locale_naturalness: 70, borrowing_consistency: 90, rhetorical_structure: 85 };
const critique = (needs: boolean, ids = needs ? ["finding-1"] : []) => ({
  score: needs ? 78.5 : 96,
  feedback: needs ? "One calque." : "No material defect.",
  needs_refinement: needs,
  dimension_scores: SCORES,
  critical_errors: 0,
  major_core_errors: needs ? 1 : 0,
  confidence: 0.8,
  findings: ids.map((id) => ({ id, severity: "major", dimension: "locale_naturalness", source_span: "It should sound familiar.", target_span: "Deveria soar familiar.", description: "Calque.", fix_hint: "Rebuild it." })),
});
// A revision whose report applies these findings.
const revised = (content: string, applied: string[] = []) => ({
  ...DRAFT,
  content,
  applied_feedback: applied.map((finding_id) => ({ finding_id, status: "applied", rationale: "rebuilt the closing sentence" })),
  declined_feedback: [],
  rewrite_summary: ["closing sentence"],
  unresolved_risks: [],
});
const FIRST = revised("A maré enche duas vezes por dia (mais ou menos).\n\nE isso deveria soar familiar.", ["finding-1"]);
const SECOND = revised("A maré enche duas vezes por dia (mais ou menos).\n\nSe isso soa familiar, não é por acaso.", ["finding-1"]);
const ISSUE = { passage: "E isso deveria soar familiar.", violates: "Punctuation conventions: prefer PT-BR clause rhythm over copied English pauses", failure: "It still moves like the English sentence." };
const review = (accept: boolean, issues = accept ? [] : [ISSUE]) => ({
  accept,
  publish_ready: accept,
  confidence: 0.9,
  residual_issues: issues,
  voice_score: 90.5,
  terminology_score: 92,
  locale_naturalness_score: accept ? 88 : 61,
});

// A model that gives these answers in turn (as JSON), and remembers what it was asked.
function scripted(...answers: unknown[]) {
  return model(...answers.map((answer) => (typeof answer === "string" ? answer : JSON.stringify(answer))));
}

const prose = (value: typeof FIRST) => ({ title: value.title, excerpt: value.excerpt, tags: value.tags, content: value.content });
const user = (question: Question) => question.messages[1]!.content;
const system = (question: Question) => question.messages[0]!.content;

test("the stages run in the old engine's order, each on its model, each given what came before it", async () => {
  const { asked, ask } = scripted(ANALYSIS, POLICY, DRAFT, critique(true), FIRST, review(true));
  const run = new DocumentRun();
  const result = await localize(TIDE, [TIDE], settings({ ask }), { run });

  assert.deepEqual(
    asked.map((question) => [question.schema.name, question.model, question.effort]),
    [
      ["source_analysis", "gpt-5.6-sol", "high"],
      ["terminology_policy", "gpt-5.6-sol", "high"],
      ["translation", "gpt-5.6-sol", "high"],
      ["critique", "claude-opus-5-5", "medium"],
      ["revision", "gpt-5.6-sol", "high"],
      ["final_review", "claude-opus-5-5", "medium"],
    ],
  );
  assert.deepEqual(
    asked.map((question) => /\n(SOURCE ANALYSIS|TERMINOLOGY POLICY|TRANSLATE|CRITIQUE|REVISE|FINAL REVIEW)\n/.exec(system(question))![1]),
    ["SOURCE ANALYSIS", "TERMINOLOGY POLICY", "TRANSLATE", "CRITIQUE", "REVISE", "FINAL REVIEW"],
  );
  const [analysis, policy, draft, critic, revision, final] = asked.map(user);
  const analysisJson = `SOURCE ANALYSIS JSON (MODEL ADVICE)\n${json(ANALYSIS)}`;
  const policyJson = /TERMINOLOGY POLICY JSON \(MODEL PROPOSAL\)\n\{[\s\S]*?\n\}/;
  assert.ok(!analysis!.includes("SOURCE ANALYSIS JSON") && analysis!.includes("The tide comes in"), "the analysis reads the source alone");
  for (const later of [policy, draft, critic, revision]) assert.ok(later!.includes(analysisJson), "the analysis goes to every stage after it but the final review");
  for (const later of [draft, critic, revision]) assert.match(later!, policyJson);
  assert.ok(policy!.indexOf("SOURCE ANALYSIS JSON") < policy!.indexOf("SOURCE MARKDOWN"));
  assert.ok(draft!.includes('"preferred_rendering": "maré"'), "the policy as its contract normalized it, as the old engine passed it on");
  assert.ok(critic!.includes(`TRANSLATED CANDIDATE JSON\n${json(DRAFT)}`), "the critic reads the draft");
  assert.ok(revision!.includes(`TRANSLATED CANDIDATE JSON\n${json(DRAFT)}`) && revision!.includes('CRITIQUE JSON\n{\n  "confidence": 0.8,'));
  assert.ok(revision!.includes('"rewrite_instruction": "Rebuild it."'), "the critique as its contract normalized it");
  assert.ok(final!.includes(`LOCALIZED CANDIDATE JSON\n${json(prose(FIRST))}`), "the final review reads the revision");

  assert.deepEqual(result.candidate, prose(FIRST));
  assert.equal(result.passes, 1);
  assert.equal(result.review.locale_naturalness_score, 88);
  assert.equal(result.usages.length, 6);
  assert.deepEqual(run.stages.map(stageName), ["source_analysis", "terminology_policy", "translate", "pass-1-critique", "pass-1-revise", "pass-1-final_review"]);
});

test("rule 1: the revision runs after every critique; needs_refinement false cannot skip it", async () => {
  const polished = revised("A maré enche duas vezes por dia (mais ou menos).\n\nIsso deveria soar familiar.");
  const { asked, ask } = scripted(ANALYSIS, POLICY, DRAFT, critique(false), polished, review(true));
  const result = await localize(TIDE, [TIDE], settings({ ask }));
  assert.deepEqual(asked.map((question) => question.schema.name), ["source_analysis", "terminology_policy", "translation", "critique", "revision", "final_review"]);
  assert.match(system(asked[4]!), /This pass is required even when critique says no refinement is needed\./);
  assert.ok(user(asked[4]!).includes('"needs_refinement": false'), "the writer sees the critic's verdict, and revises anyway");
  assert.deepEqual(result.candidate, prose(polished), "what is written is the revision, not the draft");
});

test("rule 2: the revision says, for every critique finding, applied or declined and why", async () => {
  const declined = { ...revised(DRAFT.content), declined_feedback: [{ finding_id: "finding-2", status: "declined", rationale: "The source says exactly this; the wording already meets the guidance." }] };
  const both = { ...declined, applied_feedback: [{ finding_id: "finding-1", status: "applied", rationale: "rebuilt" }], content: FIRST.content };
  const silent = revised(FIRST.content, ["finding-1"]);
  const stray = { ...both, applied_feedback: [...both.applied_feedback, { finding_id: "finding-9", status: "applied", rationale: "x" }] };
  const { asked, ask } = scripted(ANALYSIS, POLICY, DRAFT, critique(true, ["finding-1", "finding-2"]), silent, both, review(true));
  const run = new DocumentRun();
  const result = await localize(TIDE, [TIDE], settings({ ask }), { run });
  assert.match(asked[5]!.messages[3]!.content, /- Critique finding finding-2 must have exactly one entry, in applied_feedback \(applied, with the edit\) or in declined_feedback \(declined, with why\), and has 0/);
  assert.deepEqual((run.stages[4]!.output as { declined_feedback: unknown[] }).declined_feedback, declined.declined_feedback, "a declined point is kept with its reason");
  assert.deepEqual(result.candidate, prose(both as typeof FIRST));
  assert.match(system(asked[4]!), /- Give every critique finding id exactly one entry: in applied_feedback, saying what you changed, or in declined_feedback, saying why the wording stands\./);
  assert.match(system(asked[4]!), /Preserve passages that already satisfy the source and locale guidance\./);

  const again = scripted(ANALYSIS, POLICY, DRAFT, critique(true, ["finding-1", "finding-2"]), stray, stray);
  await assert.rejects(localize(TIDE, [TIDE], settings({ ask: again.ask })), (error: unknown) => {
    assert.ok(error instanceof CheckError);
    assert.deepEqual(error.findings, ["applied_feedback or declined_feedback has an entry for finding-9, which is not one of the critique's findings"]);
    return true;
  });
});

test("rule 3: a final review accepts only with accept, publish_ready and no residual issue; scores never decide", async () => {
  const low = { ...review(true), voice_score: 5, terminology_score: 5, locale_naturalness_score: 5, confidence: 0.1 };
  const accepting = await localize(TIDE, [TIDE], settings({ ask: scripted(ANALYSIS, POLICY, DRAFT, critique(false), revised(DRAFT.content), low).ask }));
  assert.equal(accepting.passes, 1, "low scores do not reject");
  assert.equal(accepting.review.voice_score, 5, "and they are recorded");

  const high = { ...review(true, [{ ...ISSUE, passage: "Deveria soar familiar." }]), voice_score: 100, terminology_score: 100, locale_naturalness_score: 100 };
  const rejecting = scripted(ANALYSIS, POLICY, DRAFT, critique(false), revised(DRAFT.content), high, critique(false), revised(DRAFT.content), review(true));
  assert.equal((await localize(TIDE, [TIDE], settings({ ask: rejecting.ask }))).passes, 2, "perfect scores with an issue do not accept");
  assert.equal(accepted(review(true, [ISSUE])), false);
  assert.equal(accepted({ ...review(true), publish_ready: false }), false);
});

test("rule 3: a residual issue must quote a real passage and name what it violates, or the review is sent back", async () => {
  const vague = review(false, [{ passage: "", violates: "Style constraints", failure: "stiff" }]);
  const unnamed = review(false, [{ passage: "Deveria soar familiar.", violates: " ", failure: "stiff" }]);
  const invented = review(false, [{ passage: "A maré está alta.", violates: "Style constraints", failure: "stiff" }]);
  const bare = { ...review(false), residual_issues: ["the prose is stiff"] };
  for (const [bad, said] of [
    [vague, /residual_issues\[0\] quotes no passage/],
    [unnamed, /residual_issues\[0\] names nothing it violates/],
    [invented, /residual_issues\[0\] quotes "A maré está alta\.", which is in neither the candidate nor the source/],
    [bare, /Field "residual_issues\[0\]" must be an object with `passage`, `violates` and `failure`/],
  ] as const) {
    const { ask } = scripted(ANALYSIS, POLICY, DRAFT, critique(false), revised(DRAFT.content), bad, bad);
    await assert.rejects(localize(TIDE, [TIDE], settings({ ask })), (error: unknown) => error instanceof CheckError && said.test(error.findings.join("\n")));
  }
  const quoted = review(false, [{ ...ISSUE, passage: "“Deveria … familiar.”" }, { ...ISSUE, passage: "It should sound familiar." }]);
  const { ask } = scripted(ANALYSIS, POLICY, DRAFT, critique(false), revised(DRAFT.content), quoted, critique(false), revised(DRAFT.content), review(true));
  assert.equal((await localize(TIDE, [TIDE], settings({ ask }))).passes, 2, "quotation marks, an ellipsis and a passage of the source all count as quoting");
});

test("rule 4: a rejected review's issues go to the next critique and revision, never to the next final review", async () => {
  const { asked, ask } = scripted(ANALYSIS, POLICY, DRAFT, critique(true), FIRST, review(false), critique(true), SECOND, review(true));
  const run = new DocumentRun();
  const result = await localize(TIDE, [TIDE], settings({ ask }), { run });
  assert.equal(asked.length, 9);
  const carried = `PREVIOUS FINAL REVIEW RESIDUAL ISSUES\nThe previous pass's final review did not accept this candidate, for these issues:\n${json([ISSUE])}`;
  for (const index of [3, 4, 5, 8]) assert.ok(!user(asked[index]!).includes("PREVIOUS FINAL REVIEW"), `call ${index + 1} has no earlier issues`);
  assert.ok(user(asked[6]!).includes(carried), "pass 2's critic gets them");
  assert.ok(user(asked[7]!).includes(carried), "and so does pass 2's revision");
  assert.ok(user(asked[6]!).includes(`TRANSLATED CANDIDATE JSON\n${json(prose(FIRST))}`), "pass 2's critic reads pass 1's revision");
  assert.deepEqual(result.candidate, prose(SECOND));
  assert.equal(result.passes, 2);
  assert.deepEqual(run.stages.slice(6).map(stageName), ["pass-2-critique", "pass-2-revise", "pass-2-final_review"]);
});

test("rule 5: the analysis and the policy are proposals; the policy's names do not join the protected list", async () => {
  const { asked, ask } = scripted(ANALYSIS, POLICY, DRAFT, critique(false), revised(DRAFT.content), review(true));
  await localize(TIDE, [TIDE], settings({ ask }));
  for (const question of asked.slice(2)) {
    const protectedNames = /\nDO_NOT_TRANSLATE_ENTITIES\n([\s\S]*?)\n\n/.exec(system(question))![1]!;
    assert.ok(!protectedNames.includes("Claude Code"), `${question.schema.name}: the policy's name is not protected`);
  }
  assert.ok(user(asked[2]!).includes('"do_not_translate": [\n    "Claude Code"\n  ]'), "it is shown as the policy's proposal");
  assert.match(user(asked[3]!), /\nTERMINOLOGY POLICY JSON \(MODEL PROPOSAL\)\n/);
  assert.match(system(asked[3]!), /a generated terminology preference is not a violation of human policy/);
});

test(`still rejected after pass ${MAX_REVISION_PASSES}, the document fails with the reviewer's residual issues`, async () => {
  assert.equal(MAX_REVISION_PASSES, 2, "the old engine's _max_revision_passes");
  const { asked, ask } = scripted(ANALYSIS, POLICY, DRAFT, critique(true), FIRST, review(false), critique(true), FIRST, review(false), review(true));
  await assert.rejects(localize(TIDE, [TIDE], settings({ ask })), (error: unknown) => {
    assert.ok(error instanceof RejectedError);
    assert.equal(error.passes, 2);
    assert.deepEqual(error.review.residual_issues, [ISSUE]);
    assert.match(error.message, /rejected the translation after 2 of 2 passes; its residual issues:\n {2}- "E isso deveria soar familiar\.": It still moves like the English sentence\. \(violates: Punctuation conventions/);
    return true;
  });
  assert.equal(asked.length, 9, "no third pass");
});

test("an answer that breaks its stage's contract is repaired once, and fails the document the second time", async () => {
  const broken = { ...critique(false), needs_refinement: "no" };
  const { asked, ask } = scripted(ANALYSIS, POLICY, DRAFT, broken, broken);
  const run = new DocumentRun();
  await assert.rejects(localize(TIDE, [TIDE], settings({ ask }), { run }), (error: unknown) => {
    assert.ok(error instanceof CheckError);
    assert.deepEqual(error.findings, ['Field "needs_refinement" must be a boolean, and is a string']);
    return true;
  });
  assert.equal(asked.length, 5);
  assert.match(asked[4]!.messages[3]!.content, /^DETERMINISTIC VALIDATION FINDINGS\n[\s\S]*- Field "needs_refinement" must be a boolean/);
  assert.deepEqual(run.stages.at(-1)!.findings, ['Field "needs_refinement" must be a boolean, and is a string']);
  assert.equal(run.stages.at(-1)!.usages.length, 2);
});

test("a revision is held to the same deterministic checks as the draft, with its one repair", async () => {
  const dashed = revised("A maré enche duas vezes por dia — mais ou menos.\n\nE isso deveria soar familiar.", ["finding-1"]);
  const { asked, ask } = scripted(ANALYSIS, POLICY, DRAFT, critique(true), dashed, FIRST, review(true));
  const run = new DocumentRun();
  const result = await localize(TIDE, [TIDE], settings({ ask }), { run });
  assert.match(asked[5]!.messages[3]!.content, /- Translation changed parenthetical asides/);
  assert.deepEqual(result.candidate, prose(FIRST));
  assert.equal(run.stages[4]!.repaired.length, 1);
});

test("the owner's revision: his comments reach the revise stage first, then the passes, and every stage sees them", async () => {
  const comments = readComments(
    "<!-- reef comment 4 · open · Daniel Cavalli · 2026-10-05T14:02Z · line 1\n> sobe\nPrefiro \"enche\".\n-->\n" +
      "<!-- reef comment 5 · open · Daniel Cavalli · 2026-10-05T14:03Z · line 3\n> Deveria\nIsso está certo?\n-->",
  );
  const owner = { current: DRAFT, comments };
  const answered = { ...revised(FIRST.content), comments: [{ id: 4, addressed: true, note: '"sobe" virou "enche".' }, { id: 5, addressed: false, note: "Uma pergunta." }] };
  const { asked, ask } = scripted(ANALYSIS, POLICY, answered, critique(false), revised(FIRST.content), review(true));
  const run = new DocumentRun();
  const result = await localize(TIDE, [TIDE], settings({ ask }), { owner, run });

  assert.deepEqual(asked.map((question) => question.schema.name), ["source_analysis", "terminology_policy", "owner_revision", "critique", "revision", "final_review"]);
  const revise = asked[2]!;
  assert.equal(revise.model, "gpt-5.6-sol");
  assert.match(system(revise), /\nREVISE\nRewrite the translated candidate using the source artifact and critique\.[\s\S]*\nOWNER REVISION\nThe owner read the translation in TRANSLATED CANDIDATE JSON/);
  assert.ok(user(revise).includes(`TRANSLATED CANDIDATE JSON\n${json(DRAFT)}`), "the translation as it stands is the candidate");
  for (const question of asked) {
    assert.ok(user(question).includes('OWNER REVISION INSTRUCTIONS\nComment 4, line 1\nQuoted passage:\n> sobe\nDaniel Cavalli wrote:\nPrefiro "enche".'), `${question.schema.name} sees the comments`);
  }
  assert.ok(user(asked[3]!).includes(`TRANSLATED CANDIDATE JSON\n${json(prose(FIRST))}`), "the critic reads the owner's revision");
  assert.deepEqual(result.handled.map(({ comment, addressed }) => [comment.id, addressed]), [[4, true], [5, false]]);
  assert.deepEqual(result.candidate, prose(FIRST));
  assert.deepEqual(run.stages.map(stageName), ["source_analysis", "terminology_policy", "revise-owner", "pass-1-critique", "pass-1-revise", "pass-1-final_review"]);
});

test("a CV goes through the same stages with its own prompts, and its revision accounts for every finding", async () => {
  const cv: CvDocument = { kind: "cv", file: "cv_data.yaml", lang: "en-us", target: "pt-br", translation: "cv_data.pt-br.yaml", digest: "c".repeat(64), data: { name: "Daniel", tagline: "Engineer", contact: { email: "d@example.com" } } };
  const draft = { name: "Daniel", tagline: "Engenheiro", contact: { email: "d@example.com" } };
  const policy = { ...POLICY, education_degree_localization_policy: { decision: "localize_equivalent", apply_consistently: true, rule: "r", exceptions: [] } };
  const report = { applied_findings: [{ finding_id: "finding-1", field_path: "tagline", change_summary: "c" }], declined_findings: [], protected_field_exceptions: [] };
  const unreported = { revised_cv: { ...draft, tagline: "Engenheiro de ML" }, revision_report: { applied_findings: [], declined_findings: [], protected_field_exceptions: [] } };
  const { asked, ask } = scripted(ANALYSIS, policy, draft, critique(true), unreported, { ...unreported, revision_report: report }, review(true, []));
  const result = await localize(cv, [cv], settings({ ask }));
  assert.deepEqual(asked.map((question) => question.schema.name), ["source_analysis", "terminology_policy", "cv_translation", "critique", "cv_revision", "cv_revision", "final_review"]);
  assert.match(system(asked[0]!), /You are preparing a localized translation for a structured CV artifact\./);
  assert.match(system(asked[4]!), /Rewrite the translated CV candidate using the source CV and critique\./);
  assert.match(asked[5]!.messages[3]!.content, /- Critique finding finding-1 must have exactly one entry, in revision_report\.applied_findings/);
  assert.ok(user(asked[2]!).includes('"education_degree_localization_policy": {'));
  assert.deepEqual(result.candidate, { ...draft, tagline: "Engenheiro de ML" });
});
