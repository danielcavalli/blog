---
content_hash: a2c222c7776931084d1f1860671c6e97
created_at: '2025-10-24T00:49:34.910255'
date: 2025-10-23
excerpt: Creating smooth, performant animations using only CSS. A deep dive into building
  coherent motion systems for the modern web.
order: 1
slug: css-animations-guide
tags:
- css
- web
- animations
- performance
title: The Art of CSS Animations
updated_at: '2025-11-25T23:01:33.869239'
---

## Why CSS Animations?

CSS animations offer several advantages over JavaScript-based animations. They are hardware-accelerated, more performant and maintain smooth 60fps frame rates even on lower-end devices. But more importantly, they enable a **declarative approach to motion**: you define what should happen and the browser handles how.

This blog is built entirely on CSS-first animations. JavaScript is used only to trigger state changes; the visual behavior lives in stylesheets.

## The Philosophy of Motion

Before choosing animation techniques, consider what the motion *means*. Every transition should answer three questions: **Where from? Where to? How does it relate to what came before?**

On this site, animations serve three core principles:
1. **Continuity**: Everything exists in one uninterrupted surface
2. **Physical Plausibility**: Motion echoes real-world dynamics without imitating them
3. **Calm Energy**: Purposeful movement without agitation

Motion is never decoration. It establishes spatial relationships and acknowledges state changes. The interface breathes.

## The Building Blocks

CSS provides three main ways to create animations:

### Transitions
Smooth interpolations between states. Used for hover effects, theme changes and dropdown expansions. The key is using shared motion constants. All transitions on this site use the same easing curve: `cubic-bezier(0.4, 0, 0.2, 1)`.

```css
:root {
    --motion-duration-core: 500ms;
    --motion-duration-quick: 300ms;
    --motion-duration-ripple: 600ms;
    --motion-easing: cubic-bezier(0.4, 0, 0.2, 1);
}

.custom-select {
    transition: all var(--motion-duration-core) var(--motion-easing);
}
```

This creates a shared temporal rhythm. Every interaction feels like part of the same choreography.

### Keyframe Animations
Multi-step choreography for complex motions. This blog uses keyframes sparingly: only for initial page load animations where elements fade in and rise upward.

```css
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### Transform Properties
The performance backbone. `translateY`, `scale` and `rotate` are hardware-accelerated and will not trigger expensive reflows. When the header slides behind the navigation bar, it uses `translateY(-120%)` with a 500ms duration, matching the core motion timing.

## View Transitions API

Modern browsers support the **View Transitions API**, which enables seamless morphing between page navigations. This blog uses it to transform post cards into full articles:

```css
::view-transition-old(post-container-1),
::view-transition-new(post-container-1) {
    animation-duration: var(--motion-duration-core);
    animation-timing-function: var(--motion-easing);
}
```

The critical insight: **fetch content BEFORE calling `startViewTransition()`**. Change the DOM synchronously inside the callback. This ensures the browser captures old and new states correctly, preventing flash-of-content issues.

```javascript
async function navigateTo(url) {
    const response = await fetch(url);
    const html = await response.text();
    
    document.startViewTransition(() => {
        // Synchronous DOM swap here
        updateDOM(html);
    });
}
```

## Performance Matters

Not all CSS properties are created equal when it comes to animation performance. 

**Hardware-accelerated (GPU):**
- `transform` (translate, scale, rotate)
- `opacity`
- `filter` (with caution: can be expensive)

**Avoid animating:**
- `width`, `height`, `margin`, `padding` (triggers layout)
- `color`, `background-color` alone (triggers paint)
- `box-shadow` (expensive, but acceptable for subtle hover states)

Use `will-change` sparingly and only during active animations:

```css
.post-card.filtering-out {
    opacity: 0;
    will-change: opacity;
}

.post-card:not(.filtering-out) {
    will-change: auto; /* Reset after animation */
}
```

This tells the browser to optimize GPU compositing, but only when needed. Leaving `will-change` active wastes memory.

## The Rhythm of Interaction

All animations on this site follow a consistent temporal rhythm defined by CSS custom properties:
- **500ms (core)** for most transitions (morphing, sliding, expansion)
- **300ms (quick)** for micro-interactions (hover feedback)
- **600ms (ripple)** for atmospheric changes (theme transitions)
- **Same easing everywhere**: `cubic-bezier(0.4, 0, 0.2, 1)`

This consistency creates a unified "breathing" feeling. When filters expand, dropdowns open and cards dissolve, they all move to the same pulse.

## Staggered Reveals

When showing multiple elements, stagger their appearance with CSS transition delays:

```css
.filter-row {
    transition: all var(--motion-duration-core) var(--motion-easing) 0.1s;
}

