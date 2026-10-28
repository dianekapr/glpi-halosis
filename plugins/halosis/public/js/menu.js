/**
 * Sorot item menu ringkas HaloSIS (RoleMenu) yang sesuai halaman saat ini.
 * GLPI menentukan menu aktif dari "sektor" halaman, yang tidak cocok dengan menu per peran, jadi
 * pencocokan dilakukan di sini: halaman persis sama > daftar tanpa filter untuk item tersebut (mis. "Semua
 * tiket" untuk halaman detail tiket; form.php dianggap bagian dari daftar .php) > daftar berfilter.
 * Hanya aktif bila menu HaloSIS terpasang; GLPI bisa merender lebih dari satu navbar (desktop/ponsel).
 */
(() => {
    const ITEM = 'i.halosis-menu-item';

    const parse = (url) => {
        const u = new URL(url, window.location.origin);
        u.searchParams.delete('reset'); // ?reset=reset hanya membersihkan filter, bukan halaman berbeda
        const raw = u.pathname.replace(/\/+$/, '');
        return { raw, path: raw.replace(/\.form\.php$/, '.php'), query: u.searchParams.toString() };
    };

    const score = (target, here) => {
        if (target.path !== here.path) {
            return 0;
        }
        if (target.raw === here.raw && target.query === here.query) {
            return 20; // halaman persis sama
        }
        if (target.raw.endsWith('.form.php')) {
            return 0; // form "buat baru" tidak mewakili halaman lihat/ubah item lain
        }
        return target.query === '' ? 5 : 3; // daftar tanpa filter diutamakan, daftar berfilter sebagai cadangan
    };

    const markNav = (nav, here) => {
        let best = null;
        let bestScore = 0;
        // Hanya item HaloSIS (termasuk isi grupnya); bagian bawaan GLPI yang tersembunyi tidak ikut dinilai
        const ours = [...nav.querySelectorAll(':scope > .nav-item')].filter((li) => li.querySelector(`:scope > .nav-link ${ITEM}`));
        ours.flatMap((li) => [...li.querySelectorAll('a.nav-link[href], a.dropdown-item[href]')]).forEach((a) => {
            const s = score(parse(a.getAttribute('href')), here);
            if (s > bestScore) {
                best = a;
                bestScore = s;
            }
        });
        if (!best) {
            return;
        }
        nav.querySelectorAll('.active').forEach((n) => n.classList.remove('active'));
        nav.querySelectorAll('[aria-current="page"]').forEach((n) => n.removeAttribute('aria-current'));
        best.classList.add('active');
        best.setAttribute('aria-current', 'page');
        const item = best.closest('.nav-item');
        item?.classList.add('active');
        item?.querySelector(':scope > .nav-link')?.classList.add('active');
    };

    const mark = () => {
        const here = parse(window.location.href);
        const navs = new Set([...document.querySelectorAll(ITEM)].map((i) => i.closest('ul.navbar-nav')).filter(Boolean));
        navs.forEach((nav) => markNav(nav, here));
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', mark);
    } else {
        mark();
    }
})();
