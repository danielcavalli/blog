import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";

import { cvHeader, discover, linkMapper, readMarkdown, readText, stateOf, toYaml } from "./documents.ts";
import type { ProseDocument } from "./documents.ts";
import { repository } from "./testing.ts";

const ROOT = path.resolve(import.meta.dirname, "../..");

const COMMENT = "<!-- reef comment 4 · open · Daniel Cavalli · 2026-10-05T14:02Z · line 3\n> a reader sees\nSay who the reader is.\n-->";

test("a Markdown file is read as front matter, body and trailer", () => {
  const text = `---\ntitle: 'One: two'\ntags:\n- a\n---\n\n# Body\n\nText.\n\n<!-- reef document k3 · revision 2 · note n -->\n${COMMENT}\n`;
  const { meta, body, trailer } = readMarkdown(text);
  assert.deepEqual(meta, { title: "One: two", tags: ["a"] });
  assert.equal(body, "# Body\n\nText.");
  assert.equal(trailer, `<!-- reef document k3 · revision 2 · note n -->\n${COMMENT}\n`);
  assert.ok(text.endsWith(trailer), "the trailer is the file's own bytes");
});

test("a file without front matter or trailer is all body", () => {
  assert.deepEqual(readMarkdown("Just text.\n"), { meta: {}, body: "Just text.", trailer: "" });
  const shown = "A comment looks like this:\n\n```\n" + COMMENT + "\n```\n\nAnd the text goes on.\n";
  assert.equal(readMarkdown(shown).trailer, "", "a reef comment shown in the body is body text");
});

test("a file that is not UTF-8 is refused", () => {
  const root = repository({});
  fs.writeFileSync(path.join(root, "latin1.md"), Buffer.from([0x63, 0x61, 0x66, 0xe9]));
  assert.throws(() => readText(path.join(root, "latin1.md")), /is not valid UTF-8/);
});

const post = (lang: string, extra = "") => `---\ntitle: T\nlang: ${lang}\nexcerpt: E\ntags:\n- x\n${extra}---\n\nBody.\n`;

test("sources are the posts, pages and CV that are not translations, each with its other language", () => {
  const root = repository({
    "posts/wave.md": post("en-us"),
    "posts/wave.pt-br.md": post("pt-br", "translation_of: wave.md\n"),
    "posts/lua.md": post("pt-br"),
    "posts/lua.en-us.md": post("en-us"), // a translation that forgot to say what it translates
    "posts/deck.md": post("en-us", "content_type: presentation\n"),
    "posts/notes.txt": "not a document",
    "pages/about.md": "---\ntitle: About\nlang: en-us\n---\n\nMe.\n",
    "cv_data.yaml": "name: D\n",
  });
  assert.deepEqual(
    discover(root).map(({ file, kind, lang, target, translation }) => ({ file, kind, lang, target, translation })),
    [
      { file: "posts/deck.md", kind: "presentation", lang: "en-us", target: "pt-br", translation: "posts/deck.pt-br.md" },
      { file: "posts/lua.md", kind: "post", lang: "pt-br", target: "en-us", translation: "posts/lua.en-us.md" },
      { file: "posts/wave.md", kind: "post", lang: "en-us", target: "pt-br", translation: "posts/wave.pt-br.md" },
      { file: "pages/about.md", kind: "about", lang: "en-us", target: "pt-br", translation: "pages/about.pt-br.md" },
      { file: "cv_data.yaml", kind: "cv", lang: "en-us", target: "pt-br", translation: "cv_data.pt-br.yaml" },
    ],
  );
});

test("the repository's own sources are found", () => {
  const sources = discover(ROOT);
  assert.equal(sources.filter((source) => source.kind === "presentation").length, 1);
  assert.equal(sources.find((source) => source.file === "posts/semiconductors-and-sovereignty.md")?.translation, "posts/semiconductors-and-sovereignty.en-us.md");
  assert.ok(!sources.some((source) => /\.(pt-br|en-us)\.md$/.test(source.file)), "a translation is not a source");
});

test("a translation is current, stale or missing by the digest it records", () => {
  const root = repository({ "posts/wave.md": post("en-us"), "cv_data.yaml": "name: D\n" });
  const [wave, cv] = discover(root);
  assert.deepEqual(stateOf(root, wave!), { status: "missing", recorded: null });
  assert.deepEqual(stateOf(root, cv!), { status: "missing", recorded: null });

  const translation = (fields: string) => fs.writeFileSync(path.join(root, "posts/wave.pt-br.md"), `---\ntitle: T\nlang: pt-br\n${fields}---\n\nCorpo.\n`);
  translation(`translation_of: wave.md\nsource_digest: ${wave!.digest}\n`);
  assert.deepEqual(stateOf(root, wave!), { status: "current", recorded: wave!.digest });
  translation(`translation_of: wave.md\nsource_digest: ${"f".repeat(64)}\n`);
  assert.deepEqual(stateOf(root, wave!), { status: "stale", recorded: "f".repeat(64) });
  translation("translation_of: wave.md\n");
  assert.deepEqual(stateOf(root, wave!), { status: "stale", recorded: null, note: "it records no source_digest" });
  translation(`translation_of: other.md\nsource_digest: ${wave!.digest}\n`);
  assert.equal(stateOf(root, wave!).note, "it says it translates other.md");
  translation("");
  assert.equal(stateOf(root, wave!).note, "it does not say what it translates");

  fs.writeFileSync(path.join(root, "posts/wave.md"), post("en-us").replace("Body.", "Body, changed."));
  translation(`translation_of: wave.md\nsource_digest: ${wave!.digest}\n`);
  assert.equal(stateOf(root, discover(root)[0]!).status, "stale", "the source changed");

  fs.writeFileSync(path.join(root, "cv_data.pt-br.yaml"), `# a note\n# translation_of: cv_data.yaml\n# source_digest: ${cv!.digest}\n\nname: D\n`);
  assert.deepEqual(stateOf(root, cv!), { status: "current", recorded: cv!.digest });
  fs.writeFileSync(path.join(root, "cv_data.pt-br.yaml"), "name: D\n# source_digest: later comments are not the header\n");
  assert.equal(stateOf(root, cv!).status, "stale");
});

