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
                
                if (main && newMain) {
                    main.replaceWith(newMain);
                }
                
                // Update navigation active state
                const currentPath = new URL(url).pathname;
                document.querySelectorAll('.nav-links a').forEach(link => {
                    const linkPath = new URL(link.href).pathname;
                    // Match exact path or index.html paths
                    const isActive = linkPath === currentPath || 
                        (linkPath.endsWith('index.html') && currentPath.endsWith('index.html'));
                    
                    if (isActive) {
                        link.classList.add('active');
                    } else {
                        link.classList.remove('active');
                    }
                });
                
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
