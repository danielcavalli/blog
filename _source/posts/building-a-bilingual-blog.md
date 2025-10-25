---
content_hash: 80e10199703f3f20dfa297cb890b150c
created_at: '2025-10-25T14:30:24.827911'
date: 2025-01-24
excerpt: 'How this blog works: Python static generation, automatic Gemini translation,
  View Transitions API for seamless navigation, and a philosophy of building with
  native web standards.'
tags:
- Web Development
- View Transitions API
- Gemini AI
- Static Sites
title: Building a Bilingual Blog with View Transitions
updated_at: '2025-10-25T14:30:24.827911'
---

This blog is a platform built with Python static site generation, automatic translation via Gemini AI, and seamless page transitions using the View Transitions API. No frameworks, no heavy dependencies—just native web standards doing real work. The architecture is simple enough to understand in an afternoon, powerful enough to feel continuous in use, and small enough to maintain alone.

The design goal was not to build the most feature-complete blog engine. It was to build the quietest one. A place where writing appears without ceremony, where navigation feels like reorganizing space rather than loading new pages, and where a second language emerges as naturally as the first. Every technical choice serves that goal.

## Static Generation with Purpose

At the core is a Python script that reads markdown files from `_source/posts` and writes HTML to two output directories: `/en` for English and `/pt` for Portuguese. The script uses `frontmatter` to parse YAML metadata and `markdown` to convert body content. There is no plugin system, no theme marketplace, no abstractions over abstractions. The script composes files. That is all it needs to do.

Each markdown file contains front matter with a title, date, excerpt, and optional tags. The script walks the posts directory, loads each file, extracts the metadata, converts the markdown to HTML, and injects it into a template. The template is not a separate system. It is a Python f-string that knows where the navigation goes, where the post title sits, and how the footer should close. Output HTML is written to disk with deterministic filenames derived from the post slug.

```python
def generate_post_html(post, post_number, lang='en'):
    lang_dir = LANGUAGES[lang]['dir']
    current_page = f"blog/{post['slug']}.html"
    
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <title>{post['title']} - dan.rio</title>
    <link rel="stylesheet" href="{BASE_PATH}/static/css/styles.css">
</head>
<body>
    <nav class="nav">...</nav>
    <main class="container">
        <article class="post">
            <h1>{post['title']}</h1>
            <div class="post-body">{post['content']}</div>
        </article>
    </main>
</body>
</html>"""
```

The build is deterministic. Run it twice on the same input and you get byte-identical output. This makes caching trivial and rebuilds predictable. The only state that persists across builds is the translation cache, which we will discuss in a moment.

## Translation as First-Class Content

Every post is written in English. Every post is automatically translated to Brazilian Portuguese using Google's Gemini 2.0 Flash model. The translation is not an afterthought. It is part of the build process, cached by content hash, and regenerated only when the English source changes.

The translator lives in `_source/translator.py`. It maintains a JSON cache at `_cache/translation-cache.json`, keyed by post slug and content hash. Before requesting a translation, the script checks if the current content hash matches the cached hash. If it does, the cached translation is used. If it doesn't, a new translation is requested via the Gemini API, and the cache is updated.

The translation prompt is careful. It tells the model to localize, not to translate literally. Technical terms that Brazilians use in English—`framework`, `backend`, `API`, `deploy`, `commit`—are preserved. Code blocks are left untouched. The narrative voice is adapted to sound natural in Portuguese while maintaining the same tone and rhythm as the original.

```python
def translate_post(self, slug: str, frontmatter: Dict, content: str):
    content_hash = self._calculate_content_hash(content)
    cached = self.cache.get_translation(slug, content_hash)
    if cached:
        return cached
    
    prompt = self._build_translation_prompt(frontmatter, content)
    response = self.model.generate_content(prompt)
    translated = self._parse_translation_response(response.text)
    
    self.cache.set_translation(slug, content_hash, translated)
    return translated
```

