/**
 * Warna aksen per peran (lihat RoleTheme): kelas `hs-role-<peran>` di <body> dari <meta name="halosis-role">
 * (profil aktif), lalu lencana nama peran di header sebelum menu pengguna. Tanpa meta (halaman login, profil di
 * luar peran HaloSIS) tidak ada yang diubah.
 */
document.addEventListener('DOMContentLoaded', () => {
    const meta = document.querySelector('meta[name="halosis-role"]');
    if (!meta || !/^[a-z-]+$/.test(meta.content)) {
        return;
    }
    document.body.classList.add(`hs-role-${meta.content}`);

    const label = meta.dataset.label;
    if (!label) {
        return;
    }
    // GLPI bisa merender header lebih dari sekali (desktop/ponsel): satu lencana per menu pengguna
    document.querySelectorAll('header.navbar .user-menu').forEach((menu) => {
        const badge = document.createElement('span');
        badge.className = 'hs-role-badge';
        badge.textContent = label;
        menu.before(badge);
    });
});

/**
 * Judul kolom daftar GLPI ("Pemohon - Pemohon", "Ditugaskan ke - Grup teknisi", "Tiket - Jumlah tiket", "Katalog layanan -
 * Kategori"): GLPI menambahkan nama kelompok opsi di depan nama kolom (templates/components/search/table.html.twig:77-79,
 * format '%1$s - %2$s' yang juga dipakai ±115 tempat lain, jadi tidak aman ditimpa lewat terjemahan). Awalan dibuang di
 * sini, hanya untuk judul kolom hasil pencarian: "A - A" → "A", dan awalan kelompok yang dikenal → nama kolomnya saja.
 */
(() => {
    const KELOMPOK = ['Ditugaskan ke', 'Tiket', 'Katalog layanan', 'Pengamat', 'Pemohon'];
    const rapikan = () => {
        document.querySelectorAll('table.search-results th[data-searchopt-id]').forEach((th) => {
            const walker = document.createTreeWalker(th, NodeFilter.SHOW_TEXT);
            for (let node = walker.nextNode(); node; node = walker.nextNode()) {
                const m = node.nodeValue.match(/^(\s*)(.+?) - (.+?)(\s*)$/);
                if (m && (m[2] === m[3] || KELOMPOK.includes(m[2]))) {
                    node.nodeValue = `${m[1]}${m[3]}${m[4]}`;
                }
            }
        });
    };
    let jadwal = null;
    const tunda = () => { clearTimeout(jadwal); jadwal = setTimeout(rapikan, 50); };
    document.addEventListener('DOMContentLoaded', () => {
        rapikan();
        new MutationObserver(tunda).observe(document.body, { childList: true, subtree: true });
    });
})();
