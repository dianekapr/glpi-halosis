<?php

namespace GlpiPlugin\Halosis;

use Glpi\Application\View\TemplateRenderer;
use Glpi\Plugin\Hooks;
use Toolbox;

/**
 * Halaman login HaloSIS (NFR-10: tanpa mengubah template inti GLPI).
 *
 * - Hook display_login merender panel brand, lencana SSO, bantuan lupa kata sandi, dan teks footer. GLPI
 *   menaruhnya di kolom kanan form login; public/js/login.js memindahkan panel brand ke kiri halaman dan
 *   menambah tombol tampil/sembunyikan kata sandi (field login_name/login_password tidak diubah).
 * - Gaya di public/css/login.css, hanya dimuat di halaman anonim (login, galat login, lupa password).
 * - Label inti GLPI ("Login to your account", "Sign in", …) diterjemahkan lewat mekanisme terjemahan lokal GLPI:
 *   locales/core/*.mo disalin ke GLPI_LOCAL_I18N_DIR/core_halosis saat plugin dipasang.
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

    public static function display(): void
    {
        global $CFG_GLPI;

        TemplateRenderer::getInstance()->display('@halosis/login.html.twig', [
            'logo' => $CFG_GLPI['root_doc'] . '/plugins/halosis/logo/halosis-logo-light.png',
            'sso'  => KeycloakAuth::isEnabled(),
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
