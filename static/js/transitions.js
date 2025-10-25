/**
 * @fileoverview View Transitions API integration for smooth page navigation
 * 
 * Features:
 * - Chromium-only View Transitions API for animated page changes
 * - Intercepts internal link clicks and uses fetch + DOM swap
 * - Graceful degradation: falls back to normal navigation if API unavailable
 * - Fetches new page content BEFORE starting transition for instant swap
 * - Updates document title, stylesheets, main content, navigation, and lang attribute
 * - Handles popstate (back/forward browser buttons)
 * - Dispatches custom event for script reinitialization after navigation
 * - **Continuity features: preserves scroll position and filters on language switches**
 * 
 * Continuity Design:
 * - Language switches feel like translation overlays, not page changes
 * - Scroll position preserved when switching /en/ ↔ /pt/ on same page
 * - Filter state preserved when switching languages on index page
 * - Regular navigation (different pages) resets to top as expected
 * - Maintains illusion of single continuous canvas across languages
 * 
 * Animation Architecture:
 * - All visual effects defined in CSS via ::view-transition-* pseudo-elements
 * - JavaScript only triggers document.startViewTransition() API
 * - Browser automatically captures "old" state, swaps DOM, captures "new" state, then animates
 * 
 * Critical Sequence:
 * 1. User clicks internal link
 * 2. Detect if language switch (maintains continuity)
 * 3. Capture scroll position and filter state if language switch
 * 4. Fetch new page HTML with cache-busting headers
 * 5. Parse HTML into newDoc
 * 6. Start transition with startViewTransition(callback)
 * 7. Inside callback: synchronously swap title, stylesheets, main, nav, lang, URL
 * 8. Restore scroll position if language switch (vs scroll to top for regular nav)
 * 9. Restore filter state if language switch on index page
 * 10. Browser animates between old and new states
 * 11. After transition.finished: dispatch 'page-navigation-complete' event
 * 12. Other scripts (theme.js, filter.js) reinitialize via event listener or MutationObserver
 * 
 * Anti-Flicker Strategy:
 * - Theme is preserved during navigation (already set in new page HTML)
 * - Scripts check if theme is already set before applying (prevents reapplication)
 * - No timing delays needed - just prevent redundant DOM mutations
 * - Same fix used for theme toggle transitions
 * 
 * Navigation Guards:
 * - Ignores external links (different origin)
 * - Ignores links with target="_blank"
 * - Ignores hash links (#anchor)
 * - Ignores links with modifier keys (Ctrl/Cmd/Shift for new tab/window)
 * - Prevents concurrent navigations via isNavigating flag
 * 
 * Error Handling:
 * - On fetch failure: falls back to window.location.href
 * - On any error: logs to console and uses normal navigation
 * 
 * Browser Requirements:
 * - Chromium only (Chrome, Edge, Brave, etc.)
 * - Requires document.startViewTransition support
 * - No Safari or Firefox support
 * 
 * Cache Control:
 * - Uses 'no-cache' to ensure fresh content on every navigation
 * - Prevents stale content from being displayed after edits
 */

