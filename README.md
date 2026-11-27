# dan.rio

Daniel Cavalli's blog: posts in English and Portuguese, published as a static site in the
[Maré Design System](https://github.com/mare-rio/mare-design-system).

A post is one Markdown file. It is written and reviewed in Reef, translated through the Maré Hub, and
built into pages that are the design system's own components: painted, alive in the browser, and
complete without it.

## Writing

Every Markdown file here is plain reef-spec Markdown. `reef .` from the repository's root shows all
of it.

| Path | What it holds |
| --- | --- |
| `posts/<slug>.md` | A post, in the language it was written in (`lang` in its front matter). |
| `posts/<slug>.<locale>.md` | Its translation (`pt-br` or `en-us`). |
| `posts/<slug>.assets/` | The post's pictures and files. |
| `pages/about.md`, `pages/about.pt-br.md` | The About page and its translation. |
| `cv_data.yaml`, `cv_data.pt-br.yaml` | The CV and its translation. |
| `decks/` | Slide decks not yet published. |
| `drafts/` | Posts not yet published. |

A post's front matter:

```markdown
---
title: A thought worth following
slug: a-thought-worth-following
date: 2026-09-05
lang: en-us
excerpt: What the reader will understand.
tags: [engineering]
---
```

What the site does with what you write:

- **A footnote is a note in the margin.** `[^label]` in the text and `[^label]: its words` at the end
  of the body: the note stands beside the line that calls it, and under the text on a phone.
- **A picture** is `![what it shows](<slug>.assets/hub-day.jpg "its caption")`, alone on its line. The
  same picture under another light is the file beside it with that light's name in place of `day`
  (`hub-night.jpg`, `hub-dusk.jpg`): the site shows the one for the reader's light.
- **A link to another post** is a link to the file beside it, `[as I said](other-post.md)`, and in a
  translation to that post in the same language (`other-post.pt-br.md`). The site sends the reader to
  that post's page in their language.
- **A callout** (`> [!note] Title`), **a table**, **a fenced block of code** and **a quote** are each
  drawn by the design system's part for it.
- **Headings** (`##`, `###`) are the page's contents, beside the text. A translation's headings keep
  the ids of the text it translates, so a link to a section holds in both languages.

`reef check posts/<file>.md` checks a document's footnotes, links and figures.

## The site

```sh
NODE_AUTH_TOKEN=$(gh auth token) npm install   # the design system is a private package
npm run dev                                    # the site as you write, at localhost:4321
npm run build                                  # the static site, into dist/
node tools/serve.mjs                           # dist/, served as the host serves it
npm run check                                  # types
npm test                                       # the tools' tests
```

Each page is built ahead of time from the Markdown and laid out with the Maré Design System's React
parts (`@mare-rio/design-system`, pinned), in the Folha box, as the design system's own reference of
dan.rio lays them out (`art/reference/proving/apps/blog.tsx` there). The same parts then run in the
browser: that is where the kit lays the paint, the wordmark lives, the light turns as the earth turns,
and a note finds its line. A reader without JavaScript gets the whole text.

| Path | What it does |
| --- | --- |
| `src/content/documents.ts` | Reads posts and translations from the Markdown files. |
| `src/reef/` | Reads a document's body into a tree at build time, and draws that tree with the design system's parts, on the server and again in the browser. |
| `src/site/` | The pages (landing, index, post, About and CV, not found), their words in each language, and what search engines and other programs read. |
| `src/pages/` | The addresses. |
| `src/layouts/Site.astro` | Every page's document: stylesheet, fonts, the light, metadata. |
| `astro.config.mjs` | The build, and the redirects from the old site's addresses. |

Nothing here styles anything: no stylesheet of the site's own, no colour, no hand-made transition.
What the design system lacks is added to the design system, released, and used from there.

Checks against the design system:

```sh
npx mare-conformance src                                        # the source: no colour literals, no spinners
node tools/serve.mjs 4321 &
npx mare-render-check http://127.0.0.1:4321/en/ --register shore
npx mare-render-check http://127.0.0.1:4321/en/blog/ --register reading
node tools/shots.mjs /tmp/shots /en/ /en/blog/                  # pictures under each light, desk and phone
```

## Addresses, search engines and other programs

- `/en/` and `/pt/` are the landing; `/en/blog/` the index; `/en/blog/<slug>` a post; `/en/about` and
  `/en/cv` the pages. `/` is the English landing and takes a Portuguese-speaking browser to `/pt/`.
- Every page names its own address, the same page in the other language, and what it is
  (schema.org). `/sitemap.xml` lists them all.
- Every address of the site before this one (`.html` pages, `/static/` pictures) answers with a
  permanent redirect to where the thing is now (`_redirects`, written by the build).
- `/en/feed.xml` and `/pt/feed.xml` are Atom feeds with every post whole.
- Every post is also served as Markdown: add `.md` to its address. `/llms.txt` lists them.
- The index searches every post's text in the reader's language, in the browser.

## Publishing

The site is static files on Cloudflare (a Worker that serves `dist/` and runs nothing per request;
`cloudflare.config.ts`). Publishing is one command from a machine that is signed in to Cloudflare:

```sh
cf auth login      # once per machine
npm run deploy     # builds, then uploads dist/
```

`node tools/serve.mjs` serves `dist/` locally the way Cloudflare does. Cloudflare's own simulator
confirmed the rest: every old address answers 301 to its new one, a missing address answers 404
with the site's page.

### Moving dan.rio from GitHub Pages (once)

Until this is done, dan.rio is still GitHub Pages serving `main`, and the pull request that holds
this rebuild must not be merged: `main` would stop having pages to serve.

1. `npm run deploy`. The site is then at `https://dan-rio.<account>.workers.dev`: look at it there.
2. In Cloudflare's DNS for dan.rio, delete the four `A` records of the apex (185.199.108-111.153,
   GitHub Pages) and the `www` CNAME (`danielcavalli.github.io`).
