// What the checks read out of a Markdown text: its fenced code, the destinations of its links and
// images, its footnote labels, its parenthetical asides, its slides.
//
// These are scanners, not a Markdown parser. They are ports of the old engine's
// (`presentation_translation.py`, `protected_markdown.py`), which compared a source with its
// translation by running the same scanner over both. A quirk in what a scanner takes for a link
// is therefore harmless: it takes the same thing on both sides.

const FENCE_OPEN = /^[ \t]{0,3}(`{3,}|~{3,}).*$/;

interface Fence {
  char: string;
  length: number;
}

const opens = (line: string): Fence | null => {
  const match = FENCE_OPEN.exec(line);
  return match ? { char: match[1]![0]!, length: match[1]!.length } : null;
};

const closes = (line: string, fence: Fence): boolean =>
  new RegExp(`^[ \\t]{0,3}${fence.char === "`" ? "`" : "~"}{${fence.length},}[ \\t]*$`).test(line);

/** CRLF read as LF: every scanner here works on LF text. */
export const lf = (text: string): string => text.replace(/\r\n?/g, "\n");

/** A text as its lines, each keeping its newline. */
function linesOf(text: string): string[] {
  return text.match(/[^\n]*\n|[^\n]+/g) ?? [];
}

/** Each line with whether it is inside a fenced code block (the fence's own lines included). */
function walk(text: string): { line: string; raw: string; fenced: boolean; opening: boolean; closing: boolean }[] {
  const out = [];
  let fence: Fence | null = null;
  for (const raw of linesOf(text)) {
    const line = raw.endsWith("\n") ? raw.slice(0, -1) : raw;
    if (!fence) {
      fence = opens(line);
      out.push({ line, raw, fenced: fence !== null, opening: fence !== null, closing: false });
      continue;
    }
    const closing = closes(line, fence);
    if (closing) fence = null;
    out.push({ line, raw, fenced: true, opening: false, closing });
  }
  return out;
}

/** The fenced code blocks of a text, delimiter lines included. An unclosed one runs to the end. */
export function fencedBlocks(text: string): string[] {
  const blocks: string[] = [];
  let current: string[] | null = null;
  for (const { raw, fenced, closing } of walk(lf(text))) {
    if (!fenced) continue;
    (current ??= []).push(raw);
    if (closing) {
      blocks.push(current.join(""));
      current = null;
    }
  }
  if (current) blocks.push(current.join(""));
  return blocks;
}

/** The opening and closing line of each fenced block: its delimiters and language, not its content. */
export function fenceSignatures(text: string): [string, string][] {
  const signatures: [string, string][] = [];
  let opening: string | null = null;
  for (const step of walk(lf(text))) {
    if (step.opening) opening = step.line;
    else if (step.closing && opening !== null) {
      signatures.push([opening, step.line]);
      opening = null;
    }
  }
  if (opening !== null) signatures.push([opening, ""]);
  return signatures;
}

/** The text with every fenced block blanked, its lines kept so that line numbers hold. */
export function stripFences(text: string): string {
  return walk(lf(text))
    .map((step) => (step.fenced ? "\n" : step.raw))
    .join("");
}

// ---------- fenced code that must not change ----------

// A Mermaid label keeps its embedded markup (line breaks, links) and gives up its words.
const label = (text: string): string => `TEXT${(text.match(/<[^>]*>/g) ?? []).join("")}`;

// A fenced block as it must survive translation: byte for byte, except a Mermaid flowchart, whose
// visible labels and accessibility text are the translator's and everything else is not.
function signature(block: string): string {
  const lines = linesOf(block);
  if (!/^\s*(?:`{3,}|~{3,})mermaid\s*$/.test(lines[0] ?? "")) return block;
  if (!lines.slice(1).some((line) => /^\s*(?:flowchart|graph)\s+(?:TB|TD|BT|RL|LR)\s*$/.test(line))) {
    return block; // a diagram grammar this does not know keeps the ordinary exact-code rule
  }
  return lines
    .map((line) => {
      if (line.trimStart().startsWith("%%") || /^\s*(?:click|style|classDef|class|linkStyle)\b/.test(line)) {
        return line; // directives and comments stay byte for byte
      }
      if (/^\s*acc(?:Title|Descr):/.test(line)) return line.replace(/(?<=:)[^\r\n]*/, " TEXT");
      // Quoted and bare node or subgraph labels; identifiers and shapes remain.
      let out = line.replace(/\["((?:\\.|[^"\\])*)"\]/g, (_, inner: string) => `["${label(inner)}"]`);
      out = out.replace(/\[([^\[\]"\r\n]*)\]/g, (_, inner: string) => `[${label(inner)}]`);
      if (/(?:--|==|\.->)/.test(out)) out = out.replace(/\|([^|\r\n]*)\|/g, (_, inner: string) => `|${label(inner)}|`);
      return out;
    })
    .join("");
}

/** Every fenced block as it must survive translation. */
export function protectedFences(text: string): string[] {
  return fencedBlocks(text.trim()).map(signature);
}

// ---------- links and images ----------

export interface Destination {
  kind: "link" | "image";
  destination: string;
}

function isEscaped(text: string, position: number): boolean {
  let backslashes = 0;
  for (let cursor = position - 1; cursor >= 0 && text[cursor] === "\\"; cursor--) backslashes++;
  return backslashes % 2 === 1;
}

function closingBracket(text: string, opening: number): number {
  for (let position = opening + 1; position < text.length; position++) {
    if (text[position] === "]" && !isEscaped(text, position)) return position;
  }
  return -1;
}

function closingParen(text: string, opening: number): number {
  let depth = 0;
  for (let position = opening; position < text.length; position++) {
    const char = text[position];
    if (char === "\\") position++;
    else if (char === "(") depth++;
    else if (char === ")" && --depth === 0) return position;
  }
  return -1;
}

function destinationOf(raw: string): string {
  const stripped = raw.trim();
  if (!stripped) return "";
  if (stripped.startsWith("<")) {
    const closing = stripped.indexOf(">");
    return closing === -1 ? stripped.slice(1) : stripped.slice(1, closing);
  }
  return stripped.split(/\s+/, 1)[0]!;
}

interface Inline {
  kind: "link" | "image";
  /** Where the construct starts (the `!` of an image, the `[` of a link) and ends (after `)`). */
  start: number;
  end: number;
  text: string;
  raw: string;
  destination: string;
}

// `[text](destination "title")` and `![alt](path "title")`, in reading order.
function inlines(text: string): Inline[] {
  const found: Inline[] = [];
  let position = 0;
  while (position < text.length) {
    const marker = text.indexOf("[", position);
    if (marker === -1) break;
    position = marker + 1;
    if (isEscaped(text, marker)) continue;
    const labelEnd = closingBracket(text, marker);
    if (labelEnd === -1 || text[labelEnd + 1] !== "(") continue;
    const end = closingParen(text, labelEnd + 1);
    if (end === -1) continue;
    const image = marker > 0 && text[marker - 1] === "!";
    const raw = text.slice(labelEnd + 2, end);
    const destination = destinationOf(raw);
    if (destination) {
      found.push({
        kind: image ? "image" : "link",
        start: image ? marker - 1 : marker,
        end: end + 1,
        text: text.slice(marker + 1, labelEnd),
        raw,
        destination,
      });
    }
    position = end + 1;
  }
  return found;
}

const REFERENCE = /^[ \t]{0,3}\[(?!\^)[^\]]+\]:[ \t]*(<[^>\n]+>|\S+)/gm;
const HTML_TAG = /<(a|img)\b([^<>]*)>/gi;
const HTML_ATTRIBUTE = /([^\s=/]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+))/g;

