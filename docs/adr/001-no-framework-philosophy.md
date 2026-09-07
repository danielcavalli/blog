# ADR 1: No-Framework Philosophy

## Context

The dan.rio blog is a bilingual personal site built as a custom Python static site generator. Its author is a senior ML engineer who writes technical posts in English and publishes them in both English and Brazilian Portuguese. The site is hosted on GitHub Pages with a custom domain.

Modern web development offers a rich ecosystem of frameworks at every layer: static site generators like Astro, Hugo, and Eleventy for build orchestration; frontend frameworks like React, Vue, and Svelte for UI composition; CSS tooling like Tailwind and Sass for styling; and template engines like Jinja2 for HTML generation. Each of these tools solves real problems and has a large community behind it. Adopting any of them would bring established conventions, plugin ecosystems, and community support.

However, each framework also brings a dependency chain, a learning curve for its abstractions, an upgrade treadmill as major versions ship, and opinions about project structure that may not align with the project's needs. The blog has a single author, a handful of page types, and no interactive application state beyond a theme toggle and post filters. Its most complex subsystem is a custom localization runtime that no framework would provide out of the box.

The project's design philosophy, documented in `AGENTS.md`, [WRITING_STYLE.md](../../.agents/skills/writing-style/references/WRITING_STYLE.md), and the `.github` design documents, is rooted in native web standards. The motion system uses the View Transitions API and the FLIP animation technique rather than animation libraries. The constraints are explicit: no Node.js build stack, no template engine, no CSS preprocessor, and no JavaScript framework.

## Decision

The build system will remain a custom Python orchestrator with focused libraries for Markdown, YAML, HTML processing, and terminal feedback. [pyproject.toml](../../pyproject.toml) owns the current dependency list. HTML will be generated via Python f-strings in renderer.py rather than a template engine. The frontend will use vanilla JavaScript with IIFEs and native browser APIs rather than a framework. Styling will use vanilla CSS with custom properties rather than a preprocessor or utility framework. Animation will use the View Transitions API and CSS transitions rather than a library like GSAP or Framer Motion. Site generation requires no JavaScript bundler or Node.js build stack. Node.js can run the browser verification scripts independently of publication.

## Status

Accepted.

## Consequences

The browser receives static HTML and focused JavaScript for navigation, reading controls, and media. Pages containing Mermaid diagrams load that rendering library on demand. There is no hydration cost, no framework bootstrap, and no bundle to optimize. The site loads as static HTML with progressive enhancement.

Dependencies are declared in pyproject.toml and locked in uv.lock. Optional browser checks can use a separately installed Playwright browser; the site generator does not depend on that installation.

The project has full control over every byte of output. There are no framework-injected class names, no hydration markers, no runtime-generated styles. This enables precise control over View Transition annotations, semantic HTML structure, and accessibility attributes, which matters for a site whose core identity is its motion design.

The technology choices are stable. Python's standard library, a Markdown parser, and a YAML parser are decades-old technologies unlikely to require migration. The core frontend uses browser-native APIs. Optional diagram rendering has its own dependency and a readable source fallback.

These benefits come at a cost. Without a component model or template partials, the main rendering, scripting, and styling files are each large and monolithic: renderer.py, filter.js, and styles.css each carry substantial implementation detail. Refactoring any of these requires manual effort that a framework's module system would reduce. The View Transitions API only works in Chromium browsers, and a framework like Svelte with a router could provide cross-browser transitions. Development has no hot module replacement; changes require a manual rebuild and browser refresh. The FLIP animation system in filter.js reimplements functionality that libraries like GSAP's Flip plugin provide in a few lines, and the SPA navigation in transitions.js handles edge cases (popstate, scroll restoration, filter preservation) that framework routers handle automatically. These are conscious tradeoffs for a single-author site where the learning value of working directly with the platform is part of the project's purpose.
