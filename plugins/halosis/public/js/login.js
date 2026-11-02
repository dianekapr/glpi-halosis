/**
 * Halaman login HaloSIS (dimuat di halaman anonim GLPI, lihat LoginPage): menyusun bagian dari hook display_login
 * dan form bawaan GLPI menjadi satu kartu dua panel. Field login_name/login_password, token CSRF, dan alamat form
 * tidak diubah.
 */
document.addEventListener('DOMContentLoaded', () => {
    const brand = document.querySelector('.halosis-login-brand');
    const parts = document.querySelector('.halosis-login-parts');
    const card = document.querySelector('.page-anonymous .main-content-card');
    const username = document.getElementById('login_name');
    const password = document.getElementById('login_password');
    if (!brand || !parts || !card || !username || !password) {
        return;
    }

    // Kartu dua panel: panel brand (kiri) + kartu form GLPI (kanan) dalam satu wadah
    const column = brand.parentElement;
    const shell = document.createElement('div');
    shell.className = 'halosis-login-shell';
    card.before(shell);
    shell.append(brand, card);
    if (column.children.length === 0) {
        column.remove();
    }
    document.body.classList.add('halosis-login');

    // Logo kecil di atas judul. Teks sambutan GLPI (config text_login) tidak ditampilkan: sambutan sudah ada di
    // panel kiri
    const title = card.querySelector('form .card-header');
    title?.prepend(parts.querySelector('.halosis-login-logo'));
    card.querySelector('form > .rich_text_container')?.remove();

    // Di bawah tombol Masuk: lencana SSO, lalu bantuan lupa kata sandi untuk akun SSO menggantikan tautan reset
    // GLPI (URL bawaan tetap berlaku untuk akun lokal: front/lostpassword.php?lostpassword=1)
    const footer = card.querySelector('.form-footer');
    footer?.querySelector('.forgot_password')?.remove();
    const badge = parts.querySelector('.halosis-login-badge');
    if (footer && badge) {
        const row = document.createElement('div');
        row.className = 'halosis-login-badge-row';
        row.append(badge);
        footer.append(row);
    }
    footer?.append(parts.querySelector('.halosis-login-help'));

    // Atribusi GLPI tetap ada (tautan & pemegang hak cipta), teksnya diringkas
    const copyright = document.querySelector('.page-anonymous a.copyright');
    if (copyright) {
        copyright.textContent = parts.querySelector('.halosis-login-footer').textContent;
        copyright.title = copyright.textContent;
    }

    // Ikon di dalam field
    const wrapField = (input, icon) => {
        const wrap = document.createElement('div');
        wrap.className = 'halosis-field';
        input.before(wrap);
        wrap.innerHTML = `<i class="ti ${icon} halosis-field-icon" aria-hidden="true"></i>`;
        wrap.append(input);
        return wrap;
    };
    wrapField(username, 'ti-user');
    const passwordField = wrapField(password, 'ti-lock');

    // Tombol tampil/sembunyikan kata sandi
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
    passwordField.classList.add('halosis-field-password');
    passwordField.append(toggle);
    // Jangan sampai browser menyimpan isian sebagai teks biasa
    password.form.addEventListener('submit', () => show(false));

    parts.remove();
});