3. Add `domains: ["dan.rio", "www.dan.rio"]` under `worker` in `cloudflare.config.ts` and run
   `npm run deploy` again: Cloudflare gives the Worker both names and their certificates.
4. Check `https://dan.rio/en/` and an old address such as
   `https://dan.rio/en/blog/dont-outsource-the-thinking.html` (it must answer 301).
5. Merge the pull request, then turn GitHub Pages off in the repository's settings.

To go back before step 5: remove `domains`, deploy, and put the four `A` records and the `www`
CNAME back (proxied). Nothing on `main` has changed until the merge.

## Reef conversations stay on your machine

Reef keeps the conversation about a document (margin comments and their replies) at the end of its
file. This repository is public and those conversations are not, so a git filter takes them out of
everything git stores and puts them back in the working files. The document's marker (its identity
and revision number) is not conversation and is stored.

```sh
npm install                      # installs the filter (it runs tools/git/setup.mjs)
npm run conversations:check      # fails if anything git stores holds a conversation
npm run conversations:refresh    # settles files whose conversation alone changed
```

Two things to know, both from how git works:

- After you or an agent comment in the margin, `git status` lists the file as modified while
  `git diff` shows nothing. `git add` it, or run the refresh: nothing is staged. Until then git
  refuses a checkout, merge or pull that would rewrite that file.
- `git restore`, `git checkout -- <file>` and `git reset --hard` put back the conversation as it was
  last kept (at the last `git add` or `git diff` of that file).

The conversations are kept in `.git/reef-conversations/`, on this machine only.
`tools/git/conversations.mjs` has the details.

## Translations

A translation's front matter says what it translates (`translation_of`), which model wrote it
(`translated_by`) and which text it was made from (`source_digest`). When the source's title, excerpt,
tags or body change, the digest no longer matches and the translation is stale.

## Licence

The code is under the [MIT licence](LICENSE). The writing (everything under `posts/`, `pages/`,
`decks/` and `drafts/`, and the CV) is under
[Creative Commons Attribution 4.0 International](LICENSE-CONTENT): share it and adapt it, with credit
to Daniel Cavalli and a link to the original.
