// Every page of the site and its value (pages.ts), worked out once per build. Server only.

import { posts, postUrl, type Lang } from "../content/documents";
import { aboutModel, cvModel, deckModel, indexModel, landingModel, postModel } from "./models";
import type { PageModel } from "./pages";
import { WORDS } from "./words";

const LANGS: Lang[] = ["en", "pt"];

export interface Route {
  path: string;
  model: () => PageModel;
}

function landing(lang: Lang, path: string): PageModel {
  const landing = landingModel(lang);
  return {
    kind: "landing",
    landing,
    meta: { title: "dan.rio · Daniel Cavalli", description: WORDS[lang].description, lang, path, canonical: `/${lang}/`, alternates: landing.alternates },
  };
}

function list(): Route[] {
  const out: Route[] = [{ path: "/", model: () => landing("en", "/") }];
  for (const lang of LANGS) {
    out.push({ path: `/${lang}/`, model: () => landing(lang, `/${lang}/`) });
    out.push({
      path: `/${lang}/blog/`,
      model: () => {
        const index = indexModel(lang);
        const path = `/${lang}/blog/`;
        return { kind: "index", index, meta: { title: `${WORDS[lang].index.title} · dan.rio`, description: WORDS[lang].description, lang, path, canonical: path, alternates: index.alternates } };
      },
    });
    for (const which of ["about", "cv"] as const) {
      const path = `/${lang}/${which}`;
      out.push({
        path,
        model: () => {
          const page = which === "about" ? aboutModel(lang) : cvModel(lang);
          return { kind: "plain", page, meta: { title: `${page.title} · dan.rio`, description: page.description, lang, path, canonical: path, alternates: page.alternates } };
        },
      });
    }
  }
  for (const post of posts()) {
    for (const lang of Object.keys(post.in) as Lang[]) {
      const path = postUrl(post, lang);
      out.push({
        path,
        model: () => {
          if (post.kind === "presentation") {
            const deck = deckModel(post, lang);
            return { kind: "deck", deck, meta: { title: `${deck.title} · dan.rio`, description: deck.dek, lang, path, canonical: path, alternates: deck.alternates } };
          }
          const model = postModel(post, lang);
          return { kind: "post", post: model, meta: { title: `${model.title} · dan.rio`, description: model.dek, lang, path, canonical: path, alternates: model.alternates } };
        },
      });
    }
  }
  return out;
}

let cached: Route[] | undefined;
const made = new Map<string, PageModel>();

export function routes(): Route[] {
  return (cached ??= list());
}

/** The value of the page at an address. Each is worked out once: the page and its data share it. */
export function routeAt(path: string): PageModel {
  const known = made.get(path);
  if (known) return known;
  const route = routes().find((candidate) => candidate.path === path);
  if (!route) throw new Error(`no page at ${path}`);
  const model = route.model();
  made.set(path, model);
  return model;
}

/** The page that answers for an address that is not there. */
export function missing(): PageModel {
  return { kind: "missing", meta: { title: "Not here · dan.rio", description: WORDS.en.missing.title, lang: "en", path: "/404", canonical: "/404", alternates: { en: "/en/", pt: "/pt/" } } };
}
