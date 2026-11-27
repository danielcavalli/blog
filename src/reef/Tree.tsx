// A document's tree (tree.ts), drawn with the Maré Design System's parts. The server draws it into
// the page that is sent; the browser draws it again from the same data, and the parts come alive.

import type React from "react";
import { createElement, useEffect, useState, type ReactNode } from "react";

import { Code, Note, NoteCall, Quote, Table } from "@mare-rio/design-system/react";
import { onTheme, theme } from "@mare-rio/design-system/theme";

import type { TreeNode } from "./tree";

export function Tree({ nodes }: { nodes: readonly TreeNode[] }) {
  return <>{nodes.map(draw)}</>;
}

function draw(node: TreeNode, key: number): ReactNode {
  if (typeof node === "string") return node;
  const [tag, given, ...children] = node;
  const properties = given ?? {};
  const inside = children.length ? children.map(draw) : undefined;
  switch (tag) {
    case "note-call":
      return <NoteCall key={key} n={String(properties.n)} />;
    case "code-block":
      return (
        <Code key={key} lang={properties.lang as string | undefined}>
          {String(properties.text ?? "")}
        </Code>
      );
    case "blockquote":
      return <Quote key={key}>{inside}</Quote>;
    case "callout":
      return (
        <Note key={key} label={String(properties.label ?? "note")}>
          {inside}
        </Note>
      );
    case "data-table": {
      const columns = JSON.parse(String(properties.columns)) as { key: string; label: string; figures: boolean }[];
      const rows = JSON.parse(String(properties.rows)) as Record<string, TreeNode[]>[];
      return (
        <Table
          key={key}
          label={String(properties.label)}
          columns={columns}
          rows={rows.map((row, line) => ({ key: String(line), ...Object.fromEntries(columns.map((column) => [column.key, <Tree nodes={row[column.key] ?? []} />])) }))}
        />
      );
    }
    case "picture":
      return <Picture key={key} {...(properties as unknown as PictureProps)} />;
    case "diagram":
      return (
        <figure key={key}>
          <div style={DIAGRAM} dangerouslySetInnerHTML={{ __html: String(properties.svg) }} />
        </figure>
      );
    default:
      return createElement(tag, { ...properties, key }, ...(inside ? [inside] : []));
  }
}

// A diagram is drawn at build time by the renderer Reef draws with (pele). It takes its colours and
// faces from these names: each is given the design system's token, so a diagram is lines of the
// page's ink on the page's paper under every light. No colour is written here.
const DIAGRAM = {
  "--pele-bg": "var(--paper)",
  "--pele-fg": "var(--ink)",
  "--pele-muted": "var(--ink-soft)",
  "--pele-line": "var(--ink-soft)",
  "--pele-surface": "var(--paper)",
  "--pele-surface-alt": "var(--surface)",
  "--pele-border": "var(--line)",
  "--pele-accent": "var(--sea)",
  "--pele-font": "var(--sans)",
  "--pele-font-mono": "var(--mono)",
  "--pele-radius": "0px",
} as React.CSSProperties;

interface PictureProps {
  src: string;
  alt: string;
  caption?: string;
  width?: number;
  height?: number;
  dusk?: string;
  night?: string;
  /** the same picture at the widths a screen may want, for each light */
  daySrcset?: string;
  duskSrcset?: string;
  nightSrcset?: string;
}

/** How wide a picture in the text is drawn: the screen less its margins on a phone, the measure on a desk. */
const SIZES = "(max-width: 760px) calc(100vw - 40px), 720px";

/** A picture, as itself, with its caption. Where it was made under more than one light, the one for the reader's. */
function Picture({ src, alt, caption, width, height, dusk, night, daySrcset, duskSrcset, nightSrcset }: PictureProps) {
  const [light, setLight] = useState<"day" | "dusk" | "night">("day");
  useEffect(() => {
    if (!dusk && !night) return;
    setLight(theme().light);
    return onTheme((now) => setLight(now.light));
  }, [dusk, night]);
  const shown = (light === "night" && night) || (light === "dusk" && dusk) || src;
  const offered = (light === "night" && night && nightSrcset) || (light === "dusk" && dusk && duskSrcset) || daySrcset;
  return (
    <figure>
      <img src={shown} srcSet={offered} sizes={offered ? SIZES : undefined} alt={alt} width={width} height={height} loading="lazy" decoding="async" />
      {caption ? <figcaption>{caption}</figcaption> : null}
    </figure>
  );
}
