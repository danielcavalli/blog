// Minimal View Transitions API integration (Chromium only)
// All animations are defined in CSS - this just triggers the browser API

(function() {
    'use strict';
    
    // Graceful degradation - if API not supported, use normal navigation
    if (!document.startViewTransition) return;

    let isNavigating = false;

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

    // Navigate with View Transitions
    function navigateTo(url) {
        if (isNavigating) return;
        isNavigating = true;

        // Use native View Transitions API - CSS handles all animations
        const transition = document.startViewTransition(async () => {
            try {
                const response = await fetch(url);
                if (!response.ok) throw new Error('Navigation failed');
                
                const html = await response.text();
                const parser = new DOMParser();
                const newDoc = parser.parseFromString(html, 'text/html');
                
                // Swap content smoothly
                document.title = newDoc.title;
                const main = document.querySelector('main');
                const newMain = newDoc.querySelector('main');
                
                if (main && newMain) {
                    main.replaceWith(newMain);
                }
                
                // Update URL
                history.pushState(null, '', url);
                
                // Scroll to top smoothly
                window.scrollTo({ top: 0, behavior: 'instant' });
            } catch (error) {
                console.error('Navigation error:', error);
                // Fallback to normal navigation
                window.location.href = url;
            }
        });

        transition.finished.finally(() => {
            isNavigating = false;
        });
    }

    // Handle back/forward navigation
    window.addEventListener('popstate', () => {
        navigateTo(location.href);
    });

})();
