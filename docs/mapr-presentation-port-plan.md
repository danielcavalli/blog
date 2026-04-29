# MAPR Presentation Blog-Native Port Plan

## Target Outcome

Build a blog-listed presentation post for "How I Use AI Agents" that appears in the normal blog index, opens as a native slide presenter, supports English and Portuguese, and leaves behind a small reusable presentation proof of concept compatible with the repo's constraints:

- Python renderer and build pipeline.
- Generated HTML committed to git.
- Vanilla CSS.
- Vanilla JavaScript.
- No Node build stack.
- No frontend framework.
- No Marp runtime or embedded Marp output.

The key architectural rule is that Marp is an import/reference format, not the runtime model. The implementation should preserve the deck content and structure while compiling it into a blog-native presentation document model rendered by the existing static site generator.

## Settled Product Contract

The following decisions are settled:

- The presentation should be treated as a blog post.
- It should appear as a clickable card in the normal blog index.
- It should be public and listed.
- The visual language should strictly follow the blog design system and motion philosophy.
- English is required.
- Portuguese is desired and should be supported through structured translation.
- No PDF fallback.
- No speaker notes.
- This is the beginning of reusable presentation support, but should be treated as a proof of concept rather than a fully generalized presentation platform.

Remaining decisions to confirm before implementation:

- Exact slug, likely `how-i-use-ai-agents`.
- Publication date, likely `2026-04-30`.
- Tags, likely some subset of `AI Agents`, `Workflow`, `Tools`, and `MLOps`.
- Whether the blog card should include a subtle content-type marker such as `Presentation`.
- Whether English and Portuguese must ship together, or whether English can land first if translation validation needs more time.

Recommendation: publish the card as a normal post with a subtle `Presentation` marker and use the same slug in both locales.

## Architecture Shape

The target pipeline should be:

```text
presentation-v2.md
  -> normalized structured presentation source
  -> English presentation post object
  -> translation artifact with structural constraints
  -> Portuguese presentation post object
  -> generated HTML under en/blog/ and pt/blog/
  -> normal blog index cards and sitemap entries
```

This avoids embedding Marp HTML, avoids translating rendered HTML, and keeps the work aligned with the blog's no-framework and generated-static-HTML architecture.

## Phase 1: Define The Presentation Source Model

Add a new presentation source location:

```text
_source/presentations/
  how-i-use-ai-agents.yaml
```

The source should be structured and semantic rather than raw HTML. A representative shape:

```yaml
slug: how-i-use-ai-agents
type: presentation
lang: en-us
title: How I Use AI Agents
excerpt: What I built, what broke, and what survived.
date: 2026-04-30
tags:
  - AI Agents
  - Workflow
  - Tools
assets:
  profile:
    src: /static/images/presentations/how-i-use-ai-agents/profile-picture.png
    alt: Daniel Cavalli
slides:
  - id: title
    layout: lead
    title: How I Use AI Agents
    subtitle: What I built, what broke, and what survived
    kicker: Daniel Cavalli | dan.rio
```

The source model should support the slide shapes present in `presentation-v2.md`:

- `lead`
- `divider`
- `bio`
- `content`
- `dark_content`
- `emphasis`
- `split`
- `card_grid`
- `table`
- `code`
- `image`
- `paragraph`
- `quote`
- `list`

Each slide should have:

- `id`
- `layout`
- `title`, when applicable
- optional `subtitle`
- `blocks`
- optional `variant`
- optional `density`, such as `normal`, `dense`, or `very_dense`

The `density` field matters because Portuguese text will often be longer than English. It lets the renderer adjust spacing, grid behavior, and overflow rules without changing content.

## Phase 2: Convert The Marp Deck

Use `/Users/daniel.cavalli/dev/nu/claude-things/cc-presentation/presentation-v2.md` as the canonical import reference and `/Users/daniel.cavalli/dev/nu/claude-things/cc-presentation/presentation-v2.pdf` as the rendered reference.

The conversion should be treated as a careful port, not a rewrite:

