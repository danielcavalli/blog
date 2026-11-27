import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";

import { readComments } from "./comments.ts";
import type { CvDocument, ProseDocument } from "./documents.ts";
import { render, repairPrompt, schemaFor, sections, systemPrompt, userPrompt } from "./prompt.ts";

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

test("a guide is read by its sections", () => {
  const found = sections("# Title\n\nintro\n\n## One\n\n- a\n- b\n\n## Two words\n\ntext\n## Empty\n");
  assert.deepEqual([...found], [["One", "- a\n- b"], ["Two words", "text"], ["Empty", ""]]);
});

test("a template's placeholders are all filled, or it is an error", () => {
  assert.equal(render("from {{a}} to {{ b }}, {{a}}", { a: "x", b: "{{a}}" }), "from x to {{a}}, x");
  assert.throws(() => render("{{missing}}", {}), /Missing prompt placeholder: missing/);
});

test("the guidance for a post is the old engine's prompt around the author's own words", () => {
  const system = systemPrompt(post());
  assert.ok(system.startsWith("UNATTENDED LOCALIZATION AGENT\nComplete the localization using the supplied source"));
  assert.match(system, /\nLOCALIZATION AUTHORITY\nThe source controls meaning\./);
  assert.match(system, /\nTRANSLATE\nProduce a localized draft .* reading as native pt-br prose\./);
  assert.match(system, /- Translate from en-us to pt-br\./);
  assert.match(system, /\nLOCALIZATION BOUNDARY\nThe source is already authored and is authoritative\./);
  assert.ok(!system.includes("{{"), "no placeholder is left");
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
  const system = systemPrompt(post({ lang: "pt-br", target: "en-us" }));
  assert.ok(system.includes(`LOCALIZATION BRIEF\n${guide("en_us_localization_brief.md")}\n`));
  assert.ok(system.includes("- Prefer idiomatic US English over literal Portuguese structure."));
  assert.ok(system.includes("GLOSSARY\n- vazão => throughput\n"));
  assert.ok(!system.includes("Target: publishable Brazilian Portuguese"));
});

test("a presentation, a diagram and the CV each bring their own rules", () => {
  const deck = systemPrompt(post({ kind: "presentation" }));
  assert.match(deck, /Produce a localized presentation draft/);
  assert.match(deck, /Preserve presentation slide markers exactly/);
  assert.ok(systemPrompt(post({ body: "```mermaid\nflowchart TB\n```" })).includes("For Mermaid flowcharts, localize visible node/edge labels"));

  const resume = systemPrompt(cv);
  assert.match(resume, /Produce a localized CV draft/);
  const kept = /DO_NOT_TRANSLATE_ENTITIES\n([\s\S]*?)\n\nLOCALE REVIEW CHECKS/.exec(resume)![1]!.split("\n");
  assert.ok(kept.includes("- Nubank") && kept.includes("- OpenCode"), "the CV's names join the direction's");
  assert.equal(kept.filter((line) => line.toLowerCase() === "- cuda").length, 1, "a name in both lists is given once");
  assert.ok(!systemPrompt(post()).includes("- Nubank"));
});

test("the document is the user message: its front matter, its links to other documents, its text", () => {
  const user = userPrompt(post(), toPortuguese);
  assert.ok(user.startsWith("DOCUMENT\nposts/tide.md (post), en-us to pt-br\n\nSOURCE FRONT MATTER\n"));
  assert.ok(user.includes('"title": "The tide"') && user.includes('"excerpt": "Why it matters."') && user.includes('"sea"'));
  assert.ok(user.includes("LINKS TO OTHER DOCUMENTS\n- `wave.md` is written `wave.pt-br.md`\n- `wave.md#big` is written `wave.pt-br.md#big`\n\n"));
  assert.ok(user.includes(`SOURCE MARKDOWN\n<source_markdown>\n${post().body}\n</source_markdown>\n`));
  assert.ok(userPrompt(post({ body: "No links." }), toPortuguese).includes("LINKS TO OTHER DOCUMENTS\n- none\n"));
  assert.ok(!user.includes("OWNER REVISION INSTRUCTIONS"));
});

