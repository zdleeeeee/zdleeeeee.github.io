(() => {
    const desktop = window.matchMedia('(min-width: 1001px)');

    document.querySelectorAll('.floating-panel[data-panel-id]').forEach((panel) => {
        const trigger = panel.querySelector('.floating-panel-trigger');
        const sidebar = panel.querySelector('.floating-panel-sidebar');
        const content = panel.querySelector('.floating-panel-content');
        const dialog = panel.querySelector('.floating-panel-dialog');
        const dialogBody = dialog?.querySelector('.floating-panel-dialog-body');
        const closeButton = dialog?.querySelector('.floating-panel-close');
        if (!trigger || !sidebar || !content || !dialog || !dialogBody || !closeButton ||
            (!content.firstElementChild && !content.textContent.trim())) return;

        let restoreTriggerFocus = true;
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

        function syncLayout() {
            restoreTriggerFocus = false;
            if (dialog.open) {
                afterClose = undefined;
                finishDialogClose();
            }
            (desktop.matches ? sidebar : dialogBody).append(content);
        }

        trigger.addEventListener('click', () => {
            if (desktop.matches) return;
            restoreTriggerFocus = true;
            trigger.focus({ preventScroll: true });
            dialog.showModal();
            trigger.setAttribute('aria-expanded', 'true');
            document.documentElement.classList.add('floating-panel-modal-open');
            panel.dispatchEvent(new CustomEvent('floating-panel:open'));
        });
        closeButton.addEventListener('click', () => closeDialog());
        dialog.addEventListener('animationend', (event) => {
            if (event.animationName === 'floating-panel-dialog-out') finishDialogClose();
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
            if (!document.querySelector('.floating-panel-dialog[open]')) {
                document.documentElement.classList.remove('floating-panel-modal-open');
            }
            if (restoreTriggerFocus && !desktop.matches) trigger.focus({ preventScroll: true });
        });
        dialog.addEventListener('click', (event) => {
            if (event.target !== dialog) return;
            const rect = dialog.getBoundingClientRect();
            if (event.clientX < rect.left || event.clientX > rect.right ||
                event.clientY < rect.top || event.clientY > rect.bottom) closeDialog();
        });
        dialog.addEventListener('click', (event) => {
            const link = event.target.closest('a[href^="#"]');
            if (!link) return;
            restoreTriggerFocus = false;
            let id;
            try { id = decodeURIComponent(link.hash.slice(1)); }
            catch { id = link.hash.slice(1); }
            const target = document.getElementById(id);
            closeDialog(() => {
                if (!target) return;
                const hadTabindex = target.hasAttribute('tabindex');
                if (!hadTabindex) target.setAttribute('tabindex', '-1');
                target.focus({ preventScroll: true });
                if (!hadTabindex) target.addEventListener('blur', () => target.removeAttribute('tabindex'), { once: true });
            });
        }, true);
        desktop.addEventListener('change', syncLayout);
        window.addEventListener('resize', syncLayout);
        syncLayout();
    });
})();
