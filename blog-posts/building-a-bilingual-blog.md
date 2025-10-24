---
title: "Building a Bilingual Blog with View Transitions"
date: 2025-10-24
excerpt: "How this blog works: Python static generation, automatic Gemini AI translation, View Transitions API for seamless navigation, and a philosophy of building with native web standards."
tags: ["Web Development", "View Transitions API", "Gemini AI", "Static Sites"]
created_at: "2025-10-23T15:14:12.277250"
updated_at: "2025-10-24T15:24:37.645164"
content_hash: "553df0755a212336d376feb065d9ff83"
---

# Building a Bilingual Blog with View Transitions

This blog is a minimal, fast-loading platform built with Python static site generation, automatic translation via Gemini AI, and seamless page transitions using the View Transitions API. No frameworks, no heavy dependencies—just native web standards doing real work.

# Building a Bilingual Blog with View Transitions

This blog is a minimal, fast-loading platform built with Python static site generation, automatic translation via Gemini AI, and seamless page transitions using the View Transitions API. No frameworks, no heavy dependencies—just native web standards doing real work.

## Architecture Overview

**Static Site Generator**: Python script (`build.py`) parses Markdown posts, extracts frontmatter, generates clean HTML. Fast, simple, maintainable.

**Automatic Translation**: Every post written in English is automatically translated to Brazilian Portuguese using Google's Gemini 2.5 Flash API. Translation cache (`translation-cache.json`) uses SHA-256 hashes—translations only regenerate when English source changes.

**View Transitions**: Chromium's View Transitions API creates morphing, continuous transitions between pages. Blog cards expand into full articles. Navigation feels like reorganizing elements on a single surface, not jumping between pages.

## Key Features

### Bilingual Content Generation

```python
translator = GeminiTranslator(api_key=os.getenv('GEMINI_API_KEY'))
translated = translator.translate_post(
    slug, frontmatter, content
)
```

The translator preserves natural Anglicisms (framework, backend, API), maintains code blocks unchanged, and produces fluent Brazilian Portuguese. Smart caching means fast rebuilds—only changed content gets retranslated.

### Seamless Page Navigation

View Transitions API enables smooth morphing between pages:

1. JavaScript intercepts navigation clicks
2. New page HTML is fetched
3. `document.startViewTransition()` captures before/after states
4. Browser animates the diff automatically

All animation behavior is defined in CSS using `::view-transition-*` pseudo-elements. JavaScript only triggers the API.

```css
::view-transition-old(blog-header) {
    animation: slide-header-up 500ms cubic-bezier(0.4, 0, 0.2, 1);
}
```

### Ambient UI Design

The language toggle shows a globe icon with "EN / PT". The active language has a **soft ambient glow** created with radial gradients and blur filters:

```css
.lang-en.active::before {
    content: '';
    position: absolute;
    background: radial-gradient(circle, rgba(0, 123, 255, 0.12) 0%, transparent 70%);
    filter: blur(10px);
}
```

Theme toggle uses a ripple effect—600ms color transitions across all elements create atmospheric lighting shifts. The goal: calm, continuous interaction.

### Post Filtering with FLIP

The index page filters posts by year, month, and tags. Layout reorganization uses the FLIP technique (First, Last, Invert, Play):

1. Capture initial card positions
2. Apply filters
3. Capture final positions
4. Animate cards from old → new positions

Two-phase animation: dissolve hidden cards (500ms), then reorganize visible cards (500ms). Smooth spatial continuity without jarring jumps.

## Motion System

All animations follow unified timing constants:

```css
--motion-duration-core: 500ms;
--motion-duration-quick: 300ms;
--motion-duration-ripple: 600ms;
--motion-easing: cubic-bezier(0.4, 0, 0.2, 1);
```

Every interaction shares the same rhythm. Post cards lift on hover (300ms), blog headers slide out (500ms), theme shifts ripple (600ms). Consistency creates cohesion.

## Anti-Flicker Engineering

One challenge: preventing visual flicker during View Transitions. The solution:

**Remove conflicting CSS classes before starting transitions:**

```javascript
// Clean up theme transition class before View Transition
document.body.classList.remove('theme-transitioning');
document.startViewTransition(() => {
    updateDOM(newContent);
});
```

The `theme-transitioning` class applies 600ms color transitions globally. If active during View Transitions, the two animation systems conflict—visible flicker. Cleanup before navigation eliminates this.

## Browser Compatibility

**Target: Chromium Only** (Chrome, Edge, Brave, Arc). View Transitions API is Chromium-exclusive. Graceful degradation: if API unavailable, navigation works normally without morphing effects.

This focused approach enables cutting-edge features without polyfills or compromises.

## Why This Approach?

**Minimal Dependencies**: No React, Next.js, or framework bloat. Native web APIs, Python, thoughtful design.

**Educational**: Every line is readable and documented. The codebase teaches View Transitions, FLIP animations, modern CSS.

**Fast**: Static HTML with aggressive caching. No heavy JavaScript parsing. Near-instant loads.

**Accessible**: Keyboard navigation, focus states, screen reader support, semantic HTML throughout.

**Maintainable**: Simple Python build script. No complex toolchains.

## File Structure

```
blog/
├── build.py                 # Main build script
├── translator.py            # Gemini translation
├── styles.css              # View Transitions CSS
├── theme.js                # Dark/light mode
├── transitions.js          # View Transitions navigation
├── filter.js               # FLIP filtering
├── blog-posts/             # Markdown sources
├── en/                     # Generated English site
└── pt/                     # Generated Portuguese site
```

## Conclusion

Modern web development can be simple, elegant, powerful—without heavy frameworks. By leveraging native browser APIs (View Transitions), static site generation, and thoughtful design, we create polished experiences with minimal code.

The design is calm. The user experience is continuous. The code is minimal. That's the goal: a blog that gets out of the way and lets content shine.
