/**
 * Halaman Kandidat Knowledge: "Jadikan artikel" membuka draf artikel baru, "Abaikan" wajib beralasan.
 * Setelah berhasil, halaman dimuat ulang (atau pindah ke draf) supaya pesan GLPI tampil.
 */
(() => {
    const root = document.querySelector('[data-halosis-kandidat]');
    if (!root) {
        return;
    }
    const minReason = Number(root.dataset.minReason) || 5;
    const errorBox = root.querySelector('[data-hk-error]');

    const send = async (data, button) => {
        const body = new FormData();
        Object.entries(data).forEach(([key, value]) => body.append(key, value));
        errorBox.classList.add('d-none');
        button.disabled = true;
        button.classList.add('btn-loading');
        try {
            const response = await fetch(root.dataset.ajaxUrl, {
                method: 'POST',
                body,
                credentials: 'same-origin',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            const result = await response.json().catch(() => ({ ok: false, message: `HTTP ${response.status}` }));
            if (result.ok) {
                window.location.href = result.url || window.location.href;
                return;
            }
            errorBox.textContent = result.message;
        } catch (e) {
            errorBox.textContent = e.message;
        }
        errorBox.classList.remove('d-none');
        button.disabled = false;
        button.classList.remove('btn-loading');
    };

    root.addEventListener('click', (event) => {
        const article = event.target.closest('[data-hk-action="article"]');
        if (article) {
            send({ action: 'article', id: article.dataset.id }, article);
            return;
        }
        const toggle = event.target.closest('[data-hk-toggle]');
        if (toggle) {
            const form = root.querySelector(`[data-hk-ignore][data-id="${toggle.dataset.id}"]`);
            form.classList.toggle('d-none');
            form.querySelector('textarea').focus();
        }
    });

    root.querySelectorAll('[data-hk-ignore]').forEach((form) => {
        const reason = form.querySelector('textarea');
        const submit = form.querySelector('button[type="submit"]');
        reason.addEventListener('input', () => { submit.disabled = reason.value.trim().length < minReason; });
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            send({ action: 'ignore', id: form.dataset.id, reason: reason.value }, submit);
        });
    });
})();
