/* Enhance the server-rendered outline and canonical notes after each navigation. */
(function () {
    'use strict';
    let dispose = () => {};

    function initialize() {
        dispose();
        const article = document.querySelector('.post--reading');
        if (!article) return;
        const body = article.querySelector('.post-body');
        const rail = article.querySelector('.article-notes');
        const notes = [...article.querySelectorAll('.sidenote')];
        const references = [...article.querySelectorAll('.note-reference')];
        const outline = article.querySelector('.article-outline');
        const details = outline?.querySelector('details');
        const links = [...(outline?.querySelectorAll('a[href^="#"]') || [])];
        const headings = links.map(link => document.getElementById(decodeURIComponent(link.hash.slice(1))));
        const wide = matchMedia('(min-width: 1280px)');
        const controller = new AbortController();
        const options = { signal: controller.signal };
        let mode;
        let frame = 0;
        let active;

        const refsFor = note => references.filter(ref => ref.dataset.noteTarget === note.id);
        const blockFor = ref => ref.closest('p, li, blockquote, h1, h2, h3, h4, h5, h6, figure, pre, table') || ref;

        function expanded(note, open) {
            note.hidden = !open;
            refsFor(note).forEach(ref => ref.setAttribute('aria-expanded', String(open)));
        }

        function revealHash(scroll = false) {
            let target;
            try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); }
            catch { return; }
            const note = target?.closest('.sidenote');
            if (note && article.contains(note)) {
                if (!wide.matches) expanded(note, true);
                notes.forEach(item => item.classList.toggle('is-current-note', item === note));
                if (scroll) requestAnimationFrame(() => target.scrollIntoView({ block: 'center' }));
            }
        }

        function setMode() {
            const next = wide.matches ? 'margin' : 'inline';
            if (next === mode) return;
            mode = next;
            article.dataset.readingMode = mode;
            if (details) details.open = wide.matches;
            const after = new Map();
            notes.forEach(note => {
                note.style.top = '';
                const refs = refsFor(note);
                refs.forEach(ref => ref.setAttribute('aria-controls', note.id));
                if (wide.matches) {
                    rail.append(note);
                    note.hidden = false;
                    refs.forEach(ref => ref.removeAttribute('aria-expanded'));
                } else {
                    const block = blockFor(refs[0]);
                    (after.get(block) || block).after(note);
                    after.set(block, note);
                    expanded(note, false);
                }
            });
            if (rail) rail.style.minHeight = '';
            revealHash(true);
        }

        function layout() {
            frame = 0;
            if (!article.isConnected) return;
            setMode();
            if (wide.matches && rail) {
                const origin = rail.getBoundingClientRect().top;
                let bottom = 0;
                notes.forEach(note => {
                    const reference = refsFor(note)[0];
                    const top = Math.max(reference.getBoundingClientRect().top - origin, bottom, 0);
                    note.style.top = `${Math.round(top)}px`;
                    bottom = top + note.getBoundingClientRect().height + 20;
                });
                rail.style.minHeight = `${Math.ceil(bottom)}px`;
            }
            updateOutline();
        }

        function schedule() {
            if (!frame) frame = requestAnimationFrame(layout);
        }

        function updateOutline() {
            if (!links.length) return;
            let index = 0;
            headings.forEach((heading, i) => {
                if (heading && heading.getBoundingClientRect().top <= 128) index = i;
            });
            if (active === links[index]) return;
            active = links[index];
            links.forEach(link => {
                if (link === active) link.setAttribute('aria-current', 'location');
                else link.removeAttribute('aria-current');
            });
            if (wide.matches && outline) {
                const bounds = outline.getBoundingClientRect();
                const selected = active.getBoundingClientRect();
                if (selected.top < bounds.top || selected.bottom > bounds.bottom) {
                    outline.scrollTop += selected.top - bounds.top - 24;
                }
            }
        }

        article.addEventListener('click', event => {
            const reference = event.target.closest?.('.note-reference');
            if (!reference || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
            const note = document.getElementById(reference.dataset.noteTarget);
            if (!note) return;
            if (!wide.matches) {
                event.preventDefault();
                const block = blockFor(reference);
                const elsewhere = note.dataset.currentReference && note.dataset.currentReference !== reference.id;
                const open = note.hidden || elsewhere;
                block.after(note);
                note.dataset.currentReference = reference.id;
                expanded(note, open);
                if (open) note.scrollIntoView({ block: 'nearest', behavior: 'instant' });
            }
            notes.forEach(item => item.classList.toggle('is-current-note', item === note));
        }, options);
        window.addEventListener('scroll', updateOutline, { ...options, passive: true });
        window.addEventListener('resize', schedule, options);
        window.addEventListener('hashchange', () => revealHash(true), options);
        const observer = new ResizeObserver(schedule);
        observer.observe(body);
        notes.forEach(note => observer.observe(note));
        const images = [...article.querySelectorAll('img')];
        images.forEach(img => img.addEventListener('load', schedule, options));
        document.fonts.ready.then(() => { if (article.isConnected) schedule(); });
        setMode();
        schedule();
        dispose = () => {
            controller.abort();
            observer.disconnect();
            if (frame) cancelAnimationFrame(frame);
        };
    }

    document.addEventListener('page-navigation-complete', initialize);
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize, { once: true });
    } else initialize();
})();
