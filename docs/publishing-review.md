# Publishing engine review

| Field | Value |
| --- | --- |
| Author(s) | Daniel Cavalli |
| Date | 2026-09-06 |
| Scope | Authoring guidance, localization boundaries, build, and source compatibility |

## September 6: simplification and source links

The explicit translation command now has one generation path, through the existing
V2 editorial stages and validated acceptance. The unused cache-backed orchestrator,
cache adapter, deferred persistence callbacks, forwarding modules, eager exports,
and post-metadata manifest are removed. Tests of those retired paths have been
replaced with real accepted-record, historical-import, and command recovery checks.
Roughly 2,200 net lines were removed across implementation and tests in this pass.

The quality stages, locale references, accepted history, candidate review, stage
checkpoints, and publication recovery remain. They address writing quality, durable
content, expensive retries, and partial publication respectively. Normal builds
remain independent of model configuration and execution caches.

Source Markdown paths now work as link destinations in articles, sidenotes, and
presentations. Rendering uses the target's frontmatter slug and the reader's
language, preserving query strings and section fragments. There is no registry,
cache, source rewrite, or translation rewrite. Missing posts and heading fragments
fail publication. See the [authoring examples](../README.md#link-to-another-post).

Verification for this pass:

- All 331 Python tests pass. Ruff and Pyright for production modules and the new
  source-link/build tests pass.
- A strict build of the 13-post accepted-source baseline produces the same 34
  HTML/XML files byte-for-byte, starting without caches. Neither the retired
  post-metadata manifest nor a translation cache is recreated.
- All 14 working source posts pass browser layout checks at 1500, 390, and 320
  pixels, including the newly authored Maré Rio post and its source-path links.
- The Maré posts' source links navigate in both directions at desktop and mobile
  widths, with JavaScript enabled or disabled, using directly rendered sources.
- Real bilingual build tests resolve source links through frontmatter slugs and
  stable source heading IDs in both languages. Full and focused builds preserve
  source/accepted bytes; missing post and heading tests preserve the previous site.
- Command-level tests exercise late-stage failure, checkpoint recovery, acceptance,
  and reuse after cache deletion or model changes without invoking a live model.

This pass does not edit authored posts or accepted translation records. Concurrent
editorial work changed the Maré agent post and added the Maré Rio article. At the
last full build check, the former's PT-BR translation was outdated and the latter's
was missing. `dan blog build` reported both before rendering and left all published
files unchanged. The remaining publication step is to localize those finished
sources and rebuild; no model calls or remote publication were made in this pass.

## September 5 review

The following records the earlier review and its source/publication snapshot.

The renderer handled all 13 source posts, including the presentation,
rich notes, tables, code, and themed figures. Source files and accepted translation
records remain byte-for-byte unchanged from the start of this review.

## What changed

Builds read accepted records directly and render each post and collection once.
They no longer initialize model runners, load writing policy, write translation
cache entries, or offer a direct-write path around staged validation. The unused
Gemini implementation, its two direct dependencies and 24 transitive packages,
the optional directory-check module, and redundant CI execution were removed.
Tests that simulated the retired build-time cache workflow were replaced with
tests of real accepted records and publication failures.

Composition, prose, and author voice now use one guidance loader. The duplicate
voice loader and silent generic fallback are gone. Every localization stage
receives the source-authority boundary; the existing V2 stage graph and locale
references remain responsible for natural PT-BR and EN-US expression. The
[publishing overview](../README.md) connects writing, notes, localization, and
the DanCLI workflow. Technical-document footer guidance is explicitly separate
from the blog's sidenotes.

Legacy numeric citations now use Markdown's parser instead of rewriting raw
lines. Code spans, fenced and indented examples, escaped brackets, and link
destinations survive unchanged. Heading anchors also use the parsed hierarchy,
including underline-style headings. Empty reference-section cleanup only applies
where notes actually moved. Translated HTML filtering operates on elements and
attributes, preserving prose and code examples containing HTML syntax.

## What remains necessary

Accepted revisions, candidate comparison and acceptance, source freshness checks,
stage checkpoints, and publication recovery solve distinct failure modes. They
remain. The editorial and locale references retain separate responsibilities;
they are not collapsed into a generic writing prompt. Historical articles about
earlier blog implementations remain authored historical material, while the
overview and operations guide own current commands.

## Source compatibility

Each source was rendered directly from `_source/posts/` and checked at 1500,
390, and 320 pixels. All checks passed: valid HTML, unique IDs, resolvable local
fragments, preserved code, complete heading outlines, and no page overflow.
Mobile citations opened their notes. The presentation retained its own renderer.

| Source file | Article headings | Sidenotes |
| --- | ---: | ---: |
| `a-network-setup-that-works-for-me.md` | 5 | 0 |
| `adding-an-agent-to-a-mare-app.md` | 6 | 2 |
| `ai-agents-and-the-ilusion-of-continuity.md` | 4 | 7 |
| `building-a-bilingual-blog.md` | 9 | 0 |
| `choosing-the-right-gpu-for-ai-learning.md` | 16 | 0 |
| `css-animations-guide.md` | 16 | 0 |
| `dont-outsource-the-thinking.md` | 3 | 0 |
| `how-i-use-ai-agents.md` | Presentation | — |
| `how-translation-system-v2-works.md` | 19 | 0 |
| `intent-harness-and-the-grammar-of-revisable-work.md` | 4 | 6 |
| `modern-web-development.md` | 5 | 0 |
| `semiconductors-and-sovereignty.md` | 5 | 32 |
| `the-living-static-system.md` | 10 | 0 |

The semiconductor source was only read. Its bilingual preview was rebuilt through
DanCLI, with its citations presented as notes and no empty Sources section.

## Verification and publication state

All 314 Python tests pass, as do Ruff and Pyright for production modules and the
new build/localization tests. Repository-wide Pyright still reports the same
152 pre-existing diagnostics in older test fixtures; this is not a claim that
the entire test tree passes static typing.

The [reading-layout](../tests/browser/reading-layout.mjs),
[article-media](../tests/browser/mare-article.mjs), and
[source-corpus](../tests/browser/source-corpus.mjs) browser checks pass. They cover
desktop and mobile notes, collisions, nested headings, keyboard use, deep links,
language changes, navigation, themes, printing, and JavaScript/CDN fallbacks.

A complete strict build passed in an isolated copy using the source revisions
stored with acceptance. In the working tree, the Maré and Intent posts have newer
source edits than their accepted PT-BR translations. A full build and `dan blog
check` correctly refuse those stale records; the failed build left every generated
page unchanged. The generated HTML and internal-link validators pass. The 11
current bilingual articles were refreshed through focused DanCLI builds. No
model calls, translation promotions, commits, or remote publication were performed
during this review.
