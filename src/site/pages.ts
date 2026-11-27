// What a page of the site is, as one value: the server writes it into the page and into
// /data/<the page's address>.json, and the browser changes from one page to the next with it, in
// place, without loading a document.

import type { IndexModel, LandingModel, PlainModel, PostModel } from "./models";
import type { Alternates, Lang } from "./words";

export interface Meta {
  title: string;
  description: string;
  lang: Lang;
  /** The page's own address. */
  path: string;
  /** The address search engines keep (the root shows the English landing, kept as /en/). */
  canonical: string;
  /** The same page in each language it exists in. */
  alternates: Alternates;
}

export type PageModel =
  | { kind: "landing"; meta: Meta; landing: LandingModel }
  | { kind: "index"; meta: Meta; index: IndexModel }
  | { kind: "post"; meta: Meta; post: PostModel }
  | { kind: "plain"; meta: Meta; page: PlainModel }
  | { kind: "missing"; meta: Meta };

/** Where a page's value is: /data/<its address>.json; the root's is /data/index.json. */
export const dataPath = (path: string): string => `/data/${path.replace(/^\/+|\/+$/g, "") || "index"}.json`;

/** The addresses the site changes to in place: the root, a landing, the index, a post, About, the CV. */
export const ROUTE = /^\/(?:(?:en|pt)\/(?:blog\/(?:[a-z0-9-]+)?|about|cv)?)?$/;
