import assert from "node:assert/strict";
import path from "node:path";
import { test } from "node:test";
import { parse as parseYaml } from "yaml";

import { asides, checkCv, checkProse, proseShape, untranslated } from "./checks.ts";
import type { ProseAnswer, ProseSource } from "./checks.ts";
import { discover, linkMapper, readMarkdown, readText, stateOf } from "./documents.ts";
import { deck, destinations, fencedBlocks, footnoteLabels, images, parentheticals, protectedFences } from "./markdown.ts";

const ROOT = path.resolve(import.meta.dirname, "../..");

// A source in English and a faithful translation of it, which every check accepts. Each test below
// breaks the translation in one way.
const BODY = `The platform keeps a record of every run.[^runs] It is small (two tables, no queue), and
it [builds on the hub](mare-rio-and-mare-hub.md#the-hub) I described before. The
[controller](https://kubernetes.io/docs/concepts/architecture/controller/) does the rest.

![The hub in day mode.](an-agent.assets/hub-day.jpg "The hub, with sample data.")

\`\`\`json
{ "name": "scout", "model": "small" }
\`\`\`

## What it costs

Almost nothing (so far).

[^runs]: One record per run, never rewritten.
`;

const TRANSLATED = `A plataforma mantém um registro de cada execução.[^runs] Ela é pequena (duas tabelas, nenhuma fila) e
[parte do hub](mare-rio-and-mare-hub.pt-br.md#the-hub) que descrevi antes. O
[controlador](https://kubernetes.io/docs/concepts/architecture/controller/) cuida do resto.

![O hub no modo dia.](an-agent.assets/hub-day.jpg "O hub, com dados de exemplo.")

\`\`\`json
{ "name": "scout", "model": "small" }
\`\`\`

## Quanto custa

Quase nada (por enquanto).

[^runs]: Um registro por execução, nunca reescrito.
`;

const source = (over: Partial<ProseSource> = {}): ProseSource => ({
  kind: "post",
  lang: "en-us",
  target: "pt-br",
  title: "An agent in a file",
  excerpt: "What it takes (not much).",
  tags: ["agents"],
  body: BODY,
  mapLink: (destination) => destination.replace(/^mare-rio-and-mare-hub\.md/, "mare-rio-and-mare-hub.pt-br.md"),
  ...over,
});

const answer = (over: Partial<ProseAnswer> = {}): ProseAnswer => ({
  title: "Um agente em um arquivo",
  excerpt: "O que é preciso (não muito).",
  tags: ["agentes"],
  content: TRANSLATED,
  ...over,
});

const findings = (content: string, from: Partial<ProseSource> = {}) => checkProse(source(from), answer({ content })).findings;

test("a faithful translation passes every check", () => {
  assert.deepEqual(checkProse(source(), answer()), { findings: [], warnings: [] });
});

// ---------- shape ----------

test("the answer must be an object with title, excerpt, tags and content", () => {
  assert.deepEqual(proseShape(answer()), []);
  assert.match(proseShape("text")[0]!, /must be one JSON object/);
  assert.match(proseShape([answer()])[0]!, /is a list/);
  assert.deepEqual(proseShape({ title: "t", excerpt: "e", tags: [] }), ['Missing required field "content"']);
  assert.deepEqual(proseShape({ ...answer(), tags: "a, b" }), ['Field "tags" must be a list of strings']);
  assert.deepEqual(proseShape({ ...answer(), tags: ["a", 2] }), ['Field "tags" must be a list of strings']);
  assert.match(proseShape({ ...answer(), title: null })[0]!, /"title" must be a string, and is a null/);
  // A wrong shape is the only finding: nothing else can be checked.
  assert.equal(checkProse(source(), { content: TRANSLATED }).findings.length, 3);
});

test("an empty translation is refused", () => {
  assert.deepEqual(findings(" \n\n "), ["Cannot accept an empty translation"]);
  assert.deepEqual(checkProse(source(), answer({ title: " " })).findings, ["The translated title is empty"]);
  assert.deepEqual(checkProse(source({ excerpt: "What it takes." }), answer({ excerpt: "" })).findings, ["The translated excerpt is empty"]);
  assert.deepEqual(checkProse(source({ excerpt: "" }), answer({ excerpt: "" })).findings, [], "no excerpt to translate");
});

// ---------- footnotes ----------

