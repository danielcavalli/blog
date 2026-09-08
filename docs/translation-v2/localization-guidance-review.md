# Localization authority verification

Reviewed on 2026-09-07 against the [human-guidance authority decision](../adr/017-localization-guidance-authority.md).

**Subsequent owner review rejected the translation quality.** The experiments below
establish specific control-flow and preservation behavior, not that the translation
system produces acceptable Brazilian prose. The later run
`build-v2-20260907204714-0a137e32db98` took 25 minutes and its final reviewer approved
an aside rewritten from parentheses into commas. Neither the earlier tests nor the
reviewer's confidence established the requested quality.

## The reported failure

The frozen fixture `tests/fixtures/translation_v2/pt_br_guidance_regression.json`
contains ten paragraphs from the source and rejected PT-BR translation of Maré
Rio. It remains independent of subsequent edits to that article.

For the live regression, source analysis and terminology were controlled test
inputs. The terminology proposal claimed authority over the human guidance and
contradictorily demanded replacing `app` while marking it protected. The critique
gave the draft 100 and said to preserve all wording and punctuation, with
`needs_refinement: false`. Revision and final review used the configured models.

The required localization pass ran anyway. It explicitly declined both the
preserve-everything advice and the generated terminology requirement. It kept
the conventional borrowing `app` consistently and reconstructed the reported
calque:

> Ele pode justificar o esforço por ser útil para mim, mesmo que ninguém mais quisesse usá-lo.

became:

> Se ele for útil para mim, o trabalho de criá-lo pode valer a pena, mesmo que ninguém mais queira usá-lo.

The writer also reworked connective movement across the paragraphs. Five copied
semicolons became two, with sentence restructuring rather than automatic character
replacement. The remaining punctuation was assessed in context; the count is not
a production rule. Both recorded rejected calques disappeared, the ten paragraphs
and protected link survived, and strict artifact validation passed.

Continuous editorial reading checked the personal value argument, distinction
between coding agents and runtime agents, platform/app responsibilities, intended
possibilities, and closing humor. The localized example is retained in the fixture
as evidence and test input, not a mandatory wording template.

Local run artifacts: `_cache/translation-runs/guidance-authority-regression-20260907/`.

## Full article and publishing path

A separate live `dan blog translate` trial localized the full source version
captured by `build-v2-20260907181725-9b0ccab59d55`. The article was reviewed against
that captured source, including its headings, future-project list, image captions,
technical responsibilities, and source-path link. The final review received no
earlier model analysis, terminology proposal, critique, or revision report.

The source continued changing during the run. The candidate therefore remains
isolated in `_cache/candidates/guidance-authority-20260907`, rather than being
promoted against a different source version.

To verify publication mechanics, a separate checkout used the captured source
and candidate. `dan blog accept`, strict `dan blog build`, and `dan blog check`
passed there: thirteen posts, valid HTML, and no broken internal links. The
unpublished Intent Harness post was excluded. The working repository's source
posts, accepted translations, and published files were not overwritten.

## Automated regression coverage

The test suite checks that a favorable critique cannot skip localization, model
proposals cannot enter the human protection list, final review does not consult
earlier verdicts, and a positive final verdict cannot override residual issues.
Cache recovery, accepted-content reuse, and source/code/link protection remain
covered. All 334 tests, Ruff, and production Pyright passed.
