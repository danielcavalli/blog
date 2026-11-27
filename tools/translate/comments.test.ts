import assert from "node:assert/strict";
import { test } from "node:test";

import { markAddressed, openComments, readComments } from "./comments.ts";

// A trailer as Reef writes it (the blocks of comments 1 and 2 are `reef comment`'s own output, with
// their status set to `open`).
const MARKER = "<!-- reef document k3x9f2 · revision 3 · note the method comes before the results -->";
const TRAILER = `${MARKER}
<!-- reef comment 1 · open · Daniel Cavalli · 2026-11-27T02:49Z · line 3 · before e Meu nome é Daniel Cavalli. Sou · after e estudei economia \\· e mais. Não
> Engenheiro de Machine Learning
Prefiro minúsculas aqui: engenheiro de machine learning --\\> assim.
-->
<!-- reef reply 1 · Claude · 2026-11-27T03:01Z
Em todo o texto, ou só aqui?
-->
<!-- reef reply 1 · Daniel Cavalli · 2026-11-27T03:05Z
Em todo o texto.
-->
<!-- reef comment 2 · open · Daniel Cavalli · 2026-11-27T02:49Z · line 5 · before e mais. Não que eu precisasse de · after para isso.
> formação formal

> citação no começo
segunda linha
-->
<!-- reef comment 3 · resolved · Daniel Cavalli · 2026-11-20T10:00Z · line 7
> duas linhas
> de citação
Já resolvido: a palavra open aqui não é um status · nem isto.
-->
<!-- reef comment 12 · addressed · Daniel Cavalli · 2026-11-21T10:00Z
Sem citação.
-->
<!-- reef scribble 9 · open · something a later Reef writes -->
`;

test("a comment is read with its fields, its quote, its text and its replies", () => {
  const [first, second, third, fourth, ...rest] = readComments(TRAILER);
  assert.deepEqual(rest, [], "the marker and blocks of unknown kinds are not comments");
  assert.deepEqual(first, {
    id: 1,
    status: "open",
    author: "Daniel Cavalli",
    time: "2026-11-27T02:49Z",
    line: 3,
    before: "e Meu nome é Daniel Cavalli. Sou",
    after: "e estudei economia · e mais. Não",
    quote: "Engenheiro de Machine Learning",
    text: "Prefiro minúsculas aqui: engenheiro de machine learning --> assim.",
    replies: [
      { author: "Claude", time: "2026-11-27T03:01Z", text: "Em todo o texto, ou só aqui?" },
      { author: "Daniel Cavalli", time: "2026-11-27T03:05Z", text: "Em todo o texto." },
    ],
  });
  assert.equal(second!.quote, "formação formal");
  assert.equal(second!.text, "> citação no começo\nsegunda linha", "a comment that starts with > is set off by a blank line");
  assert.equal(third!.quote, "duas linhas\nde citação");
  assert.equal(third!.status, "resolved");
  assert.deepEqual([fourth!.id, fourth!.status, fourth!.line, fourth!.quote, fourth!.text], [12, "addressed", null, "", "Sem citação."]);
});

test("the open comments are the ones waiting for an agent", () => {
  assert.deepEqual(openComments(TRAILER).map((comment) => comment.id), [1, 2]);
  assert.deepEqual(openComments(""), []);
  assert.deepEqual(openComments(`${MARKER}\n`), []);
});

test("escapes inside a block are removed once", () => {
  const block = "<!-- reef comment 5 · open · A \\· B · 2026-01-01T00:00Z · line 1\n> a --\\> b --\\\\> c --\\!> d\ntext\n-->";
  const [comment] = readComments(block);
  assert.equal(comment!.author, "A · B");
  assert.equal(comment!.quote, "a --> b --\\> c --!> d");
});

test("addressing a comment changes its status word and nothing else", () => {
  const after = markAddressed(TRAILER, [1]);
  assert.equal(after, TRAILER.replace("<!-- reef comment 1 · open · ", "<!-- reef comment 1 · addressed · "));
  assert.equal(after.length, TRAILER.length + "addressed".length - "open".length);
  assert.deepEqual(readComments(after).map((comment) => comment.status), ["addressed", "open", "resolved", "addressed"]);
  assert.deepEqual(readComments(after)[0]!.replies, readComments(TRAILER)[0]!.replies);
});

test("only the comments named are addressed, and only if they are open", () => {
  assert.equal(markAddressed(TRAILER, []), TRAILER);
  assert.equal(markAddressed(TRAILER, [3, 12, 9, 99]), TRAILER, "resolved, addressed, unknown and absent comments are left alone");
  const both = markAddressed(TRAILER, [2, 1]);
  assert.deepEqual(openComments(both), []);
  assert.equal(both.replaceAll(" · addressed · Daniel Cavalli · 2026-11-27", " · open · Daniel Cavalli · 2026-11-27"), TRAILER);
});

test("a trailer with CRLF line ends and no final newline is kept as it is", () => {
  const crlf = TRAILER.replaceAll("\n", "\r\n").trimEnd();
  const after = markAddressed(crlf, [2]);
  assert.equal(after, crlf.replace("<!-- reef comment 2 · open · ", "<!-- reef comment 2 · addressed · "));
  assert.deepEqual(openComments(crlf).map((comment) => comment.id), [1, 2]);
});
