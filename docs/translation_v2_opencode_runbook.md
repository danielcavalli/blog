# Translation and build operations

| Field | Value |
| --- | --- |
| Author(s) | Daniel Cavalli |
| Date | 2026-09-05 |

Strict builds localize uncached documents with an unattended agent, then render
and validate the site. Non-strict builds use the source and available current
translations without calling an agent.

## Routine work

```bash
dan blog status
dan blog build --strict
dan blog serve
# Or preview without waiting for localization:
dan blog build --no-strict
```

Artifact selectors are post slugs, source filenames, `about`, or `cv`. With no
selectors, `dan blog translate` processes missing/outdated artifacts and pending revision
requests. It reuses all other accepted translations.

Use `dan blog --help` for discovery and `dan --clean meta describe blog` for the
agent contract. Every command accepts `--path`; `DAN_BLOG_ROOT` selects a checkout
from any directory. DanCLI delegates to this repository through `uv --locked`.
The native entrypoints remain available without DanCLI: `translations.py`
provides `status`, `update`, `diff`, and `accept`; `build.py` accepts `--strict`
and `--no-strict`. DanCLI defaults to strict mode. The agent needs no interactive
approval and receives localization instructions, not repository collaboration rules.
Human progress shows titles, language direction, elapsed time, and current/updated
counts. Use `--verbose` for model diagnostics; clean JSON remains on stdout alone.

The source freshness check includes body, title, excerpt, tags, locales, and
artifact type. A model/prompt/style change does not invalidate accepted content.
Deleting generated HTML or `_cache/` does not require translating accepted content.
Strict builds generate missing or outdated content before writing generated pages.
Non-strict builds omit unavailable translations, remove their alternate-language
metadata, and resolve links to available source pages. Damaged accepted JSON still
fails explicitly in either mode.

