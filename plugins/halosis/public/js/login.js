/**
 * Halaman login HaloSIS (dimuat di halaman anonim GLPI, lihat LoginPage): menata bagian dari hook display_login
 * di sekitar form bawaan GLPI. Field login_name/login_password, token CSRF, dan alamat form tidak diubah.
 */
document.addEventListener('DOMContentLoaded', () => {
    const page = document.querySelector('.page-anonymous');
    const brand = document.querySelector('.halosis-login-brand');
    const parts = document.querySelector('.halosis-login-parts');
    const password = document.getElementById('login_password');
    if (!page || !brand || !parts || !password) {
        return;
    }

    // Panel brand: dari kolom kanan form ke sisi kiri halaman (HP: di atas)
    const column = brand.parentElement;
    page.prepend(brand);
    if (column.children.length === 0) {
        column.remove();
    }
    document.body.classList.add('halosis-login');

    // Lencana SSO di atas judul; teks login (config text_login) jadi subjudul di bawahnya
    const title = document.querySelector('.main-content-card form .card-header');
    const badge = parts.querySelector('.halosis-login-badge');
    if (title && badge) {
        title.prepend(badge);
    }
    const intro = document.querySelector('.main-content-card form > .rich_text_container');
    if (title && intro) {
        intro.classList.add('halosis-login-intro');
        title.append(intro);
    }

    // Bantuan lupa kata sandi untuk akun SSO menggantikan tautan reset GLPI (URL bawaan tetap berlaku untuk
    // akun lokal: front/lostpassword.php?lostpassword=1)
    const footer = document.querySelector('.main-content-card .form-footer');
    footer?.querySelector('.forgot_password')?.remove();
    footer?.append(parts.querySelector('.halosis-login-help'));

    // Atribusi GLPI tetap ada (tautan & pemegang hak cipta), teksnya diringkas
    const copyright = document.querySelector('.page-anonymous a.copyright');
    if (copyright) {
        copyright.textContent = parts.querySelector('.halosis-login-footer').textContent;
    }

    // Tombol tampil/sembunyikan kata sandi
    const wrap = document.createElement('div');
    wrap.className = 'halosis-password';
    password.before(wrap);
    wrap.append(password);
    const toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'halosis-password-toggle';
    toggle.setAttribute('aria-controls', password.id);
    toggle.innerHTML = '<i class="ti ti-eye" aria-hidden="true"></i>';
    const show = (visible) => {
        password.type = visible ? 'text' : 'password';
        toggle.setAttribute('aria-pressed', String(visible));
        toggle.setAttribute('aria-label', visible ? parts.dataset.hidePassword : parts.dataset.showPassword);
        toggle.title = toggle.getAttribute('aria-label');
        toggle.firstElementChild.className = visible ? 'ti ti-eye-off' : 'ti ti-eye';
    };
    show(false);
    toggle.addEventListener('click', () => show(password.type === 'password'));
    wrap.append(toggle);
    // Jangan sampai browser menyimpan isian sebagai teks biasa
    password.form.addEventListener('submit', () => show(false));

    parts.remove();
});
