(() => {
    const panel = document.querySelector('.floating-panel[data-panel-id="toc"]');
    const toc = panel?.querySelector('.toc');
    const tocInner = toc?.querySelector('.inner');
    const article = document.querySelector('.post-content');
    if (!toc || !tocInner || !article) return;

    const tocLinks = Array.from(toc.querySelectorAll('a[href^="#"]'));
    if (!tocLinks.length) return;
    const segmentFragment = document.createDocumentFragment();
    const sections = tocLinks.map((link) => {
        let id;
        try { id = decodeURIComponent(link.hash.slice(1)); }
        catch { id = link.hash.slice(1); }
        const heading = document.getElementById(id);
        if (!heading) return null;
        const segment = document.createElement('span');
        const fill = document.createElement('span');
        segment.className = 'toc-section-progress';
        segment.dataset.tocTarget = id;
        segment.setAttribute('aria-hidden', 'true');
        fill.className = 'toc-section-progress-fill';
        segment.append(fill);
        segmentFragment.append(segment);
        return { link, heading, segment, fill };
    }).filter(Boolean);
    tocInner.prepend(segmentFragment);
    let updatePending = false;

    function getLocalMetrics(element) {
        let top = 0;
        let node = element;
        while (node && node !== tocInner) {
            top += node.offsetTop;
            node = node.offsetParent;
        }
        if (node === tocInner) return { top, height: element.offsetHeight };

        const elementRect = element.getBoundingClientRect();
        const innerRect = tocInner.getBoundingClientRect();
        return { top: elementRect.top - innerRect.top, height: elementRect.height };
    }

    function updateTocState() {
        updatePending = false;
        if (!sections.length) return;

        const scrollY = window.scrollY;
        const viewportTop = scrollY + parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header-height') || 0);
        const viewportBottom = scrollY + window.innerHeight;
        const articleBottom = article.getBoundingClientRect().bottom + scrollY;

        sections.forEach((section, index) => {
            const sectionTop = section.heading.getBoundingClientRect().top + scrollY;
            const nextSection = sections[index + 1];
            const sectionBottom = nextSection
                ? nextSection.heading.getBoundingClientRect().top + scrollY
                : articleBottom;
            const isActive = sectionTop < viewportBottom && sectionBottom > viewportTop;
            const sectionLength = sectionBottom - sectionTop;
            const progress = sectionLength > 0
                ? Math.min(1, Math.max(0, (viewportBottom - sectionTop) / sectionLength))
                : Number(viewportBottom >= sectionBottom);
            const linkMetrics = getLocalMetrics(section.link);
            section.link.classList.toggle('is-active', isActive);
            section.segment.classList.toggle('is-active', isActive);
            section.segment.classList.toggle('is-read', !isActive && progress >= 1);
            section.segment.style.top = `${linkMetrics.top + 2}px`;
            section.segment.style.height = `${Math.max(3, linkMetrics.height - 4)}px`;
            section.fill.style.setProperty('--toc-section-progress', `${progress * 100}%`);
        });

        const activeLinks = tocLinks.filter(link => link.classList.contains('is-active'));
        tocInner.classList.toggle('has-active', activeLinks.length > 0);
        if (!activeLinks.length) return;
        const firstMetrics = getLocalMetrics(activeLinks[0]);
        const lastMetrics = getLocalMetrics(activeLinks[activeLinks.length - 1]);
        tocInner.style.setProperty('--toc-active-top', `${firstMetrics.top}px`);
        tocInner.style.setProperty('--toc-active-height', `${lastMetrics.top + lastMetrics.height - firstMetrics.top}px`);
    }

    function scheduleTocUpdate() {
        if (updatePending) return;
        updatePending = true;
        requestAnimationFrame(updateTocState);
    }

    window.addEventListener('scroll', scheduleTocUpdate, { passive: true });
    window.addEventListener('resize', scheduleTocUpdate);
    panel.addEventListener('floating-panel:open', scheduleTocUpdate);
    scheduleTocUpdate();
})();
