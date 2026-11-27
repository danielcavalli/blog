# Collaboration Model

Do not assume decision-making authority. Keep the user in the loop.

The assistant is autonomous in execution, investigation, and implementation, but should not assume it is working alone. Collaboration is part of the default workflow.

## Rules

Prompt the user before making consequential decisions.

Do not silently choose product, architectural, workflow, or quality-policy directions when they are not explicitly settled already.

When a decision affects behavior, system design, translation quality, workflow, or long-term maintenance:
- surface it,
- state the tradeoff briefly,
- ask the user,
- wait for direction before implementing.

For straightforward execution with low ambiguity, proceed autonomously.

## Working Style

Collaborate actively instead of assuming the assistant should decide alone.

Confirm decisions instead of inferring them when the inference would shape the solution in a meaningful way.

Treat the user as an active part of the reasoning loop, especially when broader context, taste, product intent, or cross-domain judgment matters.

Autonomy is for carrying work forward efficiently, not for bypassing collaboration.

## Working in this repository

README.md says how the repository is laid out and how the site is built. What an agent most needs:

**The design is the Maré Design System's, not this repository's.** The site is built only from its
parts (`@mare-rio/design-system/react`). Before changing how anything looks or moves, read, in the
installed package (`node_modules/@mare-rio/design-system/`): `AGENTS.md`, `art/concept.md`,
`art/rules.md`, `docs/web-react.md`, and judge the result with `art/critic.md`. Never add a
stylesheet, a colour, a wrapper `<div>` with styles, or a transition here. If the design system lacks
something the site needs, it is built in the design system (on its `main`), released, and the pinned
version here is raised. A page whose components do not run in the browser has no paint: the pages are
hydrated on purpose.

**Reef is only the reader.** Every Markdown file here is reef-spec Markdown, read and commented on in
Reef. This repository owns everything that turns the Markdown into the site, and the git filter
below. Nothing is built into Reef for the blog, and the build does not depend on Reef.

**Reef conversations never reach git.** The `<!-- reef comment … -->` and `<!-- reef reply … -->`
blocks at the end of a file are private and this repository is public. A git filter keeps them out
of everything git stores and puts them back in the working files; `npm install` sets it up.

- Keep a file's trailer byte for byte when you edit its body. Never commit around the filter
  (`git -c filter.reef-conversations.clean= …`, `--no-filters`).
- A Markdown file listed as modified by `git status` with an empty `git diff` has a changed
  conversation and nothing to commit: `git add` it, or run `npm run conversations:refresh`.
- `git restore`, `git checkout -- <file>` and `git reset --hard` throw away what was said in a
  file's margin since it was last added. Do not run them on a document with open comments.
