// A post as other programs read it: its text as plain words (for the site's search), as HTML (for
// the feed), and as Markdown with addresses that work from anywhere (for agents). Server only.

import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";

import { postOfFile, postUrl, type Document, type Post } from "../content/documents";
import { Tree } from "../reef/Tree";
import type { TreeNode } from "../reef/tree";
import { postModel } from "./models";
import { absolute } from "./seo";
import type { Lang } from "./words";

export const pathOf = (post: Post, lang: Lang) => postUrl(post, lang);

/** The words of a tree, as a reader would read them aloud. */
export function wordsOf(nodes: readonly TreeNode[]): string {
  const out: string[] = [];
  const walk = (node: TreeNode) => {
    if (typeof node === "string") return void out.push(node);
    const [tag, properties, ...children] = node;
    if (tag === "code-block") out.push(String(properties?.text ?? ""));
    if (tag === "picture") out.push(String(properties?.alt ?? ""), String(properties?.caption ?? ""));
    if (tag === "diagram") return;
    if (tag === "data-table") for (const row of JSON.parse(String(properties?.rows ?? "[]")) as Record<string, TreeNode[]>[]) Object.values(row).forEach((cell) => cell.forEach(walk));
    children.forEach(walk);
    if (/^(p|h[1-6]|li|blockquote|callout|figure|tr)$/.test(tag)) out.push("\n");
  };
  nodes.forEach(walk);
  return out.join("").replace(/[ \t]+/g, " ").replace(/\n\s+/g, "\n").trim();
}

/** A post's body as HTML, with every address made whole: for a feed reader, which shows it elsewhere. */
export function htmlOf(post: Post, lang: Lang): string {
  const model = postModel(post, lang);
  const notes = model.notes.length
    ? `<hr><ol>${model.notes.map((note) => `<li id="mare-note-${note.n}">${renderToStaticMarkup(createElement(Tree, { nodes: note.body }))}</li>`).join("")}</ol>`
    : "";
  return (renderToStaticMarkup(createElement(Tree, { nodes: model.body })) + notes).replace(/\b(href|src)="\/(?!\/)/g, `$1="${absolute("/")}`);
}

/** A post as Markdown for a program to read: what it is in a few lines of front matter, then its text. */
export function markdownOf(post: Post, lang: Lang): string {
  const document: Document = post.in[lang]!;
  const link = (to: string): string => {
    const media = /^(?:\.\/)?([^/]+)\.assets\/(.+)$/.exec(to);
    if (media) return absolute(`/media/${media[1]}/${media[2]}`);
    const file = /^(?:\.\/)?([^/#?]+\.md)(#.*)?$/.exec(to);
    const other = file && postOfFile(file[1]);
    return other ? absolute(`${postUrl(other, other.in[lang] ? lang : other.written)}.md`) + (file[2] ?? "") : to;
  };
  // Links and pictures, inline and by reference. Fenced code is left as it is.
  const body = document.body
    .split(/(^```[\s\S]*?^```[^\n]*$)/m)
    .map((part, index) => (index % 2 ? part : part.replace(/(\]\()([^)\s]+)((?:\s+"(?:[^"\\]|\\.)*")?\))/g, (_, open, to, close) => open + link(to) + close)))
    .join("");
  const quote = (text: string) => JSON.stringify(text);
  const front = [
    `title: ${quote(document.title)}`,
    `description: ${quote(document.excerpt)}`,
    `author: Daniel Cavalli`,
    `date: ${post.date}`,
    ...(post.updated ? [`updated: ${post.updated}`] : []),
    `lang: ${lang === "pt" ? "pt-BR" : "en"}`,
    `tags: [${document.tags.map(quote).join(", ")}]`,
    `url: ${absolute(postUrl(post, lang))}`,
    ...(post.written !== lang ? [`translated_from: ${absolute(`${postUrl(post, post.written)}.md`)}`] : []),
    `license: CC BY 4.0`,
  ];
  return `---\n${front.join("\n")}\n---\n\n# ${document.title}\n\n${body}\n`;
}
