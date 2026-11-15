/**
 * UC-07: info "Ditangani oleh" di detail tiket antarmuka Helpdesk (pegawai) + judul kolom daftar "Laporan saya".
 */
(() => {
  const run = () => {
    const root = (document.querySelector('script[src*="/plugins/halosis/"]')?.src || '').split('/plugins/halosis/')[0]
        || '';
    const AJAX = `${root}/plugins/halosis/ajax/ditangani.php`;

    // Judul kolom plugin: "Plugins - Ditangani oleh" → "Ditangani oleh"
    document.querySelectorAll('table.search-results thead th').forEach((th) => {
        const a = th.querySelector('a, span') || th;
        if (/^Plugins? - /i.test(a.textContent.trim())) {
            a.textContent = a.textContent.trim().replace(/^Plugins? - /i, '');
        }
    });

    const match = window.location.pathname.match(/ticket\.form\.php$/) ? new URLSearchParams(window.location.search).get('id') : null;
    if (!match || !/^\d+$/.test(match) || document.body.classList.contains('halosis-handled-done') || window.__hsHandledBusy) {
        return;
    }
    const target = document.querySelector('.itil-object .timeline-buttons, .itil-left-side, .itil-object');
    if (!target || !document.querySelector('.itil-left-side')) {
        return;
    }
    fetch(`${AJAX}?id=${match}`, { credentials: 'same-origin' }).then((r) => r.json()).then((res) => {
        if (!res.text || document.querySelector('.halosis-handled-by')) {
            return;
        }
        const box = document.createElement('div');
        box.className = 'halosis-handled-by alert alert-info py-2 mb-2';
        const b = document.createElement('strong');
        b.textContent = `${res.label}: `;
        box.append(b, document.createTextNode(res.text));
        document.querySelector('.itil-left-side').prepend(box);
        document.body.classList.add('halosis-handled-done');
    }).catch(() => {});
  };
  // Daftar tiket & detail dimuat/dirender belakangan: coba beberapa kali
  let n = 0;
  const tick = () => { run(); if (++n < 6) { setTimeout(tick, 700); } };
  if (document.readyState === 'loading') { document.addEventListener('DOMContentLoaded', tick); } else { tick(); }
})();
