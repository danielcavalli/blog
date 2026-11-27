// A deck: a document written as slides, read here into the sheets the design system's deck shows.
// Server only.
//
// A deck is Markdown like any post, with each slide between two comments:
//
//     <!-- presentation:slide id="foundation" layout="divider" density="open" -->
//     # The Foundation
//     ## Continuity is an illusion you engineer
//     <!-- /presentation:slide -->
//
// `layout` says what the slide is: `lead` (the talk's cover, and its goodbye), `divider` (a part
// opens), `emphasis` (one statement), `bio` (who speaks: words beside a portrait), and anything else
// a working sheet. `density` is the size of a working sheet's lines: `open`, `dense` or `tight`.
// Inside a slide, `<!-- presentation:block type="card_grid" -->` holds points (each a
// `<!-- presentation:card -->` with a `###` name) and `type="split"` two columns (each a
// `<!-- presentation:column -->`).

import { renderDocument, type RenderOptions } from "./render";
import type { TreeNode } from "./tree";

export type Density = "open" | "dense" | "tight";

export type SheetPart =
  | { type: "text"; nodes: TreeNode[] }
  | { type: "points"; across?: 2 | 3 | 4 | 5; points: { name: string; body: TreeNode[] }[] }
  | { type: "split"; wide?: "start" | "end"; sides: [TreeNode[], TreeNode[]] };

export type Sheet =
  | { kind: "cover"; id: string; words: string[]; voice?: string; by?: string }
  | { kind: "chapter"; id: string; name: string; claim?: string }
  | { kind: "statement"; id: string; title?: string; density: Density; statement: TreeNode[]; note: TreeNode[] }
  | { kind: "slide"; id: string; title: string; density: Density; parts: SheetPart[] };

const SLIDE = /<!-- presentation:slide ([^>]*?)-->([\s\S]*?)<!-- \/presentation:slide -->/g;
const BLOCK = /<!-- presentation:block(?: type="([a-z_]+)")? -->([\s\S]*?)<!-- \/presentation:block -->/g;
const inside = (name: string) => new RegExp(`<!-- presentation:${name} -->([\\s\\S]*?)<!-- \\/presentation:${name} -->`, "g");

// The old engine's words for a density are read as the nearest of the three.
const DENSITIES: Record<string, Density> = { open: "open", dense: "dense", tight: "tight", normal: "open", very_dense: "tight" };

/** The first heading of a level, taken out of the Markdown. */
function take(markdown: string, level: 1 | 2 | 3): { heading?: string; rest: string } {
  const line = new RegExp(`^${"#".repeat(level)} +(.+)$`, "m").exec(markdown);
  if (!line) return { rest: markdown };
  return { heading: line[1].trim(), rest: (markdown.slice(0, line.index) + markdown.slice(line.index + line[0].length)).trim() };
}

/** A cover's strokes: a name of several words is laid as two, as near in length as its words allow. */
function strokes(name: string): string[] {
  const words = name.split(/\s+/);
  if (words.length < 3 || name.length < 14) return [name];
  let best = 1;
  for (let at = 1; at < words.length; at++) {
    const lead = words.slice(0, at).join(" ").length;
    const bestLead = words.slice(0, best).join(" ").length;
    if (Math.abs(name.length - 2 * lead) < Math.abs(name.length - 2 * bestLead)) best = at;
  }
  return [words.slice(0, best).join(" "), words.slice(best).join(" ")];
}

const plain = (markdown: string) => markdown.replace(/\s*\|\s*/g, " · ").replace(/\s+/g, " ").trim();

export function readDeck(markdown: string, options: RenderOptions = {}): Sheet[] {
  const draw = (text: string) => (text.trim() ? renderDocument(text, options).body : []);
  const sheets: Sheet[] = [];
  for (const [, given, content] of markdown.matchAll(SLIDE)) {
    const said = Object.fromEntries([...given.matchAll(/([a-z_]+)="([^"]*)"/g)].map(([, key, value]) => [key, value]));
    const id = said.id ?? `sheet-${sheets.length + 1}`;
    const density = DENSITIES[said.density ?? "open"] ?? "open";
    const { heading: title = "", rest } = take(content.trim(), 1);

    if (said.layout === "lead") {
      const { heading: voice, rest: by } = take(rest, 2);
      sheets.push({ kind: "cover", id, words: strokes(title), voice, by: plain(by) || undefined });
      continue;
    }
    if (said.layout === "divider") {
      const { heading: claim } = take(rest, 2);
      sheets.push({ kind: "chapter", id, name: title, claim });
      continue;
    }
    if (said.layout === "emphasis") {
      // The statement is the slide's quote, or its first paragraph; what follows is its note.
      const quote = /^(?:> ?.*(?:\n|$))+/m.exec(rest);
      const statement = quote ? quote[0].replace(/^> ?/gm, "").trim() : rest.split(/\n\s*\n/)[0];
      const note = quote ? rest.slice(0, quote.index) + rest.slice(quote.index + quote[0].length) : rest.split(/\n\s*\n/).slice(1).join("\n\n");
      const drawn = draw(statement);
      const first = drawn[0];
      sheets.push({ kind: "statement", id, title: title || undefined, density, statement: Array.isArray(first) && first[0] === "p" ? (first.slice(2) as TreeNode[]) : drawn, note: draw(note) });
      continue;
    }

    const parts: SheetPart[] = [];
    let from = 0;
    const text = (markdownText: string) => {
      const nodes = draw(markdownText);
      if (nodes.length) parts.push({ type: "text", nodes });
    };
    for (const block of rest.matchAll(BLOCK)) {
      text(rest.slice(from, block.index));
      from = block.index + block[0].length;
      if (block[1] === "card_grid") {
        const points = [...block[2].matchAll(inside("card"))].map(([, card]) => {
          const { heading: name = "", rest: says } = take(card.trim(), 3);
          return { name, body: draw(says) };
        });
        const across = points.length === 2 || points.length === 4 ? 2 : points.length === 5 ? 5 : undefined;
        parts.push({ type: "points", across, points });
      } else {
        const [first = [], second = []] = [...block[2].matchAll(inside("column"))].map(([, column]) => draw(column));
        parts.push({ type: "split", sides: [first, second] });
      }
    }
    text(rest.slice(from));

    // Who speaks: the words at the wider side, the portrait at the other.
    if (said.layout === "bio" && parts.length === 1 && parts[0].type === "text") {
      const nodes = parts[0].nodes;
      const portrait = nodes.findIndex((node) => Array.isArray(node) && node[0] === "picture");
      if (portrait >= 0) parts.splice(0, 1, { type: "split", wide: "start", sides: [nodes.filter((_, index) => index !== portrait), [nodes[portrait]]] });
    }
    sheets.push({ kind: "slide", id, title, density, parts });
  }
  return sheets;
}
