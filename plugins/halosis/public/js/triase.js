/**
 * Panel "Saran AI" di form tiket: Terima / Ubah / Tolak dan buat saran.
 * Alasan wajib untuk Ubah & Tolak: tombol kirim aktif setelah alasan cukup panjang.
 * Setelah berhasil, halaman dimuat ulang supaya field tiket & pesan GLPI tampil terbaru.
 */
(() => {
    const panelOf = (el) => el.closest('[data-halosis-triase]');

    const showError = (panel, message) => {
        const box = panel.querySelector('[data-halosis-error]');
        box.textContent = message;
        box.classList.remove('d-none');
    };

    const send = async (panel, button, data) => {
        const body = new FormData();
        Object.entries(data).forEach(([key, value]) => body.append(key, value));
        panel.querySelector('[data-halosis-error]').classList.add('d-none');
        panel.querySelectorAll('button[data-action]').forEach((b) => { b.disabled = true; });
        button.classList.add('btn-loading');

        try {
            const response = await fetch(panel.dataset.ajaxUrl, {
                method: 'POST',
                body,
                credentials: 'same-origin',
                headers: { 'X-Requested-With': 'XMLHttpRequest' },
            });
            const result = await response.json().catch(() => ({ ok: false, message: `HTTP ${response.status}` }));
            if (result.ok) {
                window.location.reload();
                return;
            }
            showError(panel, result.message);
        } catch (e) {
            showError(panel, e.message);
        }
        button.classList.remove('btn-loading');
        panel.querySelectorAll('button[data-action]').forEach((b) => { b.disabled = false; });
        // Tombol kirim Ubah/Tolak tetap mengikuti panjang alasan
        panel.querySelectorAll('[data-halosis-section] textarea[data-reason]').forEach(updateSubmit);
    };

    const sectionOf = (el) => el.closest('[data-halosis-section]');

    const updateSubmit = (textarea) => {
        const panel = panelOf(textarea);
        const section = sectionOf(textarea);
        const min = Number(panel.dataset.minReason || 5);
        section.querySelector('button[data-action]').disabled = textarea.value.trim().length < min;
    };

    const toggleSection = (panel, name, button) => {
        panel.querySelectorAll('[data-halosis-section]').forEach((section) => {
            const show = section.dataset.halosisSection === name && section.classList.contains('d-none');
            section.classList.toggle('d-none', !show);
        });
        panel.querySelectorAll('[data-action^="show-"]').forEach((b) => {
            b.setAttribute('aria-expanded', String(b === button && !panel.querySelector(`[data-halosis-section="${name}"]`).classList.contains('d-none')));
        });
        panel.querySelector(`[data-halosis-section="${name}"] textarea`)?.focus();
    };

    // Prioritas mengikuti matriks GLPI bila petugas tidak berhak mengubah prioritas
    const recomputePriority = (panel) => {
        if (panel.dataset.canChangePriority === '1') {
            return;
        }
        const matrix = JSON.parse(panel.dataset.priorityMatrix || '{}');
        const urgency = panel.querySelector('[data-field="urgency"]').value;
        const impact = panel.querySelector('[data-field="impact"]').value;
        const priority = matrix[urgency]?.[impact];
        if (priority) {
            panel.querySelector('[data-field="priority"]').value = String(priority);
        }
    };

    document.addEventListener('click', (event) => {
        const button = event.target.closest('[data-halosis-triase] button[data-action]');
        if (!button) {
            return;
        }
        event.preventDefault();
        const panel = panelOf(button);
        const action = button.dataset.action;

        switch (action) {
            case 'generate':
                send(panel, button, { action, ticket_id: panel.dataset.ticketId });
                break;
            case 'accept':
                send(panel, button, { action, suggestion_id: panel.dataset.suggestionId });
                break;
            case 'show-modify':
                toggleSection(panel, 'modify', button);
                break;
            case 'show-reject':
                toggleSection(panel, 'reject', button);
                break;
            case 'modify':
            case 'reject': {
                const section = sectionOf(button);
                const data = { action, suggestion_id: panel.dataset.suggestionId, reason: section.querySelector('[data-reason]').value };
                section.querySelectorAll('[data-field]').forEach((field) => { data[field.dataset.field] = field.value; });
                send(panel, button, data);
                break;
            }
        }
    });

    document.addEventListener('input', (event) => {
        if (event.target.matches('[data-halosis-triase] textarea[data-reason]')) {
            updateSubmit(event.target);
        }
    });

    document.addEventListener('change', (event) => {
        if (event.target.matches('[data-halosis-triase] [data-field="urgency"], [data-halosis-triase] [data-field="impact"]')) {
            recomputePriority(panelOf(event.target));
        }
    });
})();
