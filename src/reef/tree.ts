// A document's body as data: what the server reads out of the Markdown and what the browser draws
// again with the same components, so the page a reader is sent and the page that comes alive in the
// browser are the same tree.
//
// A node is a run of text, or `[tag, properties, ...children]`. Most tags are HTML's. A few are the
// document's own, drawn by a part of the design system (Tree.tsx): `note-call`, `code-block`,
// `callout`, `data-table`, `picture`.

export type TreeNode = string | [tag: string, properties: Record<string, unknown> | null, ...children: TreeNode[]];

export interface Heading {
  id: string;
  label: string;
  /** 1 for a section, 2 for a section inside one. */
  level: 1 | 2;
}

export interface Note {
  n: number;
  body: TreeNode[];
}

export interface Rendered {
  body: TreeNode[];
  headings: Heading[];
  notes: Note[];
}
