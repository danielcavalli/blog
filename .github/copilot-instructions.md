# Blog Project - Animation Guidelines

## Project Description
A minimal, fast-loading personal blog built with Python static site generation. Targets Chromium browsers exclusively using native Web APIs.

## Visual Animation Behavior

### Page Transitions
When navigating between pages, the content should morph smoothly rather than fade or slide:

1. **Card-to-Page Morphing**
   - When clicking a blog post card on the index page, the card should expand and morph into the full article
   - The post title should stay in place and smoothly transform from card title to article heading
   - The date and excerpt should fade out as the full content fades in
   - The card container should expand to fill the viewport as the article content appears
   - Duration: ~500-600ms with smooth easing (cubic-bezier)

2. **Page-to-Card Morphing (Back Navigation)**
   - When returning to the index, the article should contract back into its card position
   - The article heading should morph back to the card title position
   - The full content fades out as the excerpt fades back in
   - The layout should smoothly compress from full-page to card size

3. **Navigation Between Pages**
   - Regular page navigation (e.g., index to about) should use a subtle cross-fade
   - No jarring white flashes or abrupt content swaps
   - Content should feel continuous and fluid

### Visual Continuity Elements
- **Post titles** maintain their position and size during morphing
- **Dates** stay anchored during card expansion
- **Layout containers** grow/shrink smoothly, not suddenly
- **Text content** fades in/out gracefully without jumpy reflows

### Performance & Polish
- Animations should feel instant and responsive (no lag)
- No white flashes or blank frames during transitions
- Smooth bezier curves, not linear transitions
- All morphing elements should move in sync

## Technical Constraints
- **Browser**: Chromium only (Chrome, Edge, Brave, etc.)
- **No Safari or Firefox support required**
- **CSS-first approach**: All visual animations defined in CSS
- **Minimal JavaScript**: Only to trigger native browser APIs
- **Graceful degradation**: If JS blocked, site works without animations

## Animation Technology
- Uses native View Transitions API (Chromium)
- Visual effects defined via CSS pseudo-elements (`::view-transition-*`)
- JavaScript only intercepts navigation and calls `document.startViewTransition()`
- No animation libraries or frameworks

## Design Philosophy
- Speed and simplicity over complexity
- Native browser capabilities over third-party libraries
- Smooth morphing over flashy effects
- Content-first with subtle polish
