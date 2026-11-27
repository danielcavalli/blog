// A reef-spec document's body, read into a tree (tree.ts). Server only: this is where Markdown is
// parsed, at build time.
//
// The body is Markdown as Reef reads it: GitHub's, with footnotes and callouts. What the design
// system has a part for is marked for that part: a fenced block for Code, a quote for Quote, a
// callout for Note, a table for Table, a picture standing alone for a figure with its caption. A
// footnote is not printed at the foot of the text: its call becomes a note call, and its words a
// note for the margin, beside the passage.

import fs from "node:fs";
import path from "node:path";

import type { Element, ElementContent, Root, RootContent } from "hast";
import { toJsxRuntime } from "hast-util-to-jsx-runtime";
import { imageSize } from "image-size";
import { render as drawDiagram } from "pele";
import type { ReactElement, ReactNode } from "react";
import { Fragment, jsx, jsxs } from "react/jsx-runtime";
import rehypeRaw from "rehype-raw";
import remarkGfm from "remark-gfm";
import remarkParse from "remark-parse";
import remarkRehype from "remark-rehype";
import { unified } from "unified";

import type { Heading, Note, Rendered, TreeNode } from "./tree";

export interface RenderOptions {
  /** Where a link written in the document leads on the site. */
  link?: (href: string) => string;
  /** The ids its headings take, in order: a translation keeps its source's, so a link to a section holds in both. */
  headingIds?: readonly string[];
  /** The document's file, from the repository's root: what its pictures and files are beside. */
  file?: string;
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

/** Every element of the tree, with the parent that holds it. An element put in another's place is not entered. */
function visit(parent: Root | Element, each: (node: Element, index: number, parent: Root | Element) => void): void {
  for (let index = 0; index < parent.children.length; index++) {
    const node = parent.children[index];
    if (!isElement(node)) continue;
    each(node, index, parent);
    if (parent.children[index] === node) visit(node, each);
  }
}

const element = (tagName: string, properties: Element["properties"] = {}, children: ElementContent[] = []): Element => ({
  type: "element",
  tagName,
  properties,
  children,
});

// ---------- a post's own files ----------

const MEDIA = /^(?:\.\/)?([^/]+)\.assets\/(.+)$/;
const LIGHTS = ["dusk", "night"] as const;

/** `<slug>.assets/<file>`, as the site serves it. */
function mediaUrl(href: string): string | undefined {
  const match = MEDIA.exec(href);
  return match ? `/media/${match[1]}/${match[2]}` : undefined;
}

/** The same picture under another light: the file beside it with that light's name in place of `day`. */
function byLight(src: string, file: string | undefined): Partial<Record<(typeof LIGHTS)[number], string>> {
  const found: Partial<Record<(typeof LIGHTS)[number], string>> = {};
  if (!file || !/-day\.[a-z0-9]+$/i.test(src)) return found;
  for (const light of LIGHTS) {
    const other = src.replace(/-day(\.[a-z0-9]+)$/i, `-${light}$1`);
    if (fs.existsSync(path.join(process.cwd(), path.dirname(file), other))) found[light] = mediaUrl(other);
  }
  return found;
}

/** A picture's own width and height, so the page keeps its place while the picture comes. */
function sizeOf(src: string, file: string | undefined): { width?: number; height?: number } {
  if (!file || !MEDIA.test(src)) return {};
  try {
    const { width, height } = imageSize(fs.readFileSync(path.join(process.cwd(), path.dirname(file), src)));
    return { width, height };
  } catch {
    return {};
  }
}

// ---------- hast to the tree ----------

function toTree(nodes: ElementContent[]): TreeNode[] {
  const drawn = toJsxRuntime({ type: "root", children: nodes }, { Fragment, jsx, jsxs }) as ReactNode;
  return flatten(drawn);
}

function flatten(node: ReactNode): TreeNode[] {
  if (node == null || typeof node === "boolean") return [];
  if (typeof node === "string" || typeof node === "number") return [String(node)];
  if (Array.isArray(node)) return node.flatMap(flatten);
  const { type, props } = node as ReactElement<Record<string, unknown>>;
  const { children, ...rest } = props;
  if (typeof type !== "string") return flatten(children as ReactNode);
  const properties = Object.fromEntries(Object.entries(rest).filter(([, value]) => value !== undefined));
  return [[type, Object.keys(properties).length ? properties : null, ...flatten(children as ReactNode)]];
}

const FIGURES = /^[\s\d.,%+\-−–~≈<>$€£R×x/:]*\d[\s\d.,%+\-−–~≈<>$€£R×x/:a-zA-Z]{0,6}$/;

/** A Markdown table as the design system's table takes it: its columns, and each line's cells by column. */
function tableOf(table: Element): Element {
  const lines = (section: string) =>
    (table.children.find((child) => isElement(child, section)) as Element | undefined)?.children.filter((child): child is Element => isElement(child, "tr")) ?? [];
  const cellsOf = (line: Element) => line.children.filter((child): child is Element => isElement(child, "th") || isElement(child, "td"));
  const head = lines("thead")[0];
  const body = lines("tbody").map(cellsOf);
  const columns = (head ? cellsOf(head) : []).map((cell, index) => ({
    key: `c${index}`,
    label: textOf(cell).trim(),
    figures: body.length > 0 && body.every((line) => FIGURES.test(textOf(line[index] ?? element("td")).trim() || "0")),
  }));
  const rows = body.map((line) => Object.fromEntries(columns.map((column, index) => [column.key, toTree(line[index]?.children ?? [])])));
  return element("data-table", { label: columns[0]?.label ?? "table", columns: JSON.stringify(columns), rows: JSON.stringify(rows) });
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
      parent.children[index] = element("note-call", { n: textOf(call as Element) });
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
        const text = textOf(code).replace(/\n$/, "");
        // A `mermaid` block is a diagram, drawn here, once, as lines and words that take the page's ink.
        if (lang === "mermaid") {
          try {
            parent.children[index] = element("diagram", { svg: drawDiagram(text).svg });
            return;
          } catch (problem) {
            throw new Error(`${options.file ?? "a document"}: its diagram cannot be drawn: ${(problem as Error).message}`);
          }
        }
        parent.children[index] = element("code-block", { lang, text });
      }
      return;
    }
    if (node.tagName === "table") {
      parent.children[index] = tableOf(node);
      return;
    }
    // A callout: a quote whose first line is `[!kind] Title`.
    if (node.tagName === "blockquote") {
      const first = node.children.find((child) => isElement(child, "p")) as Element | undefined;
      const opening = first?.children[0];
      const mark = opening?.type === "text" ? /^\[!([a-z-]+)\][+-]?[ \t]*([^\n]*)\n?/i.exec(opening.value) : null;
      if (first && opening?.type === "text" && mark) {
        opening.value = opening.value.slice(mark[0].length);
        node.tagName = "callout";
        node.properties = { label: (mark[2] || mark[1]).trim().toLowerCase() };
      }
      return;
    }
    // A picture standing alone is a figure: itself, and its title as the caption under it.
    if (node.tagName === "p") {
      const shown = node.children.filter((child) => !(child.type === "text" && !child.value.trim()));
      const picture = shown.length === 1 && isElement(shown[0], "img") ? shown[0] : undefined;
      if (picture) {
        const src = String(picture.properties.src ?? "");
        parent.children[index] = element("picture", {
          src: mediaUrl(src) ?? src,
          alt: String(picture.properties.alt ?? ""),
          caption: picture.properties.title ? String(picture.properties.title) : undefined,
          ...sizeOf(src, options.file),
          ...byLight(src, options.file),
        });
      }
      return;
    }
    if (node.tagName === "img" && typeof node.properties.src === "string") {
      node.properties.src = mediaUrl(node.properties.src) ?? node.properties.src;
      return;
    }
    if (node.tagName === "a" && typeof node.properties.href === "string") {
      const href = node.properties.href;
      node.properties.href = mediaUrl(href) ?? options.link?.(href) ?? href;
    }
  });

  const notes: Note[] = [];
  const list = footnotes && ((footnotes as Element).children.find((child) => isElement(child, "ol")) as Element | undefined);
  for (const item of list?.children.filter((child): child is Element => isElement(child, "li")) ?? []) {
    // Without the arrow back to the text: the note stands beside its passage.
    visit(item, (node, index, parent) => {
      if (node.tagName === "a" && "dataFootnoteBackref" in node.properties) parent.children.splice(index, 1, { type: "text", value: "" });
    });
    const blocks = item.children.filter((child) => isElement(child));
    const words = blocks.length === 1 && isElement(blocks[0], "p") ? (blocks[0] as Element).children : item.children;
    notes.push({ n: notes.length + 1, body: toTree(words) });
  }

  return { body: toTree(tree.children as ElementContent[]), headings, notes };
}
