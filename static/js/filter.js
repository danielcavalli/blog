/**
 * @fileoverview Blog post filtering system with animated transitions
 * 
 * Features:
 * - Breathing filter panel (expands/contracts with organic motion)
 * - Custom dropdown selectors for year and month filtering
 * - Tag button filtering with multi-select
 * - Two-phase animation choreography: dissolve → reorganize
 * - FLIP technique for smooth spatial reorganization
 * - Order toggle between "Last Updated" and "Published At"
 * - Clear filters button with conditional visibility
 * - View Transitions API compatibility via MutationObserver
 * 
 * Animation Architecture:
 * - Phase 1 (Dissolve): Non-matching cards fade out with `filtering-out` class
 * - Phase 2 (Reorganize): Remaining cards animate to new positions using FLIP
 * - FLIP steps: First (capture initial), Last (capture final), Invert (set transform), Play (animate to 0)
 * 
 * Timing Notes:
 * - Dissolve duration: 400ms (matches CSS transition)
 * - Reorganization duration: 500ms (motion-duration-core)
 * - Order toggle morph: 300ms (motion-duration-quick)
 * - Initial card animations disabled after 0.7s + stagger delay
 * 
 * Critical Initialization Order:
 * 1. Check for filter toggle presence (guards against non-index pages)
 * 2. Prevent duplicate initialization via `data-filter-initialized` attribute
 * 3. Remove initial card animations after they complete to enable filtering transitions
 * 4. Setup custom dropdowns with overflow detection
 * 5. Attach event listeners for filters, tags, clear button
 * 6. Start MutationObserver for View Transitions API navigation
 * 
 * DOM Requirements:
 * - #filter-toggle: Button to expand/collapse filter panel
 * - #filters-panel: Container for all filter controls
 * - #year-filter-wrapper, #month-filter-wrapper: Custom dropdown containers
 * - #order-toggle: Button to toggle sort order with data-label-updated and data-label-created attributes
 * - #clear-filters: Button to reset all filters
 * - .filter-tag buttons: Tag filter buttons with data-tag attribute
 * - .post-card elements: Post cards with data-year, data-month, data-tags, data-created, data-updated attributes
 * - .posts-grid: Container for post cards
 * 
 * Browser Requirements:
 * - Chromium only (uses native transitions, CSS custom properties)
 * - Requires requestAnimationFrame and MutationObserver support
 */

