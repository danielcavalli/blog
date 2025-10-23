// Enhanced navigation with View Transitions API
// This provides seamless card-to-page transitions

(function() {
    'use strict';
    
    // Check if View Transitions API is supported
    if (!document.startViewTransition) {
        console.log('View Transitions API not supported - using standard navigation');
        return;
    }

    // Configuration
    const CONFIG = {
        FETCH_TIMEOUT: 5000,
        CACHE_DURATION: 300000, // 5 minutes
    };

    // Simple page cache
    const pageCache = new Map();
    
    // Track navigation state
    let isNavigating = false;
    let abortController = null;

    // Initialize on DOM ready
    function init() {
        // Set up dynamic card indices for staggered animations
        const cards = document.querySelectorAll('.post-card');
        cards.forEach((card, index) => {
            card.style.setProperty('--card-index', index);
        });

        // Set up click handler
        document.addEventListener('click', handleClick);
        
        // Handle browser back/forward
        window.addEventListener('popstate', handlePopState);
    }

    // Handle clicks with proper guards
    function handleClick(e) {
        // Guard against multiple simultaneous navigations
        if (isNavigating) {
            e.preventDefault();
            return;
        }

        const link = e.target.closest('a');
        
        // Only handle internal links
        if (!link || 
            !isInternalLink(link) ||
            link.target === '_blank' ||
            link.hash === '#' ||
            e.ctrlKey || 
            e.metaKey || 
            e.shiftKey) {
            return;
        }

        // Prevent default navigation
        e.preventDefault();
        navigate(link.href);
    }

    // Check if link is internal
    function isInternalLink(link) {
        try {
            return link.origin === location.origin;
        } catch {
            return false;
        }
    }

    // Main navigation function
    function navigate(url) {
        if (isNavigating) return;
        
        isNavigating = true;
        abortController = new AbortController();

        // Start the view transition
        const transition = document.startViewTransition(() => {
            return navigateToPage(url);
        });

        transition.finished
            .then(() => {
                isNavigating = false;
                abortController = null;
            })
            .catch((error) => {
                console.error('Transition failed:', error);
                isNavigating = false;
                abortController = null;
            });
    }

    // Navigate to new page with caching and error handling
    async function navigateToPage(url) {
        try {
            // Check cache first
            let html;
            const cached = pageCache.get(url);
            
            if (cached && (Date.now() - cached.timestamp < CONFIG.CACHE_DURATION)) {
                html = cached.html;
            } else {
                // Fetch with timeout
                const response = await Promise.race([
                    fetch(url, { signal: abortController.signal }),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Timeout')), CONFIG.FETCH_TIMEOUT)
                    )
                ]);
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                html = await response.text();
                
                // Cache the result
                pageCache.set(url, { html, timestamp: Date.now() });
            }
            
            // Parse the new HTML
            const parser = new DOMParser();
            const newDoc = parser.parseFromString(html, 'text/html');
            
            // Update the page title
            document.title = newDoc.title;
            
            // Update the main content
            const newMain = newDoc.querySelector('main');
            const currentMain = document.querySelector('main');
            
            if (!newMain || !currentMain) {
                throw new Error('Could not find main content');
            }
            
            currentMain.replaceWith(newMain);
            
            // Handle card animations based on page type
            const isIndexPage = url.endsWith('index.html') || 
                               new URL(url).pathname === '/' ||
                               new URL(url).pathname.endsWith('/blog/');
            
            if (isIndexPage) {
                disableCardAnimations();
            }
            
            // Update navigation active state
            updateActiveNav(url);
            
            // Update URL and history
            window.history.pushState({ url, timestamp: Date.now() }, '', url);
            
            // Manage focus for accessibility
            manageFocus(newMain);
            
            // Scroll to top
            window.scrollTo({ top: 0, behavior: 'instant' });
            
            // Announce to screen readers
            announcePageChange(newDoc.title);
            
        } catch (error) {
            console.error('Navigation failed:', error);
            
            // Show user-friendly error (could be enhanced with UI)
            if (error.name === 'AbortError') {
                console.log('Navigation cancelled');
            } else {
                // Fallback to standard navigation
                window.location.href = url;
            }
        }
    }

    // Disable card animations when coming back via view transition
    function disableCardAnimations() {
        const grid = document.querySelector('.posts-grid');
        if (grid) {
            grid.classList.add('disable-animation');
        }
    }

    // Manage focus for accessibility
    function manageFocus(newMain) {
        const focusTarget = newMain.querySelector('h1, h2') || newMain;
        
        // Make element focusable if not already
        if (!focusTarget.hasAttribute('tabindex')) {
            focusTarget.setAttribute('tabindex', '-1');
        }
        
        // Focus with slight delay to ensure DOM is ready
        setTimeout(() => {
            focusTarget.focus({ preventScroll: true });
        }, 100);
    }

    // Announce page changes to screen readers
    function announcePageChange(title) {
        const announcement = document.createElement('div');
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Navigated to ${title}`;
        
        document.body.appendChild(announcement);
        
        // Remove after announcement
        setTimeout(() => announcement.remove(), 1000);
    }

    // Update active navigation link
    function updateActiveNav(url) {
        const links = document.querySelectorAll('.nav-links a');
        links.forEach(link => {
            if (link.href === url || url.includes(link.getAttribute('href'))) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    // Handle browser back/forward buttons
    function handlePopState(event) {
        if (isNavigating) return;
        navigate(location.href);
    }

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
