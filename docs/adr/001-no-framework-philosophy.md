# ADR 1: No-Framework Philosophy

## Context

The dan.rio blog is a bilingual personal site built as a custom Python static site generator. Its author is a senior ML engineer who writes technical posts in English and publishes them in both English and Brazilian Portuguese. The site is hosted on GitHub Pages with a custom domain.

Modern web development offers a rich ecosystem of frameworks at every layer: static site generators like Astro, Hugo, and Eleventy for build orchestration; frontend frameworks like React, Vue, and Svelte for UI composition; CSS tooling like Tailwind and Sass for styling; and template engines like Jinja2 for HTML generation. Each of these tools solves real problems and has a large community behind it. Adopting any of them would bring established conventions, plugin ecosystems, and community support.

However, each framework also brings a dependency chain, a learning curve for its abstractions, an upgrade treadmill as major versions ship, and opinions about project structure that may not align with the project's needs. The blog has a single author, a handful of page types, and no interactive application state beyond a theme toggle and post filters. Its most complex subsystem is a Gemini-powered translation pipeline that no framework would provide out of the box.

The project's design philosophy, documented in skill.md and the .github design documents, is rooted in native web standards. The motion system uses the View Transitions API and the FLIP animation technique rather than animation libraries. The constraints in skill.md are explicit: "Don't add Node.js/npm," "Don't add a template engine," "Don't use CSS preprocessors," "Don't add JS frameworks."

## Decision

We will use no external frameworks or build tooling anywhere in the stack. The build system will be a custom Python orchestrator using only focused libraries (markdown, python-frontmatter, pyyaml, python-dotenv, google-genai) for content processing. HTML will be generated via Python f-strings in renderer.py rather than a template engine. The frontend will use vanilla JavaScript with IIFEs and native browser APIs rather than a framework. Styling will use vanilla CSS with custom properties rather than a preprocessor or utility framework. Animation will use the View Transitions API and CSS transitions rather than a library like GSAP or Framer Motion. There will be no Node.js, no npm, no webpack, no Vite, and no package.json in the project.

## Status

Accepted.

## Consequences

The project ships zero framework runtime to the browser. The entire JavaScript payload is four hand-written files totaling roughly two thousand lines of source. There is no hydration cost, no framework bootstrap, and no bundle to optimize. The site loads as static HTML with progressive enhancement.

The dependency footprint is minimal. The pyproject.toml lists five runtime dependencies and one dev dependency (pytest). There is no node_modules directory, no lock file churn from transitive JavaScript dependencies, and no build toolchain configuration. Upgrading dependencies is a rare and simple operation.

The project has full control over every byte of output. There are no framework-injected class names, no hydration markers, no runtime-generated styles. This enables precise control over View Transition annotations, semantic HTML structure, and accessibility attributes, which matters for a site whose core identity is its motion design.

The technology choices are stable. Python's standard library, a Markdown parser, and a YAML parser are decades-old technologies unlikely to require migration. The frontend depends only on browser-native APIs. The risk of a framework reaching end-of-life and forcing a rewrite is zero.

These benefits come at a cost. Without a component model or template partials, the main rendering, scripting, and styling files are each large and monolithic: renderer.py spans 1021 lines, filter.js spans 985 lines, and styles.css spans 1617 lines. Refactoring any of these requires manual effort that a framework's module system would reduce. The View Transitions API only works in Chromium browsers, and a framework like Svelte with a router could provide cross-browser transitions. Development has no hot module replacement; changes require a manual rebuild and browser refresh. The FLIP animation system in filter.js reimplements functionality that libraries like GSAP's Flip plugin provide in a few lines, and the SPA navigation in transitions.js handles edge cases (popstate, scroll restoration, filter preservation) that framework routers handle automatically. These are conscious tradeoffs for a single-author site where the learning value of working directly with the platform is part of the project's purpose.
