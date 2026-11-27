# dan.rio

Daniel Cavalli's blog: posts in English and Portuguese, published as a static site.

This branch (`revamp/mare-reef`) is the blog being rebuilt: on the Maré Design System, written and
reviewed in Reef, translated through the Maré Hub, hosted on Cloudflare. The content has moved to its
new shape and the new site builds every post's page in both languages; the rest of the site (index,
landing, About, CV, slides, feeds) and the translation tool are not here yet. The old Python engine
under `_source/` no longer builds on this branch. The published site still comes from `main`.

## The site

```sh
NODE_AUTH_TOKEN=$(gh auth token) npm install   # the design system is a private package
npm run build                                  # the static site, into dist/
npm run dev                                    # the site as you edit, at localhost:4321
npm run check                                  # types
```

Each page is rendered at build time through the Maré Design System's own components
(`@mare-rio/design-system`, pinned to 1.0.0), as its reference of dan.rio lays them out; no React
reaches the browser. `src/content/documents.ts` reads the Markdown files, `src/reef/render.tsx` draws
a document's body with the design system's parts (a footnote becomes a note in the margin), and
`src/site/` holds the pages.

Known gaps in what is built so far: the notes in the margin are not yet placed beside their
passages, the language switch and the light toggle do nothing, there is no paint behind a post's
head, and pictures are missing. The first three wait for work in the design system; the pictures for
each post's assets to move beside it.

## Where things are

Every Markdown file here is plain [reef-spec](https://github.com/mare-rio/reef) Markdown: `reef .` from
the repository's root shows all of it.

| Path | What it holds |
| --- | --- |
| `posts/<slug>.md` | A post, in the language it was written in (`lang` in its front matter). |
| `posts/<slug>.<locale>.md` | Its translation (`pt-br` or `en-us`). |
| `pages/about.md`, `pages/about.pt-br.md` | The About page and its translation. |
| `cv_data.yaml`, `cv_data.pt-br.yaml` | The CV and its translation. |
| `tools/git/` | The filter that keeps Reef conversations out of git. |
| `tools/migrate/` | The one-off script that moved translations out of the old engine's store. |

A translation's front matter says what it translates (`translation_of`), which model wrote it
(`translated_by`) and which text it was made from (`source_digest`). When the source's title, excerpt,
tags or body change, the digest no longer matches and the translation is stale.
`tools/migrate/export_translations.py` defines the digest.

A link from one post to another is a link to the file beside it, `[as I said](other-post.md)`, and in
a translation to that post in the same language, `other-post.pt-br.md`.

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

## Checks

```sh
npm test                         # the filter's tests
reef check posts/<file>.md       # a document's footnotes, links and figures
```

## Licence

The code is under the [MIT licence](LICENSE). The writing (everything under `posts/` and `pages/`,
and the CV) is under [Creative Commons Attribution 4.0 International](LICENSE-CONTENT): share it and
adapt it, with credit to Daniel Cavalli and a link to the original.