The result is two complete, parallel sites. Both are static HTML. Both are self-contained. Both can be served from a CDN without backend infrastructure. The English site lives at `/en`, the Portuguese site at `/pt`, and the user can switch between them with a single click. The language toggle does not reload the page. It navigates with a View Transition that preserves scroll position and filter state, making the switch feel like an overlay rather than a jump.

## Navigation That Remembers

The site uses the View Transitions API to animate between pages. This API is Chromium-exclusive, which means the site targets Chrome, Edge, Brave, and other Chromium-based browsers. There is no polyfill. There is no fallback animation. If the API is not available, navigation works normally without transitions. This is a deliberate trade: cutting-edge features for users on modern browsers, graceful degradation for everyone else.

The script that handles navigation is small. It lives in `static/js/transitions.js`. When you click an internal link, the script intercepts the click, fetches the new page HTML, parses it into a document fragment, and starts a View Transition. Inside the transition callback, the script swaps the document title, stylesheets, main content, and navigation, then updates the URL with `history.pushState`. The browser captures the "before" state, runs the callback to update the DOM, captures the "after" state, and animates the difference.

```javascript
async function navigateTo(url) {
  const response = await fetch(url, { cache: 'no-cache' });
  const html = await response.text();
  const newDoc = new DOMParser().parseFromString(html, 'text/html');
  
  const transition = document.startViewTransition(() => {
    document.title = newDoc.title;
    const main = document.querySelector('main');
    const newMain = newDoc.querySelector('main');
    if (main && newMain) main.replaceWith(newMain);
    history.pushState(null, '', url);
  });
  
  await transition.finished;
}
```

All animation behavior is defined in CSS using `::view-transition-*` pseudo-elements. JavaScript only triggers the API. The CSS defines how the old content fades out, how the new content fades in, and how shared elements morph between states. Post cards on the index expand into full articles. Titles stay in place and grow. The background shifts smoothly. The sensation is not of switching pages but of reorganizing a single continuous surface.

The easing curve is the same everywhere: `cubic-bezier(0.4, 0, 0.2, 1)`. The durations are shared across all interactions: 300ms for quick hover effects, 500ms for core transitions, 600ms for theme changes. These constants live in CSS custom properties and propagate through every animation on the site. Consistency is not enforced by a framework. It is encoded in the design system itself.

## Language Switching as Spatial Translation

One of the system's subtle continuities is how language switching feels. When you toggle from English to Portuguese, you are not leaving the page. You are translating the surface you are already reading. The scroll position is preserved. The filter state on the index page is preserved. The URL changes from `/en/index.html` to `/pt/index.html`, but your place in the document does not.

This behavior is detected in the navigation script. If the path structure is identical except for the `en` or `pt` segment, the navigation is classified as a language switch. The scroll position is captured before the fetch and restored after the DOM swap. If you were halfway down an article in English and you switch to Portuguese, you remain halfway down the same article in Portuguese. The content changes, but the space does not.

The same principle applies to filtering on the index page. If you have filtered posts by year or tag, and you switch languages, the filter remains active. The translated posts appear with the same selection criteria. This makes the bilingual experience feel like a single document viewed through two lenses rather than two separate sites.

## Filtering with FLIP

The index page lists all posts with a filter panel for year, month, and tags. Filtering is instant. When you select a year, the posts that do not match fade out, and the remaining posts reorganize into a tighter grid. The reorganization is animated using the FLIP technique: First, Last, Invert, Play.

The script captures the initial position of every visible card. It applies the filter, which hides cards that do not match and causes the layout to reflow. It captures the final position of every card that remains visible. For each card, it calculates the delta between the old position and the new position, applies a CSS transform to invert the card back to its starting position, and then animates the transform back to zero.

```javascript
const rects = new Map();
cards.forEach(card => {
  rects.set(card, card.getBoundingClientRect());
});

applyFilter();

cards.forEach(card => {
  const oldRect = rects.get(card);
  const newRect = card.getBoundingClientRect();
  const dx = oldRect.left - newRect.left;
  const dy = oldRect.top - newRect.top;
  
  card.style.transform = `translate(${dx}px, ${dy}px)`;
  requestAnimationFrame(() => {
    card.style.transition = 'transform 500ms var(--motion-easing)';
    card.style.transform = 'none';
  });
});
```

