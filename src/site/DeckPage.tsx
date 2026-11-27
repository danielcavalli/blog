// A deck's page: the talk's slides, one at a time. The deck says what each slide is (its layout, its words, which
// slides sit on the dark); the design system lays it out (<Slide layout>): one grid on a 1920 × 1080 sheet, seven sizes,
// the weights that tell a level's parts apart, the serif for titles only, paint only at the doors. Nothing here sets a
// size, a colour or a place: this file reads each slide's Markdown into the system's parts.
//
// The deck is the post's head: its cover is the page's first heading, and no post head stands above it. Its controls
// are the system's (the talk's name; back, where you are and the outline, on, the whole screen). On a phone a slide is
// a portrait sheet of one height.

import type { ReactNode } from "react";

import { Deck, Slide, SlideAgenda, SlideByline, SlideColumn, SlideColumns, SlideSpeaker, SlideSplit, SlideTakeaway, Wash, type SlideLayout } from "@mare-rio/design-system/react";

import type { DeckSlide, Layout, SlidePart } from "../reef/deck";
import type { TreeNode } from "../reef/tree";
import { Tree } from "../reef/Tree";
import type { DeckModel } from "./models";
import { WORDS } from "./words";

/** the layouts the deck sets on the dark: held by the moon, whatever the reader's light */
const DARK = new Set<Layout>(["divider", "dark_content"]);
/** what a slide shows as evidence: a line after it is what the slide closes on */
const BLOCKS = new Set(["data-table", "code-block", "blockquote"]);

const tagOf = (node: TreeNode) => (Array.isArray(node) ? node[0] : undefined);
const childrenOf = (node: TreeNode) => (Array.isArray(node) ? (node.slice(2) as TreeNode[]) : []);
const propertiesOf = (node: TreeNode) => (Array.isArray(node) ? (node[1] ?? {}) : {});
const textOf = (node: TreeNode): string => (typeof node === "string" ? node : childrenOf(node).map(textOf).join(""));
/** a paragraph that holds only a line break's worth of nothing is not a paragraph */
const blank = (node: TreeNode) => (typeof node === "string" || tagOf(node) === "p") && textOf(node).trim() === "";
const inline = (node: TreeNode): ReactNode => <Tree nodes={childrenOf(node).filter((child) => tagOf(child) !== "br")} />;

/** what a slide's Markdown says, sorted into the parts a slide has: its title, the line under it, its body, and what
 *  it closes on (a line after the evidence) */
interface Said {
  title: TreeNode | undefined;
  lead: TreeNode | undefined;
  /** what stands in the body, in order: text nodes and the deck format's blocks */
  body: SlidePart[];
  /** a line after the last block: what to take away */
  closing: TreeNode[];
}

function read(slide: DeckSlide): Said {
  const parts: SlidePart[] = slide.parts.map((part) => (part.type === "text" ? { ...part, nodes: part.nodes.filter((node) => !blank(node)) } : part));
  let title: TreeNode | undefined;
  let lead: TreeNode | undefined;
  const body: SlidePart[] = [];
  parts.forEach((part, index) => {
    if (part.type !== "text") return void body.push(part);
    let nodes = part.nodes;
    if (index === 0) {
      if (tagOf(nodes[0]) === "h1") [title, ...nodes] = nodes;
      // the line under the title: a `##`, or else the first paragraph when the slide goes on after it
      if (tagOf(nodes[0]) === "h2") [lead, ...nodes] = nodes;
      else if (tagOf(nodes[0]) === "p" && (nodes.length > 1 || parts.length > 1)) [lead, ...nodes] = nodes;
    }
    if (nodes.length) body.push({ type: "text", nodes });
  });
  // what follows the last block (a table, code, columns, a quote) is what the slide closes on
  const closing: TreeNode[] = [];
  const isBlock = (node: TreeNode) => BLOCKS.has(String(tagOf(node)));
  const last = body[body.length - 1];
  if (last?.type === "text") {
    let i = last.nodes.length - 1;
    while (i >= 0 && tagOf(last.nodes[i]) === "p") i--;
    const afterBlock = last.nodes.slice(0, i + 1).some(isBlock) || (i === -1 && body.length > 1);
    if (afterBlock && i < last.nodes.length - 1) {
      closing.push(...last.nodes.slice(i + 1));
      last.nodes = last.nodes.slice(0, i + 1);
      if (!last.nodes.length) body.pop();
    }
  }
  return { title, lead, body, closing };
}

