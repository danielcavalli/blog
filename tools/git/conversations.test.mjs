import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

import { keep, kept, split, toPublic, withConversation } from "./conversations.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));

const MARKER = "<!-- reef document k3x9f2 · revision 3 · note the method comes before the results -->";
const COMMENT = `<!-- reef comment 4 · open · Daniel Cavalli · 2026-10-05T14:02Z · line 3
> a reader sees
Say who the reader is.
-->`;
const REPLY = `<!-- reef reply 4 · Claude · 2026-10-05T14:20Z
The reader is introduced in section 2, two paragraphs on.
-->`;
const BODY = "# Title\n\nThe body: everything a reader sees.[^1]\n\n[^1]: A footnote.\n";

test("a file with no trailer passes through byte for byte", () => {
  for (const text of [BODY, "no final newline", "ends with two\n\n", "crlf\r\nfile\r\n", ""]) {
    assert.equal(toPublic(text).text, text);
    assert.deepEqual(toPublic(text).conversation, []);
    assert.equal(withConversation(text, []), text);
  }
});

test("the conversation is taken out and the marker stays", () => {
  const working = `${BODY}\n${MARKER}\n${COMMENT}\n${REPLY}\n`;
  const { text, conversation } = toPublic(working);
  assert.equal(text, `${BODY}\n${MARKER}\n`);
  assert.deepEqual(conversation, [COMMENT, REPLY]);
});

test("a file with only comments becomes its body", () => {
  const { text, conversation } = toPublic(`${BODY}\n${COMMENT}\n`);
  assert.equal(text, BODY);
  assert.deepEqual(conversation, [COMMENT]);
});

test("a block of a kind this filter does not know is private", () => {
  const unknown = "<!-- reef scribble 1 · something a later Reef writes -->";
  const { text, conversation } = toPublic(`${BODY}\n${MARKER}\n${unknown}\n`);
  assert.equal(text, `${BODY}\n${MARKER}\n`);
  assert.deepEqual(conversation, [unknown]);
});

test("a reef comment shown in the body is body text", () => {
  const post = `Reef stores comments like this:\n\n\`\`\`markdown\n${COMMENT}\n\`\`\`\n\nAnd the text goes on.\n`;
  assert.equal(toPublic(post).text, post);
  const withTrailer = `${post}\n${COMMENT}\n`;
  assert.equal(toPublic(withTrailer).text, post);
  assert.equal(split(withTrailer).blocks.length, 1);
});

test("an escaped --> inside a comment does not end it early", () => {
  const tricky = "<!-- reef comment 7 · open · Daniel · 2026-10-05T14:02Z\n> x\nwrite it as --\\> here\n-->";
  const { text, conversation } = toPublic(`${BODY}\n${tricky}\n`);
  assert.equal(text, BODY);
  assert.deepEqual(conversation, [tricky]);
});

test("putting the conversation back and taking it out again gives what git stores", () => {
  for (const working of [
    `${BODY}\n${MARKER}\n${COMMENT}\n${REPLY}\n`,
    `${BODY}\n${COMMENT}\n`,
    `${BODY}\n\n\n${COMMENT}\n\n${MARKER}\n`,
    `${BODY.replaceAll("\n", "\r\n")}\r\n${MARKER}\r\n${COMMENT}\r\n`,
  ]) {
    const { text: stored, conversation } = toPublic(working);
    const restored = withConversation(stored, conversation);
    assert.equal(toPublic(restored).text, stored);
    assert.deepEqual(toPublic(restored).conversation, conversation);
    assert.equal(toPublic(stored).text, stored, "what git stores is already clean");
  }
});

test("a conversation that is replaced is kept one generation back", () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "conversations-"));
  keep("posts/a.md", [COMMENT], root);
  assert.deepEqual(kept("posts/a.md", root), [COMMENT]);
  keep("posts/a.md", [COMMENT, REPLY], root);
  assert.deepEqual(kept("posts/a.md", root), [COMMENT, REPLY]);
  keep("posts/a.md", [], root);
  assert.deepEqual(kept("posts/a.md", root), []);
  assert.equal(fs.readFileSync(path.join(root, "posts/a.md.trailer.prev"), "latin1"), `${COMMENT}\n${REPLY}\n`);
  assert.throws(() => keep("../outside.md", [COMMENT], root));
});