.filter-tags {
    transition: all var(--motion-duration-core) var(--motion-easing) 0.2s;
}
```

The filter controls appear 100ms before the tag pills, creating a cascade that guides the eye downward naturally. This breathing expansion makes the interface feel like it's unfolding from a single surface.

## Organic Boundaries

One unique pattern this blog uses: **overflow nudging**. When a dropdown list extends beyond the filter panel boundary, the entire block expands from its bottom edge, making room organically:

```css
.filters.expanded.dropdown-active {
    padding-bottom: 5rem;
}
```

JavaScript measures actual DOM overflow using `getBoundingClientRect()` and applies the class when needed. CSS handles the smooth expansion. The result feels like the page is aware of its own geometry and responds physically.

## Theme Transitions

Switching between light and dark mode is not just a color swap. It is an **atmospheric lighting shift**. The key is changing the theme FIRST, then enabling transitions:

```javascript
function applyTheme(theme, animated) {
    if (animated) {
        // Change theme immediately
        document.documentElement.setAttribute('data-theme', theme);
        
        // Force reflow
        document.body.offsetHeight;
        
        // Enable smooth transitions for 600ms
        document.body.classList.add('theme-transitioning');
        
        setTimeout(() => {
            document.body.classList.remove('theme-transitioning');
        }, 600);
    }
}
```

```css
body.theme-transitioning * {
    transition: background-color var(--motion-duration-ripple) var(--motion-easing),
                color var(--motion-duration-ripple) var(--motion-easing),
                border-color var(--motion-duration-ripple) var(--motion-easing);
}
```

The effect: the entire page ripples through a new lighting state in 600ms, maintaining the illusion of a single continuous surface. No flash, no abrupt snaps.

## FLIP: Animating Layout Changes

When filtering blog posts, cards need to reorganize smoothly. The **FLIP technique** (First, Last, Invert, Play) makes layout changes appear animated:

**Two-Phase Choreography:**
1. **Dissolve**: Cards losing relevance fade out over 500ms
2. **Reorganize**: Remaining cards slide into new positions using FLIP

```javascript
// Phase 1: Capture initial positions
const initialPositions = new Map();
cards.forEach(card => {
    const rect = card.getBoundingClientRect();
    initialPositions.set(card, { top: rect.top, left: rect.left });
});

// Apply filter changes (cards removed from layout)
cardsToHide.forEach(card => card.classList.add('filtering-out'));

// Wait for dissolve to complete via transitionend event
grid.addEventListener('transitionend', () => {
    // Phase 2: Capture final positions
    const finalPositions = new Map();
    visibleCards.forEach(card => {
        const rect = card.getBoundingClientRect();
        finalPositions.set(card, { top: rect.top, left: rect.left });
    });
    
    // FLIP: Calculate deltas and animate
    visibleCards.forEach(card => {
        const deltaY = initial.top - final.top;
        const deltaX = initial.left - final.left;
        
        card.style.setProperty('--flip-x', `${deltaX}px`);
        card.style.setProperty('--flip-y', `${deltaY}px`);
        card.classList.add('flip-animating');
    });
});
```

```css
.post-card.flip-animating {
    transition: transform var(--motion-duration-core) var(--motion-easing);
    transform: translate(var(--flip-x, 0), var(--flip-y, 0));
    will-change: transform;
}
```

The result: cards dissolve, then the grid smoothly contracts. No jarring jumps. JavaScript controls state; CSS controls visuals.

## Practical Examples

Every interaction on this blog demonstrates these principles:

- **Card hover**: `translateY(-2px)` lift with shadow bloom (300ms quick duration)
- **Tag pills**: Gradient backgrounds with 3px lift, expanding shadows (500ms core duration)
- **Dropdown unfold**: `max-height: 0 to 300px` with opacity fade (500ms)
- **Filter expansion**: Staggered reveals (100ms, 200ms delays) with bottom-edge growth
- **Post morphing**: View Transitions API for card-to-article transformation (500ms)
- **Theme ripple**: All color properties transition together (600ms atmospheric shift)
- **Card filtering**: Two-phase dissolve (500ms) then FLIP reorganization (500ms)

Each animation answers: Where from? Where to? How does it relate? Nothing appears or disappears without spatial context.

## Accessibility First

Always respect user preferences with the `prefers-reduced-motion` media query. Some users find animations distracting or disorienting:

```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

Motion should enhance, never hinder. When a user signals they need reduced motion, honor that immediately.

## The conclusion

CSS animations, when approached systematically, create interfaces that feel **alive but calm**. The goal is not to impress with flashy transitions but to build trust through spatial coherence. The goal was not performance alone, but it should also feel performant due to the idea behind the transitions: fluidity. A choppy transition takes away from this interface. While one could implement it in pure JS, I am not a good JS programmer (nor do I want to be). Heavily using the CSS features to abstract the implementation logic speeds up development while also giving performance optimization responsibilities to the browser itself.

Every animation on this blog serves the same philosophy:
- **Continuity**: One uninterrupted surface
- **Physical Plausibility**: Motion that echoes real dynamics
- **Calm Energy**: Purposeful, never agitated

Use CSS custom properties for shared timing. Let the browser handle sequencing via `transitionend` events. Apply `will-change` only during active animations. Always ask: Where from? Where to? How does it relate?

The interface does not perform. It responds.