/** cards: a name over its text; a name written "1. One session" carries its number apart */
function cardOf(given: TreeNode[], key: number) {
  const nodes = given.filter((node) => !blank(node));
  const named = tagOf(nodes[0]) === "h3" ? nodes[0] : undefined;
  const rest = named ? nodes.slice(1) : nodes;
  const written = named ? textOf(named).trim() : "";
  const numbered = /^(\d+)\.\s+(.*)$/.exec(written);
  return (
    <SlideColumn key={key} n={numbered ? numbered[1] : undefined} name={numbered ? numbered[2] : named ? inline(named) : ""}>
      <Tree nodes={rest} />
    </SlideColumn>
  );
}

/** what stands in a slide's body: cards as columns on shared rows (two blocks of two cards are one grid of four), two
 *  columns that each open on a name as columns too, other columns as two sides, and text as it is */
function Body({ parts }: { parts: SlidePart[] }) {
  const out: ReactNode[] = [];
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    if (part.type === "cards") {
      const cards = [...part.cards];
      const across = part.cards.length;
      while (parts[i + 1]?.type === "cards") cards.push(...(parts[++i] as { type: "cards"; cards: TreeNode[][] }).cards);
      out.push(
        <SlideColumns key={i} across={Math.min(4, Math.max(2, across)) as 2 | 3 | 4}>
          {cards.map((card, index) => cardOf(card, index))}
        </SlideColumns>,
      );
    } else if (part.type === "columns") {
      const named = part.columns.every((column) => tagOf(column.filter((node) => !blank(node))[0]) === "h3" && !column.some((node) => ["data-table", "code-block"].includes(String(tagOf(node)))));
      out.push(
        named ? (
          <SlideColumns key={i} across={Math.min(4, Math.max(2, part.columns.length)) as 2 | 3 | 4}>
            {part.columns.map((column, index) => cardOf(column, index))}
          </SlideColumns>
        ) : (
          <SlideSplit key={i}>
            {part.columns.map((column, index) => (
              <div key={index}>
                <Tree nodes={column} />
              </div>
            ))}
          </SlideSplit>
        ),
      );
    } else out.push(<Tree key={i} nodes={part.nodes} />);
  }
  return <>{out}</>;
}

/** who speaks (the name, the role, a few lines, the portrait) and the talk's parts (the table of sections) */
function Bio({ said }: { said: Said }) {
  const nodes = said.body.flatMap((part) => (part.type === "text" ? part.nodes : []));
  const table = nodes.find((node) => tagOf(node) === "data-table");
  const picture = nodes.find((node) => tagOf(node) === "picture") ?? nodes.flatMap((node) => childrenOf(node)).find((node) => tagOf(node) === "picture");
  const lines = nodes.filter((node) => tagOf(node) === "p" && !childrenOf(node).some((child) => tagOf(child) === "picture"));
  const role = said.lead ?? lines.shift();
  let parts: { name: ReactNode; claim?: ReactNode }[] = [];
  if (table) {
    const properties = propertiesOf(table);
    const columns = JSON.parse(String(properties.columns)) as { key: string; label: string }[];
    const rows = JSON.parse(String(properties.rows)) as Record<string, TreeNode[]>[];
    // (a column of numbers is the list's own count: the parts are the section and its claim)
    const words = columns.filter((column) => !rows.every((row) => /^\s*\d+\s*$/.test((row[column.key] ?? []).map(textOf).join(""))));
    parts = rows.map((row) => ({ name: <Tree nodes={row[words[0]?.key] ?? []} />, claim: words[1] ? <Tree nodes={row[words[1].key] ?? []} /> : undefined }));
  }
  const portrait = picture ? largest(propertiesOf(picture)) : undefined;
  return (
    <>
      <SlideSpeaker portrait={portrait} alt={picture ? String(propertiesOf(picture).alt ?? "") : undefined} name={said.title ? inline(said.title) : ""} role={role ? inline(role) : undefined}>
        {lines.length ? <Tree nodes={lines} /> : null}
      </SlideSpeaker>
      {parts.length ? <SlideAgenda parts={parts} /> : null}
    </>
  );
}