The grid never jumps. It exhales. Cards dissolve out and slide into new positions over the same 500ms window. The result feels deliberate, not surprising. The layout is always legible. The motion explains what changed.

## Theme Transitions and Anti-Flicker Engineering

The site supports light and dark themes. The toggle is a simple button in the navigation bar. When you click it, the theme ripples across the entire page over 600 milliseconds. Background colors shift, text colors adjust, borders soften or sharpen, and shadows recalculate. The transition is smooth because it is defined once, in CSS, with a single class applied to the body.

One challenge during development was preventing visual flicker when theme transitions overlapped with View Transitions. If both systems were animating the same elements simultaneously, the result was a brief flash. The solution was to remove conflicting CSS classes before starting a View Transition, and to avoid universal selectors that apply transitions to every element at once.

The theme transition is gated. It only applies when the `theme-transitioning` class is present on the body. When you toggle the theme, the class is added, the theme attribute is updated, and the class is removed after the transition completes. This ensures that theme changes are animated, but navigation does not trigger redundant theme transitions.

Another flicker source was delayed removal of CSS animations on post cards. On the index page, cards fade in with a staggered animation when the page first loads. On subsequent navigations, this animation should not run. The script detects navigation by checking `document.referrer`. If the referrer matches the site's origin, the script assumes the user navigated from another page and immediately disables the intro animation by adding `disable-animation` to the posts grid. The cards appear instantly without flashing or resetting.

## Philosophy of Simplicity

The architecture is not minimal for the sake of being minimal. It is minimal because the problem is simple. A blog is text, some images, and the sense that moving through it should feel like turning a page without losing your place. Native browser capabilities are sufficient. Python is sufficient. Dependencies are chosen carefully. If a tool does not make the cut cleaner, it does not enter the codebase.

The View Transitions API is native to Chromium. It requires no polyfill, no wrapper, no build step. The browser already knows how to capture two states of the DOM and animate between them. My job is to decide when that should happen and to keep the rest of the page from interfering. The CSS that describes the motion is declarative. It reads like a choreography score, not like a program.

Python's `frontmatter` and `markdown` libraries do exactly one thing each: parse YAML and convert Markdown to HTML. They do it well. They do not try to be build systems or routers. They parse text. That is all I need them to do. The entire build script is fewer than 600 lines of Python. You can read it in one sitting. If you can read it, you can change it.

## Maintenance in Advance

Refusing a framework here is not nostalgia. It is an alignment with the problem. Every line of code in this system is code I will have to read again in six months or six years. Every dependency is a potential future incompatibility. Every abstraction is a tax on comprehension. So the system stays small. It stays readable. It stays changeable.

The absence of machinery is not an ideology. It is maintenance practiced in advance. When I add a new post, I write markdown and run the build script. The translation happens automatically. The HTML is generated. The cache is updated. The site is ready to deploy. There is no hot-reloading server. There is no webpack configuration. There is no package.json with 300 dependencies. There is a Python script, a markdown file, and a folder of static HTML.

## The Contract with the Reader

For those who want to adapt it, the contract is small and explicit. Markdown in, HTML out. A translator that respects code and voice. A navigation layer that never blocks paints with work it could have done earlier. Styles that encode rhythm once and reuse it everywhere. If you change one thing, it should feel like you changed exactly one thing, and the rest of the system should respond with proportionate calm.

The only cleverness is in knowing when to stop. The system could do more. It could have a CMS. It could have real-time preview. It could have analytics and A/B testing and social sharing widgets. It does none of these things because none of these things make the reading experience better. The goal is not to build a platform. The goal is to write, and to let the writing be read without interference.

This is not a demonstration. It is the simplest version of a living document I could make without lying about what the web can already do. The cache remembers what has not changed. The translator preserves what should not be translated. The navigation maintains where you were looking when the language switched. The motion system encodes how long things should take and refuses to argue about it. Every decision the system makes is in service of a single idea: the document is continuous. When you move through it, the space reorganizes, but it never breaks.

That is what it means for a static site to feel alive.