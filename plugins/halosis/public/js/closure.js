/**
 * Daftar "Siap ditutup" (T21): tutup per tiket atau semua yang dicentang, lalu muat ulang.
 */
(() => {
    const root = document.querySelector('[data-halosis-closure]');
    if (!root) {
        return;
    }
    const close = async (ids, button) => {
        const body = new FormData();
        ids.forEach((id) => body.append('ids[]', id));
        button.disabled = true;
        await fetch(root.dataset.ajaxUrl, {
            method: 'POST', body, credentials: 'same-origin', headers: { 'X-Requested-With': 'XMLHttpRequest' },
        }).catch(() => null);
        window.location.reload();
    };
    root.addEventListener('click', (event) => {
        const one = event.target.closest('[data-close-id]');
        if (one) {
            close([one.dataset.closeId], one);
            return;
        }
        const all = event.target.closest('[data-close-selected]');
        if (all) {
            const ids = [...root.querySelectorAll('[data-close-check]:checked')].map((c) => c.value);
            if (ids.length) {
                close(ids, all);
            }
        }
        const toggle = event.target.closest('[data-close-all]');
        if (toggle) {
            root.querySelectorAll('[data-close-check]').forEach((c) => { c.checked = toggle.checked; });
        }
    });
})();
