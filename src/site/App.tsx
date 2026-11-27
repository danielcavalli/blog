// The whole site as one thing: every page is drawn by this root, which the browser keeps from the
// first page on. Following a link to another page of the site changes the page in place, through
// the design system's turn(): the paper stays, the bar and the wordmark hold (they are the same
// elements, never drawn again), the post's title travels from its entry to the head of its page,
// and the new page is shown with its paint up. A page's value is fetched as soon as a reader shows
// they may go there (a pointer over the link, a finger on it, focus), so by the tap it is usually
// here already.
//
// The first page a reader opens is held back until the paint on screen is up (or a second has
// passed), so the page arrives with its paint instead of before it (Site.astro starts the hold).

import { useEffect, useLayoutEffect, useRef, useState } from "react";

import { Page, turn } from "@mare-rio/design-system/react";

import { Bar, SiteFoot } from "./chrome";
import { DeckBody } from "./DeckPage";
import { IndexBody } from "./IndexPage";
import { LandingPage } from "./LandingPage";
import { MissingBody } from "./NotFoundPage";
import { dataPath, ROUTE, type PageModel } from "./pages";
import { PlainBody } from "./PlainPage";
import { PostBody } from "./PostPage";

// ---------- the pages' values, fetched once ----------

const loaded = new Map<string, Promise<PageModel>>();

function load(path: string): Promise<PageModel> {
  const url = dataPath(path);
  let value = loaded.get(url);
  if (!value) {
    value = fetch(url).then((answer) => {
      if (!answer.ok) throw new Error(`${url} answered ${answer.status}`);
      return answer.json() as Promise<PageModel>;
    });
    value.catch(() => loaded.delete(url));
    loaded.set(url, value);
  }
  return value;
}

/** Where an anchor leads, when that is a page of the site this root changes to in place. */
function inPlace(anchor: HTMLAnchorElement): URL | null {
  if ((anchor.target && anchor.target !== "_self") || anchor.hasAttribute("download")) return null;
  const url = new URL(anchor.href, window.location.href);
  return url.origin === window.location.origin && ROUTE.test(url.pathname) ? url : null;
}

const anchorOf = (target: EventTarget | null) => (target instanceof Element ? target.closest<HTMLAnchorElement>("a[href]") : null);

/** A reader on a slow or metered connection is not sent pages they have not asked for. */
const sparing = () => {
  const connection = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } }).connection;
  return !!connection?.saveData || /(^|-)2g$/.test(connection?.effectiveType ?? "");
};

// ---------- the first arrival ----------

/** At most this long after the page was asked for, the page is shown whether its paint is up or not. */
const ARRIVAL = 1000;
/** How long a page change is marked: the design system's wait for the new page's paint (a quarter of
 *  a second at most) and its crossing of the two pages, with room to spare. */
const TURNING = 900;

function arrive(): void {
  const root = document.documentElement;
  if (!root.classList.contains("dan-arriving")) return;
  const show = () => root.classList.remove("dan-arriving");
  const onScreen = (el: Element) => {
    const box = el.getBoundingClientRect();
    return box.bottom > 0 && box.top < window.innerHeight && box.width > 0 && box.height > 0;
  };
  const washes = [...document.querySelectorAll(".mare-wash")].filter(onScreen);
  const painted = new Promise<void>((resolve) => {
    const done = () => washes.every((wash) => wash.hasAttribute("data-painted"));
    if (done()) return resolve();
    const watch = new MutationObserver(() => {
      if (done()) {
        watch.disconnect();
        resolve();
      }
    });
    for (const wash of washes) watch.observe(wash, { attributes: true, attributeFilter: ["data-painted"] });
  });
  const fonts = document.fonts?.ready ?? Promise.resolve();
  const late = new Promise<void>((resolve) => setTimeout(resolve, Math.max(0, ARRIVAL - performance.now())));
  void Promise.race([Promise.all([painted, fonts]), late]).then(show);
}

// ---------- the root ----------

