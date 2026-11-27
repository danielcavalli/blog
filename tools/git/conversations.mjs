#!/usr/bin/env node
// The margin stays home.
//
// Posts here are written and reviewed in Reef, which keeps the conversation about a document at the
// end of its file: a trailer of `<!-- reef comment … -->` and `<!-- reef reply … -->` blocks
// (reef-spec, sections 1 and 2). This repository is public and those conversations are not, so git
// never sees them. This file is the git filter that does it:
//
//   clean   (working file -> what git stores)   the conversation is taken out and kept on this
//                                               machine, inside the git directory
//   smudge  (what git stores -> working file)   the conversation kept for that file is put back
//
// What stays public is the body and the document marker (`<!-- reef document <id> · revision <n> … -->`),
// which is the document's identity and revision number, not conversation. Every other block of the
// trailer is private, including kinds this file does not know.
//
// A file with no trailer passes through byte for byte in both directions.
//
// The conversations live in `<git dir>/reef-conversations/<path>.trailer`, one generation back in
// `.trailer.prev`. They are on this machine only: nothing copies them anywhere.
//
// Two things follow from how git works, and are worth knowing:
//
// - After a conversation changes, `git status` lists the file as modified although `git diff` shows
//   nothing. Git goes by the file's size before it asks the filter. `git add <file>` (or `refresh`,
//   below) settles it: nothing is staged, and the conversation as it stands is kept. Until then git
//   refuses a checkout, merge or pull that would rewrite that file, which is what protects a
//   conversation newer than the copy kept here.
// - A command that throws local changes away (`git restore`, `git checkout -- <file>`,
//   `git reset --hard`) puts back the conversation as it was last kept, so what was said in the
//   margin since the last `git add` or `git diff` of that file goes with the rest.
//
//   node tools/git/conversations.mjs clean <path>      filter, stdin -> stdout
//   node tools/git/conversations.mjs smudge <path>     filter, stdin -> stdout
//   node tools/git/conversations.mjs check             fail if anything git holds has a conversation
//   node tools/git/conversations.mjs refresh           settle files whose conversation alone changed
//   node tools/git/conversations.mjs list              the files with a conversation kept here
//
// `node tools/git/setup.mjs` installs it (it runs on `npm install`).

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const BLOCK = /<!-- reef [\s\S]*?-->/g;

// The trailer starts at the first line beginning with `<!-- reef ` after which nothing but reef
// blocks and blank space follows (reef-spec, section 1). A reef comment anywhere else is body text.
function trailerStart(text) {
  const candidates = /(^|\n)<!-- reef /g;
  let match;
  while ((match = candidates.exec(text))) {
    const at = match.index + match[1].length;
    if (onlyBlocksFrom(text, at)) return at;
  }
  return text.length;
}

function onlyBlocksFrom(text, at) {
  const block = /\s*<!-- reef [\s\S]*?-->/y;
  let end = at;
  for (;;) {
    block.lastIndex = end;
    if (!block.exec(text)) break;
    end = block.lastIndex;
  }
  return end > at && /^\s*$/.test(text.slice(end));
}

/** A file as its body and the blocks of its trailer, in order. No trailer: no blocks. */
export function split(text) {
  const at = trailerStart(text);
  return { body: text.slice(0, at), blocks: text.slice(at).match(BLOCK) ?? [] };
}

const isPublic = (block) => block.startsWith("<!-- reef document ");

function join(body, blocks, eol) {
  const text = body.replace(/\s+$/, "");
  return blocks.length ? `${text}${eol}${eol}${blocks.join(eol)}${eol}` : `${text}${eol}`;
}

const eolOf = (text) => (text.includes("\r\n") ? "\r\n" : "\n");

/** What git stores: the file without its conversation, and the conversation that was taken out. */
export function toPublic(text) {
  const { body, blocks } = split(text);
  if (!blocks.length) return { text, conversation: [] };
  return {
    text: join(body, blocks.filter(isPublic), eolOf(text)),
    conversation: blocks.filter((block) => !isPublic(block)),
  };
}

/** The working file: what git stores with a conversation put back after the marker. */
export function withConversation(text, conversation) {
  if (!conversation.length) return text;
  const { body, blocks } = split(text);
  return join(body, [...blocks, ...conversation], eolOf(text));
}

// ---------- where the conversations are kept ----------

function gitDir() {
  return execFileSync("git", ["rev-parse", "--absolute-git-dir"], { encoding: "utf8" }).trim();
}

