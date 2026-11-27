// A deck's page: a talk shown a sheet at a time at a desk, read through on a phone, in the design
// system's deck. Its doors are painted (the cover's wet strokes over the living mark, a chapter on a
// head's ground); every other sheet is paper, ink and type.

import { Chapter, Cover, Deck, Page, Point, Points, Slide, Split, Statement } from "@mare-rio/design-system/react";

import type { Sheet, SheetPart } from "../reef/deck";
import { Tree } from "../reef/Tree";
import { Bar, SiteFoot } from "./chrome";
import type { DeckModel } from "./models";
import { WORDS } from "./words";

function Part({ part }: { part: SheetPart }) {
  if (part.type === "points") {
    return (
      <Points across={part.across}>
        {part.points.map((point) => (
          <Point key={point.name} name={point.name}>
            <Tree nodes={point.body} />
          </Point>
        ))}
      </Points>
    );
  }
  if (part.type === "split") {
    return (
      <Split wide={part.wide}>
        <>
          <Tree nodes={part.sides[0]} />
        </>
        <>
          <Tree nodes={part.sides[1]} />
        </>
      </Split>
    );
  }
  return <Tree nodes={part.nodes} />;
}

function sheetOf(sheet: Sheet) {
  switch (sheet.kind) {
    case "cover":
      return <Cover key={sheet.id} id={sheet.id} words={sheet.words} voice={sheet.voice} by={sheet.by} />;
    case "chapter":
      return <Chapter key={sheet.id} id={sheet.id} name={sheet.name} claim={sheet.claim} />;
    case "statement":
      return (
        <Statement key={sheet.id} id={sheet.id} title={sheet.title} density={sheet.density} note={sheet.note.length ? <Tree nodes={sheet.note} /> : undefined}>
          <Tree nodes={sheet.statement} />
        </Statement>
      );
    case "slide":
      return (
        <Slide key={sheet.id} id={sheet.id} title={sheet.title} density={sheet.density}>
          {sheet.parts.map((part, index) => (
            <Part key={index} part={part} />
          ))}
        </Slide>
      );
  }
}

export function DeckPage({ deck }: { deck: DeckModel }) {
  const { lang } = deck;
  return (
    <Page variant="reading">
      <Bar lang={lang} at="blog" alternates={deck.alternates} />
      <Deck label={deck.title} foot={`${deck.title.toLowerCase()} · dan.rio`} words={WORDS[lang].deck}>
        {deck.sheets.map(sheetOf)}
      </Deck>
      <SiteFoot lang={lang} />
    </Page>
  );
}
