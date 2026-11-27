// A document's tree (tree.ts), drawn with the Maré Design System's parts. The server draws it into
// the page that is sent; the browser draws it again from the same data, and the parts come alive.

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
    default:
      return createElement(tag, { ...properties, key }, ...(inside ? [inside] : []));
  }
}

interface PictureProps {
  src: string;
  alt: string;
  caption?: string;
  dusk?: string;
  night?: string;
}

/** A picture, as itself, with its caption. Where it was made under more than one light, the one for the reader's. */
function Picture({ src, alt, caption, dusk, night }: PictureProps) {
  const [light, setLight] = useState<"day" | "dusk" | "night">("day");
  useEffect(() => {
    if (!dusk && !night) return;
    setLight(theme().light);
    return onTheme((now) => setLight(now.light));
  }, [dusk, night]);
  const shown = (light === "night" && night) || (light === "dusk" && dusk) || src;
  return (
    <figure>
      <img src={shown} alt={alt} loading="lazy" decoding="async" />
      {caption ? <figcaption>{caption}</figcaption> : null}
    </figure>
  );
}
