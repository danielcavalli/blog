import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";

import { readComments } from "./comments.ts";
import { validateCritique, validateTerminologyPolicy, validateVoiceIntent } from "./contracts.ts";
import type { Stage } from "./contracts.ts";
import type { CvDocument, ProseDocument } from "./documents.ts";
import { render, repairPrompt, sections, systemPrompt, templateFor, userPrompt } from "./prompt.ts";
import type { StageInputs } from "./prompt.ts";

const HERE = import.meta.dirname;
const ROOT = path.resolve(HERE, "../..");
const guide = (name: string) => fs.readFileSync(path.join(HERE, "guides", name), "utf8").trim();

const post = (over: Partial<ProseDocument> = {}): ProseDocument => ({
  kind: "post",
  file: "posts/tide.md",
  lang: "en-us",
  target: "pt-br",
  translation: "posts/tide.pt-br.md",
  digest: "d".repeat(64),
  title: "The tide",
  excerpt: "Why it matters.",
  tags: ["sea"],
  body: "The tide, as [the wave post](wave.md) says. And [again](wave.md#big), and [elsewhere](https://example.com).",
  meta: {},
  ...over,
});

const cv: CvDocument = {
  kind: "cv",
  file: "cv_data.yaml",
  lang: "en-us",
  target: "pt-br",
  translation: "cv_data.pt-br.yaml",
  digest: "c".repeat(64),
  data: {
    name: "Daniel",
    contact: { email: "d@example.com" },
    skills: ["Kubeflow"],
    experience: [
      { title: "Engineer", achievements: ["Built it."] },
      { title: "Scientist", achievements: [], location: "Rio" },
    ],
  },
};

const toPortuguese = (destination: string) => destination.replace(/^wave\.md/, "wave.pt-br.md");

const STAGES: Stage[] = ["source_analysis", "terminology_policy", "translate", "critique", "revise", "final_review"];

test("a guide is read by its sections", () => {
  const found = sections("# Title\n\nintro\n\n## One\n\n- a\n- b\n\n## Two words\n\ntext\n## Empty\n");
  assert.deepEqual([...found], [["One", "- a\n- b"], ["Two words", "text"], ["Empty", ""]]);
});

test("a template's placeholders are all filled, or it is an error", () => {
  assert.equal(render("from {{a}} to {{ b }}, {{a}}", { a: "x", b: "{{a}}" }), "from x to {{a}}, x");
  assert.throws(() => render("{{missing}}", {}), /Missing prompt placeholder: missing/);
});

test("each kind of document has its stage prompts where the old engine had them", () => {
  assert.deepEqual(STAGES.map((stage) => templateFor("post", stage)), STAGES.map((stage) => `${stage}.md`));
  assert.deepEqual(STAGES.map((stage) => templateFor("about", stage)), STAGES.map((stage) => `${stage}.md`), "About is a post");
  assert.deepEqual(STAGES.map((stage) => templateFor("cv", stage)), STAGES.map((stage) => `cv_${stage}.md`));
  assert.deepEqual(
    STAGES.map((stage) => templateFor("presentation", stage)),
    ["source_analysis.md", "terminology_policy.md", "presentation_translate.md", "critique.md", "presentation_revise.md", "final_review.md"],
  );
  for (const kind of ["post", "presentation", "about"] as const) {
    for (const stage of STAGES) {
      const system = systemPrompt(post({ kind }), stage);
      assert.ok(!system.includes("{{"), `${kind} ${stage}: no placeholder is left`);
      assert.ok(system.startsWith("LOCALIZATION AUTHORITY\nThe source controls meaning."), `${kind} ${stage} starts with the authority`);
      assert.match(system, /\nLOCALIZATION BOUNDARY\nThe source is already authored and is authoritative\./);
    }
  }
  for (const stage of STAGES) assert.ok(!systemPrompt(cv, stage).includes("{{"));
});

