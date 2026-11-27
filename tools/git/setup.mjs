#!/usr/bin/env node
// Installs the filter that keeps Reef conversations out of git (conversations.mjs says why).
//
// The filter is copied into the git directory and git is pointed at that copy, not at the file in
// the working tree: git runs filters while it is still writing a checkout, when the working tree's
// own copy may not be there yet, or may be another branch's.
//
// Runs on `npm install`. Safe to run again; it refreshes the copy.

import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const git = (...args) => execFileSync("git", args, { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] }).trim();

let common;
try {
  common = git("rev-parse", "--path-format=absolute", "--git-common-dir");
} catch {
  console.log("Not a git checkout: the Reef conversation filter is not needed here.");
  process.exit(0);
}

const source = path.join(path.dirname(fileURLToPath(import.meta.url)), "conversations.mjs");
const installed = path.join(common, "reef-conversations-filter.mjs");
fs.copyFileSync(source, installed);

const quoted = `'${installed.replaceAll("'", "'\\''")}'`;
git("config", "filter.reef-conversations.clean", `node ${quoted} clean %f`);
git("config", "filter.reef-conversations.smudge", `node ${quoted} smudge %f`);
// A filter that fails stops git, rather than letting a conversation through.
git("config", "filter.reef-conversations.required", "true");

console.log("Reef conversations stay on this machine: git stores Markdown without them.");