- Preserve all 39 slides.
- Preserve slide order.
- Preserve section structure.
- Preserve headings, body text, tables, code blocks, quotes, examples, and image usage.
- Convert Marp comments such as `_class: lead` into structured `layout` values.
- Convert `.card-row` raw HTML into structured card blocks.
- Convert `.split` raw HTML into structured column blocks.
- Convert HTML tables and Markdown tables into structured table rows.
- Convert code fences into structured code blocks with language and translation policy.
- Convert Marp image syntax into structured image blocks.

For the v2 deck, only these local assets are referenced:

```text
Data BU Presentation/profile-picture.png
Data BU Presentation/phased-dispatch.png
```

Copy those into a blog-owned static path, likely:

```text
static/images/presentations/how-i-use-ai-agents/
```

The other files under `Data BU Presentation/` should not be copied unless they become used by the structured source.

## Phase 3: Add A Presentation Loader

Add a focused loader instead of overloading Markdown post parsing:

```text
_source/presentation_loader.py
```

Responsibilities:

- Load presentation YAML.
- Validate required metadata.
- Validate that slide IDs are unique.
- Validate known slide layouts and block types.
- Validate required fields per block type.
- Produce a post-like object compatible with blog index sorting and filtering.
- Preserve raw structured source for translation.

The loader should output objects compatible with the existing post card contract:

- `title`
- `slug`
- `excerpt`
- `date`
- `published_date`
- `tags`
- `lang`
- `year`
- `month`
- `reading_time` or an equivalent display estimate
- `content_type: presentation`
- `slides`

This keeps index rendering and sitemap behavior close to existing post behavior.

## Phase 4: Integrate With The Build Pipeline

Update `_source/build.py` so the build can process both Markdown posts and structured presentation posts.

The build flow should become:

1. Load Markdown posts as today.
2. Load presentation sources.
3. Merge normal posts and presentation posts for index rendering.
4. Render source-language normal posts with `generate_post_html`.
5. Render source-language presentation posts with `generate_presentation_html`.
6. Translate target-language artifacts:
   - normal Markdown posts through the existing post translation lane
   - presentation posts through a structured presentation translation lane
7. Render translated presentation posts.
8. Render indexes.
9. Render sitemap.

Generated output should be:

```text
en/blog/how-i-use-ai-agents.html
pt/blog/how-i-use-ai-agents.html
```

The presentation should be listed in:

```text
en/index.html
pt/index.html
sitemap.xml
```

## Phase 5: Integrate With Blog Index Cards

The presentation should appear as a normal clickable blog card.

Minimal index behavior:

- The existing post card renderer can render presentation cards using the same shape as normal posts.
- If `content_type == "presentation"`, the card may include a subtle `Presentation` marker.
- Filtering and sorting should continue to work by date, tags, and update metadata.
- The card link should point to `/en/blog/how-i-use-ai-agents.html` or `/pt/blog/how-i-use-ai-agents.html`.

This satisfies the product requirement without introducing a separate presentation listing page.

## Phase 6: Add The Presentation Renderer

Add renderer functions in `_source/renderer.py`:

```python
generate_presentation_html(presentation, post_number, lang="en")
render_presentation_slide(slide, index, total, lang)
render_presentation_block(block, lang)
render_presentation_cards(block)
render_presentation_split(block)
render_presentation_table(block)
render_presentation_code(block)
```

The renderer should reuse existing shared page primitives:

- `render_head`
- `render_nav`
- `render_footer`
- `render_skip_link`
- `generate_lang_toggle_html`

A representative page shape:

```html
<main id="main-content" class="presentation-page">
  <article class="presentation-post">
    <header class="presentation-header">...</header>
    <section class="presentation-stage" data-slide-count="39">
      <section id="title" class="presentation-slide presentation-slide-lead">...</section>
      ...
    </section>
    <nav class="presentation-controls">...</nav>
  </article>
</main>
```

Recommended nav/footer behavior:

- Keep site nav visible in normal page mode.
- Keep the page semantically integrated with the blog.
- In fullscreen presenter mode, visually minimize non-presentation chrome.
- Keep controls accessible and keyboard reachable.

