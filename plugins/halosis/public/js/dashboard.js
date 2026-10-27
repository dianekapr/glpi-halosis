/**
 * Dashboard kinerja AI: tooltip per minggu pada grafik kolom bertumpuk.
 * Area hover selebar kolom minggu; muncul juga saat fokus keyboard. Isi diisi dengan textContent.
 */
(() => {
    const chart = document.querySelector('[data-hd-chart]');
    if (!chart) {
        return;
    }
    const tip = chart.querySelector('[data-hd-tooltip]');
    const svg = chart.querySelector('svg');

    const show = (hit) => {
        tip.querySelector('.hd-tooltip-title').textContent = hit.dataset.week;
        ['accept', 'modify', 'reject', 'total'].forEach((key) => {
            tip.querySelector(`[data-hd-value="${key}"]`).textContent = hit.dataset[key];
        });
        tip.hidden = false;

        // Posisikan di samping kolom, tetap di dalam area grafik
        const box = hit.getBoundingClientRect();
        const area = chart.getBoundingClientRect();
        let left = box.right - area.left + 8;
        if (left + tip.offsetWidth > area.width) {
            left = box.left - area.left - tip.offsetWidth - 8;
        }
        tip.style.left = `${Math.max(0, left)}px`;
        tip.style.top = `${Math.max(0, box.top - area.top + 8)}px`;
        svg.querySelectorAll('.hd-hit').forEach((h) => h.classList.toggle('active', h === hit));
    };
    const hide = () => {
        tip.hidden = true;
        svg.querySelectorAll('.hd-hit.active').forEach((h) => h.classList.remove('active'));
    };

    svg.querySelectorAll('.hd-hit').forEach((hit) => {
        hit.addEventListener('mouseenter', () => show(hit));
        hit.addEventListener('focus', () => show(hit));
        hit.addEventListener('mouseleave', hide);
        hit.addEventListener('blur', hide);
    });
})();