test("the guidance for a post is the old engine's prompt around the author's own words", () => {
  const system = systemPrompt(post());
  assert.ok(!system.includes("UNATTENDED LOCALIZATION AGENT"), "the single call's framing is gone");
  assert.match(system, /\nTRANSLATE\nProduce a localized draft .* reading as native pt-br prose\./);
  assert.match(system, /- Translate from en-us to pt-br\./);
  assert.ok(!system.includes("For Mermaid flowcharts"), "no diagram, no diagram rule");

  // The author's guidance, word for word.
  assert.ok(system.includes(`LOCALIZATION BRIEF\n${guide("pt_br_localization_brief.md")}\n\nSTYLE CONSTRAINTS\n`));
  const rules = sections(guide("en-us_to_pt-br.md"));
  assert.equal(rules.size, 8);
  for (const [heading, body] of rules) assert.ok(body.length > 0 && system.includes(body), `the "${heading}" rules are in the prompt`);
  assert.ok(system.includes("GLOSSARY\n- throughput => vazão\n"));
  assert.ok(system.includes("DO_NOT_TRANSLATE_ENTITIES\n- OpenCode\n- CUDA\n"));
  assert.ok(system.includes("LOCALE REVIEW CHECKS\n- Flag literal calques"));
  for (const [name, file] of [
    ["Blog composition", ".agents/skills/editorial-line/references/blog-composition.md"],
    ["Prose", ".agents/skills/prose-style/references/prose-contract.md"],
    ["Author voice", ".agents/skills/writing-style/references/WRITING_STYLE.md"],
  ]) {
    assert.ok(system.includes(`## ${name}\n\n${fs.readFileSync(path.join(ROOT, file!), "utf8").trim()}`), `${file} is in the prompt whole`);
  }
});

test("the other direction has its own brief and rules", () => {
  const system = systemPrompt(post({ lang: "pt-br", target: "en-us" }), "critique");
  assert.ok(system.includes(`LOCALIZATION BRIEF\n${guide("en_us_localization_brief.md")}\n`));
  assert.ok(system.includes("- Prefer idiomatic US English over literal Portuguese structure."));
  assert.ok(system.includes("GLOSSARY\n- vazão => throughput\n"));
  assert.ok(system.includes("- Translation direction: pt-br->en-us"));
  assert.ok(!system.includes("Target: publishable Brazilian Portuguese"));
});

test("a presentation, a diagram and the CV each bring their own rules", () => {
  const deck = systemPrompt(post({ kind: "presentation" }));
  assert.match(deck, /Produce a localized presentation draft/);
  assert.match(deck, /Preserve presentation slide markers exactly/);
  assert.match(systemPrompt(post({ kind: "presentation" }), "revise"), /Rewrite the translated presentation candidate/);
  assert.ok(systemPrompt(post({ body: "```mermaid\nflowchart TB\n```" }), "final_review").includes("For Mermaid flowcharts, localize visible node/edge labels"));

  const resume = systemPrompt(cv);
  assert.match(resume, /Produce a localized CV draft/);
  assert.match(resume, /- Use terminology_policy_json as the source of truth for ambiguous term handling/);
  const kept = /DO_NOT_TRANSLATE_ENTITIES\n([\s\S]*?)\n\nLOCALE REVIEW CHECKS/.exec(resume)![1]!.split("\n");
  assert.ok(kept.includes("- Nubank") && kept.includes("- OpenCode"), "the CV's names join the direction's");
  assert.equal(kept.filter((line) => line.toLowerCase() === "- cuda").length, 1, "a name in both lists is given once");
  assert.ok(!systemPrompt(post()).includes("- Nubank"));
  assert.match(systemPrompt(cv, "terminology_policy"), /Explicitly settle the education degree localization policy/);
  assert.match(systemPrompt(cv, "final_review"), /Review the localized CV directly against the source/);
});

test("the document is the user message: its front matter, its links to other documents, its text", () => {
  const user = userPrompt(post(), toPortuguese);
  assert.ok(user.startsWith("DOCUMENT\nposts/tide.md (post), en-us to pt-br\n\nSOURCE FRONT MATTER\n"));
  assert.ok(user.includes('"title": "The tide"') && user.includes('"excerpt": "Why it matters."') && user.includes('"sea"'));
  assert.ok(user.includes("LINKS TO OTHER DOCUMENTS\n- `wave.md` is written `wave.pt-br.md`\n- `wave.md#big` is written `wave.pt-br.md#big`\n\n"));
  assert.ok(user.endsWith(`SOURCE MARKDOWN\n<source_markdown>\n${post().body}\n</source_markdown>\n`));
  assert.ok(userPrompt(post({ body: "No links." }), toPortuguese).includes("LINKS TO OTHER DOCUMENTS\n- none\n"));
  assert.ok(!user.includes("OWNER REVISION INSTRUCTIONS"));
});