Use [source post paths](../README.md#link-to-another-post) for links between posts.
The renderer resolves them to the reader's language using frontmatter slugs.
Translation preserves the literal destinations, including section fragments;
the complete proposed site is checked for missing pages and headings.

## Model upgrades and revisions

The source is already authored. Translation reads the composition, prose, and
voice references linked from the [publishing overview](../README.md#write-the-source)
as context, while the V2 locale references guide PT-BR and EN-US expression.
It preserves the source's argument and effect; it does not edit the source or
apply an authoring checklist to reorganize the localized article. Missing or
empty authoring guidance stops generation. Rendering accepted content does not
load that guidance or initialize a model runner.

The PT-BR brief permits native grammatical subjects, sentence boundaries, and
punctuation while preserving meaning, qualification, and voice. Semicolons should
earn their place in Brazilian prose rather than mirror the English source.
The agent checks its text against the supplied guidance and returns the completed
document. Separate source-analysis, terminology-proposal, critique, revision, and
final-scoring calls have been removed from production. Deterministic checks
protect source structure, code, links, and parenthetical asides; one repair is
allowed when those checks find damage. These checks do not prove native prose.
The [build-mode decision](adr/018-unattended-localization.md) records this workflow.

The localization agent defaults to `openai/gpt-5.6-sol` with high reasoning.
Set `TRANSLATION_V2_TRANSLATION_MODEL` to select the agent model for builds.
OpenCode retains configured
provider authentication, while each model invocation uses a dedicated tool-free
agent in a temporary directory. Source and editorial instructions are supplied
in the prompt. See [OpenCode runtime configuration](https://opencode.ai/docs/config/).

Use an isolated candidate store to try a different model or revised policy:

```bash
dan blog translate <post-slug> --refresh \
  --model openai/gpt-5.6-sol --candidate-dir _cache/candidates/sol
dan blog diff <post-slug> --candidate-dir _cache/candidates/sol
dan blog accept <post-slug> --candidate-dir _cache/candidates/sol
dan blog build
```

A candidate may be revised repeatedly. Acceptance requires its current source to
match and its history to descend from the current accepted revision. A concurrent
accepted edit causes a conflict instead of being overwritten. Select the artifacts
you intend to promote; candidate stores may contain unchanged baseline copies.

For directed correction, add a revision request to `_source/translation_revision.yaml`:

```yaml
posts:
  some-post:
    pt-br:
      reason: correct terminology
      notes: Explain the particular correction here.
```

Run `dan blog translate some-post`. The notes reach the localization agent.
The accepted revision records the satisfied marker. Use a changed request or
`--refresh` to reassess again. Source-current content is reused by builds; an
explicit revision request is applied by the translate command.

## Persistence and recovery

There is no post-metadata manifest. Parsing reads publication dates and other
editorial metadata from frontmatter without writing derived state beside it.

- `_source/translations/<type>/<slug>/<locale>/current.json` selects acceptance.
- `revisions/<digest>.json` preserves immutable source, translation, and provenance.
- `_cache/translation-stages/` holds disposable successful stage checkpoints.
- `_cache/translation-runs/<run_id>/` holds prompts, responses, attempts, and events.
- `_cache/publication.json` and `publication-backup/` recover interrupted publishing.

A completed agent response remains reusable if a later write fails. Repeat the command.
Checkpoint reuse requires matching effective prompts, model, reasoning, and
contracts. Deterministic artifact failures get one bounded localization repair
before the update fails. Accepted content is unchanged on failure.
Malformed model responses get one schema-correction attempt. Mermaid flowchart
labels and accessibility text may be localized; graph structure, configuration,
embedded markup, links, and footnote identifiers remain protected.

The stage timeout defaults to 900 seconds and can be set with
`TRANSLATION_STAGE_TIMEOUT_SECONDS`. Interruption terminates the model process
group on Unix. Run IDs include a random suffix. Stage events record duration,
completion, checkpoint resumption, or failure.

Translation subprocesses default to a 65,536-token output allowance, including
reasoning. Override it with `OPENCODE_EXPERIMENTAL_OUTPUT_TOKEN_MAX`; OpenCode
also caps it at the model's output limit. A response cut off at that limit is
rejected even if its partial JSON parses. Increase the allowance before retrying;
repeating the same capped request does not receive automatic retries.

If accepted JSON is damaged, restore it from Git or its preserved history. Do not
delete accepted content as if it were cache. Corrupt historical cache and revision
instructions produce explicit errors rather than silently becoming empty state.

For old checkouts, import accepted cache entries with:

```bash
uv run python _source/translations.py import-cache
```

Only source-verifiable entries are imported. Previous source text may be recovered
from run artifacts, but those translations remain outdated until revised. The old
cache is preserved and existing accepted content is never overwritten by import.

## Focused rendering

```bash
dan blog build --post <post-slug>
```

This changes the selected bilingual post and preserves other posts, indexes,
sitemap, and all four About/CV pages. Both strict and non-strict builds stage their
outputs. HTML and internal links are checked against the complete proposed site,
including untouched pages in a focused build. No files are promoted on validation
failure. Publication errors restore every touched file; crashes recover on the next
build under the build lock.

## Verification

```bash
uv run --extra dev pytest tests/ -q
uv run --extra dev ruff check .
uv run --extra dev pyright _source
dan blog build
dan blog check
```

With `dan blog serve` running, check the reading behavior and the current sources:

```bash
node tests/browser/reading-layout.mjs
node tests/browser/mare-article.mjs
node tests/browser/source-corpus.mjs
```

Set `BLOG_URL` for a preview other than `http://127.0.0.1:8000`, and
`PLAYWRIGHT_MODULE` or `PLAYWRIGHT_CHROMIUM` for local browser installations.
The corpus check renders `_source/posts/` in the browser through request
interception, so unpublished source edits can be reviewed without changing
generated pages or invoking translation.

CI rebuilds from committed, current translations without installing OpenCode;
missing or outdated translations make a strict CI build fail until localized and
committed. Frozen
fixtures test regressions; live candidate comparisons provide separate evidence
about model behavior and editorial quality. Publication to GitHub Pages still
happens through the normal generated-output commit and push.