test("the CV goes as JSON", () => {
  const user = userPrompt(cv, toPortuguese);
  assert.ok(user.startsWith("DOCUMENT\ncv_data.yaml (cv), en-us to pt-br\n\nSOURCE CV JSON\n<source_cv>\n{\n"));
  assert.deepEqual(JSON.parse(/<source_cv>\n([\s\S]*)\n<\/source_cv>/.exec(user)![1]!), cv.data);
});

test("a revision adds the translation as it stands and the owner's comments", () => {
  const comments = readComments(
    "<!-- reef comment 4 · open · Daniel Cavalli · 2026-11-27T02:49Z · line 3 · before Sou · after e estudei\n> Engenheiro\nPrefiro minúsculas.\n-->\n" +
      "<!-- reef reply 4 · Claude · 2026-11-27T03:01Z\nEm todo o texto?\n-->\n" +
      "<!-- reef comment 7 · open · Daniel Cavalli · 2026-11-27T02:50Z\nUm comentário sem citação.\n-->",
  );
  const current = { title: "A maré", excerpt: "Por que importa.", tags: ["mar"], content: "A maré, como diz o post." };
  const user = userPrompt(post(), toPortuguese, { current, comments });
  assert.ok(user.includes('CURRENT TRANSLATION\nFront matter:\n{\n  "title": "A maré",'));
  assert.ok(user.includes("<current_translation>\nA maré, como diz o post.\n</current_translation>"));
  assert.ok(
    user.includes(
      "OWNER REVISION INSTRUCTIONS\nComment 4, line 3\nQuoted passage:\n> Engenheiro\nAround it: …Sou [the passage] e estudei…\n" +
        "Daniel Cavalli wrote:\nPrefiro minúsculas.\nClaude replied:\nEm todo o texto?\n\n" +
        "Comment 7\nDaniel Cavalli wrote:\nUm comentário sem citação.\n",
    ),
  );
  const system = systemPrompt(post(), { revise: true });
  assert.match(system, /\nOWNER REVISION\nThe owner read CURRENT TRANSLATION/);
  assert.ok(!systemPrompt(post()).includes("OWNER REVISION\n"));
});

test("the repair message carries the findings exactly", () => {
  const message = repairPrompt(["Cannot accept an empty translation", "Missing link `a.md`"]);
  assert.ok(message.startsWith("DETERMINISTIC VALIDATION FINDINGS\n"));
  assert.ok(message.includes("\n- Cannot accept an empty translation\n- Missing link `a.md`\n"));
});

test("the answer asked for has the shape of what is translated", () => {
  const prose = schemaFor(post());
  assert.equal(prose.name, "translation");
  assert.deepEqual(prose.schema.required, ["title", "excerpt", "tags", "content"]);
  assert.equal(prose.schema.additionalProperties, false);

  const revision = schemaFor(post(), { revise: true });
  assert.equal(revision.name, "revision");
  assert.deepEqual(revision.schema.required, ["title", "excerpt", "tags", "content", "comments"]);
  const entry = (revision.schema.properties as Record<string, { items: { required: string[] } }>).comments!.items;
  assert.deepEqual(entry.required, ["id", "addressed", "note"]);

  assert.deepEqual(schemaFor(cv), {
    name: "cv_translation",
    schema: {
      type: "object",
      properties: {
        name: { type: "string" },
        contact: { type: "object", properties: { email: { type: "string" } }, required: ["email"], additionalProperties: false },
        skills: { type: "array", items: { type: "string" } },
        experience: {
          type: "array",
          items: {
            type: "object",
            properties: {
              title: { type: "string" },
              achievements: { type: "array", items: { type: "string" } },
              location: { type: "string" },
            },
            required: ["title", "achievements"],
            additionalProperties: false,
          },
        },
      },
      required: ["name", "contact", "skills", "experience"],
      additionalProperties: false,
    },
  });
});