test("in a repository: git never stores the conversation, and a checkout brings it back", () => {
  const repo = fs.mkdtempSync(path.join(os.tmpdir(), "conversations-repo-"));
  const git = (...args) => execFileSync("git", args, { cwd: repo, encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
  git("init", "-q", "-b", "main");
  git("config", "user.email", "test@example.invalid");
  git("config", "user.name", "Test");
  fs.mkdirSync(path.join(repo, "tools/git"), { recursive: true });
  fs.mkdirSync(path.join(repo, "posts"));
  for (const name of ["conversations.mjs", "setup.mjs"]) fs.copyFileSync(path.join(here, name), path.join(repo, "tools/git", name));
  fs.writeFileSync(path.join(repo, ".gitattributes"), "*.md filter=reef-conversations\n");
  const post = path.join(repo, "posts/a.md");
  fs.writeFileSync(post, BODY);
  execFileSync("node", ["tools/git/setup.mjs"], { cwd: repo });
  git("add", ".");
  git("commit", "-q", "-m", "a post");

  const run = (...args) => execFileSync("node", ["tools/git/conversations.mjs", ...args], { cwd: repo, encoding: "utf8" });
  const refused = (...args) => {
    try {
      git(...args);
    } catch (error) {
      return String(error.stderr);
    }
    return null;
  };

  // A comment arrives, as Reef writes it. Git has nothing to commit: the diff is empty. It lists the
  // file as modified all the same (it goes by size), until the file is added or refreshed.
  const commented = `${BODY}\n${COMMENT}\n`;
  fs.writeFileSync(post, commented);
  assert.equal(git("diff"), "");
  assert.equal(git("status", "--porcelain"), " M posts/a.md\n");
  assert.match(run("refresh"), /posts\/a\.md: conversation kept, nothing to commit/);
  assert.equal(git("status", "--porcelain"), "");
  assert.equal(git("show", "HEAD:posts/a.md"), BODY);
  assert.equal(fs.readFileSync(post, "utf8"), commented);

  // The body changes under the comment: only the body is committed.
  const edited = commented.replace("everything a reader sees", "everything the reader sees");
  fs.writeFileSync(post, edited);
  assert.match(run("refresh"), /Nothing to settle/, "a changed body is the writer's to commit");
  git("commit", "-q", "-am", "reword");
  assert.equal(git("show", "HEAD:posts/a.md"), BODY.replace("everything a reader sees", "everything the reader sees"));
  assert.equal(fs.readFileSync(post, "utf8"), edited);

  // A reply arrives. Git will not rewrite the file while its conversation is newer than the copy kept.
  const replied = `${edited}${REPLY}\n`;
  fs.writeFileSync(post, replied);
  assert.match(refused("checkout", "-q", "HEAD~1") ?? "", /would be overwritten by checkout/);
  assert.equal(fs.readFileSync(post, "utf8"), replied);
  run("refresh");

  // Now git rewrites the file (the commit before, then this one again), and the conversation comes back.
  git("checkout", "-q", "HEAD~1");
  assert.match(fs.readFileSync(post, "utf8"), /everything a reader sees[\s\S]*<!-- reef comment 4 [\s\S]*<!-- reef reply 4 /);
  git("checkout", "-q", "main");
  assert.equal(fs.readFileSync(post, "utf8"), replied);
  assert.equal(git("status", "--porcelain"), "");
  // (The filter's own source names the blocks, so the history is searched under posts/ only.)
  assert.doesNotMatch(git("log", "--all", "-p", "--format=", "--", "posts"), /reef (comment|reply)/, "no commit holds a conversation");

  assert.match(run("check"), /No Reef conversation/);
  assert.match(run("list"), /posts\/a\.md: 1 comment/);
});
