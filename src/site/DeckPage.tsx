// A deck's page: the talk's slides shown one at a time, laid out as the deck was first laid out (the old engine's
// presentation.css): the same regions in the same places and proportions, every layout as it was. What changed is the
// art, the tokens and the parts, which are the design system's: its paper and ink in the site's box under the
// reader's light, its three voices (the serif for titles and headings, the sans for every line of text, the mono for
// labels and code), a card or a column standing on its own ground of paint (<Panel>), code, quotes and tables in the
// system's own parts, and a slide the deck sets on a dark ground held by the moon. The layout is in deck.css.

import "./deck.css";

import type { CSSProperties } from "react";

import { Deck, HorizonMark, Page, Panel, Quote, Reading, ReadingHead, Slide, Wash } from "@mare-rio/design-system/react";

import type { DeckSlide, Layout, SlidePart } from "../reef/deck";
import type { TreeNode } from "../reef/tree";
import { Tree } from "../reef/Tree";
import { Bar, SiteFoot } from "./chrome";
import type { DeckModel } from "./models";
import { WORDS } from "./words";

/** the layouts the deck sets on a dark ground: held by the moon, whatever the reader's light */
const DARK = new Set<Layout>(["divider", "dark_content"]);

const tagOf = (node: TreeNode) => (Array.isArray(node) ? node[0] : undefined);
const childrenOf = (node: TreeNode) => (Array.isArray(node) ? (node.slice(2) as TreeNode[]) : []);

const textOf = (node: TreeNode): string => (typeof node === "string" ? node : Array.isArray(node) ? (node.slice(2) as TreeNode[]).map(textOf).join("") : "");

/** a table's columns share the slide's width as a table laid out by its words does: each as wide as what it holds,
 *  the room left shared in proportion to it */
function tracksOf(node: TreeNode): string {
  const properties = (Array.isArray(node) ? node[1] : undefined) ?? {};
  const columns = JSON.parse(String(properties.columns ?? "[]")) as { key: string; label: string }[];
  const rows = JSON.parse(String(properties.rows ?? "[]")) as Record<string, TreeNode[]>[];
  return columns.map((column) => `minmax(max-content, ${Math.max(column.label.length, ...rows.map((row) => (row[column.key] ?? []).map(textOf).join("").length))}fr)`).join(" ");
}

/** a slide's text, in order: a quote stands on a ground of its own, as it did */
function Text({ nodes }: { nodes: TreeNode[] }) {
  return (
    <>
      {nodes.map((node, index) =>
        tagOf(node) === "data-table" ? (
          <div key={index} className="deck-table" style={{ "--deck-table-columns": tracksOf(node) } as CSSProperties}>
            <Tree nodes={[node]} />
          </div>
        ) : tagOf(node) === "blockquote" ? (
          <Panel key={index}>
            <div className="deck-quote">
              <Quote voice="sans">
                <Tree nodes={childrenOf(node)} />
              </Quote>
            </div>
          </Panel>
        ) : (
          <Tree key={index} nodes={[node]} />
        ),
      )}
    </>
  );
}

function Part({ part }: { part: SlidePart }) {
  if (part.type === "cards") {
    return (
      <div className="deck-cards">
        {part.cards.map((card, index) => (
          <Panel key={index} accent="top">
            <article className="deck-card">
              <Text nodes={card} />
            </article>
          </Panel>
        ))}
      </div>
    );
  }
  if (part.type === "columns") {
    return (
      <div className="deck-split">
        {part.columns.map((column, index) => (
          <Panel key={index} accent="left">
            <section className="deck-column">
              <Text nodes={column} />
            </section>
          </Panel>
        ))}
      </div>
    );
  }
  return <Text nodes={part.nodes} />;
}

/** who speaks: the name, the role, a few lines and the portrait at the left; the talk's parts at the right, each on
 *  a ground of its own, its number in a fine ring */
function Bio({ nodes }: { nodes: TreeNode[] }) {
  const table = nodes.find((node) => tagOf(node) === "data-table");
  const rest = nodes.filter((node) => node !== table);
  let agenda: TreeNode[][][] = [];
  if (table && Array.isArray(table)) {
    const properties = table[1] ?? {};
    const columns = JSON.parse(String(properties.columns)) as { key: string }[];
    const rows = JSON.parse(String(properties.rows)) as Record<string, TreeNode[]>[];
    agenda = rows.map((row) => columns.map((column) => row[column.key] ?? []));
  }
  return (
    <>
      <Text nodes={rest} />
      <ol className="deck-agenda">
        {agenda.map(([n = [], section = [], claim = []], index) => (
          <li key={index}>
            <Panel>
              <div className="deck-agenda-part">
                <span className="deck-agenda-n">
                  <Tree nodes={n} />
                </span>
                <span className="deck-agenda-section">
                  <Tree nodes={section} />
                </span>
                <span className="deck-agenda-claim">
                  <Tree nodes={claim} />
                </span>
              </div>
            </Panel>
          </li>
        ))}
      </ol>
    </>
  );
}

/** the paint under a slide the deck set on a ground of its own: the cover's light ground and its sea, a dark one's */
function groundOf(layout: Layout) {
  if (layout === "lead")
    return (
      <div className="deck-ground" data-layout={layout}>
        <Wash recipe="slideGround" />
        <HorizonMark />
      </div>
    );
  if (DARK.has(layout))
    return (
      <div className="deck-ground" data-layout={layout}>
        <Wash recipe="slideGround" />
      </div>
    );
  return undefined;
}

/** one slide; `id` is its address (the deck reads it from here) */
function SlideOf({ slide, n }: { id: string; slide: DeckSlide; n: number }) {
  const dark = DARK.has(slide.layout);
  return (
    <Slide id={slide.id} label={slide.title} box={dark ? "folha" : undefined} light={dark ? "night" : undefined} ground={groundOf(slide.layout)}>
      <div className="deck-slide" data-layout={slide.layout} data-density={slide.density}>
        <div className="deck-inner">
          <div className="deck-body">
            {slide.layout === "bio" && slide.parts.length === 1 && slide.parts[0].type === "text" ? (
              <Bio nodes={slide.parts[0].nodes} />
            ) : (
              slide.parts.map((part, index) => <Part key={index} part={part} />)
            )}
          </div>
        </div>
        <span className="deck-number" aria-hidden="true">
          {n}
        </span>
        <span className="deck-site" aria-hidden="true">
          dan.rio
        </span>
      </div>
    </Slide>
  );
}

export function DeckPage({ deck }: { deck: DeckModel }) {
  const { lang } = deck;
  const words = WORDS[lang];
  return (
    <Page variant="reading">
      <Bar lang={lang} at="blog" alternates={deck.alternates} />
      <Reading>
        <ReadingHead
          back={{ label: words.post.back, href: `/${lang}/blog/` }}
          carry={`post-${deck.slug}`}
          facts={deck.facts}
          title={deck.title}
          dek={deck.dek}
          tags={deck.tags.map((tag) => ({ label: tag, href: `/${lang}/blog/` }))}
        />
      </Reading>
      <div className="deck-stage">
        <Deck label={deck.title} words={words.deck}>
          {deck.slides.map((slide, index) => (
            <SlideOf key={slide.id} id={slide.id} slide={slide} n={index + 1} />
          ))}
        </Deck>
      </div>
      <SiteFoot lang={lang} />
    </Page>
  );
}
