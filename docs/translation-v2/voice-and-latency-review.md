# Voice, parenthetical asides, and latency

Historical investigation. The owner subsequently selected a single unattended
localization agent and strict/non-strict build modes; see
[ADR 018](../adr/018-unattended-localization.md). The experiments and timings below
describe the earlier comparison, not the current runtime graph.

The owner's 2026-09-07 review identified flattened voice, literal phrasing,
parenthetical asides rewritten as comma clauses, and excessive execution time.
The earlier localization-authority experiments did not establish acceptable prose.

## Reproduced failure

Run `build-v2-20260907204714-0a137e32db98` produced the accepted Maré Rio
translation used for this investigation. Its five serial model calls took:

| Stage | Seconds |
| --- | ---: |
| Source analysis | 74 |
| Terminology proposal | 157 |
| Critique | 720 |
| Revision | 316 |
| Final review | 235 |
| Total | 1502 |

The final reviewer approved the output with no residual issues. Both source
parenthetical groups disappeared. `pt_br_voice_regression.json` freezes one of
these passages independently of ongoing edits to the post.

The pipeline treated every refresh as another revision of existing Portuguese,
which kept the weak translation in the writer's input. Prompts also allowed
punctuation replacement indiscriminately and emphasized a serious register even
when the source was irritated, enthusiastic, or ironic.

## Implemented corrections

The human briefs and shared stage instructions now explicitly preserve the
speaker's conviction, irritation, enthusiasm, humor, and rhetorical punctuation.
Parenthetical asides must enclose the same thought in parentheses. A usable
extended metaphor should survive rather than becoming a generic technical noun.

New translation generation and candidate acceptance compare prose parenthesis
structure independently of model verdicts. Markdown links, code, HTML attributes,
and image paths are excluded; nested parentheses and translated contents are
supported. A failure cannot replace an accepted revision. Existing accepted
content remains readable and buildable without new model calls.

This structural check cannot establish that the same meaning remains inside each
aside, or that the text sounds Brazilian. Those are editorial requirements, not
claims made by a delimiter counter.

## Controlled timing comparison

The experiments use the source snapshot from the failed run, the existing full
human writing and locale guides, and the same translator and reviewer models.
They generate directly from source and review independently, without generated
source analysis, terminology proposals, or a separate critique. One uses the
current high reasoning setting; another measures medium reasoning.

Artifacts are under `_cache/translation-runs/voice-speed-direct-20260907/` and
`_cache/translation-runs/voice-speed-medium-20260907/`. These experiments do not
replace accepted content. At the time of these trials, the shorter graph had not
yet been selected for production.


### Results

| Path | Writing | Review | Total |
| --- | ---: | ---: | ---: |
| Recorded five-stage update, high reasoning | 316 s revision | Other stages: 1186 s | 25m 02s |
| Direct localization + review, high reasoning | 445 s | 166 s | 10m 10s |
| Direct localization + review, medium reasoning | 149 s | 172 s | 5m 21s |

This is one article and one trial per setting, not a latency guarantee. Both
trials used the same frozen source and existing full guidance. The medium run
also included the clarified register entries in `locale_rules.py`; the high run
started immediately before that small edit. Both received the new locale brief
and shared source/voice/parentheses instructions. The comparison therefore does
not isolate reasoning effort as the only cause of the timing difference.

Both passed strict artifact validation and the new parenthesis check. Both model
reviewers approved with no findings. Continuous reading found a clear failure in
the medium draft: “faça meus impostos” transfers English syntax where the high
draft says “faça minha declaração de imposto de renda”. The medium reviewer also
missed “Finance sobre Open Finance”. Medium reasoning is not adopted.

The high draft preserves both asides, the recurring concrete infrastructure
imagery (“construir o encanamento uma vez só”), the refusal to repeat decisions,
the categorical framework claim, and the sarcastic assistant comparison. Its
structural checks and this focused review support trying the shorter high-reasoning
path; a model verdict does not establish that every wording choice meets the
owner's taste. In particular, the technical use of “domicílio” still deserves an
owner terminology decision rather than another model's decree.

The trial source differs from the current source file, so neither translation is
promoted. No authored posts, accepted revisions, or published HTML were changed
by this investigation. The subsequent implementation removes separate review
calls and retains high reasoning for the localization agent.

Verification: 348 tests pass; Ruff and production Pyright pass. Tests cover the
reported aside, nesting, Markdown/HTML/code exclusions, frontmatter, candidate
rejection, failed repair preserving the accepted revision, and accepted-history
compatibility.

## Unattended build verification

The subsequent strict-build trial used an isolated copy of the current Maré Rio
source. Run `build-v2-20260907224514-e24caa27fcd1` made a 383-second localization
call. The result added a parenthetical group that was absent from the source;
deterministic validation required a repair, which took another 310 seconds and
passed. The translation was stored and the article rendered successfully.
No separate critic or scoring call ran. This was a newer source snapshot than
the controlled comparison above, so the timings do not isolate pipeline effects.

The same accepted result, rebuilt with the final engine, took 0.57 seconds and
made no model calls. A full non-strict build of all 13 current source posts passed
HTML and internal-link validation in 1.28 seconds without agent calls. These
trials did not replace the working checkout's posts or accepted translations.

The final automated suite has 357 passing tests; Ruff and production Pyright pass.
DanCLI's release gate passes. The actual translate command was also checked in
58-column and 110-column terminals, with color disabled, and with clean JSON on
stdout and progress on stderr. Structural checks and command tests do not establish
that every localized sentence meets the owner's editorial taste.
