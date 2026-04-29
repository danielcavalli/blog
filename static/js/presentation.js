/**
 * @fileoverview Blog-native presentation controls.
 *
 * The script is safe to load sitewide. It does nothing unless the current DOM
 * contains .presentation-page, and it can initialize again after SPA swaps.
 */

(function() {
    'use strict';

    const PAGE_SELECTOR = '.presentation-page';
    const SLIDE_SELECTOR = '.presentation-slide[data-slide-id]';
    const ACTIVE_CLASS = 'is-active';

    const state = {
        page: null,
        slides: [],
        currentIndex: 0,
        listenersReady: false,
    };

    function currentPage() {
        return document.querySelector(PAGE_SELECTOR);
    }

    function slideIdFromHash() {
        if (!location.hash) return '';
        try {
            return decodeURIComponent(location.hash.slice(1));
        } catch (_) {
            return location.hash.slice(1);
        }
    }

    function indexFromHash(slides) {
        const targetId = slideIdFromHash();
        if (!targetId) return 0;
        const index = slides.findIndex((slide) => slide.id === targetId);
        return index >= 0 ? index : 0;
    }

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function labels(page) {
        const fullscreen = page.querySelector('[data-presentation-action="fullscreen"]');
        return {
            fullscreen: fullscreen?.dataset.labelEnter || 'Fullscreen',
            exitFullscreen: fullscreen?.dataset.labelExit || 'Exit fullscreen',
        };
    }

    function progressTemplate(page) {
        const stageTemplate = page.querySelector('[data-presentation-stage]')?.dataset.progressTemplate;
        if (stageTemplate) return stageTemplate;
        const text = page.querySelector('[data-presentation-progress-text]')?.textContent || '';
        if (text.includes(' de ')) return 'Slide {current} de {total}';
        return 'Slide {current} of {total}';
    }

    function updateLangToggleHash(page, slide) {
        const toggle = page.closest('body')?.querySelector('.lang-toggle');
        if (!toggle || !slide?.id) return;
        const baseHref = (toggle.getAttribute('href') || '').split('#')[0];
        toggle.setAttribute('href', `${baseHref}#${encodeURIComponent(slide.id)}`);
    }

    function updateProgress(page, index) {
        const slides = state.slides;
        const total = slides.length;
        const current = total ? index + 1 : 0;
        const text = page.querySelector('[data-presentation-progress-text]');
        const progress = page.querySelector('.presentation-progress[role="progressbar"]');
        const bar = page.querySelector('[data-presentation-progress-bar]');
        const input = page.querySelector('[data-presentation-slide-input]');
        const previous = page.querySelector('[data-presentation-action="previous"]');
        const next = page.querySelector('[data-presentation-action="next"]');

        if (text) {
            text.textContent = progressTemplate(page)
                .replace('{current}', String(current))
                .replace('{total}', String(total));
        }

        if (bar) {
            const percentage = total <= 1 ? 100 : ((current / total) * 100);
            bar.style.width = `${percentage}%`;
        }

        if (progress) {
            progress.setAttribute('aria-valuemax', String(total || 1));
            progress.setAttribute('aria-valuenow', String(current || 1));
            progress.dataset.current = String(current || 1);
            progress.dataset.total = String(total || 1);
        }

        if (input) {
            input.value = String(current || 1);
            input.max = String(total || 1);
        }

        if (previous) previous.disabled = index <= 0;
        if (next) next.disabled = index >= total - 1;
    }

    function navBottomOffset() {
        const nav = document.querySelector('.nav');
        const navBottom = nav ? nav.getBoundingClientRect().bottom : 0;
        return Math.max(navBottom, 0) + 12;
    }

    function settleStageViewport(page) {
        if (document.fullscreenElement) return;
        const stage = page.querySelector('[data-presentation-stage]');
        if (!stage) return;

        resetStageScroll(stage);
        const rect = stage.getBoundingClientRect();
        const targetTop = navBottomOffset();
        const isSmallViewport = window.matchMedia('(max-width: 640px)').matches;
        const isCovered = rect.top < targetTop;
        const isTooLow = isSmallViewport && rect.top > targetTop + 48;
        if (!isCovered && !isTooLow) return;

        window.scrollBy({
            top: rect.top - targetTop,
            left: 0,
            behavior: 'auto',
        });
    }

    function resetStageScroll(stage) {
        stage.scrollLeft = 0;
        stage.scrollTop = 0;
        stage.scrollTo({ top: 0, left: 0 });
    }

    function fitCodeBlocks(slide) {
        if (!slide) return;
        const inner = slide.querySelector('.presentation-slide-inner');
        const blocks = Array.from(slide.querySelectorAll('.presentation-code, pre'));
        if (!inner || blocks.length === 0) return;

        blocks.forEach((block) => {
            block.style.fontSize = '';
        });

        window.requestAnimationFrame(() => {
            let attempts = 0;
            while (
                attempts < 18 &&
                (inner.scrollHeight > inner.clientHeight || inner.scrollWidth > inner.clientWidth)
            ) {
                blocks.forEach((block) => {
                    const current = Number.parseFloat(window.getComputedStyle(block).fontSize);
                    if (!Number.isFinite(current) || current <= 8) return;
                    block.style.fontSize = `${Math.max(8, current - 0.75)}px`;
                });
                attempts += 1;
            }
        });
    }

    function activateSlide(index, options = {}) {
        const page = state.page;
        const slides = state.slides;
        if (!page || slides.length === 0) return;

        const nextIndex = clamp(index, 0, slides.length - 1);
        const stage = page.querySelector('[data-presentation-stage]');
        state.currentIndex = nextIndex;

        if (stage) {
            delete stage.dataset.slideDirection;
            resetStageScroll(stage);
        }

        slides.forEach((slide, slideIndex) => {
            const isActive = slideIndex === nextIndex;
            slide.classList.toggle(ACTIVE_CLASS, isActive);
            slide.setAttribute('aria-hidden', isActive ? 'false' : 'true');
        });

        updateProgress(page, nextIndex);

        const activeSlide = slides[nextIndex];
        if (stage) {
            resetStageScroll(stage);
            window.setTimeout(() => resetStageScroll(stage), 0);
            window.setTimeout(() => resetStageScroll(stage), 80);
        }
        activeSlide?.querySelector('.presentation-slide-inner')?.scrollTo({ top: 0, left: 0 });
        fitCodeBlocks(activeSlide);
        updateLangToggleHash(page, activeSlide);
        if (options.updateHash !== false && activeSlide?.id) {
            const nextUrl = new URL(location.href);
            nextUrl.hash = activeSlide.id;
            const method = options.replaceHash ? 'replaceState' : 'pushState';
            history[method](
                { ...(history.state || {}), presentationSlide: activeSlide.id },
                '',
                nextUrl.toString()
            );
        }

        if (options.focusStage) {
            page.querySelector('[data-presentation-stage]')?.focus({ preventScroll: true });
        }

        if (options.settleViewport) {
            window.requestAnimationFrame(() => {
                window.requestAnimationFrame(() => settleStageViewport(page));
            });
        }
    }

    function goToSlide(index, options = {}) {
        activateSlide(index, options);
    }

    function nextSlide() {
        goToSlide(state.currentIndex + 1, { focusStage: true });
    }

    function previousSlide() {
        goToSlide(state.currentIndex - 1, { focusStage: true });
    }

    function firstSlide() {
        goToSlide(0, { focusStage: true });
    }

    function lastSlide() {
        goToSlide(state.slides.length - 1, { focusStage: true });
    }

    function bindControls(page) {
        page.querySelectorAll('[data-presentation-action]').forEach((control) => {
            if (control.dataset.presentationBound === 'true') return;
            control.dataset.presentationBound = 'true';

            control.addEventListener('click', () => {
                const action = control.dataset.presentationAction;
                if (action === 'previous') previousSlide();
                if (action === 'next') nextSlide();
                if (action === 'fullscreen') toggleFullscreen();
            });
        });

        page.querySelectorAll('[data-presentation-jump-form]').forEach((form) => {
            if (form.dataset.presentationBound === 'true') return;
            form.dataset.presentationBound = 'true';

            form.addEventListener('submit', (event) => {
                event.preventDefault();
                const input = form.querySelector('[data-presentation-slide-input]');
                const requested = Number.parseInt(input?.value || '', 10);
                if (!Number.isFinite(requested)) return;
                goToSlide(requested - 1, { focusStage: true });
            });
        });
    }

    function isInteractiveTarget(target) {
        if (!(target instanceof Element)) return false;
        return !!target.closest(
            'input, textarea, select, button, a[href], summary, [contenteditable="true"], [role="textbox"], [role="button"], [role="link"], [role="menuitem"], [data-presentation-ignore-keys]'
        );
    }

    function closestScrollable(target) {
        let node = target instanceof Element ? target : target?.parentElement;
        while (node && node !== document.body) {
            const style = window.getComputedStyle(node);
            const overflowY = style.overflowY;
            const overflowX = style.overflowX;
            const canScrollY = /(auto|scroll)/.test(overflowY) && node.scrollHeight > node.clientHeight;
            const canScrollX = /(auto|scroll)/.test(overflowX) && node.scrollWidth > node.clientWidth;
            if (canScrollY || canScrollX || node.dataset.overflow === 'scroll') return node;
            if (node.classList?.contains('presentation-slide')) break;
            node = node.parentElement;
        }
        return null;
    }

    function shouldIgnoreKey(event) {
        if (!state.page || event.defaultPrevented) return true;
        if (event.altKey || event.ctrlKey || event.metaKey) return true;

        const target = event.target;
        const actionControl =
            target instanceof Element ? target.closest('[data-presentation-action]') : null;
        if (target && isInteractiveTarget(target) && !actionControl) return true;
        if (target && target !== document.body && closestScrollable(target)) return true;

        return false;
    }

    function handleKeydown(event) {
        if (shouldIgnoreKey(event)) return;

        if (event.key === 'ArrowRight' || event.key === 'PageDown') {
            event.preventDefault();
            nextSlide();
            return;
        }

        if (event.key === 'ArrowLeft' || event.key === 'PageUp') {
            event.preventDefault();
            previousSlide();
            return;
        }

        if (event.key === ' ' && event.shiftKey) {
            event.preventDefault();
            previousSlide();
            return;
        }

        if (event.key === ' ') {
            event.preventDefault();
            nextSlide();
            return;
        }

        if (event.key === 'Home') {
            event.preventDefault();
            firstSlide();
            return;
        }

        if (event.key === 'End') {
            event.preventDefault();
            lastSlide();
            return;
        }

        if (event.key.toLowerCase() === 'f') {
            event.preventDefault();
            toggleFullscreen();
        }
    }

    async function toggleFullscreen() {
        const page = state.page;
        if (!page) return;

        if (document.fullscreenElement) {
            await document.exitFullscreen();
            return;
        }

        const target = page.querySelector('.presentation-post') || page;
        if (target.requestFullscreen) {
            try {
                await target.requestFullscreen();
            } catch (_) {
                target.classList.remove('is-presentation-fullscreen');
            }
        }
    }

    function updateFullscreenControl() {
        const page = state.page;
        if (!page) return;

        const control = page.querySelector('[data-presentation-action="fullscreen"]');
        if (!control) return;

        const ui = labels(page);
        const isFullscreen = !!document.fullscreenElement;
        const target = page.querySelector('.presentation-post');
        if (target) {
            target.classList.toggle(
                'is-presentation-fullscreen',
                isFullscreen && (document.fullscreenElement === target || target.contains(document.fullscreenElement))
            );
        }
        const label = isFullscreen ? ui.exitFullscreen : ui.fullscreen;
        control.setAttribute('aria-label', label);
        control.setAttribute('aria-pressed', isFullscreen ? 'true' : 'false');
    }

    function syncFromHash() {
        if (!state.page) return;
        goToSlide(indexFromHash(state.slides), { updateHash: false, settleViewport: true });
    }

    function ensureDocumentListeners() {
        if (state.listenersReady) return;
        state.listenersReady = true;

        document.addEventListener('keydown', handleKeydown);
        document.addEventListener('fullscreenchange', updateFullscreenControl);
        window.addEventListener('hashchange', syncFromHash);
        window.addEventListener('popstate', syncFromHash);
    }

    function initializePresentation() {
        const page = currentPage();
        if (!page) {
            state.page = null;
            state.slides = [];
            state.currentIndex = 0;
            return;
        }

        state.page = page;
        state.slides = Array.from(page.querySelectorAll(SLIDE_SELECTOR));
        bindControls(page);
        ensureDocumentListeners();

        const initialIndex = indexFromHash(state.slides);
        goToSlide(initialIndex, {
            updateHash: !!location.hash && state.slides.length > 0,
            replaceHash: true,
            settleViewport: true,
        });
        updateFullscreenControl();
    }

    window.addEventListener('resize', () => {
        fitCodeBlocks(state.slides[state.currentIndex]);
    });

    document.addEventListener('DOMContentLoaded', initializePresentation);
    document.addEventListener('page-navigation-complete', initializePresentation);
})();