## Phase 7: Add Blog-Native Presentation CSS

Add:

```text
static/css/presentation.css
```

Do not copy the Marp stylesheet. Build the design from the blog's existing tokens:

- `--color-bg`
- `--color-text`
- `--color-text-secondary`
- `--color-border`
- `--color-surface-elevated`
- `--accent-color`
- `--accent-color-bright`
- `--ocean-color-*`
- `--font-sans`
- `--font-mono`
- `--space-*`
- `--motion-duration-*`
- `--motion-easing`

Design requirements:

- Slides should feel like focused blog surfaces, not Marp screenshots.
- No Google Fonts import.
- No copied Marp CSS.
- No framework classes.
- Cards should use restrained surfaces, borders, and radius around the existing 8px system.
- Tables should be readable and responsive.
- Code blocks should be close to the blog article code style, but with slide-density adjustments.
- Dark slides should use theme-aware tokens rather than hardcoded Marp colors.
- Divider slides should feel like deliberate blog moments rather than corporate section breaks.
- Motion should be restrained, purposeful, and disabled under `prefers-reduced-motion`.

Responsive behavior should support translation:

- `card_grid` can move from 4 columns to 2 or 1.
- `split` can stack.
- Tables can scroll horizontally or become compact.
- Code blocks can scroll internally.
- Dense slides can use smaller internal type within bounded limits.
- Controls should keep stable dimensions and avoid overlapping slide content.

Avoid fully automatic font scaling based on viewport width. Prefer semantic density and responsive wrapping.

## Phase 8: Add Deterministic Fit Rules

Use data-driven layout attributes:

```html
<section
  class="presentation-slide"
  data-layout="card_grid"
  data-density="dense"
>
```

Renderer and CSS should support:

- `data-density="normal"` for default slide typography and spacing.
- `data-density="dense"` for reduced spacing and compact cards.
- `data-density="very_dense"` for compact grids and scrollable content zones.
- `data-overflow="scroll"` for code-heavy and table-heavy slides.

For Portuguese, if text expansion still causes overflow, the renderer should allow:

- slide-internal vertical scroll on dense content,
- stacked mobile layout,
- smaller card body type within bounded limits,
- horizontal table scroll,
- scrollable code/transcript blocks.

This keeps translation feasible without requiring Portuguese slides to visually match English line-for-line.

## Phase 9: Add Presenter JavaScript

Add:

```text
static/js/presentation.js
```

Responsibilities:

- Track active slide.
- Navigate to next and previous slides.
- Update `location.hash`.
- Load directly to a slide hash.
- Support previous and next buttons.
- Support a progress indicator.
- Support fullscreen toggle.
- Avoid conflicts with existing SPA navigation.

Keyboard behavior:

- `ArrowRight`, `Space`, `PageDown`: next slide.
- `ArrowLeft`, `Shift+Space`, `PageUp`: previous slide.
- `Home`: first slide.
- `End`: last slide.

Optional POC behavior:

- touch swipe,
- overview mode,
- copy link to current slide,
- print mode.

Not in scope:

- speaker notes,
- PDF fallback,
- remote presenter mode,
- timer, unless Daniel explicitly requests it.

Interaction with `static/js/transitions.js`:

- Existing SPA navigation ignores hash-only links.
- Presentation slide navigation should operate inside the current page.
- Slide controls should be buttons rather than internal anchors where possible.
- Hash updates should not trigger a site fetch/swap.

## Phase 10: Structured Translation Contract

Do not translate generated HTML. Translate structured presentation data.

The translation artifact should preserve structure:

```json
{
  "title": "...",
  "excerpt": "...",
  "slides": [
    {
      "id": "title",
      "title": "...",
      "subtitle": "...",
      "blocks": []
    }
  ]
}
```

Fields that must not be translated:

- `slug`
- `id`
- `layout`
- `variant`
- `density`
- `asset.src`
- `block.type`
- URLs
- code blocks marked `translate: false`
- technical identifiers

Fields that may be translated:

- slide titles,
- slide subtitles,
- paragraph text,
- quote text,
- card titles,
- card bodies,
- table headings and cells when they are prose,
- transcript-like code blocks marked `translate: true`.