export function App({ initial }: { initial: PageModel }) {
  const [model, setModel] = useState(initial);
  const shown = useRef(model);
  shown.current = model;
  /** Where the page that is coming opens: a place in it, or how far down. */
  const opening = useRef<{ hash: string; scroll: number } | null>(null);

  useEffect(arrive, []);

  // The page for an address that is not there speaks the language of the address asked for.
  useEffect(() => {
    if (model.kind === "missing" && window.location.pathname.startsWith("/pt")) setModel({ ...model, meta: { ...model.meta, lang: "pt" } });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if ("scrollRestoration" in history) history.scrollRestoration = "manual";
    history.replaceState({ ...(history.state ?? {}), scroll: window.scrollY }, "");
    let latest = 0;
    let settling = 0;

    const go = async (url: URL, push: boolean, scroll = 0) => {
      const ticket = ++latest;
      let next: PageModel;
      try {
        next = await load(url.pathname);
      } catch {
        window.location.assign(url.href);
        return;
      }
      if (ticket !== latest) return;
      if (push) {
        history.replaceState({ ...(history.state ?? {}), scroll: window.scrollY }, "");
        history.pushState({ scroll: 0 }, "", url.pathname + url.search + url.hash);
      }
      opening.current = { hash: url.hash, scroll };
      // While the page changes, the new page's paint is whole as soon as it is laid (site.css): the
      // change is taken with it, not with a stroke still fading in.
      const root = document.documentElement;
      root.classList.add("dan-turning");
      window.clearTimeout(settling);
      settling = window.setTimeout(() => root.classList.remove("dan-turning"), TURNING);
      turn(() => setModel(next));
    };

    const onClick = (event: MouseEvent) => {
      if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
      const anchor = anchorOf(event.target);
      const url = anchor && inPlace(anchor);
      if (!url) return;
      if (url.pathname === window.location.pathname) {
        // A place on this page is the browser's to go to; this page itself is its top.
        if (url.hash) return;
        event.preventDefault();
        window.scrollTo({ top: 0, behavior: "smooth" });
        return;
      }
      event.preventDefault();
      void go(url, true);
    };

    const onPop = (event: PopStateEvent) => {
      const url = new URL(window.location.href);
      if (url.pathname === shown.current.meta.path) return;
      if (!ROUTE.test(url.pathname)) {
        window.location.reload();
        return;
      }
      void go(url, false, typeof event.state?.scroll === "number" ? event.state.scroll : 0);
    };

    const onIntent = (event: Event) => {
      const anchor = anchorOf(event.target);
      const url = anchor && inPlace(anchor);
      if (url && url.pathname !== window.location.pathname) void load(url.pathname);
    };

    document.addEventListener("click", onClick);
    window.addEventListener("popstate", onPop);
    const intents = ["pointerover", "touchstart", "focusin"] as const;
    for (const type of intents) document.addEventListener(type, onIntent, { passive: true });
    return () => {
      document.removeEventListener("click", onClick);
      window.removeEventListener("popstate", onPop);
      for (const type of intents) document.removeEventListener(type, onIntent);
    };
  }, []);

  // A page changed in place: what the browser and those who listen are told, and where it opens.
  useLayoutEffect(() => {
    const at = opening.current;
    if (!at) return;
    opening.current = null;
    const { meta } = model;
    document.title = meta.title;
    document.documentElement.lang = meta.lang === "pt" ? "pt-BR" : "en";
    document.querySelector('meta[name="description"]')?.setAttribute("content", meta.description);
    document.querySelector('link[rel="canonical"]')?.setAttribute("href", new URL(meta.canonical, window.location.origin).href);
    const place = at.hash ? document.getElementById(decodeURIComponent(at.hash.slice(1))) : null;
    if (place) place.scrollIntoView();
    else window.scrollTo(0, at.scroll);
    const heading = document.querySelector<HTMLElement>("main h1");
    if (heading) {
      heading.tabIndex = -1;
      heading.focus({ preventScroll: true });
    }
  }, [model]);

  // When the reader is idle, the pages the screen leads to are fetched ahead.
  useEffect(() => {
    if (sparing()) return;
    const idle = (window as Window & { requestIdleCallback?: (run: () => void, o?: { timeout: number }) => number }).requestIdleCallback;
    const ahead = () => {
      const seen = new Set<string>();
      for (const anchor of document.querySelectorAll<HTMLAnchorElement>("main a[href]")) {
        const url = inPlace(anchor);
        const box = anchor.getBoundingClientRect();
        if (!url || url.pathname === window.location.pathname || box.top > window.innerHeight * 1.5 || box.bottom < 0) continue;
        seen.add(url.pathname);
        if (seen.size >= 8) break;
      }
      for (const path of seen) void load(path);
    };
    const timer = idle ? idle(ahead, { timeout: 3000 }) : window.setTimeout(ahead, 1500);
    return () => {
      if (!idle) window.clearTimeout(timer);
    };
  }, [model]);

  if (model.kind === "landing") return <LandingPage landing={model.landing} />;
  const at = model.kind === "plain" ? model.page.which : model.kind === "missing" ? undefined : "blog";
  return (
    <Page variant="reading">
      <Bar lang={model.meta.lang} at={at} alternates={model.meta.alternates} />
      <Body key={model.meta.path} model={model} />
      <SiteFoot lang={model.meta.lang} />
    </Page>
  );
}

function Body({ model }: { model: Exclude<PageModel, { kind: "landing" }> }) {
  switch (model.kind) {
    case "index":
      return <IndexBody index={model.index} />;
    case "post":
      return <PostBody post={model.post} />;
    case "deck":
      return <DeckBody deck={model.deck} />;
    case "plain":
      return <PlainBody page={model.page} />;
    case "missing":
      return <MissingBody lang={model.meta.lang} />;
  }
}
