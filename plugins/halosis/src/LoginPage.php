<?php

namespace GlpiPlugin\Halosis;

use Glpi\Application\View\TemplateRenderer;
use Glpi\Plugin\Hooks;
use Session;
use Toolbox;

/**
 * Halaman login HaloSIS (NFR-10: tanpa mengubah template inti GLPI).
 *
 * - Hook display_login merender panel brand (ilustrasi + lengkung), logo, lencana SSO, bantuan lupa kata sandi,
 *   dan teks footer. GLPI menaruhnya di kolom kanan form login; public/js/login.js menyusunnya jadi satu kartu
 *   dua panel dan menambah ikon field + tombol tampil/sembunyikan kata sandi (login_name/login_password tetap).
 * - Gaya di public/css/login.css, hanya dimuat di halaman anonim (login, galat login, lupa password).
 * - Label inti GLPI ("Login to your account", "Sign in", …) diterjemahkan lewat mekanisme terjemahan lokal GLPI:
 *   locales/core/*.mo disalin ke GLPI_LOCAL_I18N_DIR/core_halosis saat plugin dipasang.
 * - Halaman anonim memakai bahasa default instansi (config language), bukan bahasa browser (useDefaultLanguage).
 */
final class LoginPage
{
    /** Folder override terjemahan inti di GLPI_LOCAL_I18N_DIR (GLPI memuat semua folder core_*) */
    private const CORE_LOCALE_DIR = 'core_halosis';

    public static function register(): void
    {
        global $PLUGIN_HOOKS;

        $PLUGIN_HOOKS[Hooks::ADD_CSS_ANONYMOUS_PAGE]['halosis']        = [plugin_halosis_asset('css/login.css')];
        $PLUGIN_HOOKS[Hooks::ADD_JAVASCRIPT_ANONYMOUS_PAGE]['halosis'] = [plugin_halosis_asset('js/login.js')];
        $PLUGIN_HOOKS[Hooks::DISPLAY_LOGIN]['halosis']                 = [self::class, 'display'];
    }

    /**
     * GLPI memilih bahasa halaman anonim dari header Accept-Language browser, sehingga browser berbahasa Inggris
     * melihat login berbahasa Inggris. Sebelum login, pakai bahasa default instansi (id_ID); sesudah login GLPI
     * mengganti bahasa sesi sesuai preferensi pengguna. Panggilan API tidak diubah.
     */
    public static function useDefaultLanguage(): void
    {
        global $CFG_GLPI;

        $default = (string) ($CFG_GLPI['language'] ?? '');
        if (
            PHP_SAPI === 'cli'
            || $default === ''
            || Session::getLoginUserID() !== false
            || ($_SESSION['glpilanguage'] ?? '') === $default
            || preg_match('#/api(rest)?\.php#', (string) ($_SERVER['REQUEST_URI'] ?? '')) === 1
        ) {
            return;
        }
        $_SESSION['glpilanguage'] = $default;
        Session::loadLanguage();
    }

    public static function display(): void
    {
        global $CFG_GLPI;

        TemplateRenderer::getInstance()->display('@halosis/login.html.twig', [
            'logo'         => $CFG_GLPI['root_doc'] . '/plugins/halosis/logo/halosis-logo-dark.png',
            'illustration' => $CFG_GLPI['root_doc'] . '/plugins/halosis/img/login-ilustrasi.svg',
            'sso'          => KeycloakAuth::isEnabled(),
        ]);
    }

    /**
     * Salin terjemahan label inti ke folder terjemahan lokal GLPI. Dipanggil saat install; cache terjemahan
     * perlu dibersihkan sesudahnya (`bin/console cache:clear`) agar label baru terbaca.
     */
    public static function installCoreLocales(): void
    {
        $target = GLPI_LOCAL_I18N_DIR . '/' . self::CORE_LOCALE_DIR;
        if (!is_dir($target) && !@mkdir($target, 0755, true)) {
            Toolbox::logInFile('halosis', "Folder terjemahan lokal tidak bisa dibuat: {$target}\n", true);
            return;
        }
        foreach (glob(dirname(__DIR__) . '/locales/core/*.mo') ?: [] as $mo) {
            copy($mo, $target . '/' . basename($mo));
        }
    }

    public static function uninstallCoreLocales(): void
    {
        $target = GLPI_LOCAL_I18N_DIR . '/' . self::CORE_LOCALE_DIR;
        foreach (glob($target . '/*.mo') ?: [] as $mo) {
            unlink($mo);
        }
        if (is_dir($target)) {
            @rmdir($target);
        }
    }
}
