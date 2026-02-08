---
content_hash: f376fc36df021a1d7977b337e5907986548b8aa5f726bce6451c27c3c269d693
created_at: '2025-10-25T14:30:40.761318'
date: 2025-01-25
excerpt: 'Inside a bilingual static site that moves as one surface: a Python build,
  a translation pipeline, and native transitions that keep space continuous.'
order: 0
slug: the-living-static-system
tags:
- Web Development
- View Transitions API
- Static Sites
- Python
title: The Living Static System
updated_at: '2026-02-08T01:10:31.331791'
---

The system began as a question: how little does a blog need to feel alive. Not animated for its own sake, but alive in the way a tide advances: inevitable, continuous, without edges. What emerged is a static generator that writes two mirrors of itself, one in English and one in Portuguese, and a thin layer of motion that never breaks the surface. Pages do not switch. Space reorganizes.

## The Build Pipeline

The build is a single pass of deliberate work. Markdown enters through a narrow door. Front matter is read, content is parsed and a page model is assembled with just enough structure to render precisely what is needed and nothing else. The script does not orchestrate a framework. It composes files.

Inside `_source/build.py`, posts are discovered by walking the `_source/posts` directory. Each markdown file is parsed with the `frontmatter` library, which separates YAML metadata from body content. The body flows through Python's `markdown` library with extensions for fenced code blocks and tables. What comes out the other side is clean HTML wrapped in a template that knows exactly where the title goes, where the date sits and how the navigation should breathe.

The only cache that matters is the one that respects change. A content hash is computed from the English source using MD5, and any transformation that follows inherits that decision. The hash lives in the front matter itself, written back to the markdown file after parsing:

```python
def parse_markdown_post(filepath):
    post = frontmatter.load(filepath)
    content_hash = calculate_content_hash(post.content)
    
    stored_hash = post.get('content_hash')
    needs_update = False
    
    if not created_at:
        # New post - set creation date
        post['created_at'] = now
        post['content_hash'] = content_hash
        needs_update = True
    elif stored_hash != content_hash:
        # Content changed - update timestamp
        post['updated_at'] = now
        post['content_hash'] = content_hash
        needs_update = True
```

When nothing changed, nothing rebuilds. When a sentence moves, the pipeline wakes up and moves with it. The build script writes to two output directories, `/en` and `/pt`, both at the project root. Both are complete sites. Both are first-class. There is no fallback and no runtime fetch.

## Translation as a Mirror

Translation is not a decoration. It is a second surface drawn with the same hand. English goes in; Portuguese comes out through Gemini with constraints that preserve code blocks, technical terminology and the tone of the original.

The translator is initialized with an API key from the environment. It maintains a JSON cache file at `_cache/translation-cache.json`, keyed by the slug of each post and the content hash. The rule is simple: if the source has not changed, the translation is already true. If the hash differs, a new translation is requested and the cache is updated atomically.

The translation prompt is not a simple instruction. It is a contract:

> You are a bilingual Brazilian technical writer translating an English blog post into natural, localized Brazilian Portuguese. Your task is not to perform a literal translation but to localize the text—transforming it into something that reads as if it were originally written in Portuguese by the same author.

The prompt continues with principles: preserve technical terms that Brazilians use in English (`framework`, `build`, `pipeline`, `deploy`), but localize narrative and personal content to sound fluent and culturally accurate. The translator respects the grain of the original while making every sentence breathe naturally in the second language.

```python
translated = translator.translate_post(
    slug, frontmatter, content
)
```

The result is cached, and the next build skips the API call entirely. This is how a bilingual site can rebuild in seconds rather than minutes. The cache is the memory of what has already been said.

## Navigation as Continuous Space

Navigation behaves as if the document were a single plane that learns new shapes. In the browser, the View Transitions API is not a special effect. It is a memory of before and after. New HTML is fetched ahead of time. The swap happens inside a single synchronous callback and the browser captures two states of the same space. The code is small because the browser is doing what it is designed to do.

The `navigateTo` function in `static/js/transitions.js` intercepts clicks on internal links. It fetches the new page, parses it into a document fragment and prepares the swap. Before the transition begins, it removes `view-transition-name` attributes from post cards in the new document. This prevents the browser from creating extra pseudo-elements that would flash during cleanup. Then the transition starts:

```javascript
const transition = document.startViewTransition(() => {
  document.title = newDoc.title;
  
  const main = document.querySelector('main');
  const newMain = newDoc.querySelector('main');
  if (main && newMain) main.replaceWith(newMain);
  
  history.pushState(null, '', url);
  window.scrollTo({ top: 0, behavior: 'instant' });
});

await transition.finished;
```

The choreography is written in CSS, not in JavaScript. The code above only decides when the surface should remember. Everything else lives in styles: easing curves shared across interactions, durations that rhyme and `::view-transition` pseudo-elements that let titles morph without ever disappearing. The motion constants sit in one place and they do not bargain with the rest of the design:

```css
:root {
  --motion-duration-core: 500ms;
  --motion-duration-quick: 300ms;
  --motion-duration-ripple: 600ms;
  --motion-easing: cubic-bezier(0.4, 0, 0.2, 1);
}
```

Every interaction on the site uses these variables. Post cards lift on hover for 300ms. Theme transitions ripple for 600ms. View transitions morph for 500ms. The consistency is not an accident. It is the sound of the same clock ticking everywhere.

## Filtering Without Surprise

Cards on the index page learn to behave like good citizens. Their first duty is to appear, then stay still. Sorting and filtering are done with FLIP, not with surprise. FLIP stands for First, Last, Invert, Play: measure where each card starts, apply the filter or sort, measure where each card ends, then animate the delta.