/** a picture's largest width (a 4K screen draws the portrait at twice its sheet's size): the widest of its set */
function largest(properties: Record<string, unknown>): string {
  const set = String(properties.daySrcset ?? "");
  const widest = set
    .split(",")
    .map((entry) => entry.trim().split(/\s+/))
    .filter(([url, width]) => url && width?.endsWith("w"))
    .sort((a, b) => Number.parseInt(b[1], 10) - Number.parseInt(a[1], 10))[0];
  return widest?.[0] ?? String(properties.src ?? "");
}

/** the system's layout for what the deck format calls a slide */
function layoutOf(slide: DeckSlide, index: number, total: number): SlideLayout {
  switch (slide.layout) {
    case "lead":
      return index === 0 ? "title" : index === total - 1 ? "close" : "section";
    case "divider":
      return "section";
    case "bio":
      return "bio";
    case "emphasis":
    case "quote":
      return "statement";
    case "card_grid":
      return "columns";
    case "split":
      return slide.parts.some((part) => part.type === "columns") ? "split" : "content";
    case "table":
      return "table";
    case "code":
      return "code";
    case "dark_content":
      return slide.parts.some((part) => part.type === "cards") ? "columns" : "content";
    default:
      return "content";
  }
}

/** A deck's body: the deck itself, the post's head (the page, the bar and the foot are the site's root's). */
export function DeckBody({ deck }: { deck: DeckModel }) {
  const { lang } = deck;
  const words = WORDS[lang];
  const total = deck.slides.length;
  // each slide's part (the divider before it) and each divider's place among the parts
  const parts: string[] = [];
  const partOf: string[] = [];
  for (const slide of deck.slides) {
    if (slide.layout === "divider") parts.push(slide.title);
    partOf.push(slide.layout === "lead" ? "" : parts[parts.length - 1] ?? "");
  }
  return (
    <Deck label={deck.title} words={words.deck} narrow="sheet">
      {deck.slides.map((slide, index) => {
        const layout = layoutOf(slide, index, total);
        const said = read(slide);
        const dark = DARK.has(slide.layout);
        const door = layout === "title" || layout === "close" || layout === "section";
        const part = partOf[index];
        const kicker = slide.layout === "divider" ? words.part(parts.indexOf(slide.title) + 1, parts.length) : undefined;
        const ground = layout === "title" || layout === "close" ? <Wash recipe="slideGround" /> : undefined;
        const lines = said.body.flatMap((p) => (p.type === "text" ? p.nodes : []));
        return (
          <Slide
            key={slide.id}
            id={slide.id}
            label={slide.title}
            part={part || undefined}
            layout={layout}
            density={slide.density === "normal" ? undefined : "dense"}
            level={index === 0 ? 1 : 2}
            kicker={kicker}
            title={layout === "bio" ? undefined : said.title ? inline(said.title) : slide.title}
            lead={layout === "bio" ? undefined : said.lead ? inline(said.lead) : undefined}
            box={dark ? "folha" : undefined}
            light={dark ? "night" : undefined}
            ground={ground}
          >
            {layout === "bio" ? (
              <Bio said={said} />
            ) : door ? (
              lines.map((node, i) => <SlideByline key={i}>{inline(node)}</SlideByline>)
            ) : (
              <>
                <Body parts={said.body} />
                {said.closing.map((node, i) => (
                  <SlideTakeaway key={i}>{inline(node)}</SlideTakeaway>
                ))}
              </>
            )}
          </Slide>
        );
      })}
    </Deck>
  );
}