test("the CV goes as JSON", () => {
  const user = userPrompt(cv, toPortuguese);
  assert.ok(user.startsWith("DOCUMENT\ncv_data.yaml (cv), en-us to pt-br\n\nSOURCE CV JSON\n<source_cv>\n{\n"));
  assert.deepEqual(JSON.parse(/<source_cv>\n([\s\S]*)\n<\/source_cv>/.exec(user)![1]!), cv.data);
});

test("the earlier stages' answers follow the document in the old prompts' order, and the owner's comments close it", () => {
  const comments = readComments(
    "<!-- reef comment 4 · open · Daniel Cavalli · 2026-11-27T02:49Z · line 3 · before Sou · after e estudei\n> Engenheiro\nPrefiro minúsculas.\n-->\n" +
      "<!-- reef reply 4 · Claude · 2026-11-27T03:01Z\nEm todo o texto?\n-->\n" +
      "<!-- reef comment 7 · open · Daniel Cavalli · 2026-11-27T02:50Z\nUm comentário sem citação.\n-->",
  );
  const candidate = { title: "A maré", excerpt: "Por que importa.", tags: ["mar"], content: "A maré, como diz o post." };
  const issues = [{ passage: "A maré", violates: "Glossary", failure: "f" }];
  const user = userPrompt(post(), toPortuguese, { analysis: { tone: "dry" }, policy: { keep_english: [] }, candidate, issues, critique: { score: 80 }, comments });
  const order = ["LINKS TO OTHER DOCUMENTS", "SOURCE ANALYSIS JSON (MODEL ADVICE)", "TERMINOLOGY POLICY JSON (MODEL PROPOSAL)", "SOURCE MARKDOWN", "TRANSLATED CANDIDATE JSON", "PREVIOUS FINAL REVIEW RESIDUAL ISSUES", "CRITIQUE JSON", "OWNER REVISION INSTRUCTIONS"];
  const at = order.map((heading) => user.indexOf(`\n${heading}\n`));
  assert.ok(at.every((index, i) => index > 0 && (i === 0 || index > at[i - 1]!)), `in order: ${at.join(", ")}`);
  assert.ok(user.includes('TRANSLATED CANDIDATE JSON\n{\n  "content": "A maré, como diz o post.",\n  "excerpt": "Por que importa.",\n  "tags": [\n    "mar"\n  ],\n  "title": "A maré"\n}'), "as the old engine dumped it: keys sorted, two spaces");
  assert.ok(
    user.endsWith(
      "OWNER REVISION INSTRUCTIONS\nComment 4, line 3\nQuoted passage:\n> Engenheiro\nAround it: …Sou [the passage] e estudei…\n" +
        "Daniel Cavalli wrote:\nPrefiro minúsculas.\nClaude replied:\nEm todo o texto?\n\n" +
        "Comment 7\nDaniel Cavalli wrote:\nUm comentário sem citação.\n",
    ),
  );
  assert.match(userPrompt(post(), toPortuguese, { candidate, candidateLabel: "LOCALIZED CANDIDATE JSON" }), /\nLOCALIZED CANDIDATE JSON\n\{/);
  const system = systemPrompt(post(), "revise", { owner: true });
  assert.match(system, /\nOWNER REVISION\nThe owner read the translation in TRANSLATED CANDIDATE JSON/);
  assert.match(system, /\nREVISE\nRewrite the translated candidate using the source artifact and critique\./);
  assert.ok(!systemPrompt(post(), "revise").includes("OWNER REVISION\n"));
});

test("the repair message carries the findings exactly", () => {
  const message = repairPrompt(["Cannot accept an empty translation", "Missing link `a.md`"]);
  assert.ok(message.startsWith("DETERMINISTIC VALIDATION FINDINGS\n"));
  assert.ok(message.includes("\n- Cannot accept an empty translation\n- Missing link `a.md`\n"));
});

// ---------- against the old engine's own rendering ----------

interface Section {
  heading: string;
  text?: string;
  sha256?: string;
  items?: string[];
}

// The old engine's prompts for one post, rendered by tools/translate/fixtures/old_engine.py.
const OLD = JSON.parse(fs.readFileSync(path.join(HERE, "fixtures", "old-engine.json"), "utf8")) as {
  post: { file: string; title: string; excerpt: string; tags: string[]; body: string };
  candidate: Record<string, unknown>;
  payloads: Record<string, unknown>;
  rendered_2d9a250: Record<Stage, Section[]>;
  headings_8c6735a: Record<Stage, string[]>;
};

const OLD_POST = post({ ...OLD.post, body: OLD.post.body });

// What the earlier stages answered, as their contracts normalize it: what the old engine showed later stages.
const normalized = <T>(validated: { value: T } | { finding: string }): T => ("value" in validated ? validated.value : assert.fail(validated.finding));
const analysis = normalized(validateVoiceIntent(OLD.payloads.source_analysis));
const policy = normalized(validateTerminologyPolicy(OLD.payloads.terminology_policy));
const critique = normalized(validateCritique(OLD.payloads.critique));
const INPUTS: Record<Stage, StageInputs> = {
  source_analysis: {},
  terminology_policy: { analysis },
  translate: { analysis, policy },
  critique: { analysis, policy, candidate: OLD.candidate },
  revise: { analysis, policy, candidate: OLD.candidate, critique },
  final_review: { candidate: OLD.candidate, candidateLabel: "LOCALIZED CANDIDATE JSON" },
};

// The sections that are the document or an earlier stage's answer: the user message has them.
const MOVED = new Set([
  "SOURCE MARKDOWN",
  "SOURCE ANALYSIS JSON (MODEL ADVICE)",
  "TERMINOLOGY POLICY JSON (MODEL PROPOSAL)",
  "TRANSLATED CANDIDATE JSON",
  "LOCALIZED CANDIDATE JSON",
  "CRITIQUE JSON",
]);
const OURS = ["LOCALIZATION AUTHORITY", "LOCALIZATION BOUNDARY", "ARTIFACT CONTEXT AND OWNER REVISION INSTRUCTIONS", "DOCUMENT", "SOURCE FRONT MATTER", "LINKS TO OTHER DOCUMENTS", "PREVIOUS FINAL REVIEW RESIDUAL ISSUES"];
const HEADINGS = new Set([...Object.values(OLD.rendered_2d9a250).flatMap((list) => list.map((section) => section.heading)), ...OURS]);

// A message's section under a heading: the lines after it, up to the next heading.
function cut(message: string, heading: string): string | null {
  const lines = message.split("\n");
  const start = lines.indexOf(heading);
  if (start === -1) return null;
  let end = start + 1;
  while (end < lines.length && !HEADINGS.has(lines[end]!)) end++;
  return lines.slice(start + 1, end).join("\n").replace(/^\n+|\n+$/g, "");
}

const PROSE_CONTRACT =
  "- `title`, `excerpt` and `tags` are the source front matter's, translated. Where the source has no excerpt, return an empty string; where it has no tags, an empty list.\n" +
  "- `content` is the complete translated Markdown body, without front matter.";

// Every change to the old wording, as old → new. Nothing else may differ.
const EDITS: Partial<Record<Stage, Record<string, [string, string][]>>> = {
  translate: {
    TRANSLATE: [
      [
        "- Keep markdown link destinations byte-for-byte unchanged and preserve the link text intent.",
        "- Keep markdown link destinations byte-for-byte unchanged and preserve the link text intent. The one exception is a link to another document of this site (a sibling `.md` file): it points to that document's file in pt-br, and LINKS TO OTHER DOCUMENTS gives the exact destination to write for each one.\n" +
          "- Keep every image's path byte-for-byte unchanged. Translate its alt text and its title (the quoted text after the path, which the page shows as the picture's caption).",
      ],
    ],
    "OUTPUT CONTRACT": [["- Include all required keys with correct primitive types.", `- Include all required keys with correct primitive types.\n${PROSE_CONTRACT}`]],
  },
  // The owner's rule from ADR 017: every finding accounted for, applied or declined with why.
  revise: {
    REVISE: [
      [
        "- applied_feedback should describe actual edits; declined_feedback records justified non-edits.",
        "- applied_feedback should describe actual edits; declined_feedback records justified non-edits.\n" +
          "- Give every critique finding id exactly one entry: in applied_feedback, saying what you changed, or in declined_feedback, saying why the wording stands. Record rewrites the critique did not ask for in rewrite_summary.",
      ],
    ],
    "OUTPUT CONTRACT": [["- Do not wrap in markdown fences.", `- Do not wrap in markdown fences.\n${PROSE_CONTRACT}`]],
    BEGIN_OUTPUT_JSON: [['"applied_feedback": ["string"],', '"applied_feedback": [{"finding_id": "string", "status": "applied", "rationale": "string"}],']],
  },
  // And every residual issue quotes its passage and names what it violates.
  final_review: {
    "OUTPUT CONTRACT": [
      [
        "- Numerical scores are diagnostic only and cannot excuse a guidance violation.",
        "- Numerical scores are diagnostic only and cannot excuse a guidance violation.\n" +
          "- Each residual issue quotes the exact passage at fault in `passage` (from the candidate, or from the source for something left out), names the source claim or human guidance rule it violates in `violates`, and states the concrete failure in `failure`. An issue without a passage and what it violates is refused.",
      ],
    ],
  },
};

const sha256 = (text: string): string => createHash("sha256").update(text, "utf8").digest("hex");

for (const stage of STAGES) {
  test(`the ${stage} stage says what the old engine's said, section for section`, () => {
    const system = systemPrompt(OLD_POST, stage);
    const user = userPrompt(OLD_POST, (destination) => destination, INPUTS[stage]);
    const order: Record<"system" | "user", number[]> = { system: [], user: [] };
    for (const section of OLD.rendered_2d9a250[stage]) {
      const where = MOVED.has(section.heading) ? "user" : "system";
      const message = where === "user" ? user : system;
      const body = cut(message, section.heading);
      assert.notEqual(body, null, `${section.heading} is in the ${where} message`);
      order[where].push(message.split("\n").indexOf(section.heading));
      if (section.sha256) assert.equal(sha256(body!), section.sha256, `${section.heading} is the guidance file, whole`);
      else if (section.items) assert.deepEqual(body!.split("\n").map((line) => line.replace(/^- /, "")), section.items, `${section.heading} has the same items`);
      else if (section.heading === "SOURCE MARKDOWN") assert.equal(body, `<source_markdown>\n${section.text}\n</source_markdown>`);
      else {
        const expected = (EDITS[stage]?.[section.heading] ?? []).reduce((text, [from, to]) => {
          assert.ok(text.includes(from), `the old ${section.heading} has "${from}"`);
          return text.replace(from, to);
        }, section.text!);
        assert.equal(body, expected, `${section.heading} is the old wording`);
      }
    }
    for (const [where, lines] of Object.entries(order)) {
      assert.deepEqual(lines, [...lines].sort((a, b) => a - b), `the ${where} message keeps the old order`);
    }
  });
}

test("each stage is given what it was given at 8c6735a, except what the later wording took out", () => {
  // The later prompts (2d9a250) took these out: the author voice profile (gone with its file), and
  // everything the final review saw besides the source and the candidate (ADR 017).
  const dropped: Partial<Record<Stage, string[]>> = {
    source_analysis: ["AUTHOR VOICE PROFILE"],
    final_review: ["SOURCE ANALYSIS JSON", "TERMINOLOGY POLICY JSON", "CRITIQUE JSON", "REVISION REPORT JSON", "REVIEW INSTRUCTIONS"],
  };
  const renamed = (stage: Stage, heading: string): string =>
    ({
      "SOURCE ANALYSIS JSON": "SOURCE ANALYSIS JSON (MODEL ADVICE)",
      "TERMINOLOGY POLICY JSON": "TERMINOLOGY POLICY JSON (MODEL PROPOSAL)",
      "REVISED CANDIDATE JSON": "LOCALIZED CANDIDATE JSON",
      ...(stage === "source_analysis" ? { "WRITING STYLE BRIEF": "AUTHORING CONTEXT (PRESERVE THE AUTHORED SOURCE)" } : {}),
    })[heading] ?? heading;
  for (const stage of STAGES) {
    const messages = `${systemPrompt(OLD_POST, stage)}\n${userPrompt(OLD_POST, (destination) => destination, INPUTS[stage])}`.split("\n");
    for (const heading of OLD.headings_8c6735a[stage]) {
      if (dropped[stage]?.includes(heading)) continue;
      assert.ok(messages.includes(renamed(stage, heading)), `${stage} still has ${heading}`);
    }
  }
  assert.ok(OLD.headings_8c6735a.translate.includes("SOURCE ANALYSIS JSON") && OLD.headings_8c6735a.translate.includes("TERMINOLOGY POLICY JSON"));
});
