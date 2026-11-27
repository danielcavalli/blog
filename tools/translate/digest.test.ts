import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import path from "node:path";
import { test } from "node:test";

import { cvDigest, sourceDigest } from "./digest.ts";
import { cvHeader, discover, readMarkdown, readText, stateOf } from "./documents.ts";

const ROOT = path.resolve(import.meta.dirname, "../..");
const sha256 = (text: string) => createHash("sha256").update(text, "utf8").digest("hex");

test("the digest is the SHA-256 of title, excerpt, tags, a blank line and the body", () => {
  const digest = sourceDigest({ title: "Maré", excerpt: "What it is.", tags: ["a", "b c"], body: "First.\n\nSecond." });
  assert.equal(digest, sha256("title: Maré\nexcerpt: What it is.\ntags: a, b c\n\nFirst.\n\nSecond."));
  assert.match(digest, /^[0-9a-f]{64}$/);
});

test("a missing field is the empty string", () => {
  assert.equal(sourceDigest({ title: "", excerpt: "", tags: [], body: "" }), sha256("title: \nexcerpt: \ntags: \n\n"));
});

test("the body is what is after the front matter and before the trailer, CRLF read as LF, trimmed", () => {
  const front = "---\ntitle: T\nexcerpt: E\ntags:\n- x\n- y\ndate: 2026-01-01\n---\n";
  const trailer = "<!-- reef document k3x9f2 · revision 3 · note n -->\n<!-- reef comment 4 · open · D · 2026-10-05T14:02Z · line 1\n> One\nNo.\n-->\n";
  const digestOf = (text: string) => {
    const { meta, body } = readMarkdown(text);
    return sourceDigest({ title: String(meta.title), excerpt: String(meta.excerpt), tags: (meta.tags as string[]).map(String), body });
  };
  const plain = digestOf(`${front}\nOne.\n\nTwo.\n`);
  assert.equal(plain, sha256("title: T\nexcerpt: E\ntags: x, y\n\nOne.\n\nTwo."));
  assert.equal(digestOf(`${front}\n\n\nOne.\n\nTwo.\n\n\n`), plain, "blank lines at either end do not count");
  assert.equal(digestOf(`${front}\nOne.\n\nTwo.\n\n${trailer}`), plain, "the trailer does not count");
  assert.equal(digestOf(`${front}\nOne.\n\nTwo.\n`.replaceAll("\n", "\r\n")), plain, "CRLF is read as LF");
  assert.equal(digestOf(`${front.replace("2026-01-01", "2027-02-02")}\nOne.\n\nTwo.\n`), plain, "a date does not count");
  assert.notEqual(digestOf(`${front}\nOne.\n\nTwo!\n`), plain, "a word a reader sees does");
  assert.notEqual(digestOf(`${front.replace("title: T", "title: U")}\nOne.\n\nTwo.\n`), plain);
});

test("the CV's digest is of its data, whatever the order of its keys", () => {
  assert.equal(cvDigest({ name: "D", contact: { github: "g", email: "e" } }), sha256('{"contact":{"email":"e","github":"g"},"name":"D"}'));
  assert.equal(cvDigest({ b: [{ y: 1, x: "é" }], a: null }), cvDigest({ a: null, b: [{ x: "é", y: 1 }] }));
  assert.notEqual(cvDigest({ skills: ["a", "b"] }), cvDigest({ skills: ["b", "a"] }), "the order of a list is part of it");
});

// The proof that this is the digest the first translations were stamped with: two values worked out
// by another implementation (Python's hashlib and json, as the migration that wrote the first
// digests used them), frozen here. They do not depend on what the repository holds today: whether
// every translation is current is what `npm run translate -- status` answers, not a unit test.
test("the digest agrees with the values another implementation gave", () => {
  const digest = sourceDigest({
    title: "Maré Rio: o software",
    excerpt: "Um “resumo” com aspas — e travessão.",
    tags: ["Maré", "IA"],
    body: "Primeiro parágrafo.\n\n## Seção\n\nCom nota[^n].\n\n[^n]: A nota.",
  });
  assert.equal(digest, "21f7fa6dc1e6e9235468d26c129b5bac1ed105935ed0c0b6f9bc25c1932338bd");
  assert.equal(
    cvDigest({"name": "Daniel", "skills": ["Kubeflow", "Sistemas distribuídos"], "contact": {"github": "g", "email": "e@x.io"}, "experience": [{"title": "Engenheiro", "period": "2026 - Presente"}]}),
    "aef929a11b42383665d8638d262e740e140fe27529ac917b54248e600dcc4cb4",
  );
});

test("every document in the repository is found with its translation, and a recorded digest is a digest", () => {
  const sources = discover(ROOT);
  assert.ok(sources.some((source) => source.file.startsWith("posts/")), "the posts are sources");
  assert.ok(sources.some((source) => source.file === "pages/about.md"), "About is a source");
  const cv = sources.find((source) => source.kind === "cv");
  assert.ok(cv, "cv_data.yaml is a source");
  assert.equal(cvHeader(readText(path.join(ROOT, cv.translation))).translation_of, "cv_data.yaml");
  for (const source of sources) {
    assert.match(source.digest, /^[0-9a-f]{64}$/);
    assert.ok(["current", "stale", "missing"].includes(stateOf(ROOT, source).status));
  }
});
