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

    // Track the current logical document (path + query), excluding hash.
    // Hash-only changes should stay native and never trigger SPA fetch/swap.
    let lastPathAndSearch = `${location.pathname}${location.search}`;

    // Fix #2 (race condition): track in-flight fetch so we can abort it when
    // a new navigation starts before the previous one completes.
    let currentFetchController = null;

    // Fix #3 (scroll restoration): take manual control so the browser does not
    // automatically restore scroll on popstate before we have swapped the DOM.
    if (history.scrollRestoration) {
        history.scrollRestoration = 'manual';
    }

    // Fix #3: stamp the initial history entry with its scroll position so
    // popstate can restore it.  replaceState does not trigger popstate.
    // Merge with any existing state to avoid clobbering data set by other code.
    const existingState = history.state || {};
    if (existingState.scrollY == null) {
        history.replaceState({ ...existingState, scrollY: window.scrollY }, '');
    }

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
     * - Current year/month filter values (always stored as canonical English strings)
     * - Current sort order ('created' or 'updated')
     * - Active tag filters, keyed on the stable `data-tag-key` attribute when
     *   present, falling back to `data-tag`.
     *   `data-tag-key` holds a language-independent slug (e.g. "home-server")
     *   so that state survives a language switch where display labels differ.
     * 
     * Only captures if we're on the index page with filters.
     * Post pages don't have filters, so returns null.
     * 
     * @returns {Object|null} Filter state object or null if no filters
     */
    function captureFilterState() {
        const yearTrigger = document.querySelector('#year-filter-wrapper .select-trigger');
        const monthTrigger = document.querySelector('#month-filter-wrapper .select-trigger');
        const orderToggle = document.querySelector('.order-toggle');
        const activeTagButtons = document.querySelectorAll('.filter-tag.active');
        
        if (!orderToggle) return null;
        
        return {
            yearValue: yearTrigger?.dataset.value || '',
            monthValue: monthTrigger?.dataset.value || '',
            // Prefer the stable data-tag-key slug; fall back to data-tag (localized text).
            // When build.py emits data-tag-key, cross-language restoration is exact.
            // Without it, restoration is best-effort (only works if labels are identical
            // across languages, e.g. proper-noun tags like "Python", "cuda").
            activeTags: Array.from(activeTagButtons).map(btn =>
                btn.dataset.tagKey || btn.dataset.tag
            ),
            sortOrder: orderToggle.dataset.order || 'created'
        };
    }
    
    /**
     * Restore filter state after navigation
     * 
     * Restores:
     * - Year/month filter values
     * - Active tag filters
     * - Sort order
     * 
     * Tag buttons are located by `data-tag-key` (stable slug) when the attribute
     * is present in the new page's HTML, falling back to `data-tag`.  This means
     * filter state survives a language switch even when display labels differ
     * between languages — provided build.py emits `data-tag-key`.
     * 
     * Uses synthetic click to drive the filter logic inside filter.js (the
     * activeFilters Set is closure-local and not otherwise reachable).
     * Waits for filter.js to reinitialize via delayed RAF.
     * 
     * @param {Object} state - Filter state from captureFilterState()
     * @returns {void}
     */
    function restoreFilterState(state) {
        // Wait for filter.js to reinitialize
        setTimeout(() => {
            requestAnimationFrame(() => {
                // Restore year filter
                if (state.yearValue) {
                    const yearOption = document.querySelector(`#year-filter-wrapper .select-option[data-value="${state.yearValue}"]`);
                    if (yearOption) yearOption.click();
                }
                
                // Restore month filter
                if (state.monthValue) {
                    const monthOption = document.querySelector(`#month-filter-wrapper .select-option[data-value="${state.monthValue}"]`);
                    if (monthOption) monthOption.click();
                }
                
                // Restore active tags.
                // Each stored value is either a stable slug (data-tag-key) or a
                // localized label (data-tag fallback from the source page).
                // Try to match the new page's buttons by data-tag-key first, then
                // fall back to data-tag, so we work correctly in both cases.
                if (state.activeTags && state.activeTags.length > 0) {
                    state.activeTags.forEach(tagKey => {
                        // Prefer stable key lookup; fall back to label match
                        const tagButton =
                            document.querySelector(`.filter-tag[data-tag-key="${CSS.escape(tagKey)}"]`) ||
                            document.querySelector(`.filter-tag[data-tag="${CSS.escape(tagKey)}"]`);
                        if (tagButton && !tagButton.classList.contains('active')) {
                            tagButton.click();
                        }
                    });
                }
                
                // Restore sort order
                const orderToggle = document.querySelector('.order-toggle');
                if (orderToggle && state.sortOrder && orderToggle.dataset.order !== state.sortOrder) {
                    orderToggle.click();
                }
            });
        }, 100); // Small delay to ensure filter.js has initialized
    }

    // Intercept internal link clicks
    document.addEventListener('click', (e) => {
        const link = e.target.closest('a');

        // Always allow same-document hash navigation (citation links, TOCs, etc.)
        // so the browser performs native in-page scrolling.
        const rawHref = link?.getAttribute('href') || '';
        if (rawHref.startsWith('#')) {
            return;
        }

        let targetUrl = null;
        try {
            targetUrl = link ? new URL(link.href, location.href) : null;
        } catch (_) {
            targetUrl = null;
        }

        const isSameDocumentHash =
            !!targetUrl &&
            !!targetUrl.hash &&
            targetUrl.origin === location.origin &&
            targetUrl.pathname === location.pathname &&
            targetUrl.search === location.search;
        if (isSameDocumentHash) {
            return;
        }
        
        // Only handle internal same-origin links
        if (!link || 
            link.origin !== location.origin ||
            link.target === '_blank' ||
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
     * - history.pushState / no-op: Update URL without triggering popstate (skipped on popstate)
     * - window.scrollTo: Scroll to top, preserve position for language switches, or restore saved position on popstate
     * 
     * Error Handling:
     * - On fetch failure: throws error and falls back to window.location.href
     * - On any error: logs to console and uses normal navigation fallback
     * - AbortError (cancelled fetch) is swallowed silently
     * 
     * Concurrency Guard:
     * - Uses isNavigating flag to prevent multiple simultaneous navigations
     * - Aborts previous in-flight fetch via AbortController when a new navigation starts
     * 
     * @param {string} url - The absolute URL to navigate to
     * @param {boolean} [isPop=false] - True when called from popstate (back/forward).
     *   When true: skip history.pushState (URL is already correct), restore saved scrollY.
     * @returns {Promise<void>} Resolves when transition completes or rejects on error
     */
    async function navigateTo(url, isPop = false) {
        // Fix #2 (race condition): abort any previous in-flight fetch so that a
        // slow earlier response never overwrites a newer navigation's result.
        // We do this BEFORE the isNavigating guard so that back/forward presses
        // can cancel an ongoing forward navigation rather than being silently dropped.
        if (currentFetchController) {
            currentFetchController.abort();
            currentFetchController = null;
            isNavigating = false; // reset so the new navigation can proceed
        }

        if (isNavigating) return;
        isNavigating = true;

        currentFetchController = new AbortController();
        const { signal } = currentFetchController;

        try {
            // Fix #4 (landing page back-navigation): the root landing page has a
            // completely different DOM structure (no <main>, no <nav>) from inner
            // pages. The SPA swap logic would silently do nothing and leave the
            // browser showing a broken inner-page shell at the root URL. Instead,
            // let the browser do a real reload to the landing page.
            const targetPath = new URL(url, location.href).pathname;
            if (targetPath === '/' || targetPath === '/index.html') {
                window.location.href = url;
                return;
            }

            // Detect if this is a language switch (maintains continuity)
            const currentPath = location.pathname;
            const newPath = targetPath;
            const isLanguageSwitch = isLanguageSwitchNavigation(currentPath, newPath);
            
            // Capture state for continuity
            const scrollPosition = isLanguageSwitch ? window.scrollY : 0;
            const filterState = isLanguageSwitch ? captureFilterState() : null;
            
            // Fix #3 (scroll restoration on popstate): read saved scrollY from
            // history state so back-navigation restores the reader's position.
            // Only used when isPop=true; ignored for forward navigations.
            const restoredScrollY = (isPop && history.state && history.state.scrollY != null)
                ? history.state.scrollY
                : 0;

            // Save current scroll position into the history entry we are leaving
            // so that a future popstate back to this page can restore it.
            // This is a replaceState on the CURRENT entry (before pushState creates a new one).
            if (!isPop) {
                try {
                    history.replaceState(
                        { ...(history.state || {}), scrollY: window.scrollY },
                        ''
                    );
                } catch (_) { /* SecurityError in rare cross-origin edge cases */ }
            }
            
            // Fetch new page content BEFORE starting transition
            // Add cache-busting to ensure we get fresh content
            const response = await fetch(url, {
                cache: 'no-cache',
                headers: {
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache'
                },
                signal
            });
            if (!response.ok) throw new Error('Navigation failed: ' + response.status);
            
            const html = await response.text();
            const parser = new DOMParser();
            const newDoc = parser.parseFromString(html, 'text/html');

            // Validate that the fetched page has the elements we need for SPA swap.
            // If the target page lacks <main> (e.g. a restructured landing page or
            // error page), fall back to a full navigation to avoid a broken state.
            const newMain = newDoc.querySelector('main');
            if (!newMain) {
                window.location.href = url;
                return;
            }
            
            // Start the transition - view-transition-names are ESSENTIAL for morphing
            const transition = document.startViewTransition(() => {
                
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
                
                if (main) {
                    main.replaceWith(newMain);
                } else {
                    // No existing <main> to replace — append the new one.
                    // This handles edge cases where the DOM is in an unexpected state
                    // (e.g. after a failed partial swap).
                    const body = document.body;
                    const footer = document.querySelector('footer');
                    if (footer) {
                        body.insertBefore(newMain, footer);
                    } else {
                        body.appendChild(newMain);
                    }
                }
                
                // DO NOT REPLACE NAV - it has view-transition-name: site-nav and stays fixed
                // Only update the active link states within the existing nav
                const currentNav = document.querySelector('nav');
                const newNav = newDoc.querySelector('nav');
                
                if (currentNav && newNav) {
                    // Update only the nav-links to reflect active page.
                    // Use view-transition-name matching for robustness instead of
                    // index-based pairing, since nav structures could differ across pages.
                    const currentLinks = currentNav.querySelectorAll('.nav-links a');
                    const newLinks = newNav.querySelectorAll('.nav-links a');
                    
                    // Build a lookup from view-transition-name to new link state
                    const newLinksByVTN = new Map();
                    newLinks.forEach(link => {
                        const vtn = link.style.getPropertyValue('view-transition-name') ||
                                    link.getAttribute('style')?.match(/view-transition-name:\s*([^;]+)/)?.[1]?.trim();
                        if (vtn) newLinksByVTN.set(vtn, link);
                    });

                    currentLinks.forEach((link, index) => {
                        // Try matching by view-transition-name first, fall back to index
                        const vtn = link.style.getPropertyValue('view-transition-name') ||
                                    link.getAttribute('style')?.match(/view-transition-name:\s*([^;]+)/)?.[1]?.trim();
                        const matchedNew = (vtn && newLinksByVTN.get(vtn)) || newLinks[index];
                        
                        if (matchedNew) {
                            // Copy active class state
                            if (matchedNew.classList.contains('active')) {
                                link.classList.add('active');
                            } else {
                                link.classList.remove('active');
                            }
                            // Update href in case of language change
                            link.href = matchedNew.href;
                            // Sync visible nav label for cross-language switches
                            link.textContent = matchedNew.textContent;
                        }
                    });
                    
                    // Update language toggle to reflect current language
                    const currentLangToggle = currentNav.querySelector('.lang-toggle');
                    const newLangToggle = newNav.querySelector('.lang-toggle');
                    
                    if (currentLangToggle && newLangToggle) {
                        currentLangToggle.href = newLangToggle.href;
                        const newAriaLabel = newLangToggle.getAttribute('aria-label');
                        const newCurrentLang = newLangToggle.getAttribute('data-current-lang');
                        if (newAriaLabel) currentLangToggle.setAttribute('aria-label', newAriaLabel);
                        if (newCurrentLang) currentLangToggle.setAttribute('data-current-lang', newCurrentLang);
                        
                        // Update EN/PT active states
                        const currentEN = currentLangToggle.querySelector('.lang-en');
                        const currentPT = currentLangToggle.querySelector('.lang-pt');
                        const newEN = newLangToggle.querySelector('.lang-en');
                        const newPT = newLangToggle.querySelector('.lang-pt');
                        
                        if (currentEN && newEN) {
                            if (newEN.classList.contains('active')) {
                                currentEN.classList.add('active');
                                currentPT?.classList.remove('active');
                            } else {
                                currentEN.classList.remove('active');
                                currentPT?.classList.add('active');
                            }
                        }
                    }
                }
                
                // DO NOT REPLACE FOOTER - it has view-transition-name: site-footer
                // Footer content is identical across pages, only position changes
                
                // Update html lang attribute
                const newLang = newDoc.documentElement.lang;
                if (newLang) {
                    document.documentElement.lang = newLang;
                }
                
                // Fix #1 (popstate double-pushState): when navigateTo is called
                // from popstate, the URL is already correct (browser set it before
                // firing popstate). Calling pushState again would add a duplicate
                // forward entry to the history stack, breaking back/forward counts.
                // Fix #3: store scrollY=0 for new entries (top of new page).
                if (!isPop) {
                    history.pushState({ scrollY: 0 }, '', url);
                }

                // Keep document key in sync after URL updates.
                lastPathAndSearch = `${location.pathname}${location.search}`;
                
                // Scroll behaviour:
                // - language switch: maintain reader position (continuity design)
                // - back/forward (isPop): restore scroll saved in history.state
                // - regular forward navigation: reset to top
                if (isLanguageSwitch) {
                    window.scrollTo({ top: scrollPosition, behavior: 'instant' });
                } else if (isPop) {
                    window.scrollTo({ top: restoredScrollY, behavior: 'instant' });
                } else {
                    // Regular navigation - scroll to top
                    window.scrollTo({ top: 0, behavior: 'instant' });
                }
            });

            await transition.finished;
            
            // Restore filter state for language switches
            if (isLanguageSwitch && filterState) {
                restoreFilterState(filterState);
            }
            
            // Re-initialize scripts after DOM replacement
            requestAnimationFrame(() => {
                requestAnimationFrame(() => {
                    reinitializeScripts();
                    
                    // Move focus to main content after navigation for keyboard/AT users.
                    // Use the skip-link target (#main-content) when available;
                    // fall back to <main>.  tabIndex=-1 lets us focus a non-interactive
                    // element without adding it to the tab order.
                    if (!isLanguageSwitch) {
                        const mainContent = document.getElementById('main-content') || document.querySelector('main');
                        if (mainContent) {
                            if (!mainContent.hasAttribute('tabindex')) {
                                mainContent.setAttribute('tabindex', '-1');
                            }
                            mainContent.focus({ preventScroll: true });
                        }
                    }
                });
            });
        } catch (error) {
            // Fix #2: an AbortError means a newer navigation cancelled this fetch.
            // That is expected and normal — do not fall back to full reload.
            if (error.name === 'AbortError') return;
            console.error('Navigation error:', error);
            // Fallback to normal navigation
            window.location.href = url;
        } finally {
            currentFetchController = null;
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
        document.dispatchEvent(new CustomEvent('page-navigation-complete'));
    }

    // Handle back/forward navigation.
    // Fix #1: pass isPop=true so navigateTo does NOT call history.pushState again
    // (the browser already updated location.href before firing popstate).
    // Hash-only popstate events (same pathname/search) are ignored so
    // in-document anchors like #ref-17 keep native scrolling behavior.
    //
    // Guard: some browsers fire an initial popstate on page load (e.g. Safari).
    // We track whether we've set up and ignore any popstate that fires before
    // the first user interaction by checking the event's state.
    window.addEventListener('popstate', (e) => {
        const currentPathAndSearch = `${location.pathname}${location.search}`;
        if (currentPathAndSearch === lastPathAndSearch) {
            return;
        }

        // Guard: if the user navigated back to the landing page, do a full
        // reload immediately.  This avoids entering navigateTo(), which would
        // set isNavigating/currentFetchController and then hit the landing
        // page guard (window.location.href = url) — leaving dirty state if
        // bfcache restores the page later.
        const path = location.pathname;
        if (path === '/' || path === '/index.html') {
            window.location.href = location.href;
            return;
        }
        navigateTo(location.href, true);
    });

})();
