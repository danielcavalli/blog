# Unattended localization and build modes

Status: accepted by the owner, 2026-09-07.

Localization is an unattended agent task. The owner triggers a strict build; the
engine reuses translations for the current source and localizes uncached documents
before rendering. A non-strict build makes no agent calls and renders the source
with available current translations. DanCLI defaults to strict mode.

The agent receives the source, committed PT-BR or EN-US localization guidance,
and the writing references that explain the author's voice. It returns a complete
document without asking questions, requesting approval, or editing source files.
Repository collaboration instructions are not injected into its isolated runtime.

Remove the serial analysis, terminology, critic, revision, and final-review chain.
One localization call does the work. Deterministic validation protects structure,
code, links, and parenthetical asides, with one bounded repair for a failed check.
There is no model-score acceptance gate. This removes latency and competing model
opinions; native voice remains an editorial requirement that tests cannot prove.

Accepted translations remain durable and versioned. Source changes require fresh
localization; model, prompt, or guidance changes alone do not expire accepted text.
Optional explicit refreshes and candidate comparisons remain available. Completed
responses can resume after failure, and a failed build preserves the generated site.
In non-strict output, missing translations are omitted and internal links resolve
to available source pages instead of producing broken links.
