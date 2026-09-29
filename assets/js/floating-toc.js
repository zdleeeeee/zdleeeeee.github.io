(() => {
    const sidebar = document.getElementById('toc-sidebar');
    const dialog = document.getElementById('toc-dialog');
    const trigger = document.getElementById('toc-trigger');
    const toc = sidebar?.querySelector('.toc');
    if (!toc || !toc.querySelector('a[href^="#"]') || !dialog || !trigger) return;

    const desktop = window.matchMedia('(min-width: 1001px)');
    const dialogBody = dialog.querySelector('.toc-dialog-body');
    const tocInner = toc.querySelector('.inner');
    const tocLinks = Array.from(toc.querySelectorAll('a[href^="#"]'));
    const article = document.querySelector('.post-content');
    const segmentFragment = document.createDocumentFragment();
    const sections = tocLinks.map((link) => {
        let id;
        try {
            id = decodeURIComponent(link.hash.slice(1));
        } catch {
            id = link.hash.slice(1);
        }
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
    let restoreTriggerFocus = true;
    let updatePending = false;
    let closeTimer;
    let afterClose;
    trigger.hidden = false;

    function finishDialogClose() {
        clearTimeout(closeTimer);
        closeTimer = undefined;
        dialog.classList.remove('is-closing');
        if (dialog.open) dialog.close();
        const callback = afterClose;
        afterClose = undefined;
        callback?.();
    }

    function closeDialog(callback) {
        if (!dialog.open) return;
        if (callback) afterClose = callback;
        if (dialog.classList.contains('is-closing')) return;
        dialog.classList.add('is-closing');
        closeTimer = setTimeout(finishDialogClose, 250);
    }

    function updateTocState() {
        updatePending = false;
        if (!article || !tocInner || !sections.length) return;

        const scrollY = window.scrollY;
        const viewportTop = scrollY + parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--header-height') || 0);
        const viewportBottom = scrollY + window.innerHeight;
        const articleRect = article.getBoundingClientRect();
        const articleBottom = articleRect.bottom + scrollY;
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

    function syncLayout() {
        restoreTriggerFocus = false;
        if (dialog.open) {
            afterClose = undefined;
            finishDialogClose();
        }
        (desktop.matches ? sidebar : dialogBody).append(toc);
        scheduleTocUpdate();
    }

    trigger.addEventListener('click', () => {
        if (desktop.matches) return;
        restoreTriggerFocus = true;
        trigger.focus({ preventScroll: true });
        dialog.showModal();
        trigger.setAttribute('aria-expanded', 'true');
        document.documentElement.classList.add('toc-modal-open');
        scheduleTocUpdate();
    });
    dialog.querySelector('.toc-close').addEventListener('click', () => closeDialog());
    dialog.addEventListener('animationend', (event) => {
        if (event.animationName === 'toc-dialog-out') finishDialogClose();
    });
    dialog.addEventListener('cancel', (event) => {
        event.preventDefault();
        closeDialog();
    });
    dialog.addEventListener('close', () => {
        clearTimeout(closeTimer);
        closeTimer = undefined;
        dialog.classList.remove('is-closing');
        trigger.setAttribute('aria-expanded', 'false');
        document.documentElement.classList.remove('toc-modal-open');
        if (restoreTriggerFocus && !desktop.matches) trigger.focus({ preventScroll: true });
    });
    dialog.addEventListener('click', (event) => {
        if (event.target !== dialog) return;
        const rect = dialog.getBoundingClientRect();
        if (event.clientX < rect.left || event.clientX > rect.right ||
            event.clientY < rect.top || event.clientY > rect.bottom) closeDialog();
    });
    // Close before the theme's anchor handler scrolls to the heading.
    dialog.addEventListener('click', (event) => {
        const link = event.target.closest('a[href^="#"]');
        if (!link) return;
        restoreTriggerFocus = false;
        const heading = document.getElementById(decodeURIComponent(link.hash.slice(1)));
        closeDialog(() => {
            if (!heading) return;
            const hadTabindex = heading.hasAttribute('tabindex');
            if (!hadTabindex) heading.setAttribute('tabindex', '-1');
            heading.focus({ preventScroll: true });
            if (!hadTabindex) heading.addEventListener('blur', () => heading.removeAttribute('tabindex'), { once: true });
        });
    }, true);
    window.addEventListener('scroll', scheduleTocUpdate, { passive: true });
    window.addEventListener('resize', scheduleTocUpdate);
    desktop.addEventListener('change', syncLayout);
    syncLayout();
})();