Code block policy matters. Some blocks in the deck are real YAML/JSON/code examples and should usually remain unchanged. Some are simulated installer conversations and may be localized. The source model should make this explicit:

```yaml
type: code
language: text
translate: true
```

For the first implementation, preserve actual code blocks byte-for-byte unless Daniel explicitly wants the content localized.

## Phase 11: Translation Validation

Before accepting a Portuguese presentation artifact, validate structural invariants:

- Same slide count.
- Same slide IDs in the same order.
- Same layout per slide.
- Same block count per slide.
- Same block types per slide.
- Same card counts.
- Same table row and column counts.
- Same asset keys and paths.
- Required fields still present.
- No unexpected HTML in plain text fields.
- Code blocks marked `translate: false` are byte-identical.

Possible implementation locations:

```text
_source/presentation_loader.py
_source/presentation_translation.py
_source/translation_common.py
```

The implementation should follow existing `translation_v2` artifact patterns rather than create a separate translation runtime.

## Phase 12: SEO And Sitemap

Because the presentation is public and listed, sitemap behavior should match normal blog posts.

Update `_source/seo.py` if needed so presentation posts are included in generated sitemap entries.

The generated pages should have:

- canonical URL,
- reciprocal hreflang links,
- Open Graph metadata,
- Twitter card metadata,
- JSON-LD.

`BlogPosting` remains acceptable because the presentation is being published as a blog post. If useful, add presentation-oriented hints such as:

- `genre: "Presentation"`
- `learningResourceType: "Presentation"`

Do not add a PDF fallback because Daniel explicitly rejected it.

## Phase 13: Testing Strategy

Add focused tests rather than large HTML snapshots.

Loader tests:

- Parses a fixture presentation.
- Rejects duplicate slide IDs.
- Rejects unknown layouts.
- Rejects unknown block types.
- Validates required fields.
- Confirms the real deck has 39 slides.

Renderer tests:

- Includes `presentation.css`.
- Includes `presentation.js`.
- Emits slide IDs.
- Emits controls.
- Emits progress metadata.
- Emits accessible labels.
- Escapes text fields correctly.
- Renders cards, split blocks, tables, code blocks, quotes, and images.

Build/index tests:

- Build writes `en/blog/how-i-use-ai-agents.html`.
- Build writes `pt/blog/how-i-use-ai-agents.html` when translation is available.
- Index includes the presentation card.
- Sorting and filtering still work with mixed normal posts and presentation posts.
- Sitemap includes presentation URLs.

Translation validation tests:

- Reject slide count drift.
- Reject changed slide IDs.
- Reject changed block types.
- Reject changed table shape.
- Reject changed non-translatable code blocks.
- Accept valid translated text with preserved structure.

Validation commands:

```bash
uv run python _source/build.py --strict
uv run python _source/link_checker.py
uv run --extra dev python _source/html_validator.py
```

## Phase 14: Manual Visual Validation

Manual validation should cover:

- All 39 English slides render.
- All 39 Portuguese slides render.
- No broken assets.
- Dense slides do not overlap controls.
- Code blocks remain readable.
- Tables do not escape the viewport.
- Theme toggle works.
- Reduced motion works.
- Keyboard navigation works.
- Hash reload works.
- Fullscreen works.
- Mobile layout is usable.

Screenshots are especially useful for:

- title slide,
- bio/agenda slide,
- dark content slide,
- card grid slide,
- split/code slide,
- table slide,
- dense installer transcript slide,
- Portuguese dense slide.

## Phase 15: Subagent Execution Plan

If implementing with subagents, split ownership by file and responsibility to avoid conflicts.

### Worker 1: Source Conversion

Ownership:

```text
_source/presentations/how-i-use-ai-agents.yaml
static/images/presentations/how-i-use-ai-agents/
```

Responsibilities:

- Convert all 39 slides.
- Preserve content and order.
- Convert Marp/HTML constructs into structured blocks.
- Reference copied assets.
- Do not touch build or renderer files.