test("the head of a translated CV says what it translates", () => {
  const yaml = "# The CV in pt-br.\n# translation_of: cv_data.yaml\n# source_digest: abc\n# translated_by: gpt-5.6-sol (high), via mare-hub\n# translated_at: 2026-11-26\n\nname: D\n";
  assert.deepEqual(cvHeader(yaml), {
    translation_of: "cv_data.yaml",
    source_digest: "abc",
    translated_by: "gpt-5.6-sol (high), via mare-hub",
    translated_at: "2026-11-26",
  });
});

test("a link to another document moves to that document's file in the target language", () => {
  const root = repository({
    "posts/tide.md": post("en-us"),
    "posts/wave.md": post("en-us"),
    "posts/lua.md": post("pt-br"),
    "pages/about.md": "---\ntitle: About\nlang: en-us\n---\n\nMe.\n",
  });
  const sources = discover(root);
  const from = (file: string) => linkMapper(sources.find((source) => source.file === file)!, sources);

  const english = from("posts/tide.md"); // read in Portuguese
  assert.equal(english("wave.md"), "wave.pt-br.md", "written in English: the Portuguese file is the translation");
  assert.equal(english("lua.en-us.md"), "lua.md", "written in Portuguese: the Portuguese file is the source");
  assert.equal(english("./wave.md#the-big-one"), "./wave.pt-br.md#the-big-one");
  assert.equal(english("wave.md?x=1#y"), "wave.pt-br.md?x=1#y");
  assert.equal(english("../pages/about.md"), "../pages/about.pt-br.md");
  assert.equal(english("tide.md"), "tide.pt-br.md", "a document may link to itself");

  const portuguese = from("posts/lua.md"); // read in English
  assert.equal(portuguese("wave.pt-br.md"), "wave.md");
  assert.equal(portuguese("lua.md"), "lua.en-us.md");

  for (const kept of [
    "https://example.com/wave.md",
    "mailto:someone@example.com",
    "#a-heading",
    "/en/blog/wave",
    "unknown.md",
    "wave.assets/photo.jpg",
    "README.md",
    "../README.md",
    "wave.mdx",
  ]) {
    assert.equal(english(kept), kept);
  }

  assert.equal(from("pages/about.md")("../posts/wave.md"), "../posts/wave.pt-br.md");
  assert.equal(from("pages/about.md")("wave.md"), "wave.md", "there is no pages/wave.md");
});

test("the repository's own links between posts map onto the links its translations have", () => {
  const sources = discover(ROOT);
  const hub = sources.find((source) => source.file === "posts/mare-rio-and-mare-hub.md") as ProseDocument;
  const map = linkMapper(hub, sources);
  assert.equal(map("dont-outsource-the-thinking.md"), "dont-outsource-the-thinking.pt-br.md");
  assert.equal(map("adding-an-agent-to-a-mare-app.md"), "adding-an-agent-to-a-mare-app.pt-br.md");
  const translated = readText(path.join(ROOT, hub.translation));
  assert.ok(translated.includes("](dont-outsource-the-thinking.pt-br.md)"));
});

test("front matter is written the way the repository's translations already are", () => {
  // Every translation migrated from the old engine comes back byte for byte from its own values.
  let seen = 0;
  for (const source of discover(ROOT)) {
    if (source.kind === "cv") continue;
    const text = readText(path.join(ROOT, source.translation));
    const front = /^---\n([\s\S]*?\n)---\n/.exec(text)![1]!;
    if (!front.includes("via opencode")) continue;
    assert.equal(toYaml(readMarkdown(text).meta), front, source.translation);
    seen++;
  }
  // (a post translated again through the Hub leaves the old engine's set: the ones that remain must still round-trip)
  assert.ok(seen >= 1, `expected the migrated translations, found ${seen}`);
});

test("a value YAML would read as something else is quoted", () => {
  assert.equal(
    toYaml({ title: "Maré Rio: o software", translated_at: "2026-11-26", tags: ["no", "a: b", "plain"], none: [], quote: "it's" }),
    "title: 'Maré Rio: o software'\ntranslated_at: '2026-11-26'\ntags:\n- 'no'\n- 'a: b'\n- plain\nnone: []\nquote: it's\n",
  );
});
