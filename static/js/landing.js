/**
 * @fileoverview Landing page transition orchestration
 * 
 * Implements the morphing transition from landing state to full site.
 * Uses View Transitions API to create continuous surface transformation.
 * 
 * Design Philosophy:
 * - Landing page is not a separate layer; it's the origin state
 * - Transition feels like environment reorganizing, not page changing
 * - Title morphs upward into logo position
 * - Navigation buttons slide and reorganize into nav bar
 * - Selected page unfolds beneath, expanding from same visual layer
 * - Motion is restrained: 550ms with cubic-bezier(0.45, 0, 0.25, 1)
 * - Origin is clear: begins from clicked element, flows outward
 * 
 * Continuity principles:
 * - Single continuous surface throughout
 * - Physical plausibility in motion
 * - Calm energy - purposeful, not performative
 * 
 * SPA Boundary:
 * - The landing page does NOT participate in the inner-page SPA router
 *   (transitions.js).  It has a completely different DOM structure: no
 *   <main>, no <nav class="nav">, no <footer>.
 * - After the morphing transition, the full inner-page DOM is in place
 *   and transitions.js (loaded via the new scripts) takes over all
 *   subsequent navigations.
 * - Back-navigation from an inner page to the landing page is handled
 *   by transitions.js via a full reload (see its "/" guard).
 */

(function() {
    'use strict';
    
    // Check View Transitions API support
    if (!document.startViewTransition) {
        // Graceful degradation - just navigate normally
        return;
    }

    // Concurrency guard — prevent double-click from firing two transitions.
    let isMorphing = false;

    // AbortController for in-flight fetch cancellation.
    let morphFetchController = null;
    
    // Get all landing links
    const landingLinks = document.querySelectorAll('.landing-link');
    
    landingLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            const targetUrl = link.getAttribute('href');
            
            // Start the morphing transition
            morphToSite(targetUrl);
        });
    });
    
    /**
     * Orchestrate the morphing transition from landing to full site
     * 
     * Sequence:
     * 1. Fetch target page content
     * 2. Start View Transition
     * 3. Inside transition callback: swap DOM
     * 4. Browser automatically animates the morph based on view-transition-names
     * 
     * The magic happens through CSS:
     * - landing-title morphs to logo position
     * - landing-links reorganize to nav positions
     * - Main content unfolds into view
     * 
     * @param {string} url - Target page URL
     */
    async function morphToSite(url) {
        // Abort any previous in-flight fetch (e.g. rapid double-click)
        if (morphFetchController) {
            morphFetchController.abort();
            morphFetchController = null;
            isMorphing = false;
        }

        if (isMorphing) return;
        isMorphing = true;

        morphFetchController = new AbortController();
        const { signal } = morphFetchController;

        try {
            // Fetch the target page
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

            // Validate that the fetched page has a <body> with content.
            if (!newDoc.body || !newDoc.body.innerHTML.trim()) {
                throw new Error('Fetched page has empty body');
            }
            
            // Track load promises for scripts injected during the transition
            // callback, so we can await them after the transition finishes.
            let scriptLoadPromises = [];
            
            // Start the view transition
            const transition = document.startViewTransition(() => {
                // Capture current theme before DOM swap
                const currentTheme = document.documentElement.getAttribute('data-theme');
                
                // Update title
                document.title = newDoc.title;
                
                // Update language attribute
                const newLang = newDoc.documentElement.getAttribute('lang');
                if (newLang) {
                    document.documentElement.setAttribute('lang', newLang);
                }
                
                // CRITICAL: Ensure theme is set on documentElement BEFORE body swap
                // This prevents flash of unstyled content during the transition
                if (currentTheme) {
                    document.documentElement.setAttribute('data-theme', currentTheme);
                }
                
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
                
                // CRITICAL: Also add new script tags (like filter.js, transitions.js)
                const currentScripts = Array.from(document.querySelectorAll('script[src]')).map(s => s.src);
                const newScripts = Array.from(newDoc.querySelectorAll('script[src]')).map(s => s.getAttribute('src'));
                
                // Track load promises so we can wait for all scripts before
                // dispatching page-navigation-complete.
                const scriptLoadPromises = [];
                
                // Add any new scripts that don't exist
                newScripts.forEach(src => {
                    const fullSrc = new URL(src, url).href;
                    if (!currentScripts.includes(fullSrc)) {
                        const script = document.createElement('script');
                        script.src = src;
                        const loadPromise = new Promise(resolve => {
                            script.onload = resolve;
                            script.onerror = resolve; // don't block on failure
                        });
                        scriptLoadPromises.push(loadPromise);
                        document.head.appendChild(script);
                    }
                });
                
                // Replace body content (theme is already preserved above)
                document.body.innerHTML = newDoc.body.innerHTML;
                
                // Update URL with proper state object so transitions.js popstate
                // handler and scroll restoration work correctly.
                // scrollY: 0 because the inner page starts at the top.
                history.pushState({ scrollY: 0 }, '', url);
            });
            
            // Wait for transition to complete
            await transition.finished;
            
            // Remove landing.css AFTER transition completes to prevent style recalculation during morph
            requestAnimationFrame(() => {
                const landingCss = document.querySelector('link[href*="landing.css"]');
                if (landingCss) {
                    landingCss.remove();
                }
            });
            
            // Wait for all injected scripts to finish loading before
            // dispatching page-navigation-complete.  Without this, the
            // SPA router (transitions.js) and filter system (filter.js)
            // may not be active yet when the event fires.
            if (scriptLoadPromises.length > 0) {
                await Promise.all(scriptLoadPromises);
            }
            
            // Re-initialize scripts on the new page
            reinitializeScripts();
            
        } catch (error) {
            // AbortError is expected when a newer navigation cancels this one
            if (error.name === 'AbortError') return;
            console.error('Morphing transition error:', error);
            // Fallback to normal navigation
            window.location.href = url;
        } finally {
            morphFetchController = null;
            isMorphing = false;
        }
    }
    
    /**
     * Re-initialize theme and other scripts after DOM replacement
     */
    function reinitializeScripts() {
        // Wait for scripts to load in the new DOM
        // Need to delay slightly to ensure new page's scripts are loaded
        requestAnimationFrame(() => {
            // Dispatch event for other scripts to reinitialize
            document.dispatchEvent(new CustomEvent('page-navigation-complete'));
        });
    }
    
})();
