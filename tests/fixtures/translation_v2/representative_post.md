---
slug: deterministic-mock-post
source_locale: en-us
target_locale: pt-br
title: Why deterministic translation fixtures matter
excerpt: A practical note on reproducible translation tests.
tags:
  - testing
  - localization
---

## Context

Teams ship faster when translation tests are deterministic.

### What to validate

1. Frontmatter fields remain coherent.
2. Markdown structure is preserved.
3. Stage outputs can be asserted without network calls.