function keptAt(file, root = path.join(gitDir(), "reef-conversations")) {
  const clean = path.posix.normalize(file.replaceAll("\\", "/"));
  if (clean.startsWith("../") || path.isAbsolute(clean)) throw new Error(`not a path inside the repository: ${file}`);
  return path.join(root, `${clean}.trailer`);
}

// Bytes are read and written as latin1 so that nothing is re-encoded on the way through.
const read = (file) => (fs.existsSync(file) ? fs.readFileSync(file, "latin1") : null);

function write(file, text) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const partial = `${file}.${process.pid}.tmp`;
  fs.writeFileSync(partial, text, "latin1");
  fs.renameSync(partial, file);
}

/** Keep a file's conversation. What it replaces is kept one generation back, never thrown away. */
export function keep(file, conversation, root) {
  const at = keptAt(file, root);
  const before = read(at);
  const now = conversation.length ? `${conversation.join("\n")}\n` : null;
  if (now === before) return;
  if (before !== null) write(`${at}.prev`, before);
  if (now === null) fs.rmSync(at, { force: true });
  else write(at, now);
}

/** The conversation kept for a file. */
export function kept(file, root) {
  return (read(keptAt(file, root)) ?? "").match(BLOCK) ?? [];
}

// ---------- the command line ----------

function stdin() {
  return fs.readFileSync(0, "latin1");
}

function tracked() {
  const out = execFileSync("git", ["ls-files", "-z", "--", "*.md"], { encoding: "utf8" });
  return out.split("\0").filter(Boolean);
}

function main([command, file]) {
  if (command === "clean" && file) {
    const { text, conversation } = toPublic(stdin());
    keep(file, conversation);
    process.stdout.write(text, "latin1");
    return 0;
  }
  if (command === "smudge" && file) {
    process.stdout.write(withConversation(stdin(), kept(file)), "latin1");
    return 0;
  }
  if (command === "check") {
    const holding = tracked().filter((name) => {
      const stored = execFileSync("git", ["cat-file", "blob", `:${name}`], { encoding: "latin1", maxBuffer: 1 << 28 });
      return toPublic(stored).conversation.length > 0;
    });
    for (const name of holding) console.error(`${name}: a Reef conversation is in what git stores`);
    if (holding.length) {
      console.error("\nRun `node tools/git/setup.mjs`, then `git add --renormalize .` and commit.");
      return 1;
    }
    console.log("No Reef conversation is in what git stores.");
    return 0;
  }
  if (command === "refresh") {
    // Modified in the working tree, nothing staged, and no difference once the filter has run:
    // only the conversation changed. Adding the file stages nothing and keeps the conversation.
    const status = execFileSync("git", ["status", "--porcelain", "-z", "--", "*.md"], { encoding: "utf8" });
    const settled = [];
    for (const entry of status.split("\0").filter(Boolean)) {
      if (!entry.startsWith(" M ")) continue;
      const name = entry.slice(3);
      try {
        execFileSync("git", ["diff", "--quiet", "--", name], { stdio: "ignore" });
      } catch {
        continue; // the body changed too: that is the writer's to commit
      }
      execFileSync("git", ["add", "--", name]);
      settled.push(name);
    }
    for (const name of settled) console.log(`${name}: conversation kept, nothing to commit`);
    if (!settled.length) console.log("Nothing to settle.");
    return 0;
  }
  if (command === "list") {
    const root = path.join(gitDir(), "reef-conversations");
    const walk = (dir) =>
      fs.existsSync(dir)
        ? fs.readdirSync(dir, { withFileTypes: true }).flatMap((entry) =>
            entry.isDirectory() ? walk(path.join(dir, entry.name)) : [path.join(dir, entry.name)],
          )
        : [];
    for (const at of walk(root).filter((name) => name.endsWith(".trailer"))) {
      const name = path.relative(root, at).slice(0, -".trailer".length);
      const comments = (read(at).match(/<!-- reef comment /g) ?? []).length;
      console.log(`${name}: ${comments} ${comments === 1 ? "comment" : "comments"}`);
    }
    return 0;
  }
  console.error("usage: conversations.mjs clean <path> | smudge <path> | check | refresh | list");
  return 2;
}

if (process.argv[1] && fs.realpathSync(process.argv[1]) === fs.realpathSync(fileURLToPath(import.meta.url))) {
  process.exitCode = main(process.argv.slice(2));
}
