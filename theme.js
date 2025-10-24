// Dark/Light Mode Toggle
// Executes early to prevent FOUC (Flash of Unstyled Content)

(function() {
    'use strict';
    
    // Get initial theme from localStorage or system preference
    function getInitialTheme() {
        const stored = localStorage.getItem('theme-preference');
        if (stored) {
            return stored;
        }
        
        // Check system preference
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        
        return 'light';
    }
    
    // Apply theme to document with smooth ripple
    function applyTheme(theme, animated = false) {
        if (animated) {
            // CRITICAL ORDER: Change theme FIRST, then enable transitions
            // This prevents flash where transitions apply to old theme
            document.documentElement.setAttribute('data-theme', theme);
            
            // Force reflow to ensure theme change is applied
            document.body.offsetHeight;
            
            // Now add transition class for smooth color ripple
            document.body.classList.add('theme-transitioning');
            
            // Remove transition class after animation completes (600ms ripple duration)
            setTimeout(() => {
                document.body.classList.remove('theme-transitioning');
            }, 600);
        } else {
            document.documentElement.setAttribute('data-theme', theme);
        }
    }
    
    // Toggle between light and dark
    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'light' ? 'dark' : 'light';
        
        applyTheme(next, true); // Animated transition
        localStorage.setItem('theme-preference', next);
        
        // Announce to screen readers
        announceThemeChange(next);
    }
    
    // Announce theme change for accessibility
    function announceThemeChange(theme) {
        const announcement = document.createElement('div');
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `${theme === 'dark' ? 'Dark' : 'Light'} mode activated`;
        
        document.body.appendChild(announcement);
        setTimeout(() => announcement.remove(), 1000);
    }
    
    // Apply theme immediately (before DOM loads)
    applyTheme(getInitialTheme());
    
    // Set up toggle button when DOM is ready
    function init() {
        const toggleButton = document.getElementById('theme-toggle');
        if (toggleButton) {
            toggleButton.addEventListener('click', toggleTheme);
            
            // Set initial ARIA label
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            toggleButton.setAttribute('aria-label', 
                `Switch to ${currentTheme === 'light' ? 'dark' : 'light'} mode`
            );
            
            // Update ARIA label on theme change
            const observer = new MutationObserver(() => {
                const theme = document.documentElement.getAttribute('data-theme') || 'light';
                toggleButton.setAttribute('aria-label', 
                    `Switch to ${theme === 'light' ? 'dark' : 'light'} mode`
                );
            });
            
            observer.observe(document.documentElement, {
                attributes: true,
                attributeFilter: ['data-theme']
            });
        }
        
        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                // Only update if user hasn't set a preference
                if (!localStorage.getItem('theme-preference')) {
                    applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }
    
    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
