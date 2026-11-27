// The margin comments in a file's reef trailer (reef-spec, sections 1 and 2).
//
//   <!-- reef comment <id> · <status> · <author> · <time> · line <n> …
//   > the quoted passage, one "> " line per line
//   The comment, any number of lines.
//   -->
//
//   <!-- reef reply <id> · <author> · <time>
//   The reply.
//   -->
//
// Reading is all this does to a trailer, with one exception: a comment's status word may go from
// `open` to `addressed`. Every other byte of the trailer is kept.

const BLOCK = /<!-- reef [\s\S]*?-->/g;
const SEPARATOR = " · ";

export interface Reply {
  author: string;
  time: string;
  text: string;
}

export interface Comment {
  id: number;
  /** `open`, `addressed`, `replied` or `resolved`. */
  status: string;
  author: string;
  time: string;
  /** The line of the body where the quote starts, when the comment says. */
  line: number | null;
  /** The words just before and just after the quote, when the comment keeps them. */
  before: string | null;
  after: string | null;
  /** The passage the comment is about. */
  quote: string;
  text: string;
  replies: Reply[];
}

// Inside a block `-->` is written `--\>` (and `--!>`, `--\!>`); in a field a `·` between spaces is
// written `\·`. One backslash is the escape; any others were there before it.
const unescapeText = (text: string): string => text.replace(/--\\(\\*!?>)/g, "--$1");
const unescapeField = (field: string): string => field.replace(/\\(\\*·)/g, "$1");

// A block as its header's fields and the lines under the header.
function parts(block: string): { fields: string[]; lines: string[] } {
  const inner = block.replace(/^<!-- reef /, "").replace(/\s*-->$/, "");
  const [header = "", ...lines] = inner.split(/\r?\n/);
  return { fields: header.split(SEPARATOR).map((field) => unescapeField(field.trim())), lines };
}

/** Every comment in a trailer, in the order written, each with the replies under it. */
export function readComments(trailer: string): Comment[] {
  const comments: Comment[] = [];
  for (const block of trailer.match(BLOCK) ?? []) {
    const { fields, lines } = parts(block);
    const [kind, id] = fields[0]!.split(/\s+/);
    if (kind === "reply") {
      const comment = comments.find((candidate) => candidate.id === Number(id));
      comment?.replies.push({
        author: fields[1] ?? "",
        time: fields[2] ?? "",
        text: unescapeText(lines.join("\n")).trim(),
      });
      continue;
    }
    if (kind !== "comment" || !/^\d+$/.test(id ?? "")) continue;
    let at = 0;
    while (at < lines.length && lines[at]!.startsWith(">")) at++;
    const quote = lines.slice(0, at).map((line) => line.replace(/^> ?/, ""));
    // A comment whose own first line starts with `>` is set off from the quote by one blank line.
    if (at > 0 && lines[at] === "" && lines[at + 1]?.startsWith(">")) at++;
    const hint = (name: string): string | null => {
      const field = fields.slice(4).find((candidate) => candidate === name || candidate.startsWith(`${name} `));
      return field === undefined ? null : field.slice(name.length + 1);
    };
    const line = hint("line");
    comments.push({
      id: Number(id),
      status: fields[1] ?? "",
      author: fields[2] ?? "",
      time: fields[3] ?? "",
      line: line !== null && /^\d+$/.test(line) ? Number(line) : null,
      before: hint("before"),
      after: hint("after"),
      quote: unescapeText(quote.join("\n")),
      text: unescapeText(lines.slice(at).join("\n")).trim(),
      replies: [],
    });
  }
  return comments;
}

/** The comments that are the agent's to answer. */
export const openComments = (trailer: string): Comment[] =>
  readComments(trailer).filter((comment) => comment.status === "open");

/**
 * The trailer with the status of each of these comments changed from `open` to `addressed`.
 * Nothing else changes: not a comment that is not open, not a byte outside that one word.
 */
export function markAddressed(trailer: string, ids: Iterable<number>): string {
  const wanted = new Set(ids);
  return trailer.replace(BLOCK, (block) =>
    block.replace(/^(<!-- reef comment (\d+) · )open(?= · )/, (whole, head: string, id: string) =>
      wanted.has(Number(id)) ? `${head}addressed` : whole,
    ),
  );
}