(function() {
    'use strict';
    
    // Graceful degradation - if API not supported, use normal navigation
    if (!document.startViewTransition) return;

    let isNavigating = false;

    /**
     * Detect if navigation is a language switch
     * 
     * Language switches are detected by:
     * - Path changing from /en/ to /pt/ or vice versa
     * - Rest of path structure remaining the same
     * 
     * Examples:
     * - /en/index.html → /pt/index.html (language switch)
     * - /en/blog/post.html → /pt/blog/post.html (language switch)
     * - /en/index.html → /en/about.html (regular navigation)
     * 
     * @param {string} oldPath - Current pathname
     * @param {string} newPath - Target pathname
     * @returns {boolean} True if this is a language switch
     */
    function isLanguageSwitchNavigation(oldPath, newPath) {
        const oldLang = oldPath.match(/^\/(en|pt)\//)?.[1];
        const newLang = newPath.match(/^\/(en|pt)\//)?.[1];
        
        if (!oldLang || !newLang || oldLang === newLang) return false;
        
        // Check if paths are the same except for language
        const oldPathWithoutLang = oldPath.replace(/^\/(en|pt)\//, '/');
        const newPathWithoutLang = newPath.replace(/^\/(en|pt)\//, '/');
        
        return oldPathWithoutLang === newPathWithoutLang;
    }
    
    /**
     * Capture current filter state from the index page
     * 
     * Captures:
     * - Current filter text (from filter input)
     * - Current sort order ('created' or 'updated')
     * 
     * Only captures if we're on the index page with filters.
     * Post pages don't have filters, so returns null.
     * 
     * @returns {Object|null} Filter state object or null if no filters
     */
    function captureFilterState() {
        const filterInput = document.querySelector('.filter-input');
        const orderToggle = document.querySelector('.order-toggle');
        
        if (!filterInput || !orderToggle) return null;
        
        return {
            filterText: filterInput.value,
            sortOrder: orderToggle.textContent.trim()
        };
    }
    
    /**
     * Restore filter state after navigation
     * 
     * Restores:
     * - Filter text (triggers filtering)
     * - Sort order (triggers re-sorting)
     * 
     * Uses events to trigger the actual filtering/sorting logic.
     * Waits for DOM to be ready via small delay.
     * 
     * @param {Object} state - Filter state from captureFilterState()
     * @returns {void}
     */
    function restoreFilterState(state) {
        // Wait for filter.js to reinitialize
        requestAnimationFrame(() => {
            const filterInput = document.querySelector('.filter-input');
            const orderToggle = document.querySelector('.order-toggle');
            
            if (filterInput && state.filterText) {
                filterInput.value = state.filterText;
                // Trigger input event to apply filter
                filterInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
            
            if (orderToggle && state.sortOrder) {
                // Check if sort order needs to be changed
                const currentOrder = orderToggle.textContent.trim();
                if (currentOrder !== state.sortOrder) {
                    // Trigger click to toggle sort order
                    orderToggle.click();
                }
            }
        });
    }

    // Intercept internal link clicks
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');
        
        // Only handle internal same-origin links
        if (!link || 
            link.origin !== location.origin ||
            link.target === '_blank' ||
            link.hash ||
            e.ctrlKey || e.metaKey || e.shiftKey ||
            isNavigating) {
            return;
        }

        e.preventDefault();
        navigateTo(link.href);
    });

    /**
     * Navigate to URL with View Transitions API
     * 
     * Sequence:
     * 1. Detect if this is a language switch (maintains continuity)
     * 2. Capture current scroll position and filter state
     * 3. Fetch new page HTML with cache-busting headers
     * 4. Parse response into DOMParser document
     * 5. Start view transition with startViewTransition(callback)
     * 6. Inside callback: synchronously swap document parts (title, stylesheets, main, nav, lang, URL)
     * 7. Browser captures old state before callback, new state after callback, then animates
     * 8. Restore scroll position if language switch
     * 9. Restore filter state via custom event
     * 10. Dispatch 'page-navigation-complete' event for script reinitialization
     * 
     * Continuity Features:
     * - Language switches preserve scroll position (reader stays in same place)
     * - Language switches preserve filter state (same view, different language)
     * - Regular navigation resets to top (different content)
     * 
     * Anti-Flicker Strategy:
     * - New page HTML already has correct theme attribute set
     * - Scripts check if theme exists before applying (prevents redundant setAttribute)
     * - No theme reapplication during View Transition = no flicker
     * - Same pattern used for theme toggle flicker fix
     * 
     * DOM Updates (synchronous inside transition callback):
     * - document.title: Update page title
     * - Stylesheets: Add new stylesheets if not already present
     * - <main>: Replace entire main element
     * - <nav>: Replace entire nav element (for language-specific links)
     * - document.documentElement.lang: Update language attribute
     * - history.pushState: Update URL without triggering popstate
     * - window.scrollTo: Scroll to top (or preserve position for language switches)
     * 
     * Error Handling:
     * - On fetch failure: throws error and falls back to window.location.href
     * - On any error: logs to console and uses normal navigation fallback
     * 
     * Concurrency Guard:
     * - Uses isNavigating flag to prevent multiple simultaneous navigations
     * 
     * @param {string} url - The absolute URL to navigate to
     * @returns {Promise<void>} Resolves when transition completes or rejects on error
     */
    async function navigateTo(url) {
        if (isNavigating) return;
        isNavigating = true;

        try {
            // Detect if this is a language switch (maintains continuity)
            const currentPath = location.pathname;
            const newPath = new URL(url).pathname;
            const isLanguageSwitch = isLanguageSwitchNavigation(currentPath, newPath);
            
            // Capture state for continuity
            const scrollPosition = isLanguageSwitch ? window.scrollY : 0;
            const filterState = isLanguageSwitch ? captureFilterState() : null;
            
            // Fetch new page content BEFORE starting transition
            // Add cache-busting to ensure we get fresh content
            const response = await fetch(url, {
                cache: 'no-cache',
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache'
                }
            });
            if (!response.ok) throw new Error('Navigation failed');
            
            const html = await response.text();
            const parser = new DOMParser();
            const newDoc = parser.parseFromString(html, 'text/html');
            
            // CRITICAL: Remove view-transition-names from cards in NEW document BEFORE starting transition
            // This prevents the browser from creating pseudo-elements that cause flash on cleanup
            const newPostCards = newDoc.querySelectorAll('.post-card');
            if (newPostCards.length > 0) {
                console.log('[TRANSITIONS] Removing view-transition-names from', newPostCards.length, 'cards in new document');
                newPostCards.forEach(card => {
                    card.removeAttribute('style'); // Remove inline style with view-transition-name
                    // Also remove from children
                    card.querySelectorAll('[style*="view-transition-name"]').forEach(el => {
                        el.removeAttribute('style');
                    });
                });
            }
            
            // Now start the transition with the new content ready
            const transition = document.startViewTransition(() => {
                // This callback executes synchronously - DOM swap happens here
                // Browser captures the "old" state, then we swap, then captures "new" state
                
                document.title = newDoc.title;
                
                // Update stylesheets if different
                const currentStylesheets = Array.from(document.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href);
                const newStylesheets = Array.from(newDoc.querySelectorAll('link[rel="stylesheet"]')).map(l => l.href);
                
                // Add any new stylesheets that don't exist
                newStylesheets.forEach(href => {
                    if (!currentStylesheets.includes(href)) {
                        const link = document.createElement('link');
                        link.rel = 'stylesheet';
                        link.href = href;
                        document.head.appendChild(link);
                    }
                });
                
                // Swap main content
                const main = document.querySelector('main');
                const newMain = newDoc.querySelector('main');
                
                console.log('[TRANSITIONS] Swapping main content');
                
                if (main && newMain) {
                    main.replaceWith(newMain);
                    console.log('[TRANSITIONS] Main content swapped');
                    
                    // CRITICAL: Disable card animations immediately after DOM swap
                    // This prevents CSS animations from being applied to cards during navigation
                    const postsGrid = document.querySelector('.posts-grid');
                    if (postsGrid) {
                        console.log('[TRANSITIONS] Found posts-grid, adding disable-animation class');
                        postsGrid.classList.add('disable-animation');
                        const postCards = document.querySelectorAll('.post-card');
                        console.log('[TRANSITIONS] Posts grid now has', postCards.length, 'cards');
                    } else {
                        console.log('[TRANSITIONS] No posts-grid found');
                    }
                }
                
                // Update entire navigation to get language-specific links
                const nav = document.querySelector('nav');
                const newNav = newDoc.querySelector('nav');
                
                if (nav && newNav) {
                    nav.replaceWith(newNav);
                }
                
                // Update html lang attribute
                const newLang = newDoc.documentElement.lang;
                if (newLang) {
                    document.documentElement.lang = newLang;
                }
                
                // Update URL
                history.pushState(null, '', url);
                
                // Preserve scroll position for language switches, reset for regular navigation
                if (isLanguageSwitch) {
                    // Don't scroll - maintain reader's position
                    window.scrollTo({ top: scrollPosition, behavior: 'instant' });
                } else {
                    // Regular navigation - scroll to top
                    window.scrollTo({ top: 0, behavior: 'instant' });
                }
            });

            console.log('[TRANSITIONS] Waiting for transition to finish...');
            await transition.finished;
            console.log('[TRANSITIONS] View Transition finished');
            
            // Restore filter state for language switches
            if (isLanguageSwitch && filterState) {
                console.log('[TRANSITIONS] Restoring filter state for language switch');
                restoreFilterState(filterState);
            }
            
            // Re-initialize scripts after DOM replacement
            // Use double RAF to defer reinitialization until after paint cycle completes
            // This prevents flicker from DOM mutations (replaceChild, setAttribute) during rendering
            console.log('[TRANSITIONS] Scheduling reinitializeScripts with double RAF');
            requestAnimationFrame(() => {
                console.log('[TRANSITIONS] First RAF complete');
                requestAnimationFrame(() => {
                    console.log('[TRANSITIONS] Second RAF complete, calling reinitializeScripts');
                    reinitializeScripts();
                    console.log('[TRANSITIONS] reinitializeScripts complete');
                });
            });
        } catch (error) {
            console.error('Navigation error:', error);
            // Fallback to normal navigation
            window.location.href = url;
        } finally {
            isNavigating = false;
        }
    }
    
    /**
     * Re-initialize event listeners after navigation
     * 
     * Dispatches 'page-navigation-complete' custom event for other scripts to detect navigation.
     * This allows theme.js and filter.js to reinitialize their event listeners on new DOM elements.
     * 
     * Note: filter.js uses MutationObserver as alternative detection mechanism.
     * 
     * Side Effects:
     * - Dispatches CustomEvent on document
     * 
     * @returns {void}
     */
    function reinitializeScripts() {
        // Dispatch event for theme.js and filter.js to reinitialize
        console.log('[TRANSITIONS] Dispatching page-navigation-complete event');
        document.dispatchEvent(new CustomEvent('page-navigation-complete'));
        console.log('[TRANSITIONS] page-navigation-complete event dispatched');
    }

    // Handle back/forward navigation
    window.addEventListener('popstate', () => {
        navigateTo(location.href);
    });

})();
