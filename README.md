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

dan.rio is static files on Cloudflare: a Worker named `dan-rio` that serves `dist/` and runs nothing
per request (`cloudflare.config.ts`), with `dan.rio` as its custom domain. Publishing is one command
from a machine that is signed in to Cloudflare:

```sh
cf auth login      # once per machine
npm run deploy     # builds, then uploads dist/
```

`node tools/serve.mjs` serves `dist/` locally the way Cloudflare does.

How the domain is set up, for whoever has to change it:

- `dan.rio` is the Worker's custom domain; Cloudflare keeps its DNS records and certificate.
- `www.dan.rio` is sent to `dan.rio` with a permanent redirect by a redirect rule on the zone (its
  `CNAME` record only keeps the name resolving through Cloudflare).
- Every address of the site before this one answers 301 to where the thing is now (`_redirects`,
  written by the build).
- The site was on GitHub Pages until 2026-11-27. To go back, remove `domains` from
  `cloudflare.config.ts` and deploy, restore the apex's four `A` records (185.199.108.153 to
  185.199.111.153, proxied), and turn GitHub Pages on for a commit from before the rebuild.

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

A translation is the file beside its source. Its front matter says what it translates
(`translation_of`), which model wrote it (`translated_by`) and which text it was made from
(`source_digest`). When the source's title, excerpt, tags or body change, the digest no longer
matches and the translation is stale. You read a translation in Reef like any other document, and a
comment in its margin is how you ask for it to be revised.

Translating a document is the localization process the old engine ran, as decision 017 left it,
now through the Maré Hub, which this machine reaches over the tailnet with no credential. Each step
is one model call with its own prompt:

1. **Source analysis**: the author's voice, tone, rhythm, rhetorical moves and what must survive.
2. **Terminology policy**: which terms stay in English, which are localized, and how ambiguous ones
   are settled for the whole document.
3. **Translate**: the draft, written with the analysis and the policy.
4. Up to **two passes** of:
   - **Critique**: a second model's findings, each grounded in the source or a human guidance rule.
   - **Revise**: a full localization pass over the whole text, after every critique; the critic
     cannot skip it by saying nothing needs refinement. The writer keeps wording that already meets
     the source and the guidance, and may decline a finding it judges mistaken: its report says, for
     every finding, applied (with the edit) or declined (with why).
   - **Final review**: the second model reads only the source, the text and the human guidance. It
     accepts only when it says accept and publish-ready and lists no residual issue. Each issue must
     quote the passage at fault and name the source claim or guidance rule it violates, or the review
     is sent back. Its scores are recorded and decide nothing.

   The document is done at the first final review that accepts it. A rejected review's issues go to
   the next pass's critique and revision (not to its final review). If the second pass still rejects
   it, nothing is written and the reviewer's residual issues are printed.

The analysis and the policy are proposals: they never override the human guidance, and the names
the policy would protect are not added to the guidance's list. The translation model analyses,
drafts and revises; the critic model critiques and reviews. A post takes 6 to 9 calls. The CV has
its own prompt for every step, and a presentation its own translate and revise.

```sh
npm run translate -- status                        # where every translation stands; fails unless all are current
npm run translate -- posts/<slug>.md               # translate it if its translation is missing or stale
npm run translate -- --all                         # the same, for every post, page and the CV
npm run translate -- revise posts/<slug>.pt-br.md  # revise a translation by the open comments in its margin
npm run translate -- stamp posts/<slug>.md         # you changed both by hand the same way: record that they agree
```

`--force` translates a current document again. `--model` and `--effort` choose the translation
model (default `gpt-5.6-sol` at `high`), `--critic-model` and `--critic-effort` the critic and final
reviewer (default `claude-opus-5-5` at `medium`).
`--dry-run` calls nothing and writes nothing, and `--out <dir>` writes under another folder instead
of the repository, for trials. Each document prints a line per step with its tokens and cost (the
Hub reports no cost for a model it serves from a subscription), the critique's and the final
review's verdicts and scores, and how many passes it took.

- **What every step said** is kept for you to read in `.translate-runs/<run>/<document>/`, which
  git ignores: each step's answer as JSON (the analysis, the policy, every critique, every revision
  with its report, and every final review with its scores and residual issues), the messages it was
  sent, and a
  `summary.json`. None of it goes into a published file.
- **The checks** compare every draft and revision with the source: footnotes, fenced code, link
  destinations (a link to another post must point to that post in the translation's language),
  picture paths, parenthetical asides, a presentation's slide markers, About's paragraphs, the CV's
  entries and contact details, and that the text was translated at all. Every answer must also have
  its step's shape. After a failed check the model is asked once more with the exact findings; if
  that fails too, nothing is written.
- **A translation's reef trailer is never rewritten.** Translating a document again replaces its
  body and keeps the conversation at its end byte for byte.
- **`revise`** is for a translation you reviewed in Reef. It runs the same process with your open
  comments as the owner's instructions: the analysis and the policy, then a revise step that applies
  your comments to the translation as it stands, then the critique, revise and final review passes.
  Every step sees your comments. If the text is accepted, it is written and each comment the
  revision acted on goes from `open` to `addressed`; a comment it did not act on (a question, say)
  stays open, with the reason printed.
- **The guidance** the models are given is Markdown: the locale briefs, rules and glossaries in
  `tools/translate/guides/`, each step's prompt around them in `tools/translate/prompts/`, and the
  writing references under `.agents/skills/`. Edit those to change how translations read.

## Licence

The code is under the [MIT licence](LICENSE). The writing (everything under `posts/`, `pages/`,
`decks/` and `drafts/`, and the CV) is under
[Creative Commons Attribution 4.0 International](LICENSE-CONTENT): share it and adapt it, with credit
to Daniel Cavalli and a link to the original.
