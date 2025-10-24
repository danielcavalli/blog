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
 */

(function() {
    'use strict';
    
    // Check View Transitions API support
    if (!document.startViewTransition) {
        // Graceful degradation - just navigate normally
        return;
    }
    
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
        try {
            // Fetch the target page
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
            
            // Start the view transition
            const transition = document.startViewTransition(() => {
                // Replace entire document content
                // This is the synchronous DOM swap that triggers the morph
                document.documentElement.innerHTML = newDoc.documentElement.innerHTML;
                
                // Update URL
                history.pushState(null, '', url);
            });
            
            // Wait for transition to complete
            await transition.finished;
            
            // Re-initialize scripts on the new page
            reinitializeScripts();
            
        } catch (error) {
            console.error('Morphing transition error:', error);
            // Fallback to normal navigation
            window.location.href = url;
        }
    }
    
    /**
     * Re-initialize theme and other scripts after DOM replacement
     */
    function reinitializeScripts() {
        // Dispatch event for other scripts to reinitialize
        document.dispatchEvent(new CustomEvent('page-navigation-complete'));
        
        // Theme toggle might need reinitialization
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle && window.theme && typeof window.theme.init === 'function') {
            window.theme.init();
        }
    }
    
})();
