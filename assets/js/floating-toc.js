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

    function updateTocState() {
        updatePending = false;
        if (!sections.length) return;

        const scrollY = window.scrollY;
        const viewportTop = scrollY + parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header-height') || 0);
        const viewportBottom = scrollY + window.innerHeight;
        const articleBottom = article.getBoundingClientRect().bottom + scrollY;
        const innerRect = tocInner.getBoundingClientRect();

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
            const linkRect = section.link.getBoundingClientRect();
            section.link.classList.toggle('is-active', isActive);
            section.segment.classList.toggle('is-active', isActive);
            section.segment.classList.toggle('is-read', !isActive && progress >= 1);
            section.segment.style.top = `${linkRect.top - innerRect.top + 2}px`;
            section.segment.style.height = `${Math.max(3, linkRect.height - 4)}px`;
            section.fill.style.setProperty('--toc-section-progress', `${progress * 100}%`);
        });

        const activeLinks = tocLinks.filter(link => link.classList.contains('is-active'));
        tocInner.classList.toggle('has-active', activeLinks.length > 0);
        if (!activeLinks.length) return;
        const firstRect = activeLinks[0].getBoundingClientRect();
        const lastRect = activeLinks[activeLinks.length - 1].getBoundingClientRect();
        tocInner.style.setProperty('--toc-active-top', `${firstRect.top - innerRect.top}px`);
        tocInner.style.setProperty('--toc-active-height', `${lastRect.bottom - firstRect.top}px`);
    }

    function scheduleTocUpdate() {
        if (updatePending) return;
        updatePending = true;
        requestAnimationFrame(updateTocState);
    }

    window.addEventListener('scroll', scheduleTocUpdate, { passive: true });
    window.addEventListener('resize', scheduleTocUpdate);
    scheduleTocUpdate();
})();
