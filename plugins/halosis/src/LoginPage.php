<?php

namespace GlpiPlugin\Halosis;

use Config as CoreConfig;
use Glpi\Application\View\TemplateRenderer;
use Glpi\Cache\CacheManager;
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
 *   locales/core/*.mo disalin ke GLPI_LOCAL_I18N_DIR/core_halosis (saat install, dan otomatis bila berkas .mo
 *   berubah setelah `git pull`, lihat syncLocales).
 * - HaloSIS hanya berbahasa Indonesia: halaman anonim selalu id_ID, apa pun bahasa browser (useIndonesian).
 */
final class LoginPage
{
    /** Folder override terjemahan inti di GLPI_LOCAL_I18N_DIR (GLPI memuat semua folder core_*) */
    private const CORE_LOCALE_DIR = 'core_halosis';
    /** Penanda versi berkas .mo yang terakhir dipasang (ukuran + waktu ubah), di folder CORE_LOCALE_DIR */
    private const SIGNATURE_FILE = '.halosis-sumber';
    /** Satu-satunya bahasa antarmuka HaloSIS */
    public const LANGUAGE = 'id_ID';

    public static function register(): void
    {
        global $PLUGIN_HOOKS;

        $PLUGIN_HOOKS[Hooks::ADD_CSS_ANONYMOUS_PAGE]['halosis']        = [plugin_halosis_asset('css/login.css')];
        $PLUGIN_HOOKS[Hooks::ADD_JAVASCRIPT_ANONYMOUS_PAGE]['halosis'] = [plugin_halosis_asset('js/login.js')];
        $PLUGIN_HOOKS[Hooks::DISPLAY_LOGIN]['halosis']                 = [self::class, 'display'];
    }

    /**
     * GLPI memilih bahasa halaman anonim dari header Accept-Language browser, sehingga browser berbahasa Inggris
     * melihat login berbahasa Inggris. Sebelum login selalu id_ID (tidak bergantung config language, yang di
     * instalasi lama bisa masih en_GB); sesudah login bahasa sesi = bahasa akun (id_ID untuk akun demo & SSO).
     * Panggilan API & CLI tidak diubah.
     */
    public static function useIndonesian(): void
    {
        if (PHP_SAPI === 'cli' || preg_match('#/api(rest)?\.php#', (string) ($_SERVER['REQUEST_URI'] ?? '')) === 1) {
            return;
        }
        $reload = self::syncLocales();
        if (Session::getLoginUserID() === false && ($_SESSION['glpilanguage'] ?? '') !== self::LANGUAGE) {
            $_SESSION['glpilanguage'] = self::LANGUAGE;
            $reload = true;
        }
        if ($reload && isset($_SESSION['glpilanguage'])) {
            Session::loadLanguage();
        }
    }

    /**
     * Anggota tim yang menarik versi baru (`git pull`) tanpa memasang ulang plugin tetap mendapat terjemahan baru:
     * bila berkas .mo plugin/inti berubah, salin ulang label inti & kosongkan cache terjemahan GLPI (cache lama
     * tidak memuat string baru sehingga tampil dalam bahasa Inggris). Cukup stat 2 berkas per request.
     *
     * @return bool true bila terjemahan baru saja dipasang ulang
     */
    public static function syncLocales(): bool
    {
        $marker = GLPI_LOCAL_I18N_DIR . '/' . self::CORE_LOCALE_DIR . '/' . self::SIGNATURE_FILE;
        if (@file_get_contents($marker) === self::signature()) {
            return false;
        }
        self::installCoreLocales();
        return true;
    }

    private static function signature(): string
    {
        $files = array_merge(glob(dirname(__DIR__) . '/locales/*.mo') ?: [], glob(dirname(__DIR__) . '/locales/core/*.mo') ?: []);
        sort($files);
        return md5(implode('|', array_map(static fn ($f) => basename(dirname($f)) . '/' . basename($f) . ':' . filesize($f) . ':' . filemtime($f), $files)));
    }

    /**
     * Bahasa bawaan GLPI = id_ID (konfigurasi, bukan kode inti). Dipanggil saat install; scripts/pasang.sh juga
     * menyetelnya.
     */
    public static function setDefaultLanguage(): void
    {
        CoreConfig::setConfigurationValues('core', ['language' => self::LANGUAGE]);
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
     * Salin terjemahan label inti ke folder terjemahan lokal GLPI dan kosongkan cache terjemahan agar label baru
     * langsung terbaca. Dipanggil saat install dan oleh syncLocales.
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
        (new CacheManager())->getTranslationsCacheInstance()->clear();
        @file_put_contents($target . '/' . self::SIGNATURE_FILE, self::signature());
    }

    public static function uninstallCoreLocales(): void
    {
        $target = GLPI_LOCAL_I18N_DIR . '/' . self::CORE_LOCALE_DIR;
        foreach (array_merge(glob($target . '/*.mo') ?: [], [$target . '/' . self::SIGNATURE_FILE]) as $file) {
            @unlink($file);
        }
        if (is_dir($target)) {
            @rmdir($target);
        }
    }
}
