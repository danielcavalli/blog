// A deck: a document written as slides, read here into the slides the deck page lays out. Server only.
//
// A deck is Markdown like any post, with each slide between two comments:
//
//     <!-- presentation:slide id="foundation" layout="divider" density="normal" -->
//     # The Foundation
//     ## Continuity is an illusion you engineer, not something the model gives you
//     <!-- /presentation:slide -->
//
// The slide is read as it is written, in order: its Markdown drawn as the site draws any text (a fenced block is
// the design system's Code, a quote its Quote, a table its Table, a picture standing alone a figure), and the two
// blocks the deck format adds kept as blocks: `<!-- presentation:block type="card_grid" -->` holds cards (each a
// `<!-- presentation:card -->`), `type="split"` two columns (each a `<!-- presentation:column -->`). Nothing is
// re-arranged: `layout` and `density` are the slide's own words, and how each layout is laid out is the deck page's
// (DeckPage.tsx), as the deck was first laid out.

import { renderDocument, type RenderOptions } from "./render";
import type { TreeNode } from "./tree";

/** what a slide is, in the deck format's own words */
export type Layout = "lead" | "divider" | "bio" | "content" | "dark_content" | "emphasis" | "split" | "card_grid" | "table" | "code" | "image" | "paragraph" | "quote" | "list";
/** how much a slide says */
export type Density = "normal" | "dense" | "very_dense";

export type SlidePart =
  | { type: "text"; nodes: TreeNode[] }
  | { type: "cards"; cards: TreeNode[][] }
  | { type: "columns"; columns: TreeNode[][] };

export interface DeckSlide {
  id: string;
  layout: Layout;
  density: Density;
  /** its first heading, for those who listen */
  title: string;
  parts: SlidePart[];
}

const SLIDE = /<!-- presentation:slide ([^>]*?)-->([\s\S]*?)<!-- \/presentation:slide -->/g;
const BLOCK = /<!-- presentation:block(?: type="([a-z_]+)")? -->([\s\S]*?)<!-- \/presentation:block -->/g;
const inside = (name: string) => new RegExp(`<!-- presentation:${name} -->([\\s\\S]*?)<!-- \\/presentation:${name} -->`, "g");
const LAYOUTS = new Set<Layout>(["lead", "divider", "bio", "content", "dark_content", "emphasis", "split", "card_grid", "table", "code", "image", "paragraph", "quote", "list"]);
const DENSITIES = new Set<Density>(["normal", "dense", "very_dense"]);

export function readDeck(markdown: string, options: RenderOptions = {}): DeckSlide[] {
  const draw = (text: string) => (text.trim() ? renderDocument(text, options).body : []);
  const slides: DeckSlide[] = [];
  for (const [, given, content] of markdown.matchAll(SLIDE)) {
    const said = Object.fromEntries([...given.matchAll(/([a-z_]+)="([^"]*)"/g)].map(([, key, value]) => [key, value]));
    const layout = LAYOUTS.has(said.layout as Layout) ? (said.layout as Layout) : "content";
    const density = DENSITIES.has(said.density as Density) ? (said.density as Density) : "normal";
    const title = /^# +(.+)$/m.exec(content)?.[1].trim() ?? said.id ?? "";
    const parts: SlidePart[] = [];
    let from = 0;
    const text = (markdownText: string) => {
      const nodes = draw(markdownText);
      if (nodes.length) parts.push({ type: "text", nodes });
    };
    for (const block of content.matchAll(BLOCK)) {
      text(content.slice(from, block.index));
      from = block.index + block[0].length;
      if (block[1] === "card_grid") parts.push({ type: "cards", cards: [...block[2].matchAll(inside("card"))].map(([, card]) => draw(card)) });
      else if (block[1] === "split") parts.push({ type: "columns", columns: [...block[2].matchAll(inside("column"))].map(([, column]) => draw(column)) });
      else text(block[2]);
    }
    text(content.slice(from));
    slides.push({ id: said.id ?? `slide-${slides.length + 1}`, layout, density, title, parts });
  }
  return slides;
}
