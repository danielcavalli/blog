/* Render fenced Mermaid blocks on demand, using the blog's current theme. */
(function() {
    'use strict';

    const sources = new WeakMap();
    let library;
    let queue = Promise.resolve();
    let revision = 0;
    let nextId = 0;

    async function render(request) {
        const blocks = [...document.querySelectorAll('.post-body pre')].filter((block) => {
            const code = block.querySelector('code.language-mermaid');
            if (code) sources.set(block, code.textContent);
            return sources.has(block);
        });
        if (!blocks.length || request !== revision) return;

        // Pages without diagrams never download Mermaid. Keep the version pinned.
        library ||= import('https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.esm.min.mjs');
        const { default: mermaid } = await library;
        await document.fonts.ready;
        if (request !== revision) return;

        const style = getComputedStyle(document.documentElement);
        const color = (name) => style.getPropertyValue(name).trim();
        const theme = document.documentElement.dataset.theme || 'light';
        const background = color('--color-bg');
        const surface = color('--color-surface-elevated');
        const foreground = color('--color-text');
        const accent = color('--accent-color');
        mermaid.initialize({
            startOnLoad: false,
            securityLevel: 'strict',
            theme: 'base',
            htmlLabels: false,
            suppressErrorRendering: true,
            // Mermaid measures positions while drawing. Global motion rules must
            // not animate these transforms, including in reduced-motion mode.
            themeCSS: '* { transition: none !important; animation: none !important; }',
            flowchart: { curve: 'linear', padding: 16, rankSpacing: 32 },
            themeVariables: {
                darkMode: theme === 'dark',
                fontFamily: color('--font-sans'),
                fontSize: '16px',
                background,
                primaryColor: surface,
                primaryTextColor: foreground,
                primaryBorderColor: accent,
                secondaryColor: surface,
                secondaryTextColor: foreground,
                secondaryBorderColor: accent,
                tertiaryColor: surface,
                tertiaryTextColor: foreground,
                tertiaryBorderColor: accent,
                lineColor: color('--color-text-secondary'),
                textColor: foreground,
                edgeLabelBackground: background,
            },
        });

        for (const block of blocks) {
            if (request !== revision || !block.isConnected) return;
            if (block.dataset.mermaidTheme === theme) continue;
            try {
                const { svg } = await mermaid.render(`post-diagram-${++nextId}`, sources.get(block));
                if (request !== revision || !block.isConnected) return;
                block.innerHTML = svg;
                block.classList.add('mermaid-diagram');
                block.dataset.mermaidTheme = theme;
            } catch (error) {
                // Preserve the source (or previous rendering) if a diagram is invalid.
                console.warn('Could not render Mermaid diagram:', error);
            }
        }
    }

    function schedule() {
        const request = ++revision;
        queue = queue.then(() => render(request)).catch((error) => {
            library = undefined;
            console.warn('Could not load Mermaid:', error);
        });
    }

    new MutationObserver(schedule).observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-theme'],
    });
    document.addEventListener('page-navigation-complete', schedule);
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', schedule, { once: true });
    } else {
        schedule();
    }
})();