The implementation in `static/js/filter.js` captures the initial bounding rectangles of all visible cards, applies the filter logic to hide or show cards, then captures the final positions. Each card that moved is given a CSS transform to invert it back to its starting position, and then the transform is removed over the animation duration. The card appears to slide smoothly from the old position to the new one.

```javascript
const rects = new Map();
cards.forEach(card => {
  rects.set(card, card.getBoundingClientRect());
});

// Apply filter (hides/shows cards, layout reflows)
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

The grid never jumps. It exhales. When navigation arrives from elsewhere, the initial keyframe reveal is bypassed entirely. The script detects navigation by checking `document.referrer` for the same origin. If the referrer matches, it assumes the user navigated from another page on the site, and it immediately disables the intro animation by adding `disable-animation` to the posts grid and setting `animation: none` on each card. The result is quiet: nothing flashes, nothing resets, nothing asserts itself after the fact.

## Language Switching as Translation Overlay

One of the system's subtler continuities is how language switching feels. When you click the language toggle, you are not leaving the page. You are translating the surface you are already reading. The scroll position is preserved. The filter state is preserved. The URL changes from `/en/index.html` to `/pt/index.html`, but your place in the document does not.

This is handled in `transitions.js` by detecting a language switch: the path structure is identical except for the `en` or `pt` segment. If this pattern is detected, the scroll position is captured before the fetch and restored after the DOM swap. If you were halfway down a long article in English and you switch to Portuguese, you stay halfway down the same article. The content changes, but the space does not.

The same principle extends to the filter state on the index page. If you have filtered posts by year or tag and you switch languages, the filter remains active. The translated posts appear, but the selection criteria are preserved. This is how a bilingual site feels like a single document viewed through two lenses rather than two separate sites.

## Customization Without Scaffolding

Customization respects the grain of the system. The entry point is configuration and text, not scaffolding. Open `_source/config.py` and you will find everything that can change: base path, language definitions, site metadata and UI strings for both languages. Change the base path and the build writes links that obey. Adjust typographic variables in `static/css/styles.css` and the entire surface tightens or loosens uniformly.

The language set is the only assumption baked in. English is the source of truth. Portuguese is a faithful translation. If a third language is needed, the rule extends: add a second mirror, give it a cache, keep the hashes honest. The builder is a script you can read in one sitting. If you can read it, you can change it. There is no magic. There are no hidden layers. The system is exactly as complex as the problem it solves.

## Why No Framework

Refusing a framework here is not nostalgia. It is an alignment with the problem. A blog is text, a few images and the sense that moving through it should feel like turning a page without losing the line you were reading. Native browser capabilities are already sufficient. Python is already sufficient. Dependencies are chosen like tools on a small bench: if a tool does not make the cut cleaner, it stays in the drawer.

The absence of machinery is not an ideology. It is maintenance practiced in advance. Every line of code in this system is code I will have to read again in six months or six years. Every dependency is a potential future incompatibility. Every abstraction is a tax on comprehension. So the system stays small. It stays readable. It stays changeable.

The View Transitions API is native to Chromium. It requires no polyfill, no wrapper, no build step. The browser already knows how to capture two states of the DOM and animate between them. My job is to decide when that should happen and to keep the rest of the page from interfering. The CSS that describes the motion is declarative. It reads like a choreography score, not like a program.

Python's `frontmatter` and `markdown` libraries do exactly one thing each: parse YAML and convert Markdown to HTML. They do it well. They do not try to be build systems. They do not try to be routers. They parse text. That is all I need them to do.

## The Philosophy of Motion

The philosophy of motion is the philosophy of attention. Nothing should insist. Transitions answer three questions: where from, where to and how this state relates to the last one. Theme changes ripple like a cloud passing over the sun. A card lifts a few pixels when you hover, then returns to rest. The surface never lies about what moved or why.

When something must be removed, it dissolves over 500 milliseconds. When something must arrive, it emerges from where it could plausibly have been. The post card on the index expands into the full article. The title stays in place and grows. The date anchors itself in the corner. The layout breathes outward without breaking continuity. When you press back, the article contracts into the card again. Space is conserved.

The easing curve is the same everywhere: `cubic-bezier(0.4, 0, 0.2, 1)`. This is not a random choice. It is the Material Design standard ease, chosen because it feels natural to human perception. Motion starts with intention, accelerates smoothly, and decelerates as it completes. Nothing snaps. Nothing glides at constant speed. Everything moves as if it has weight.

## The Contract with the Reader

For those who want to adapt it, the contract is small and explicit. Markdown in, HTML out. A translator that respects code and voice. A navigation layer that never blocks paints with work it could have done earlier. Styles that encode rhythm once and reuse it everywhere. If you change one thing, it should feel like you changed exactly one thing and the rest of the system should respond with proportionate calm.

The only cleverness is in knowing when to stop. The system could do more. It could have a CMS. It could have real-time preview. It could have analytics, A/B testing and social sharing widgets. It does none of these things because none of these things make the reading experience better. The goal is not to build a platform. The goal is to write and to let the writing be read without interference.

## What the System Knows

This is not a demonstration. It is the simplest version of a living document I could make without lying about what the web can already do. On most nights I write with the windows open in Copacabana and the sound of the avenue folding into the sea. The system learns that rhythm and keeps it. Things flow not because they are fast, but because they do not get in their own way.

The cache remembers what has not changed. The translator preserves what should not be translated. The navigation maintains where you were looking when the language switched. The motion system encodes how long things should take and refuses to argue about it. Every decision the system makes is in service of a single idea: the document is continuous. When you move through it, the space reorganizes, but it never breaks.

That is what it means for a static site to feel alive.