/** Where every link and image outside fenced code points: inline, by reference, and in inline HTML. */
export function destinations(text: string): Destination[] {
  const prose = stripFences(text);
  const found: Destination[] = inlines(prose).map(({ kind, destination }) => ({ kind, destination }));
  for (const match of prose.matchAll(REFERENCE)) {
    const destination = destinationOf(match[1]!);
    if (destination) found.push({ kind: "link", destination });
  }
  for (const tag of prose.matchAll(HTML_TAG)) {
    const wanted = tag[1]!.toLowerCase() === "a" ? "href" : "src";
    let value: string | undefined;
    for (const attribute of tag[2]!.matchAll(HTML_ATTRIBUTE)) {
      if (attribute[1]!.toLowerCase() === wanted) value = attribute[2] ?? attribute[3] ?? attribute[4];
    }
    if (value) found.push({ kind: wanted === "href" ? "link" : "image", destination: value });
  }
  return found;
}

export interface Image {
  path: string;
  alt: string;
  /** The quoted text after the path, which the page shows as the picture's caption. */
  title: string | null;
}

const TITLE = /^\s*(?:"((?:\\.|[^"\\])*)"|'((?:\\.|[^'\\])*)'|\(((?:\\.|[^()\\])*)\))\s*$/;

function titleOf(raw: string): string | null {
  const stripped = raw.trim();
  const rest = stripped.startsWith("<") ? stripped.slice(stripped.indexOf(">") + 1) : stripped.replace(/^\S+/, "");
  const match = TITLE.exec(rest);
  return match ? (match[1] ?? match[2] ?? match[3] ?? "") : null;
}