### Worker 2: Loader And Validation

Ownership:

```text
_source/presentation_loader.py
tests/test_presentation_loader.py
```

Responsibilities:

- Define presentation loading and validation.
- Produce post-like objects.
- Validate slide/block structure.
- Add focused loader tests.

### Worker 3: Renderer

Ownership:

```text
_source/renderer.py
tests/test_renderer_presentation.py
```

Responsibilities:

- Add presentation renderer functions.
- Render all supported slide block types.
- Include CSS/JS assets.
- Add generated HTML structure tests.

### Worker 4: CSS And JS

Ownership:

```text
static/css/presentation.css
static/js/presentation.js
```

Responsibilities:

- Build blog-native presentation styling.
- Implement keyboard navigation.
- Implement progress and hash state.
- Implement fullscreen support.
- Add responsive and reduced-motion behavior.

### Worker 5: Build, Index, Sitemap Integration

Ownership:

```text
_source/build.py
_source/seo.py
tests/test_build_presentation.py
```

Responsibilities:

- Load presentations in the build.
- Merge presentation posts into index lists.
- Render presentation pages.
- Include presentation pages in sitemap.
- Preserve normal post behavior.

### Worker 6: Translation Contract

Ownership:

```text
_source/presentation_translation.py
tests/test_presentation_translation.py
```

Responsibilities:

- Serialize presentation artifacts for translation.
- Protect non-translatable fields.
- Validate translated structure.
- Wire into existing translation artifact patterns.

The main agent should integrate results, resolve conflicts, run validation, inspect output, and do final visual QA.

## Phase 16: Recommended Implementation Order

The safest first slice should prove the full path with a tiny fixture before converting the entire deck:

1. Add a minimal presentation YAML fixture with three slides: title, bio, and one content slide.
2. Add the loader and validation.
3. Render the English presentation page.
4. Make it appear in the English index.
5. Add CSS and JS controls.
6. Run build and validators.
7. Convert all 39 slides.
8. Add remaining block renderers.
9. Add presentation translation serialization and validation.
10. Generate Portuguese output.
11. Polish layout issues in English and Portuguese.
12. Run full validation.
13. Perform manual visual QA.

This sequencing prevents discovering build/index/renderer problems only after the full deck has already been converted.

## Main Risks And Mitigations

### Portuguese Text Expansion

Risk: Portuguese strings can overflow dense 16:9 slide layouts.

Mitigation: translate structured fields, use semantic density, allow responsive stacking and internal scroll zones.

### Translation Pipeline Shape

Risk: existing translation paths assume Markdown post content.

Mitigation: add a structured presentation artifact lane that follows existing `translation_v2` patterns but validates presentation-specific invariants.

### Renderer Bloat

Risk: `_source/renderer.py` is already large.

Mitigation: keep presentation renderer functions grouped and focused. If the implementation grows too much, move presentation rendering into a dedicated module and import it from `renderer.py` or `build.py`.

### Index Assumptions

Risk: index sorting/filtering may assume all entries are Markdown posts.

Mitigation: make presentation objects satisfy the existing post card contract and add tests for mixed content.

### Hash Navigation

Risk: slide hash navigation could conflict with SPA transitions.

Mitigation: use buttons for controls, let presentation JS own slide state, and avoid internal anchor navigation for next/previous.

### Scope Creep

Risk: reusable presentation support can expand into a full slide framework.

Mitigation: define reusable as "a second deck should be possible with the same primitives," not "support arbitrary Marp."

## Definition Of Done

The work is complete when:

- The presentation appears as a listed blog post.
- English presentation page is generated under `en/blog/`.
- Portuguese presentation page is generated under `pt/blog/`, unless Daniel explicitly accepts an English-first release.
- The page uses blog-native styling and motion.
- The page has working keyboard navigation, controls, progress, hashes, and fullscreen.
- All 39 slides are present and ordered correctly.
- Used local assets render from blog-owned static paths.
- No PDF fallback is included.
- No speaker notes are included.
- Build, link checker, and HTML validator pass.
- Manual desktop/mobile checks pass for representative dense slides.
