<?php

/**
 * HaloSIS — plugin GLPI untuk layanan TI BPS.
 *
 * Berisi modul AI dengan human-in-the-loop: saran triase tiket, chatbot self-service,
 * deteksi pola insiden, dan dashboard kinerja AI. Semua pemanggilan AI dilakukan
 * di sisi server; API key tidak pernah dikirim ke browser.
 *
 * @license GPLv3+
 */

use Glpi\Plugin\Hooks;
use GlpiPlugin\Halosis\Config;
use GlpiPlugin\Halosis\Profile;

define('PLUGIN_HALOSIS_VERSION', '0.1.0');

// Plugin ditulis & diuji untuk GLPI 12.0.x (hook dan API bisa berubah di versi mayor berikutnya)
define('PLUGIN_HALOSIS_MIN_GLPI', '12.0.0');
define('PLUGIN_HALOSIS_MAX_GLPI', '12.0.99');

/**
 * Informasi plugin yang ditampilkan di Setup › Plugins.
 */
function plugin_version_halosis(): array
{
    return [
        'name'         => 'HaloSIS',
        'version'      => PLUGIN_HALOSIS_VERSION,
        'author'       => 'Tim HaloSIS BPS',
        'license'      => 'GPLv3+',
        'homepage'     => '',
        'requirements' => [
            'glpi' => [
                'min' => PLUGIN_HALOSIS_MIN_GLPI,
                'max' => PLUGIN_HALOSIS_MAX_GLPI,
            ],
            'php' => [
                'min' => '8.2',
            ],
        ],
    ];
}

/**
 * Inisialisasi plugin: daftarkan hook & kelas. Dipanggil di setiap request selama plugin aktif.
 */
function plugin_init_halosis(): void
{
    global $PLUGIN_HOOKS;

    // API key disimpan terenkripsi oleh GLPI (GLPIKey) dan ikut diproses oleh `glpi:security:changekey`
    $PLUGIN_HOOKS[Hooks::SECURED_CONFIGS]['halosis'] = [Config::API_KEY];

    // Gaya bersama komponen plugin (file di public/css, disajikan sebagai /plugins/halosis/css/...)
    $PLUGIN_HOOKS[Hooks::ADD_CSS]['halosis'] = ['css/halosis.css'];

    // Tab "HaloSIS" di form Profil untuk mengatur hak akses plugin
    Plugin::registerClass(Profile::class, ['addtabon' => [\Profile::class]]);

    // Ikon kunci pas di daftar plugin → halaman konfigurasi (hanya untuk yang berhak)
    if (Session::haveRight(Profile::RIGHT_CONFIG, UPDATE)) {
        $PLUGIN_HOOKS[Hooks::CONFIG_PAGE]['halosis'] = 'front/config.form.php';
    }
}
