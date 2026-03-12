# ADR 2: Python F-String HTML Rendering

## Context

The dan.rio blog is a bilingual static site generator written in Python. It must produce complete HTML documents for six distinct page types: individual blog posts, a post index with filtering, an about page, a CV page, a root landing page, and a sitemap. Each page requires SEO metadata (Open Graph tags, Twitter Cards, JSON-LD structured data), bilingual navigation, accessibility features, and View Transition API annotations. The build system already depends on Python for Markdown parsing, Gemini-powered translation, and YAML-based configuration, so the rendering layer shares the same runtime.

The standard approach for generating HTML from a Python build system is a template engine. Jinja2 is the dominant choice in the Python ecosystem, used by Flask, Pelican, and most static site generators. Mako is another mature option, favored by Pyramid and SQLAlchemy's migration tooling. Both provide template inheritance, automatic HTML escaping, macro systems, and IDE support with syntax highlighting and error reporting for the template language. These are well-understood tools with large communities.

The project's design philosophy, documented in skill.md, explicitly rejects template engines. The relevant constraint reads: "Don't add a template engine -- HTML is generated via Python f-strings by design." This constraint exists alongside parallel rejections of Node.js, CSS preprocessors, and JavaScript frameworks. The project values minimal dependencies, native tooling, and keeping the entire system legible as plain Python.

The rendering module, renderer.py, currently spans 1021 lines. It contains six fragment functions that produce reusable HTML chunks (render_head, render_nav, render_footer, render_skip_link, render_theme_toggle_svg, generate_lang_toggle_html) and six page-level generators that compose those fragments into complete HTML documents (generate_post_html, generate_index_html, generate_about_html, generate_cv_html, generate_root_index, and generate_post_card). Every function returns a string, and the composition mechanism is ordinary function calls whose return values are interpolated into f-strings.

## Decision

We will generate all HTML output using Python f-strings composed through function calls in renderer.py, without adopting a template engine. Fragment functions will produce reusable HTML strings for shared structures like the navigation bar, footer, head section, and accessibility links. Page generators will call these fragments and interpolate their return values, along with page-specific data, into f-string literals that produce complete HTML documents. All HTML escaping will be performed explicitly using html.escape from the standard library at each interpolation point. Configuration data from config.py and formatting utilities from helpers.py will be called directly in the rendering functions, since Python f-strings have full access to the call stack without requiring a separate template context object.

## Status

Accepted.

## Consequences

The rendering logic and its control flow live in the same language as the rest of the build system. Conditional rendering, loops over post tags, and data transformations happen with ordinary Python constructs rather than a template dialect. This means any Python developer can read, debug, and modify the rendering pipeline without learning a template language's scoping rules, filter syntax, or inheritance model. Refactoring tools like rename-symbol, extract-function, and find-all-references work across the rendering code just as they do in the rest of the codebase.

The composition pattern in renderer.py keeps the architecture reasonably modular. The render_head function, for example, is called by every page generator with different arguments for title, stylesheets, and meta tags, which is functionally equivalent to a base template with overridable blocks. Adding a new shared element means writing a new Python function and calling it from the relevant generators.

The project avoids adding Jinja2, Mako, or any other template engine as a dependency. The only standard library import renderer.py needs for escaping is the html module. This aligns with the broader project philosophy of minimal dependencies, where even the frontend avoids frameworks, preprocessors, and bundlers.

However, f-strings provide no automatic HTML escaping. Every interpolation of user-controlled or content-derived data must be wrapped in an explicit html.escape call. Renderer.py currently contains dozens of these calls across its 1021 lines. A missed escape is a potential XSS vector, and there is no tooling to catch omissions. Template engines like Jinja2 solve this by escaping all interpolations by default, requiring an explicit "safe" marker to output raw HTML. That safety net does not exist here.

HTML embedded in Python f-strings receives no syntax highlighting, no tag-matching, and no structural validation in standard editors. A developer working on the Open Graph meta block in generate_post_html sees a Python string, not an HTML document. Mismatched tags, unclosed elements, and malformed attributes are invisible until the output is inspected in a browser. Template engines, by contrast, are recognized by most editors and provide at least basic HTML-mode support within template files.

The file's size is a readability concern. At 1021 lines, renderer.py contains the complete HTML structure for every page type, including inline SVG icons for social links and the theme toggle. Certain patterns are duplicated across page generators, most notably the Open Graph and Twitter Card meta blocks, which appear with minor variations in five of the six generators. A template engine's inheritance and include mechanisms would naturally deduplicate these, but in the f-string approach, deduplication requires extracting more Python functions, which the project has chosen not to do for the meta blocks so far.

These tradeoffs are acceptable for a single-author static blog where the rendering surface is bounded and the developer is also the only content author. If the project were to grow significantly in page types or contributors, the balance would shift toward reconsidering this decision.
