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
use GlpiPlugin\Halosis\Chatbot;
use GlpiPlugin\Halosis\Config;
use GlpiPlugin\Halosis\ConfigMenu;
use GlpiPlugin\Halosis\Profile;
use GlpiPlugin\Halosis\Triage;
use GlpiPlugin\Halosis\TriagePanel;

define('PLUGIN_HALOSIS_VERSION', '0.2.0');

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

    // Profil Helpdesk hanya membawa hak yang terdaftar di Profile::$helpdesk_rights ke sesi
    // (Profile::cleanProfile); tanpa ini hak chatbot Pegawai selalu terbaca 0.
    if (!in_array(Profile::RIGHT_CHATBOT, \Profile::$helpdesk_rights, true)) {
        \Profile::$helpdesk_rights[] = Profile::RIGHT_CHATBOT;
    }

    // Gaya & skrip bersama komponen plugin (file di public/, disajikan sebagai /plugins/halosis/css|js/...)
    $PLUGIN_HOOKS[Hooks::ADD_CSS]['halosis']        = ['css/halosis.css'];
    $PLUGIN_HOOKS[Hooks::ADD_JAVASCRIPT]['halosis'] = ['js/triase.js'];

    // Widget chatbot: hanya di antarmuka Helpdesk untuk pemegang hak chatbot (fitur aktif)
    if (Chatbot::isAvailable()) {
        $PLUGIN_HOOKS[Hooks::ADD_JAVASCRIPT]['halosis'][] = 'js/chat.js';
    }

    // Saran triase AI: dibuat saat tiket baru disimpan, ditampilkan di atas panel isian tiket
    $PLUGIN_HOOKS[Hooks::ITEM_ADD]['halosis']              = [Ticket::class => [Triage::class, 'onTicketAdd']];
    $PLUGIN_HOOKS[Hooks::PRE_ITIL_INFO_SECTION]['halosis'] = [TriagePanel::class, 'display'];

    // Tab "HaloSIS" di form Profil untuk mengatur hak akses plugin
    Plugin::registerClass(Profile::class, ['addtabon' => [\Profile::class]]);

    // Halaman konfigurasi: ikon kunci pas di Setup › Plugins dan menu Setup › AI HaloSIS
    // (menu dibutuhkan Administrator yang tidak punya akses ke Setup › Plugins)
    if (Session::haveRight(Profile::RIGHT_CONFIG, UPDATE)) {
        $PLUGIN_HOOKS[Hooks::CONFIG_PAGE]['halosis'] = 'front/config.form.php';
        $PLUGIN_HOOKS[Hooks::MENU_TOADD]['halosis']  = ['config' => [ConfigMenu::class]];
    }
}
