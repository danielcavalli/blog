/**
 * @fileoverview Blog post filtering system with animated transitions
 * 
 * Version: 2.0 - Fixed re-initialization after View Transitions
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
        // State
        const activeFilters = {
            year: '',
            month: '',
            tags: new Set()
        };
        
        let currentOrderBy = 'created'; // Default to "Published At" (created date)

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

        if (!filterToggle || !filtersPanel) {
            return;
        }

        // Note: We allow re-initialization because View Transitions replace the entire DOM
        // Old event listeners are destroyed with old DOM, so we need to rebind everything
        
        // Remove initial animations after they complete to allow filtering transitions
        // Only needed on FIRST LOAD - navigation already disables animations via transitions.js
        // Check if posts-grid has disable-animation class (added during View Transitions navigation)
        const postsGridHasDisableAnimation = postsGrid && postsGrid.classList.contains('disable-animation');
        
        // Also check if this is a navigation (not initial page load)
        // If navigated from another page, don't animate
        const isNavigation = document.referrer && new URL(document.referrer).origin === window.location.origin;
        
        if (!postsGridHasDisableAnimation && !isNavigation) {
            // This is initial page load - animations are running
            // Schedule removal after they complete
            postCards.forEach((card, index) => {
                const animationDelay = index * 0.08 + 0.1; // Match CSS animation delay
                const animationDuration = 0.7; // Match CSS animation duration
                const totalTime = (animationDelay + animationDuration) * 1000;
                
                setTimeout(() => {
                    // Use RAF to prevent flicker from style recalculation
                    requestAnimationFrame(() => {
                        card.style.animation = 'none';
                        card.style.opacity = '1'; // Explicitly set after animation
                        card.classList.add('animation-complete');
                    });
                }, totalTime);
            });
        } else {
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
         * Filter posts with three-phase choreography: dissolve → reorganize → reveal
         * 
         * Phase 1 (Dissolve):
         * - Identifies non-matching cards based on activeFilters state
         * - Applies 'filtering-out' class to trigger scale-down + fade CSS transition (350ms)
         * - Identifies cards transitioning from hidden to visible for later reveal
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
         * Phase 3 (Reveal):
         * - Newly-visible cards enter with staggered scale-up + fade-in (400ms each, 60ms stagger)
         * - Reveal begins 150ms into FLIP animation for overlap, or immediately if no FLIP
         * 
         * Side Effects:
         * - Updates clear button visibility based on activeFilters state
         * - Modifies card classes: filtering-out, filtered-out, filtering-in, filtering-in-active,
         *   flip-measuring, flip-animating
         * - Sets CSS custom properties: --flip-x, --flip-y
         * - Cleans up all animation classes and properties after completion
         * 
         * Performance Notes:
         * - Uses requestAnimationFrame for browser-driven timing
         * - Uses transitionend event instead of setTimeout for accurate phase transition
         * - Only animates cards with position changes > 1px threshold
         * 
         * @returns {void}
         */
        function filterPosts() {
            // CRITICAL: Re-query DOM on every filter call to get current elements
            // After View Transitions, the original postCards NodeList references destroyed elements
            const currentPostCards = document.querySelectorAll('.post-card');
            
            // Capture initial positions (FLIP: First)
            const initialPositions = new Map();
            currentPostCards.forEach(card => {
                const rect = card.getBoundingClientRect();
                initialPositions.set(card, { top: rect.top, left: rect.left });
            });

            const cardsToHide = [];
            const cardsToReveal = [];

            // Phase 1: Identify and start dissolving non-matching cards
            requestAnimationFrame(() => {
                currentPostCards.forEach((card, index) => {
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
                        const wasHidden = card.classList.contains('filtered-out') || card.classList.contains('filtering-out');
                        card.classList.remove('filtering-out', 'filtered-out');
                        if (wasHidden) {
                            // Card is being revealed — stage it for animated entrance
                            card.classList.add('filtering-in');
                            cardsToReveal.push(card);
                        }
                    } else {
                        if (!card.classList.contains('filtered-out')) {
                            // Card doesn't match — begin dissolve (Phase 1)
                            card.classList.add('filtering-out');
                            cardsToHide.push(card);
                        }
                    }
                });

                // Phase 2: After dissolve completes, trigger reorganization
                // Check if animations are disabled - if so, skip transition wait
                const currentPostsGrid = document.querySelector('.posts-grid');
                const animationsDisabled = currentPostsGrid && currentPostsGrid.classList.contains('disable-animation');

                if (cardsToHide.length > 0 && !animationsDisabled) {
                    // Wait for transition to complete before reorganizing
                    const handleDissolveComplete = (e) => {
                        // Only respond to opacity transitions on cards being hidden
                        if (e.propertyName !== 'opacity' || !cardsToHide.includes(e.target)) {
                            return;
                        }

                        // Remove listener to prevent multiple triggers
                        const grid = document.querySelector('.posts-grid');
                        grid.removeEventListener('transitionend', handleDissolveComplete);

                        performReorganization(cardsToReveal);
                    };

                    const grid = document.querySelector('.posts-grid');
                    grid.addEventListener('transitionend', handleDissolveComplete);
                } else {
                    // No cards to hide OR animations disabled - reorganize immediately
                    performReorganization(cardsToReveal);
                }
            });

            /**
             * Perform spatial reorganization of visible cards using FLIP technique,
             * then reveal any newly-visible cards with staggered animation.
             * 
             * @param {Element[]} revealCards - Cards to animate into view after reorganization
             * @returns {void}
             */
            function performReorganization(revealCards) {
                // Re-query current cards for reorganization
                const currentCards = document.querySelectorAll('.post-card');
                
                // Remove dissolved cards from layout
                currentCards.forEach((card, index) => {
                    if (card.classList.contains('filtering-out')) {
                        card.classList.add('filtered-out');
                    }
                });

                // Wait for layout to settle, then animate reorganization (FLIP technique)
                requestAnimationFrame(() => {
                    // Capture final positions (FLIP: Last)
                    const finalPositions = new Map();
                    currentCards.forEach(card => {
                        if (!card.classList.contains('filtered-out')) {
                            const rect = card.getBoundingClientRect();
                            finalPositions.set(card, { top: rect.top, left: rect.left });
                        }
                    });

                    // Calculate deltas and apply inverse transforms (FLIP: Invert)
                    let hasFlipAnimations = false;
                    currentCards.forEach(card => {
                        if (!card.classList.contains('filtered-out') && !card.classList.contains('filtering-in')) {
                            const initial = initialPositions.get(card);
                            const final = finalPositions.get(card);
                            
                            if (initial && final) {
                                const deltaY = initial.top - final.top;
                                const deltaX = initial.left - final.left;
                                
                                // Only animate if position actually changed
                                if (Math.abs(deltaY) > 1 || Math.abs(deltaX) > 1) {
                                    hasFlipAnimations = true;
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

                    // Reveal cards with staggered entrance after FLIP settles
                    const flipDuration = hasFlipAnimations ? 500 : 0;
                    const revealDelay = Math.min(flipDuration, 150); // Start reveal slightly into FLIP

                    if (revealCards.length > 0) {
                        setTimeout(() => {
                            revealCards.forEach((card, i) => {
                                // Stagger each card's entrance by 60ms
                                setTimeout(() => {
                                    requestAnimationFrame(() => {
                                        card.classList.add('filtering-in-active');
                                    });
                                }, i * 60);
                            });

                            // Clean up filtering-in classes after all reveals complete
                            const totalRevealTime = 400 + (revealCards.length * 60);
                            setTimeout(() => {
                                requestAnimationFrame(() => {
                                    revealCards.forEach(card => {
                                        card.classList.remove('filtering-in', 'filtering-in-active');
                                    });
                                });
                            }, totalRevealTime);
                        }, revealDelay);
                    }

                    // Clean up FLIP classes after animation completes
                    if (hasFlipAnimations) {
                        setTimeout(() => {
                            requestAnimationFrame(() => {
                                requestAnimationFrame(() => {
                                    currentCards.forEach(card => {
                                        card.classList.remove('flip-animating');
                                        card.style.removeProperty('--flip-x');
                                        card.style.removeProperty('--flip-y');
                                    });
                                });
                            });
                        }, 500); // Match motion-duration-core
                    }
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
            // CRITICAL: Re-query postsGrid and cards on every sort call
            const currentPostsGrid = document.querySelector('.posts-grid');
            if (!currentPostsGrid) return;
            
            // Capture initial positions (FLIP: First)
            const initialPositions = new Map();
            const currentPostCards = document.querySelectorAll('.post-card');
            const visibleCards = Array.from(currentPostCards).filter(card => !card.classList.contains('filtered-out'));
            
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
                currentPostsGrid.appendChild(card);
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
            clearButton.style.display = 'none';
        }
    }

    // Initialize on load
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initFilters);
    } else {
        initFilters();
    }

    // Re-initialize after View Transitions navigation
    // Listen for custom event dispatched by transitions.js after DOM swap completes
    // This replaces MutationObserver to prevent interference during transitions
    document.addEventListener('page-navigation-complete', () => {
        const filterToggle = document.getElementById('filter-toggle');
        if (filterToggle) {
            // Always re-initialize after navigation because DOM elements are replaced
            // The data-filter-initialized attribute is on the NEW DOM, not the old one
            initFilters();
        }
    });

})();

