/**
 * Cari knowledge: tombol "Membantu / Tidak membantu" per hasil (KR-07). Satu kali per hasil per halaman.
 */
(() => {
    const root = document.querySelector('[data-halosis-cari]');
    if (!root) {
        return;
    }

    root.addEventListener('click', async (event) => {
        const button = event.target.closest('[data-hf-helpful]');
        if (!button) {
            return;
        }
        const box = button.closest('[data-hf]');
        const body = new FormData();
        body.append('ref', box.dataset.ref);
        body.append('score', box.dataset.score);
        body.append('helpful', button.dataset.hfHelpful);
        box.querySelectorAll('button').forEach((b) => { b.disabled = true; });
        const response = await fetch(root.dataset.ajaxUrl, {
            method: 'POST',
            body,
            credentials: 'same-origin',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
        }).catch(() => null);
        const result = response ? await response.json().catch(() => null) : null;
        if (result?.ok) {
            box.querySelector('[data-hf-done]').classList.remove('d-none');
            button.classList.add('active');
        } else {
            box.querySelectorAll('button').forEach((b) => { b.disabled = false; });
        }
    });
})();
