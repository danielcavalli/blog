/**
 * @fileoverview Dark/Light Mode Theme Toggle System
 * 
 * Manages theme preferences with localStorage persistence and system preference detection.
 * Executes early in page load to prevent FOUC (Flash of Unstyled Content).
 * 
 * Features:
 * - Persists user theme preference across sessions
 * - Respects system dark/light mode preference as default
 * - Smooth animated transitions between themes (600ms ripple effect)
 * - Accessibility announcements for screen readers
 * - Auto-reinitialization after View Transitions navigation
 * 
 * Theme Application Order (Critical):
 * 1. Change data-theme attribute (instant)
 * 2. Force browser reflow
 * 3. Enable CSS transitions
 * 4. Remove transition class after 600ms
 * 
 * This order prevents visual flash where transitions apply to the wrong theme.
 * 
 * @requires localStorage API for persistence
 * @requires CSS custom properties for theming
 * @listens page-navigation-complete - Reinitializes after SPA navigation
 */

(function() {
    'use strict';
    
    // Locale-aware labels for accessibility announcements.
    // Keys match the <html lang="..."> attribute set by the build.
    const I18N = {
        'en': {
            darkActivated: 'Dark mode activated',
            lightActivated: 'Light mode activated',
            switchToDark: 'Switch to dark mode',
            switchToLight: 'Switch to light mode',
        },
        'pt': {
            darkActivated: 'Modo escuro ativado',
            lightActivated: 'Modo claro ativado',
            switchToDark: 'Mudar para modo escuro',
            switchToLight: 'Mudar para modo claro',
        },
    };

    /** Returns the i18n strings for the current page language, defaulting to EN. */
    function getStrings() {
        const lang = document.documentElement.lang || 'en';
        return I18N[lang] || I18N['en'];
    }
    
    /**
     * Retrieves initial theme from localStorage or system preference.
     * 
     * @returns {string} Theme name: 'light' or 'dark'
     */
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
    
    /**
     * Applies theme to document root element.
     * 
     * @param {string} theme - Theme name ('light' or 'dark')
     * @param {boolean} [animated=false] - Whether to animate (deprecated, always animated via CSS)
     * 
     * Theme changes are always animated via permanent CSS transitions on body.
     * No classes needed - transitions are always present in the base styles.
     */
    function applyTheme(theme, animated = false) {
        // Set the theme attribute - CSS variables update, triggering permanent transitions
        document.documentElement.setAttribute('data-theme', theme);
    }
    
    /**
     * Toggles between light and dark themes.
     * Persists choice to localStorage and announces change for accessibility.
     */
    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'light' ? 'dark' : 'light';
        
        applyTheme(next, true); // Animated transition
        localStorage.setItem('theme-preference', next);
        
        // Announce to screen readers
        announceThemeChange(next);
    }
    
    /**
     * Creates accessible announcement for theme changes.
     * Adds temporary ARIA live region that announces to screen readers.
     * 
     * @param {string} theme - New theme name ('light' or 'dark')
     */
    function announceThemeChange(theme) {
        const announcement = document.createElement('div');
        announcement.setAttribute('role', 'status');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        const strings = getStrings();
        announcement.textContent = theme === 'dark' ? strings.darkActivated : strings.lightActivated;
        announcement.style.position = 'absolute';
        announcement.style.left = '-10000px';
        announcement.style.width = '1px';
        announcement.style.height = '1px';
        announcement.style.overflow = 'hidden';
        
        document.body.appendChild(announcement);
        
        // Remove after screen readers have announced
        // Use RAF to prevent flicker from DOM removal
        setTimeout(() => {
            requestAnimationFrame(() => {
                if (announcement.parentNode) {
                    announcement.parentNode.removeChild(announcement);
                }
            });
        }, 2000); // Wait 2s - well after 600ms transition completes
    }
    
    // Apply theme immediately on script load (before DOM loads to prevent FOUC)
    // CRITICAL: Only apply if not already set - prevents reapplication during View Transitions
    // During navigation, the new page HTML already has data-theme attribute set correctly
    // Reapplying would cause a flicker as the attribute changes during the transition animation
    if (!document.documentElement.hasAttribute('data-theme')) {
        applyTheme(getInitialTheme());
    }
    
    // Tracks the active MutationObserver for the ARIA label sync so we can
    // disconnect it before creating a new one on re-initialization.
    let themeObserver = null;

    // System-preference listener is registered once at module level (not inside
    // init()) so repeated calls to init() after SPA navigation don't accumulate
    // duplicate listeners on the MediaQueryList.
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            // Only update if user hasn't set a preference
            if (!localStorage.getItem('theme-preference')) {
                applyTheme(e.matches ? 'dark' : 'light');
            }
        });
    }

    /**
     * Initializes theme toggle button and event listeners.
     * Called on DOMContentLoaded and after View Transitions navigation.
     * 
     * Prevents duplicate event listeners by cloning the button element.
     * Disconnects any previous MutationObserver before creating a new one.
     * The matchMedia listener is registered only once (above, at module level).
     * 
     * Accessibility:
     * - Sets aria-pressed to reflect whether dark mode is active
     * - Updates aria-label to describe the next toggle action
     * - Adds keydown handler for Enter/Space activation
     */
    /**
     * Updates ARIA attributes on the toggle button to reflect current theme.
     * Sets aria-label (next action) and aria-pressed (dark mode active).
     * 
     * @param {HTMLElement} button - The theme toggle button element
     */
    function updateToggleAria(button) {
        const theme = document.documentElement.getAttribute('data-theme') || 'light';
        const strings = getStrings();
        button.setAttribute('aria-label', 
            theme === 'light' ? strings.switchToDark : strings.switchToLight
        );
        button.setAttribute('aria-pressed', theme === 'dark' ? 'true' : 'false');
    }

    function init() {
        let toggleButton = document.getElementById('theme-toggle');
        if (toggleButton) {
            // Disconnect the previous ARIA-label observer before creating a new one.
            // Without this, every navigation adds another live observer on
            // document.documentElement, leaking memory and doing redundant work.
            if (themeObserver) {
                themeObserver.disconnect();
                themeObserver = null;
            }

            // Remove old click listener if it exists by replacing the button with a clone.
            // This prevents duplicate event listeners after navigation.
            if (toggleButton.hasAttribute('data-theme-initialized')) {
                const newButton = toggleButton.cloneNode(true);
                toggleButton.parentNode.replaceChild(newButton, toggleButton);
                toggleButton = newButton;
            }
            
            toggleButton.setAttribute('data-theme-initialized', 'true');
            toggleButton.addEventListener('click', toggleTheme);
            
            // Keyboard support: ensure Enter and Space activate the toggle.
            // Native <button> handles these, but this guards against cases where
            // the element is rendered as a non-button or has default prevented.
            toggleButton.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleTheme();
                }
            });
            
            // Set initial ARIA attributes (label + pressed state)
            updateToggleAria(toggleButton);
            
            // Update ARIA attributes whenever the theme attribute changes.
            // Store the observer reference so we can disconnect it next time.
            themeObserver = new MutationObserver(() => {
                updateToggleAria(toggleButton);
            });
            
            themeObserver.observe(document.documentElement, {
                attributes: true,
                attributeFilter: ['data-theme']
            });
        }
    }
    
    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Re-initialize after View Transitions navigation
    document.addEventListener('page-navigation-complete', init);
})();
