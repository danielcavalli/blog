// A reef-spec document's body, drawn with the design system's own parts.
//
// The body is Markdown as Reef reads it: GitHub's, with footnotes. It becomes a tree of React
// elements built from the Maré Design System's components (Code, Quote, NoteCall, MarginNote), so
// the markup a reader gets is the design system's own. A footnote is not printed at the foot of the
// text: its call becomes a note call, and its words a note for the margin, beside the passage.

import type { Element, ElementContent, Root, RootContent } from "hast";
import { toJsxRuntime } from "hast-util-to-jsx-runtime";
import type { ReactNode } from "react";
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import rehypeRaw from "rehype-raw";
import remarkGfm from "remark-gfm";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import { unified } from "unified";

import { Code, NoteCall, Quote } from "@mare-rio/design-system/react";

export interface Heading {
  id: string;
  label: string;
  /** 1 for a section, 2 for a section inside one. */
  level: 1 | 2;
}

export interface Note {
  n: number;
  body: ReactNode;
}

export interface Rendered {
  body: ReactNode;
  headings: Heading[];
  notes: Note[];
}

export interface RenderOptions {
  /** Where a link written in the document leads on the site. */
  link?: (href: string) => string;
  /** The ids its headings take, in order: a translation keeps its source's, so a link to a section holds in both. */
  headingIds?: readonly string[];
}

const reader = unified().use(remarkParse).use(remarkGfm).use(remarkRehype, { allowDangerousHtml: true }).use(rehypeRaw);

const isElement = (node: unknown, tag?: string): node is Element =>
  typeof node === "object" && node !== null && (node as Element).type === "element" && (!tag || (node as Element).tagName === tag);

function textOf(node: Root | RootContent): string {
  if (node.type === "text") return node.value;
  return "children" in node ? (node.children as RootContent[]).map(textOf).join("") : "";
}

export function slugOf(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/** Every element of the tree, with the parent that holds it. Children are visited after replacing. */
function visit(parent: Root | Element, each: (node: Element, index: number, parent: Root | Element) => void): void {
  for (let index = 0; index < parent.children.length; index++) {
    const node = parent.children[index];
    if (!isElement(node)) continue;
    each(node, index, parent);
    const now = parent.children[index];
    if (isElement(now)) visit(now, each);
  }
}

function toReact(nodes: ElementContent[], components: Record<string, unknown>): ReactNode {
  return toJsxRuntime({ type: "root", children: nodes }, { Fragment, jsx, jsxs, components: components as never });
}

export function renderDocument(markdown: string, options: RenderOptions = {}): Rendered {
  const tree = reader.runSync(reader.parse(markdown)) as Root;
  const headings: Heading[] = [];
  const taken = new Set<string>();
  let footnotes: Element | undefined;

  visit(tree, (node, index, parent) => {
    // The list of footnotes Markdown puts at the end: taken out, to become the margin's notes.
    if (node.tagName === "section" && "dataFootnotes" in node.properties) {
      footnotes = node;
      parent.children.splice(index, 1, { type: "text", value: "" });
      return;
    }
    // A footnote's call.
    const call = node.tagName === "sup" && node.children.find((child) => isElement(child, "a") && "dataFootnoteRef" in child.properties);
    if (call) {
      parent.children[index] = { type: "element", tagName: "note-call", properties: { n: textOf(call as Element) }, children: [] };
      return;
    }
    if (node.tagName === "h2" || node.tagName === "h3") {
      const label = textOf(node).trim();
      let id = options.headingIds?.[headings.length] ?? slugOf(label);
      for (let again = 2; taken.has(id); again++) id = `${slugOf(label)}-${again}`;
      taken.add(id);
      node.properties.id = id;
      headings.push({ id, label, level: node.tagName === "h2" ? 1 : 2 });
      return;
    }
    // A fenced block: the design system's code part, which colours it.
    if (node.tagName === "pre") {
      const code = node.children.find((child) => isElement(child, "code")) as Element | undefined;
      if (code) {
        const classes = (code.properties.className as string[] | undefined) ?? [];
        const lang = classes.find((name) => name.startsWith("language-"))?.slice("language-".length);
        parent.children[index] = { type: "element", tagName: "code-block", properties: { lang, text: textOf(code).replace(/\n$/, "") }, children: [] };
      }
      return;
    }
    if (node.tagName === "a" && typeof node.properties.href === "string" && options.link) {
      node.properties.href = options.link(node.properties.href);
    }
  });

  const components = {
    "note-call": ({ n }: { n: string }) => <NoteCall n={n} />,
    "code-block": ({ lang, text }: { lang?: string; text: string }) => <Code lang={lang}>{text}</Code>,
    blockquote: ({ children }: { children: ReactNode }) => <Quote>{children}</Quote>,
  };

  const notes: Note[] = [];
  const list = footnotes?.children.find((child) => isElement(child, "ol")) as Element | undefined;
  for (const item of list?.children.filter((child): child is Element => isElement(child, "li")) ?? []) {
    // Without the arrow back to the text: the note stands beside its passage.
    visit(item, (node, index, parent) => {
      if (node.tagName === "a" && "dataFootnoteBackref" in node.properties) parent.children.splice(index, 1, { type: "text", value: "" });
    });
    const blocks = item.children.filter((child) => isElement(child));
    const words = blocks.length === 1 && isElement(blocks[0], "p") ? (blocks[0] as Element).children : item.children;
    notes.push({ n: notes.length + 1, body: toReact(words, components) });
  }

  return { body: toReact(tree.children as ElementContent[], components), headings, notes };
}