test("footnote labels and how often each is used are unchanged", () => {
  assert.deepEqual([...footnoteLabels(BODY)], [["runs", 2]]);
  assert.match(findings(TRANSLATED.replace("execução.[^runs]", "execução."))[0]!, /footnote identifiers or reference counts: \[\^runs\] appears 2 time\(s\) in the source and 1/);
  const renamed = findings(TRANSLATED.replaceAll("[^runs]", "[^execucoes]"))[0]!;
  assert.match(renamed, /\[\^runs\] appears 2 time\(s\) in the source and 0/);
  assert.match(renamed, /\[\^execucoes\] appears 0 time\(s\) in the source and 2/);
});

test("a footnote label inside fenced code or after a backslash is not a footnote", () => {
  assert.deepEqual([...footnoteLabels("a[^1]\n\n```\n[^2]\n```\n\n\\[^3]\n\n[^1]: note")], [["1", 2]]);
});

// ---------- fenced code ----------

test("fenced code is unchanged", () => {
  assert.deepEqual(fencedBlocks(BODY), ['```json\n{ "name": "scout", "model": "small" }\n```\n']);
  assert.match(findings(TRANSLATED.replace('"small"', '"pequeno"'))[0]!, /protected fenced code: fenced block 1 .* must be byte for byte the source's/);
  assert.match(findings(TRANSLATED.replace("```json", "```"))[0]!, /protected fenced code/);
  assert.match(
    findings(TRANSLATED.replace(/```json[\s\S]*?```\n/, ""))[0]!,
    /the source has 1 fenced block\(s\) and the translation 0/,
  );
});

test("a fence is closed only by its own kind, at least as long", () => {
  const text = "````md\n```js\ncode\n```\n````\n\n~~~\n```\n~~~\n";
  assert.deepEqual(fencedBlocks(text), ["````md\n```js\ncode\n```\n````\n", "~~~\n```\n~~~\n"]);
  assert.deepEqual(fencedBlocks("```\nnever closed\n"), ["```\nnever closed\n"]);
});

const MERMAID = `\`\`\`mermaid
%%{init: {"flowchart": {"nodeSpacing": 24}}}%%
flowchart TB
    accTitle: How a run is executed
    accDescr: Moon invokes Scout through the bridge.
    M["Moon · SDK"] <-->|invoke · poll| B
    subgraph P["Maré Platform"]
        B["Agent bridge<br/>Verify caller"] -->|create| R[AgentRun]
    end
    click B "https://example.com/bridge"
\`\`\``;

test("a Mermaid flowchart's labels and accessibility text may be translated, and nothing else", () => {
  const diagram = (text: string) => findings(`${TRANSLATED}\n${text}\n`, { body: `${BODY}\n${MERMAID}\n` });
  const localized = MERMAID.replace("How a run is executed", "Como uma execução acontece")
    .replace("Moon invokes Scout through the bridge.", "O Moon invoca o Scout pela ponte.")
    .replace("invoke · poll", "invocar · consultar")
    .replace("Maré Platform", "Plataforma Maré")
    .replace("Agent bridge<br/>Verify caller", "Ponte de agentes<br/>Verificar chamador")
    .replace("|create|", "|criar|");
  assert.deepEqual(diagram(localized), []);
  assert.equal(protectedFences(localized)[0], protectedFences(MERMAID)[0]);
  assert.match(diagram(localized.replace("M[", "Lua["))[0]!, /except for its visible labels and accessibility text/);
  assert.match(diagram(localized.replace("<br/>", " "))[0]!, /protected fenced code/, "embedded markup is kept");
  assert.match(diagram(localized.replace("-->|criar|", "---|criar|"))[0]!, /protected fenced code/, "edges are kept");
  assert.match(diagram(localized.replace("example.com/bridge", "example.com/ponte"))[0]!, /protected fenced code/);
  assert.match(diagram(localized.replace('"nodeSpacing": 24', '"nodeSpacing": 30'))[0]!, /protected fenced code/);
});

test("a diagram that is not a flowchart is ordinary code", () => {
  const sequence = "```mermaid\nsequenceDiagram\n    A->>B: hello [there]\n```";
  assert.notEqual(protectedFences(sequence)[0], protectedFences(sequence.replace("[there]", "[aqui]"))[0]);
});

// ---------- links and images ----------

test("destinations are read from inline links, images, references and inline HTML, outside fenced code", () => {
  const text = [
    "[a](one.md) and ![b](two.png \"title\") and [c](<three four.md> 'x') and \\[not](a-link.md).",
    "[ref]: https://example.com/ref",
    "[^note]: not a reference",
    '<a href="five.html">x</a> <img alt="y" src=six.jpg>',
    "```\n[code](seven.md)\n```",
    "[wiki](https://en.wikipedia.org/wiki/Tide_(disambiguation))",
  ].join("\n\n");
  assert.deepEqual(destinations(text), [
    { kind: "link", destination: "one.md" },
    { kind: "image", destination: "two.png" },
    { kind: "link", destination: "three four.md" },
    { kind: "link", destination: "https://en.wikipedia.org/wiki/Tide_(disambiguation)" },
    { kind: "link", destination: "https://example.com/ref" },
    { kind: "link", destination: "five.html" },
    { kind: "image", destination: "six.jpg" },
  ]);
});

test("link destinations are unchanged, and a link to another post moves to its file in the target language", () => {
  assert.match(
    findings(TRANSLATED.replace("mare-rio-and-mare-hub.pt-br.md", "mare-rio-and-mare-hub.md"))[0]!,
    /protected link destinations: missing link `mare-rio-and-mare-hub\.pt-br\.md#the-hub`; not in the source link `mare-rio-and-mare-hub\.md#the-hub`/,
  );
  assert.match(findings(TRANSLATED.replace("#the-hub", "#o-hub"))[0]!, /protected link destinations/);
  assert.match(
    findings(TRANSLATED.replace("kubernetes.io/docs", "kubernetes.io/pt-br/docs"))[0]!,
    /missing link `https:\/\/kubernetes\.io\/docs\/concepts/,
  );
  assert.match(
    findings(TRANSLATED.replace("[controlador](https://kubernetes.io/docs/concepts/architecture/controller/)", "controlador"))[0]!,
    /protected link destinations: missing link/,
  );
});

test("the same destination may be linked from another place in the text, but as many times", () => {
  const twice = `${BODY}\nSee [it](https://example.com) and [it again](https://example.com).\n`;
  const moved = `Veja [de novo](https://example.com).\n\n${TRANSLATED}\nE [isso](https://example.com).\n`;
  assert.deepEqual(findings(moved, { body: twice }), []);
  assert.match(findings(`${TRANSLATED}\nVeja [isso](https://example.com).\n`, { body: twice })[0]!, /missing link `https:\/\/example\.com`/);
});

test("a picture keeps its path; its alt text and its caption are translated, not dropped", () => {
  assert.deepEqual(images(BODY), [{ path: "an-agent.assets/hub-day.jpg", alt: "The hub in day mode.", title: "The hub, with sample data." }]);
  assert.match(findings(TRANSLATED.replace("hub-day.jpg", "hub-dia.jpg"))[0]!, /missing image `an-agent\.assets\/hub-day\.jpg`/);
  assert.deepEqual(findings(TRANSLATED.replace(' "O hub, com dados de exemplo."', "")), [
    "Image `an-agent.assets/hub-day.jpg` lost its title (the caption, in quotes after the path): translate it",
  ]);
  assert.deepEqual(findings(TRANSLATED.replace("![O hub no modo dia.]", "![]")), [
    "Image `an-agent.assets/hub-day.jpg` lost its alt text: translate it",
  ]);
  const bare = "![Daniel Cavalli](me.assets/me.png)";
  assert.deepEqual(findings(`${TRANSLATED}\n${bare}\n`, { body: `${BODY}\n${bare}\n` }), [], "a name is the same in both");
  assert.match(
    findings(`${TRANSLATED}\n![Daniel Cavalli](me.assets/me.png "Eu.")\n`, { body: `${BODY}\n${bare}\n` })[0]!,
    /gained a title the source does not have/,
  );
});

// ---------- parenthetical asides ----------

test("parenthetical asides are read from prose alone", () => {
  const text = [
    "A thought (an aside (nested) here) and a call `fn(x)` and a [link (really)](https://example.com/a_(b)).",
    "A bare URL https://example.com/wiki/Tide_(sea) and one in an aside (see https://example.com/x).",
    '![alt (ignored)](pic.assets/a.png "A caption (with an aside)")',
    "```\ncode (ignored)\n```",
    "- an item with an unclosed ( parenthesis\n- the next item (complete)",
    "<!-- a comment (ignored) --> and <span title=\"(ignored)\">text (kept)</span>",
  ].join("\n\n");
  assert.deepEqual(parentheticals(text), [
    "(an aside (nested) here)",
    "(really)",
    "(see )",
    "(with an aside)",
    "(complete)",
    "(kept)",
  ]);
});

test("a parenthetical aside stays in parentheses", () => {
  const dashed = findings(TRANSLATED.replace("(duas tabelas, nenhuma fila)", "— duas tabelas, nenhuma fila —"))[0]!;
  assert.match(dashed, /Translation changed parenthetical asides: preserve parentheses around the same thoughts/);
  assert.match(dashed, /The source has 2 and the translation 1\. The source's, in order: 1\. "\(two tables, no queue\)" 2\. "\(so far\)"/);
  assert.match(findings(TRANSLATED.replace("Quase nada", "Quase nada (de verdade)"))[0]!, /The source has 2 and the translation 3/);
  const nested = findings(TRANSLATED.replace("(por enquanto)", "(por (enquanto))"))[0]!;
  assert.match(nested, /Aside 2 is "\(so far\)" in the source and "\(por \(enquanto\)\)" in the translation/);
});

test("the title and the excerpt keep their asides too", () => {
  assert.match(checkProse(source(), answer({ excerpt: "O que é preciso: não muito." })).findings[0]!, /parenthetical asides in the excerpt/);
  assert.match(checkProse(source({ title: "Agents (again)" }), answer()).findings[0]!, /parenthetical asides in the title/);
  assert.deepEqual(asides("One (two) three", "Um (dois) três"), []);
});

// ---------- About ----------

test("About keeps its number of paragraphs", () => {
  const about = { kind: "about" as const, body: "First.\n\nSecond (really).\n\nThird." };
  assert.deepEqual(findings("Primeiro.\n\nSegundo (mesmo).\n\nTerceiro.", about), []);
  assert.deepEqual(findings("Primeiro. Segundo (mesmo).\n\nTerceiro.", about), [
    "About translation changed the paragraph count: the source has 3 paragraphs and the translation 2",
  ]);
  assert.deepEqual(findings("# Sobre\n\nPrimeiro.\n\nSegundo (mesmo).\n\nTerceiro.", about), [], "a leading title is not a paragraph");
  assert.deepEqual(findings("Primeiro.\n\nSegundo (mesmo). Terceiro.", { body: about.body }), [], "a post may merge paragraphs");
});

// ---------- untranslated text, unclosed markup ----------

test("a paragraph that came back in the source's language is refused", () => {
  const lines = TRANSLATED.split("\n");
  const echoed = [...BODY.split("\n").slice(0, 3), ...lines.slice(3)].join("\n").replace("mare-rio-and-mare-hub.md", "mare-rio-and-mare-hub.pt-br.md");
  assert.match(findings(echoed)[0]!, /Paragraph 1 appears untranslated \(100% word overlap after removing glossary terms\): "The platform keeps a record/);
  assert.match(checkProse(source(), answer({ content: BODY.replace("mare-rio-and-mare-hub.md", "mare-rio-and-mare-hub.pt-br.md") })).findings.join("\n"), /Paragraph 1 appears untranslated/);
});

test("names, code and shared technical terms do not make a paragraph untranslated", () => {
  assert.deepEqual(untranslated("Kubernetes, Docker and the GPU cluster.", "Kubernetes, Docker e o cluster de GPU."), []);
  assert.deepEqual(untranslated("## Sources\n\n[1] Some Book, 2024.", "## Sources\n\n[1] Some Book, 2024."), []);
  assert.match(untranslated("One. Two. Three. Four. Five.", "One. Two. Three. Four. Five.").join("\n"), /4 consecutive identical sentences/);
});

test("the translation leaves no HTML tag open that the source closes", () => {
  const html = `${BODY}\n<details><summary>More</summary>Hidden.</details>\n`;
  assert.deepEqual(findings(`${TRANSLATED}\n<details><summary>Mais</summary>Oculto.</details>\n`, { body: html }), []);
  assert.deepEqual(findings(`${TRANSLATED}\n<details><summary>Mais</summary>Oculto.\n`, { body: html }), [
    "1 unclosed <details> tag(s) in the translation",
  ]);
  const snippet = "\n```html\n<div>\n```\n\nA line break<br> and a `<p>` tag the source leaves open: <p>\n";
  const translated = snippet.replace("A line break<br> and a `<p>` tag the source leaves open", "Uma quebra de linha<br> e uma tag `<p>` que a fonte deixa aberta");
  assert.deepEqual(findings(TRANSLATED + translated, { body: BODY + snippet }), [], "what the source leaves open is not the translation's fault");
});

test("a translation under half the source's length is a warning, not a refusal", () => {
  const long = "A long paragraph of prose that goes on. ".repeat(20);
  const verdict = checkProse(source({ body: long, excerpt: "", title: "T" }), answer({ content: "Curto.", excerpt: "" }));
  assert.deepEqual(verdict.findings, []);
  assert.match(verdict.warnings[0]!, /suspiciously short: 6 characters against the source's 7\d\d/);
});

// ---------- presentations ----------

const SLIDES = `<!-- presentation:slide id="title" layout="lead" density="normal" -->

# How I use agents

<!-- /presentation:slide -->

<!-- presentation:slide id="rules" layout="card_grid" density="dense" -->

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
Plan first (always). See [the post](dont-outsource-the-thinking.md).
<!-- /presentation:card -->
<!-- /presentation:block -->

\`\`\`text
You: summarize this
\`\`\`

<!-- /presentation:slide -->
`;

const SLIDES_PT = SLIDES.replace("How I use agents", "Como eu uso agentes")
  .replace("Plan first (always). See [the post](dont-outsource-the-thinking.md).", "Planeje primeiro (sempre). Veja [o post](dont-outsource-the-thinking.pt-br.md).")
  .replace("You: summarize this", "Você: resuma isto");

const presentation = (content: string) =>
  checkProse(
    source({ kind: "presentation", body: SLIDES, excerpt: "", mapLink: (destination) => destination.replace(/\.md$/, ".pt-br.md") }),
    answer({ content, excerpt: "" }),
  ).findings;

test("a presentation is read as its slides", () => {
  const { markers, slides, error } = deck(SLIDES);
  assert.equal(error, null);
  assert.deepEqual(slides.map((slide) => slide.id), ["title", "rules"]);
  assert.equal(markers.length, 8);
  assert.match(deck("# No slides")!.error!, /no slide markers/);
  assert.match(deck(SLIDES.replace("<!-- /presentation:slide -->", ""))!.error!, /nested slide marker at line 7/);
  assert.match(deck(`${SLIDES}<!-- presentation:slide id="title" layout="lead" density="normal" -->\n`)!.error!, /duplicate slide id "title"/);
  assert.match(deck('```\n<!-- presentation:slide id="x" -->\n```\n<!-- /presentation:slide -->')!.error!, /closing slide marker without an opener/);
});

test("a presentation keeps its slide markers, and its text inside plain fences may be translated", () => {
  assert.deepEqual(presentation(SLIDES_PT), []);
  assert.match(presentation(SLIDES_PT.replace('layout="lead"', 'layout="divider"'))[0]!, /Presentation markers changed: marker 1 is `<!-- presentation:slide id="title" layout="lead" density="normal" -->` in the source/);
  assert.match(presentation(SLIDES_PT.replace('id="rules"', 'id="regras"'))[0]!, /Presentation markers changed: marker 3/);
  assert.match(presentation(SLIDES_PT.replace("<!-- presentation:card -->\n", ""))[0]!, /the source has 8 and the translation 7/);
  assert.match(presentation(SLIDES_PT.replace('type="card_grid" -->', 'type="card_grid"-->'))[0]!, /markers must remain byte for byte/);
  assert.match(presentation(SLIDES_PT.replace("```text", "```texto"))[0]!, /Code fence structure changed in slide "rules"/);
  assert.match(
    presentation(SLIDES_PT.replace("dont-outsource-the-thinking.pt-br.md", "dont-outsource-the-thinking.md"))[0]!,
    /Image\/link destinations changed in slide "rules": expected link `dont-outsource-the-thinking\.pt-br\.md`; found link `dont-outsource-the-thinking\.md`/,
  );
  assert.match(presentation(SLIDES_PT.replace("(sempre)", "— sempre —"))[0]!, /parenthetical asides/);
});

// ---------- the CV ----------

const CV = {
  name: "Daniel Cavalli",
  contact: { email: "daniel@example.com", github: "danielcavalli" },
  skills: ["Kubeflow", "Distributed Systems"],
  experience: [
    { title: "Engineer", company: "Nubank", period: "2023 - Present", achievements: ["Built it.", "Ran it."] },
    { title: "Scientist", company: "M4U", period: "2019 - 2020", achievements: ["Measured it."] },
  ],
  education: [{ degree: "Bachelor of Economics", school: "UFRJ", period: "2017 - 2023" }],
};

const CV_PT = {
  education: [{ degree: "Bacharelado em Economia", school: "UFRJ", period: "2017 - 2023" }],
  name: "Daniel Cavalli",
  contact: { github: "danielcavalli", email: "daniel@example.com" },
  skills: ["Kubeflow", "sistemas distribuídos"],
  experience: [
    { title: "Engenheiro", company: "Nubank", period: "2023 - Present", achievements: ["Construí.", "Operei."] },
    { title: "Cientista", company: "M4U", period: "2019 - 2020", achievements: ["Medi."] },
  ],
};

const cv = (change: (draft: typeof CV_PT) => unknown) => {
  const draft = structuredClone(CV_PT);
  return checkCv(CV, change(draft) ?? draft).findings;
};

test("a translated CV has the source's shape, entry for entry, in any key order", () => {
  assert.deepEqual(checkCv(CV, CV_PT), { findings: [], warnings: [] });
});

test("a translated CV keeps the number of entries in every list", () => {
  assert.deepEqual(cv((draft) => void draft.experience.pop()), [
    "CV translation changed the number of experience entries: 2 in the source, 1 in the translation",
  ]);
  assert.deepEqual(cv((draft) => void draft.skills.push("MLOps")), [
    "CV translation changed the number of skills entries: 2 in the source, 3 in the translation",
  ]);
  assert.deepEqual(cv((draft) => void draft.experience[0]!.achievements.pop()), [
    "CV translation changed the number of experience[0].achievements entries: 2 in the source, 1 in the translation",
  ]);
  assert.deepEqual(cv((draft) => void draft.education.push(draft.education[0]!)), [
    "CV translation changed the number of education entries: 1 in the source, 2 in the translation",
  ]);
});

test("a translated CV keeps contact details untouched", () => {
  assert.deepEqual(cv((draft) => void (draft.contact.email = "daniel@exemplo.com")), [
    "CV translation changed contact details: every value under `contact` must be the source's, byte for byte",
  ]);
});

test("a translated CV has every field of the source, of the same kind, and none of its own", () => {
  assert.deepEqual(cv((draft) => void delete (draft.experience[1] as Partial<(typeof draft.experience)[0]>).period), [
    "CV translation is missing experience[1].period",
  ]);
  assert.deepEqual(cv((draft) => void Object.assign(draft, { hobbies: ["surf"] })), ["CV translation has hobbies, which the source does not"]);
  assert.deepEqual(cv((draft) => void Object.assign(draft, { skills: "Kubeflow" })), [
    "CV translation changed skills: a list in the source, a string in the translation",
  ]);
  assert.deepEqual(cv((draft) => void (draft.education[0]!.degree = " ")), ["CV translation left education[0].degree empty"]);
  assert.match(checkCv(CV, "not an object").findings[0]!, /must be one JSON object/);
});

// ---------- the translations already in the repository ----------

// Real documents through the same scanners: every translation that is current passes every check,
// except that five made before the parenthetical check existed do not pass that one.
test("the repository's current translations pass the checks", () => {
  const sources = discover(ROOT);
  let checked = 0;
  for (const document of sources) {
    if (stateOf(ROOT, document).status !== "current") continue;
    checked++;
    if (document.kind === "cv") {
      assert.deepEqual(checkCv(document.data, parseYaml(readText(path.join(ROOT, document.translation)))).findings, []);
      continue;
    }
    const { meta, body } = readMarkdown(readText(path.join(ROOT, document.translation)));
    const translated = {
      title: String(meta.title ?? ""),
      excerpt: String(meta.excerpt ?? ""),
      tags: Array.isArray(meta.tags) ? meta.tags.map(String) : [],
      content: body,
    };
    const found = checkProse({ ...document, mapLink: linkMapper(document, sources) }, translated).findings;
    const older = !String(meta.translated_by).includes("gpt-5.6") && !String(meta.translated_by).includes("mare-hub");
    const counted = older ? found.filter((finding) => !finding.startsWith("Translation changed parenthetical asides")) : found;
    assert.deepEqual(counted, [], document.translation);
  }
  assert.ok(checked > 0, "nothing was checked");
});
