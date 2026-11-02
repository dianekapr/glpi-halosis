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
