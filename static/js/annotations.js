/**
 * @fileoverview Reader-facing deep-link affordances for post annotations.
 *
 * Features:
 * - Hover-only section-link affordances for headings
 * - Selection-triggered share nudge for linkable passage blocks
 * - Persistent target highlighting for canonical #section and #block-### links
 * - Calm arrival-state animation that complements the transition system
 */

(function() {
    'use strict';

    const ARRIVAL_CLASS = 'is-highlight-arriving';
    const ACTIVE_BLOCK_CLASS = 'is-highlight-active';
    const ACTIVE_HEADING_CLASS = 'is-heading-highlight-active';
    const HEADING_SELECTOR = '.post-body .section-heading[id]';
    const HEADING_ANCHOR_SELECTOR = '.post-body .heading-anchor';
    const BLOCK_SELECTOR = '.post-body .linkable-block[id]';
    const BLOCK_SHAREABLE_TAGS = new Set(['P', 'LI', 'BLOCKQUOTE']);
    const COPY_STATE_MS = 1800;
    const NUDGE_MARGIN = 14;
    let arrivalTimeoutId = null;
    let selectionNudge = null;
    let activeSelectionBlockId = '';

    function labels() {
        const body = document.body;
        return {
            copySection: body?.dataset.copySectionLink || 'Copy section link',
            copyPassage: body?.dataset.copyPassageLink || 'Copy passage link',
            copied: body?.dataset.linkCopied || 'Link copied',
        };
    }

    function baseUrlForTarget(targetId) {
        const next = new URL(location.href);
        next.hash = targetId ? `#${targetId}` : '';
        return next.toString();
    }

    async function copyText(text) {
        if (navigator.clipboard?.writeText) {
            await navigator.clipboard.writeText(text);
            return;
        }

        const fallback = document.createElement('textarea');
        fallback.value = text;
        fallback.setAttribute('readonly', '');
        fallback.style.position = 'absolute';
        fallback.style.left = '-9999px';
        document.body.appendChild(fallback);
        fallback.select();
        document.execCommand('copy');
        fallback.remove();
    }

    function setCopiedState(control) {
        if (!control) return;
        control.dataset.copyState = 'copied';
        window.setTimeout(() => {
            if (control.dataset.copyState === 'copied') {
                control.dataset.copyState = 'ready';
            }
        }, COPY_STATE_MS);
    }

    function clearHighlightState() {
        document
            .querySelectorAll(`.${ACTIVE_BLOCK_CLASS}, .${ACTIVE_HEADING_CLASS}, .${ARRIVAL_CLASS}`)
            .forEach((element) => {
                element.classList.remove(ACTIVE_BLOCK_CLASS, ACTIVE_HEADING_CLASS, ARRIVAL_CLASS);
            });
    }

    function activateTargetById(targetId, { animate = true } = {}) {
        clearHighlightState();

        if (!targetId) return;
        const target = document.getElementById(targetId);
        if (!target) return;

        if (target.classList.contains('linkable-block')) {
            target.classList.add(ACTIVE_BLOCK_CLASS);
        } else if (target.classList.contains('section-heading')) {
            target.classList.add(ACTIVE_HEADING_CLASS);
        } else {
            return;
        }

        if (!animate) return;
        target.classList.add(ARRIVAL_CLASS);
        if (arrivalTimeoutId) {
            window.clearTimeout(arrivalTimeoutId);
        }
        arrivalTimeoutId = window.setTimeout(() => {
            target.classList.remove(ARRIVAL_CLASS);
        }, 1400);
    }

    function syncTargetFromLocation({ animate = true } = {}) {
        const targetId = decodeURIComponent(location.hash.replace(/^#/, ''));
        activateTargetById(targetId, { animate });
    }

    function updateLocationHash(targetId) {
        const nextUrl = new URL(location.href);
        nextUrl.hash = `#${targetId}`;
        history.replaceState(history.state, '', nextUrl.toString());
    }

    async function copyTargetLink(targetId, control) {
        const url = baseUrlForTarget(targetId);
        await copyText(url);
        updateLocationHash(targetId);
        activateTargetById(targetId, { animate: true });
        setCopiedState(control);
    }

    function enhanceHeadingAnchor(anchor) {
        if (!anchor || anchor.dataset.annotationReady === 'true') return;
        const ui = labels();
        const heading = anchor.closest('.section-heading');
        if (!heading?.id) return;

        anchor.dataset.annotationReady = 'true';
        anchor.dataset.copyState = 'ready';
        anchor.dataset.shareLabel = ui.copySection;
        anchor.dataset.copiedLabel = ui.copied;
        anchor.setAttribute('aria-label', ui.copySection);
        anchor.setAttribute('title', ui.copySection);

        anchor.addEventListener('click', async (event) => {
            event.preventDefault();
            try {
                await copyTargetLink(heading.id, anchor);
            } catch (error) {
                console.error('Failed to copy section link:', error);
            }
        });
    }

    function enhanceHeading(heading) {
        if (!heading || heading.dataset.annotationReady === 'true') return;
        heading.dataset.annotationReady = 'true';
        heading.classList.add('is-linkable-heading');
    }

    function ensureSelectionNudge() {
        if (selectionNudge) return selectionNudge;

        const ui = labels();
        selectionNudge = document.createElement('button');
        selectionNudge.type = 'button';
        selectionNudge.className = 'selection-share-nudge';
        selectionNudge.hidden = true;
        selectionNudge.dataset.copyState = 'ready';
        selectionNudge.dataset.shareLabel = ui.copyPassage;
        selectionNudge.dataset.copiedLabel = ui.copied;
        selectionNudge.setAttribute('aria-label', ui.copyPassage);
        selectionNudge.setAttribute('title', ui.copyPassage);
        selectionNudge.innerHTML = `
            <span class="selection-share-icon" aria-hidden="true"></span>
            <span class="sr-only">${ui.copyPassage}</span>
        `;

        selectionNudge.addEventListener('click', async (event) => {
            event.preventDefault();
            if (!activeSelectionBlockId) return;
            try {
                await copyTargetLink(activeSelectionBlockId, selectionNudge);
                hideSelectionNudge();
                const selection = window.getSelection();
                if (selection) {
                    selection.removeAllRanges();
                }
            } catch (error) {
                console.error('Failed to copy passage link:', error);
            }
        });

        document.body.appendChild(selectionNudge);
        return selectionNudge;
    }

    function hideSelectionNudge() {
        if (!selectionNudge) return;
        selectionNudge.hidden = true;
        selectionNudge.classList.remove('is-visible');
        selectionNudge.style.left = '';
        selectionNudge.style.top = '';
        activeSelectionBlockId = '';
    }

    function closestLinkableBlock(node) {
        if (!node) return null;
        const base = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
        return base?.closest?.('.post-body .linkable-block[id]') || null;
    }

    function currentSelectionBlock() {
        const selection = window.getSelection();
        if (!selection || selection.isCollapsed) return null;
        if (!selection.toString().trim()) return null;
        if (selection.rangeCount === 0) return null;

        const startBlock = closestLinkableBlock(selection.anchorNode);
        const endBlock = closestLinkableBlock(selection.focusNode);
        if (!startBlock || !endBlock || startBlock !== endBlock) return null;
        if (!BLOCK_SHAREABLE_TAGS.has(startBlock.tagName)) return null;
        return startBlock;
    }

    function selectionRect(selection) {
        if (!selection || selection.rangeCount === 0) return null;
        const range = selection.getRangeAt(0);
        const rect = range.getBoundingClientRect();
        if (rect.width || rect.height) {
            return rect;
        }

        const rects = range.getClientRects();
        return rects.length > 0 ? rects[0] : null;
    }

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function showSelectionNudge(block, rect) {
        const nudge = ensureSelectionNudge();
        const nudgeWidth = 40;
        const nudgeHeight = 40;
        const top = clamp(
            rect.top - nudgeHeight - NUDGE_MARGIN,
            12,
            window.innerHeight - nudgeHeight - 12
        );
        const left = clamp(
            rect.left + rect.width - (nudgeWidth * 0.5),
            12,
            window.innerWidth - nudgeWidth - 12
        );

        activeSelectionBlockId = block.id;
        nudge.hidden = false;
        nudge.style.top = `${top}px`;
        nudge.style.left = `${left}px`;
        requestAnimationFrame(() => {
            nudge.classList.add('is-visible');
        });
    }

    function updateSelectionNudge() {
        const selection = window.getSelection();
        const block = currentSelectionBlock();
        if (!selection || !block) {
            hideSelectionNudge();
            return;
        }

        const rect = selectionRect(selection);
        if (!rect) {
            hideSelectionNudge();
            return;
        }

        showSelectionNudge(block, rect);
    }

    function enhanceLinkableBlock(block) {
        if (!block || block.dataset.annotationReady === 'true') return;
        block.dataset.annotationReady = 'true';
    }

    function initializeAnnotations() {
        document.querySelectorAll(HEADING_ANCHOR_SELECTOR).forEach(enhanceHeadingAnchor);
        document.querySelectorAll(HEADING_SELECTOR).forEach(enhanceHeading);
        document.querySelectorAll(BLOCK_SELECTOR).forEach(enhanceLinkableBlock);
        ensureSelectionNudge();
    }

    document.addEventListener('DOMContentLoaded', () => {
        initializeAnnotations();
        syncTargetFromLocation({ animate: !!location.hash });
    });

    document.addEventListener('page-navigation-complete', () => {
        initializeAnnotations();
        hideSelectionNudge();
        syncTargetFromLocation({ animate: !!location.hash });
    });

    document.addEventListener('selectionchange', () => {
        updateSelectionNudge();
    });

    document.addEventListener('pointerdown', (event) => {
        if (event.target.closest('.selection-share-nudge')) return;
        hideSelectionNudge();
    });

    window.addEventListener('hashchange', () => {
        hideSelectionNudge();
        syncTargetFromLocation({ animate: true });
    });

    window.addEventListener('scroll', () => {
        if (!selectionNudge || selectionNudge.hidden) return;
        updateSelectionNudge();
    }, { passive: true });

    window.addEventListener('resize', () => {
        if (!selectionNudge || selectionNudge.hidden) return;
        updateSelectionNudge();
    });
})();
