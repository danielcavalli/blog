// Blog Post Filtering - Breathing UI with Spatial Reorganization
// Filters emerge from the page like an exhale, posts drift and fade organically

(function() {
    'use strict';
    
    // Initialize the filter system
    function initFilters() {
        // State
        const activeFilters = {
            year: '',
            month: '',
            tags: new Set()
        };

        // DOM elements
        const filterToggle = document.getElementById('filter-toggle');
        const filtersPanel = document.getElementById('filters-panel');
        const yearFilterWrapper = document.getElementById('year-filter-wrapper');
        const monthFilterWrapper = document.getElementById('month-filter-wrapper');
        const clearButton = document.getElementById('clear-filters');
        const tagButtons = document.querySelectorAll('.filter-tag');
        const postCards = document.querySelectorAll('.post-card');

        if (!filterToggle || !filtersPanel) return; // Not on index page

        // Prevent re-initialization
        if (filterToggle.hasAttribute('data-filter-initialized')) return;
        filterToggle.setAttribute('data-filter-initialized', 'true');

        // Custom dropdown functionality
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
                    
                    // Check if dropdown will overflow the filters block
                    // Use actual DOM measurements instead of magic numbers
                    requestAnimationFrame(() => {
                        if (filtersPanel && options) {
                            const filtersRect = filtersPanel.getBoundingClientRect();
                            const optionsRect = options.getBoundingClientRect();
                            
                            // Calculate actual overflow (dropdown bottom - filters bottom)
                            const actualOverflow = optionsRect.bottom - filtersRect.bottom;
                            
                            // Only nudge if dropdown extends beyond filters boundary
                            if (actualOverflow > 0) {
                                filtersPanel.classList.add('dropdown-active');
                            }
                        }
                    });
                } else {
                    // Check if any dropdowns remain open
                    setTimeout(() => {
                        const anyOpen = document.querySelector('.custom-select.open');
                        if (!anyOpen && filtersPanel) {
                            filtersPanel.classList.remove('dropdown-active');
                        }
                    }, 50);
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
                    setTimeout(() => {
                        const anyOpen = document.querySelector('.custom-select.open');
                        if (!anyOpen && filtersPanel) {
                            filtersPanel.classList.remove('dropdown-active');
                        }
                    }, 50);
                    
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

        // Filter posts with two-phase choreography: dissolve, then reorganize
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
                postCards.forEach((card) => {
                    const cardYear = card.dataset.year;
                    const cardMonth = card.dataset.month;
                    const cardTags = card.dataset.tags ? card.dataset.tags.split(',') : [];

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
                    setTimeout(() => {
                        postCards.forEach(card => {
                            card.classList.remove('flip-animating');
                            card.style.removeProperty('--flip-x');
                            card.style.removeProperty('--flip-y');
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

        // Tag filter toggle
        tagButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tag = e.target.dataset.tag;
                
                if (activeFilters.tags.has(tag)) {
                    activeFilters.tags.delete(tag);
                    e.target.classList.remove('active');
                } else {
                    activeFilters.tags.add(tag);
                    e.target.classList.add('active');
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

    // Re-initialize after navigation (View Transitions API compatibility)
    // Create a MutationObserver to detect when the filter toggle is back in the DOM
    const observer = new MutationObserver((mutations) => {
        // Check if filter toggle exists and needs initialization
        const filterToggle = document.getElementById('filter-toggle');
        if (filterToggle && !filterToggle.hasAttribute('data-filter-initialized')) {
            initFilters();
        }
    });
    
    // Start observing
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

})();