(function() {
    'use strict';
    
    /**
     * Initialize the filter system with state, DOM references, and event handlers
     * 
     * Sets up:
     * - Filter state tracking (year, month, tags, order)
     * - DOM element references
     * - Custom dropdown functionality with overflow detection
     * - Filter panel toggle (breathing motion)
     * - Post filtering with two-phase choreography
     * - Order toggle with morphing text
     * - Tag filter buttons
     * - Clear filters button
     * 
     * Guards:
     * - Returns early if filter toggle not found (not on index page)
     * - Prevents re-initialization via data-filter-initialized attribute
     * 
     * Post-Initialization:
     * - Removes initial card animations after they complete (0.7s + stagger)
     * - Hides clear button initially
     * 
     * @returns {void}
     */
    function initFilters() {
        console.log('[FILTER] initFilters() called');
        
        // State
        const activeFilters = {
            year: '',
            month: '',
            tags: new Set()
        };
        
        let currentOrderBy = 'updated'; // Default to "Updated"

        // DOM elements
        const filterToggle = document.getElementById('filter-toggle');
        const filtersPanel = document.getElementById('filters-panel');
        const yearFilterWrapper = document.getElementById('year-filter-wrapper');
        const monthFilterWrapper = document.getElementById('month-filter-wrapper');
        const orderToggle = document.getElementById('order-toggle');
        const clearButton = document.getElementById('clear-filters');
        const tagButtons = document.querySelectorAll('.filter-tag');
        const postCards = document.querySelectorAll('.post-card');
        const postsGrid = document.querySelector('.posts-grid');

        console.log('[FILTER] Found', postCards.length, 'post cards');
        console.log('[FILTER] Posts grid:', postsGrid);

        if (!filterToggle || !filtersPanel) {
            console.log('[FILTER] Not on index page, returning');
            return;
        }

        // Prevent re-initialization
        if (filterToggle.hasAttribute('data-filter-initialized')) {
            console.log('[FILTER] Already initialized, returning');
            return;
        }
        filterToggle.setAttribute('data-filter-initialized', 'true');
        console.log('[FILTER] Marked as initialized');
        
        // Remove initial animations after they complete to allow filtering transitions
        // Only needed on FIRST LOAD - navigation already disables animations via transitions.js
        // Check if posts-grid has disable-animation class (added during View Transitions navigation)
        const postsGridHasDisableAnimation = postsGrid && postsGrid.classList.contains('disable-animation');
        
        // Also check if this is a navigation (not initial page load)
        // If navigated from another page, don't animate
        const isNavigation = document.referrer && new URL(document.referrer).origin === window.location.origin;
        
        console.log('[FILTER] Posts grid has disable-animation:', postsGridHasDisableAnimation);
        console.log('[FILTER] Is navigation (has same-origin referrer):', isNavigation);
        
        if (!postsGridHasDisableAnimation && !isNavigation) {
            console.log('[FILTER] Initial page load - scheduling animation removal for', postCards.length, 'cards');
            // This is initial page load - animations are running
            // Schedule removal after they complete
            postCards.forEach((card, index) => {
                const animationDelay = index * 0.08 + 0.1; // Match CSS animation delay
                const animationDuration = 0.7; // Match CSS animation duration
                const totalTime = (animationDelay + animationDuration) * 1000;
                
                console.log(`[FILTER] Card ${index}: scheduling animation removal in ${totalTime}ms`);
                
                setTimeout(() => {
                    console.log(`[FILTER] Card ${index}: removing animation (RAF)`);
                    // Use RAF to prevent flicker from style recalculation
                    requestAnimationFrame(() => {
                        card.style.animation = 'none';
                        card.style.opacity = '1'; // Explicitly set after animation
                        card.classList.add('animation-complete');
                        console.log(`[FILTER] Card ${index}: animation removed, classes:`, card.classList.toString());
                    });
                }, totalTime);
            });
        } else {
            console.log('[FILTER] Navigation or disable-animation present - adding disable-animation and skipping animations');
            if (postsGrid && !postsGridHasDisableAnimation) {
                postsGrid.classList.add('disable-animation');
            }
            // Immediately mark cards as complete
            postCards.forEach(card => {
                card.style.animation = 'none';
                card.style.opacity = '1';
                card.classList.add('animation-complete');
            });
        }

        /**
         * Setup custom dropdown functionality for year/month filters
         * 
         * Implements:
         * - Click outside to close all dropdowns
         * - Option selection updates trigger text and closes dropdown
         * - Overflow detection: nudges filters panel downward if dropdown extends beyond panel boundary
         * - Auto-contracts panel when all dropdowns close
         * 
         * @param {HTMLElement|null} wrapper - The .custom-select container element
         * @param {Function} onSelect - Callback invoked with selected value when option clicked
         * @returns {void}
         */
        function setupCustomSelect(wrapper, onSelect) {
            if (!wrapper) return;
            
            const trigger = wrapper.querySelector('.select-trigger');
            const options = wrapper.querySelector('.select-options');
            const optionElements = wrapper.querySelectorAll('.select-option');
            const label = trigger.querySelector('.select-label');
            
            // Toggle dropdown
            trigger.addEventListener('click', (e) => {
                e.stopPropagation();
                const isOpen = wrapper.classList.contains('open');
                
                // Close all other dropdowns
                document.querySelectorAll('.custom-select.open').forEach(select => {
                    select.classList.remove('open');
                });
                
                if (!isOpen) {
                    wrapper.classList.add('open');
                    
                    // Measure potential overflow immediately
                    // Use requestAnimationFrame to ensure DOM update has happened
                    requestAnimationFrame(() => {
                        if (filtersPanel && options) {
                            // Get the actual content height of the dropdown
                            const optionsScrollHeight = options.scrollHeight;
                            const filtersRect = filtersPanel.getBoundingClientRect();
                            const triggerRect = trigger.getBoundingClientRect();
                            
                            // Calculate where dropdown bottom will be (trigger bottom + dropdown height)
                            const dropdownBottom = triggerRect.bottom + optionsScrollHeight;
                            const actualOverflow = dropdownBottom - filtersRect.bottom;
                            
                            // Only nudge if dropdown extends beyond filters boundary
                            if (actualOverflow > 0) {
                                filtersPanel.classList.add('dropdown-active');
                            }
                        }
                    });
                } else {
                    // Check if any dropdowns remain open
                    // Use RAF to avoid triggering style recalc during animation
                    requestAnimationFrame(() => {
                        const anyOpen = document.querySelector('.custom-select.open');
                        if (!anyOpen && filtersPanel) {
                            filtersPanel.classList.remove('dropdown-active');
                        }
                    });
                }
            });
            
            // Select option
            optionElements.forEach(option => {
                option.addEventListener('click', (e) => {
                    e.stopPropagation();
                    const value = option.dataset.value;
                    const text = option.textContent;
                    
                    // Update trigger
                    trigger.dataset.value = value;
                    label.textContent = text;
                    
                    // Update selected state
                    optionElements.forEach(opt => opt.classList.remove('selected'));
                    option.classList.add('selected');
                    
                    // Close dropdown
                    wrapper.classList.remove('open');
                    
                    // Contract filters block when dropdown closes
                    // Use RAF to avoid triggering style recalc during animation
                    requestAnimationFrame(() => {
                        const anyOpen = document.querySelector('.custom-select.open');
                        if (!anyOpen && filtersPanel) {
                            filtersPanel.classList.remove('dropdown-active');
                        }
                    });
                    
                    // Callback
                    if (onSelect) onSelect(value);
                });
            });
        }
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', () => {
            document.querySelectorAll('.custom-select.open').forEach(select => {
                select.classList.remove('open');
            });
            // Contract filters block when all dropdowns close
            if (filtersPanel) {
                filtersPanel.classList.remove('dropdown-active');
            }
        });

        // Toggle filter panel - breathing motion
        filterToggle.addEventListener('click', () => {
            const isExpanded = filtersPanel.classList.contains('expanded');
            
            if (isExpanded) {
                // Inhale - contract
                filtersPanel.classList.remove('expanded');
                filterToggle.classList.remove('active');
            } else {
                // Exhale - expand
                filtersPanel.classList.add('expanded');
                filterToggle.classList.add('active');
            }
        });

        /**
         * Filter posts with two-phase choreography: dissolve, then reorganize
         * 
         * Phase 1 (Dissolve):
         * - Identifies non-matching cards based on activeFilters state
         * - Applies 'filtering-out' class to trigger fade-out CSS transition (400ms)
         * - Listens for transitionend event to detect when dissolve completes
         * 
         * Phase 2 (Reorganize):
         * - Applies 'filtered-out' class to remove dissolved cards from layout
         * - Uses FLIP technique to animate remaining cards to new positions:
         *   1. First: Capture initial positions before layout change
         *   2. Last: Capture final positions after layout change
         *   3. Invert: Apply inverse transform (--flip-x, --flip-y) to freeze cards at initial positions
         *   4. Play: Animate transforms to (0, 0) to slide cards to final positions (500ms)
         * 
         * Side Effects:
         * - Updates clear button visibility based on activeFilters state
         * - Modifies card classes: filtering-out, filtered-out, flip-measuring, flip-animating
         * - Sets CSS custom properties: --flip-x, --flip-y
         * - Cleans up FLIP classes and properties after animation completes
         * 
         * Performance Notes:
         * - Uses requestAnimationFrame for browser-driven timing
         * - Uses transitionend event instead of setTimeout for accurate phase transition
         * - Only animates cards with position changes > 1px threshold
         * 
         * @returns {void}
         */
        function filterPosts() {
            // Capture initial positions (FLIP: First)
            const initialPositions = new Map();
            postCards.forEach(card => {
                const rect = card.getBoundingClientRect();
                initialPositions.set(card, { top: rect.top, left: rect.left });
            });

            const cardsToHide = [];

            // Phase 1: Identify and start dissolving non-matching cards
            requestAnimationFrame(() => {
                postCards.forEach((card, index) => {
                    const cardYear = card.dataset.year;
                    const cardMonth = card.dataset.month;
                    const cardTags = card.dataset.tags ? card.dataset.tags.split(',').map(t => t.trim()) : [];

                    // Check if card matches all active filters
                    const yearMatch = !activeFilters.year || cardYear === activeFilters.year;
                    const monthMatch = !activeFilters.month || cardMonth === activeFilters.month;
                    const tagsMatch = activeFilters.tags.size === 0 || 
                        cardTags.some(tag => activeFilters.tags.has(tag));

                    const shouldShow = yearMatch && monthMatch && tagsMatch;

                    if (shouldShow) {
                        // Card should be visible - ensure it's not in filtering state
                        card.classList.remove('filtering-out', 'filtered-out');
                    } else {
                        // Card doesn't match - begin dissolve (Phase 1)
                        card.classList.add('filtering-out');
                        cardsToHide.push(card);
                    }
                });

                // Phase 2: After dissolve completes, trigger reorganization
                // Use transitionend event instead of setTimeout for browser-driven timing
                if (cardsToHide.length > 0) {
                    const handleDissolveComplete = (e) => {
                        // Only respond to opacity transitions on cards being hidden
                        if (e.propertyName !== 'opacity' || !cardsToHide.includes(e.target)) {
                            return;
                        }

                        // Remove listener to prevent multiple triggers
                        const grid = document.querySelector('.posts-grid');
                        grid.removeEventListener('transitionend', handleDissolveComplete);

                        performReorganization();
                    };

                    const grid = document.querySelector('.posts-grid');
                    grid.addEventListener('transitionend', handleDissolveComplete);
                } else {
                    // No cards to hide, but still reorganize visible cards
                    performReorganization();
                }
            });

            /**
             * Perform spatial reorganization of visible cards using FLIP technique
             * 
             * Called after Phase 1 dissolve completes. Applies 'filtered-out' class to dissolved cards,
             * waits for layout to settle, then animates remaining cards to their new grid positions.
             * 
             * FLIP Steps:
             * 1. Last: Capture final positions after layout change
             * 2. Invert: Calculate deltas and apply inverse transforms to freeze cards at initial positions
             * 3. Play: Animate transforms to (0, 0) over 500ms to slide cards to final positions
             * 
             * Side Effects:
             * - Adds 'filtered-out' class to cards with 'filtering-out' class
             * - Adds 'flip-measuring' class during transform application (disables transitions)
             * - Adds 'flip-animating' class during animation (enables transitions)
             * - Sets --flip-x and --flip-y custom properties
             * - Cleans up classes and properties after 500ms
             * 
             * @returns {void}
             */
            function performReorganization() {
                // Remove dissolved cards from layout
                postCards.forEach((card) => {
                    if (card.classList.contains('filtering-out')) {
                        card.classList.add('filtered-out');
                    }
                });

                // Wait for layout to settle, then animate reorganization (FLIP technique)
                requestAnimationFrame(() => {
                    // Capture final positions (FLIP: Last)
                    const finalPositions = new Map();
                    postCards.forEach(card => {
                        if (!card.classList.contains('filtered-out')) {
                            const rect = card.getBoundingClientRect();
                            finalPositions.set(card, { top: rect.top, left: rect.left });
                        }
                    });

                    // Calculate deltas and apply inverse transforms (FLIP: Invert)
                    postCards.forEach(card => {
                        if (!card.classList.contains('filtered-out')) {
                            const initial = initialPositions.get(card);
                            const final = finalPositions.get(card);
                            
                            if (initial && final) {
                                const deltaY = initial.top - final.top;
                                const deltaX = initial.left - final.left;
                                
                                // Only animate if position actually changed
                                if (Math.abs(deltaY) > 1 || Math.abs(deltaX) > 1) {
                                    // Freeze transitions to set initial position (FLIP: Invert)
                                    card.classList.add('flip-measuring');
                                    card.style.setProperty('--flip-x', `${deltaX}px`);
                                    card.style.setProperty('--flip-y', `${deltaY}px`);
                                    
                                    // Force reflow to apply instant position
                                    card.offsetHeight;
                                    
                                    // Enable animation and slide to natural position (FLIP: Play)
                                    card.classList.remove('flip-measuring');
                                    card.classList.add('flip-animating');
                                    
                                    // Reset custom properties to trigger animation to (0, 0)
                                    requestAnimationFrame(() => {
                                        card.style.setProperty('--flip-x', '0');
                                        card.style.setProperty('--flip-y', '0');
                                    });
                                }
                            }
                        }
                    });

                    // Clean up FLIP classes after animation completes
                    // Use double RAF + class removal strategy to prevent flicker
                    setTimeout(() => {
                        requestAnimationFrame(() => {
                            requestAnimationFrame(() => {
                                postCards.forEach(card => {
                                    // Remove the class first to prevent CSS transitions from firing
                                    card.classList.remove('flip-animating');
                                    // Then clean up custom properties and inline styles
                                    // These no longer trigger transitions since flip-animating is removed
                                    card.style.removeProperty('--flip-x');
                                    card.style.removeProperty('--flip-y');
                                });
                            });
                        });
                    }, 500); // Match motion-duration-core
                });
            }

            // Update clear button visibility
            const hasActiveFilters = activeFilters.year || activeFilters.month || activeFilters.tags.size > 0;
            if (clearButton) {
                clearButton.style.display = hasActiveFilters ? 'inline-block' : 'none';
            }
        }

        // Setup custom dropdowns
        setupCustomSelect(yearFilterWrapper, (value) => {
            activeFilters.year = value;
            filterPosts();
        });
        
        setupCustomSelect(monthFilterWrapper, (value) => {
            activeFilters.month = value;
            filterPosts();
        });
        
        // Order toggle button with morphing text
        if (orderToggle) {
            const textSpan = orderToggle.querySelector('.order-toggle-text');
            
            orderToggle.addEventListener('click', () => {
                // Toggle order
                currentOrderBy = currentOrderBy === 'updated' ? 'created' : 'updated';
                
                // Morph text (fade out, change, fade in)
                orderToggle.classList.add('morphing');
                
                // Get labels from data attributes (for i18n support)
                const labelUpdated = orderToggle.dataset.labelUpdated || 'Last Updated';
                const labelCreated = orderToggle.dataset.labelCreated || 'Published At';
                
                // Use RAF to prevent flicker from DOM updates during opacity transition
                setTimeout(() => {
                    requestAnimationFrame(() => {
                        textSpan.textContent = currentOrderBy === 'updated' ? labelUpdated : labelCreated;
                        orderToggle.dataset.order = currentOrderBy;
                        orderToggle.classList.remove('morphing');
                        
                        // Sort posts with new order
                        sortPosts();
                    });
                }, 300); // Match motion-duration-quick
            });
        }
        
        /**
         * Sort posts by created or updated date with FLIP animation
         * 
         * Sorts visible cards by currentOrderBy ('created' or 'updated'), reorders them in the DOM,
         * then animates the spatial reorganization using FLIP technique.
         * 
         * FLIP Steps:
         * 1. First: Capture initial positions before DOM reorder
         * 2. DOM Reorder: Sort cards and appendChild to postsGrid (newest first)
         * 3. Last: Capture final positions after DOM reorder
         * 4. Invert: Calculate deltas and apply inverse transforms
         * 5. Play: Animate transforms to (0, 0) over 500ms
         * 
         * Sort Order:
         * - 'created': data-created timestamp (descending)
         * - 'updated': data-updated timestamp (descending)
         * 
         * Side Effects:
         * - Reorders DOM elements via appendChild
         * - Adds/removes flip-measuring and flip-animating classes
         * - Sets/removes --flip-x and --flip-y custom properties
         * - Only animates cards with position changes > 1px
         * 
         * @returns {void}
         */
        function sortPosts() {
            if (!postsGrid) return;
            
            // Capture initial positions (FLIP: First)
            const initialPositions = new Map();
            const visibleCards = Array.from(postCards).filter(card => !card.classList.contains('filtered-out'));
            
            visibleCards.forEach(card => {
                const rect = card.getBoundingClientRect();
                initialPositions.set(card, { top: rect.top, left: rect.left });
            });
            
            // Sort cards by selected order
            const sortedCards = visibleCards.sort((a, b) => {
                const aDate = new Date(currentOrderBy === 'created' ? a.dataset.created : a.dataset.updated).getTime();
                const bDate = new Date(currentOrderBy === 'created' ? b.dataset.created : b.dataset.updated).getTime();
                return bDate - aDate; // Newest first
            });
            
            // Reorder DOM
            sortedCards.forEach(card => {
                postsGrid.appendChild(card);
            });
            
            // Capture final positions after reorder (FLIP: Last)
            requestAnimationFrame(() => {
                const finalPositions = new Map();
                visibleCards.forEach(card => {
                    const rect = card.getBoundingClientRect();
                    finalPositions.set(card, { top: rect.top, left: rect.left });
                });
                
                // Animate the movement (FLIP: Invert & Play)
                visibleCards.forEach(card => {
                    const initial = initialPositions.get(card);
                    const final = finalPositions.get(card);
                    
                    if (initial && final) {
                        const deltaY = initial.top - final.top;
                        const deltaX = initial.left - final.left;
                        
                        // Only animate if position changed
                        if (Math.abs(deltaY) > 1 || Math.abs(deltaX) > 1) {
                            // FLIP: Invert - Set initial transform to freeze card at old position
                            card.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
                            card.style.transition = 'none';
                            
                            // Force reflow to apply the transform
                            card.offsetHeight;
                            
                            // FLIP: Play - Enable transition and let card animate to natural position
                            card.style.transition = `transform var(--motion-duration-core) var(--motion-easing)`;
                            card.style.willChange = 'transform';
                            
                            requestAnimationFrame(() => {
                                card.style.transform = 'translate(0, 0)';
                            });
                        }
                    }
                });
                
                // Clean up after animation
                // Use double RAF + batched removals to prevent flicker
                setTimeout(() => {
                    requestAnimationFrame(() => {
                        requestAnimationFrame(() => {
                            visibleCards.forEach(card => {
                                // Remove all inline styles at once to minimize repaints
                                card.style.transform = '';
                                card.style.transition = '';
                                card.style.willChange = '';
                            });
                        });
                    });
                }, 500); // Match motion-duration-core
            });
        }

        // Tag filter toggle
        tagButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                // Use currentTarget to always get the button element, not child elements
                const tag = e.currentTarget.dataset.tag;
                
                if (!tag) {
                    return;
                }
                
                if (activeFilters.tags.has(tag)) {
                    activeFilters.tags.delete(tag);
                    e.currentTarget.classList.remove('active');
                } else {
                    activeFilters.tags.add(tag);
                    e.currentTarget.classList.add('active');
                }
                
                filterPosts();
            });
        });

        // Clear all filters
        if (clearButton) {
            clearButton.addEventListener('click', () => {
                // Reset state
                activeFilters.year = '';
                activeFilters.month = '';
                activeFilters.tags.clear();

                // Reset custom dropdowns
                if (yearFilterWrapper) {
                    const trigger = yearFilterWrapper.querySelector('.select-trigger');
                    const label = trigger.querySelector('.select-label');
                    const firstOption = yearFilterWrapper.querySelector('.select-option');
                    trigger.dataset.value = '';
                    label.textContent = firstOption.textContent;
                    yearFilterWrapper.querySelectorAll('.select-option').forEach(opt => opt.classList.remove('selected'));
                    firstOption.classList.add('selected');
                }
                
                if (monthFilterWrapper) {
                    const trigger = monthFilterWrapper.querySelector('.select-trigger');
                    const label = trigger.querySelector('.select-label');
                    const firstOption = monthFilterWrapper.querySelector('.select-option');
                    trigger.dataset.value = '';
                    label.textContent = firstOption.textContent;
                    monthFilterWrapper.querySelectorAll('.select-option').forEach(opt => opt.classList.remove('selected'));
                    firstOption.classList.add('selected');
                }
                
                tagButtons.forEach(btn => btn.classList.remove('active'));

                // Show all posts with gentle reveal
                filterPosts();
            });
        }

        // Cards already have transitions defined in CSS - no inline styles needed

        // Hide clear button initially
        if (clearButton) {
            console.log('[FILTER] Hiding clear button');
            clearButton.style.display = 'none';
        }
        
        console.log('[FILTER] initFilters() complete');
    }

    // Initialize on load
    console.log('[FILTER] Document ready state:', document.readyState);
    if (document.readyState === 'loading') {
        console.log('[FILTER] Waiting for DOMContentLoaded');
        document.addEventListener('DOMContentLoaded', () => {
            console.log('[FILTER] DOMContentLoaded fired');
            initFilters();
        });
    } else {
        console.log('[FILTER] Document already loaded, calling initFilters immediately');
        initFilters();
    }

    // Re-initialize after View Transitions navigation
    // Listen for custom event dispatched by transitions.js after DOM swap completes
    // This replaces MutationObserver to prevent interference during transitions
    document.addEventListener('page-navigation-complete', () => {
        console.log('[FILTER] page-navigation-complete event received');
        const filterToggle = document.getElementById('filter-toggle');
        if (filterToggle && !filterToggle.hasAttribute('data-filter-initialized')) {
            console.log('[FILTER] Filter toggle exists and not initialized, calling initFilters');
            initFilters();
        } else {
            console.log('[FILTER] Filter toggle already initialized or missing');
        }
    });

})();