/** The Markdown images of a text, in reading order. */
export function images(text: string): Image[] {
  return inlines(stripFences(text))
    .filter((inline) => inline.kind === "image")
    .map((inline) => ({ path: inline.destination, alt: inline.text, title: titleOf(inline.raw) }));
}

// ---------- footnotes ----------

/** How many times each footnote label appears outside fenced code: its definition and every reference. */
export function footnoteLabels(text: string): Map<string, number> {
  const counts = new Map<string, number>();
  for (const match of stripFences(text).matchAll(/(?<!\\)\[\^([^\]\s]+)\]/g)) {
    counts.set(match[1]!, (counts.get(match[1]!) ?? 0) + 1);
  }
  return counts;
}

// ---------- parenthetical asides ----------

// The prose a reader sees, one block per paragraph, list item, heading, table cell or caption:
// no code, no markup, no link destination, no image path, no alt text.
function proseBlocks(markdown: string): string[] {
  let text = stripFences(markdown);
  text = text.replace(/<!--[\s\S]*?-->/g, "");
  text = text.replace(/<(script|style|pre|code)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, "");
  // Inline code: a run of backticks up to the next run of the same length, within one paragraph.
  text = text.replace(/(?<!`)(`+)(?!`)(?:(?!\n[ \t]*\n)[\s\S])*?(?<!`)\1(?!`)/g, "");
  // An image leaves its caption, as a block of its own; a link leaves its text.
  let rebuilt = "";
  let at = 0;
  for (const inline of inlines(text)) {
    rebuilt += text.slice(at, inline.start);
    rebuilt += inline.kind === "image" ? `\n\n${titleOf(inline.raw) ?? ""}\n\n` : inline.text;
    at = inline.end;
  }
  text = rebuilt + text.slice(at);
  text = text.replace(REFERENCE, "");
  text = text.replace(/^[ \t]{0,3}\[\^[^\]\s]+\]:[ \t]*/gm, "");
  text = text.replace(/\[\^[^\]\s]+\]/g, "");
  text = text.replace(/\[([^\]]*)\]\[[^\]]*\]/g, "$1");
  text = text.replace(/<(https?:\/\/[^>\s]+)>/g, "$1");
  text = text.replace(/<\/?[a-zA-Z][^<>]*>/g, "");

  const blocks: string[] = [];
  for (const paragraph of text.split(/\n[ \t]*\n/)) {
    let current = "";
    for (const line of paragraph.split("\n")) {
      const row = /^\s*\|.*\|\s*$/.test(line);
      if (row || /^\s*(?:[-*+]|\d+[.)])\s+|^\s{0,3}#{1,6}\s/.test(line)) {
        blocks.push(current);
        current = "";
      }
      if (row) blocks.push(...line.split("|"));
      else current += `${line}\n`;
    }
    blocks.push(current);
  }
  return blocks.filter((block) => block.trim());
}

const count = (text: string, char: string): number => text.split(char).length - 1;

/**
 * The parenthetical asides of a text's prose, in reading order: each balanced group, with what it
 * encloses and any asides nested in it. A parenthesis that never closes within its block is not one.
 */
export function parentheticals(markdown: string): string[] {
  const groups: string[] = [];
  for (let block of proseBlocks(lf(markdown))) {
    // A bare URL is a protected destination, not an aside. Its balanced parentheses are its own;
    // an unmatched closing one closes an aside that ends with the URL.
    block = block.replace(/https?:\/\/\S+/g, (url) => ")".repeat(Math.max(0, count(url, ")") - count(url, "("))));
    let depth = 0;
    let current = "";
    for (const char of block) {
      if (char === "(") depth++;
      if (depth) current += char;
      if (char === ")" && depth && --depth === 0) {
        groups.push(current);
        current = "";
      }
    }
  }
  return groups;
}

/** An aside's shape: its parentheses alone, which is what must survive translation. */
export const shapeOf = (group: string): string => group.replace(/[^()]/g, "");

// ---------- presentations ----------

export interface Slide {
  id: string;
  /** What is between the slide's markers. */
  markdown: string;
}

export interface Deck {
  /** Every `<!-- presentation:… -->` comment outside fenced code, in order, as written. */
  markers: string[];
  slides: Slide[];
  /** Why the slide markers cannot be read, if they cannot. */
  error: string | null;
}

const SLIDE_OPEN = /^\s*<!--\s*presentation:slide\s+(.*?)\s*-->\s*$/;
const SLIDE_CLOSE = /^\s*<!--\s*\/presentation:slide\s*-->\s*$/;
const MARKER = /<!--\s*\/?presentation:.*?-->/g;

/** A presentation as its slides. Only whole-line slide markers outside fenced code are markers. */
export function deck(text: string): Deck {
  const markers: string[] = [];
  const slides: Slide[] = [];
  const seen = new Set<string>();
  let error: string | null = null;
  let open: { id: string; line: number; lines: string[] } | null = null;
  let number = 0;
  for (const step of walk(lf(text))) {
    number++;
    if (step.fenced) {
      open?.lines.push(step.raw);
      continue;
    }
    markers.push(...(step.line.match(MARKER) ?? []));
    const opening = SLIDE_OPEN.exec(step.line);
    if (opening) {
      const id = /(?:^|\s)id="([^"]*)"/.exec(opening[1]!)?.[1];
      if (open) error ??= `nested slide marker at line ${number}`;
      else if (!id) error ??= `slide marker without an id at line ${number}`;
      else if (seen.has(id)) error ??= `duplicate slide id "${id}" at line ${number}`;
      open = { id: id ?? "", line: number, lines: [] };
      continue;
    }
    if (SLIDE_CLOSE.test(step.line)) {
      if (!open) error ??= `closing slide marker without an opener at line ${number}`;
      else {
        slides.push({ id: open.id, markdown: open.lines.join("") });
        seen.add(open.id);
      }
      open = null;
      continue;
    }
    open?.lines.push(step.raw);
  }
  if (open) error ??= `slide "${open.id}" opened at line ${open.line} is never closed`;
  if (!slides.length) error ??= "no slide markers found";
  return { markers, slides, error };
}
