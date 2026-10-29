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
use GlpiPlugin\Halosis\DashboardMenu;
use GlpiPlugin\Halosis\HelpdeskHome;
use GlpiPlugin\Halosis\KnowledgeIndex;
use GlpiPlugin\Halosis\PatternDetector;
use GlpiPlugin\Halosis\Profile;
use GlpiPlugin\Halosis\Reassignment;
use GlpiPlugin\Halosis\RoleMenu;
use GlpiPlugin\Halosis\Triage;
use GlpiPlugin\Halosis\TriagePanel;

define('PLUGIN_HALOSIS_VERSION', '0.5.0');

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
    $PLUGIN_HOOKS[Hooks::ADD_CSS]['halosis']        = [plugin_halosis_asset('css/halosis.css')];
    $PLUGIN_HOOKS[Hooks::ADD_JAVASCRIPT]['halosis'] = [plugin_halosis_asset('js/triase.js')];
    if (DashboardMenu::canViewDashboard()) {
        $PLUGIN_HOOKS[Hooks::ADD_JAVASCRIPT]['halosis'][] = plugin_halosis_asset('js/dashboard.js');
    }
    // Kandidat Knowledge (UC-09): Knowledge Manager & Administrator
    if (Session::haveRight(Profile::RIGHT_KANDIDAT, READ)) {
        $PLUGIN_HOOKS[Hooks::ADD_JAVASCRIPT]['halosis'][] = plugin_halosis_asset('js/kandidat.js');
    }

    // Chatbot (antarmuka Helpdesk, pemegang hak chatbot, fitur aktif): halaman penuh "Tanya HaloSIS"
    // sebagai beranda Pegawai + widget melayang di halaman Helpdesk lain. Lihat HelpdeskHome.
    if (Chatbot::isAvailable()) {
        $PLUGIN_HOOKS[Hooks::ADD_JAVASCRIPT]['halosis'][] = plugin_halosis_asset('js/chat.js');
        if (HelpdeskHome::shouldRedirectHome()) {
            $PLUGIN_HOOKS[Hooks::ADD_HEADER_TAG]['halosis'] = HelpdeskHome::getRedirectHeaderTags();
        }
    }
    // Menu ringkas per peran (prototipe halosis-web): Helpdesk Pegawai + sidebar petugas. Lihat RoleMenu.
    $PLUGIN_HOOKS[Hooks::REDEFINE_MENUS]['halosis'] = [RoleMenu::class, 'redefine'];
    $PLUGIN_HOOKS[Hooks::ADD_JAVASCRIPT]['halosis'][] = plugin_halosis_asset('js/menu.js');

    // Saran triase AI: dibuat saat tiket baru disimpan, ditampilkan di atas panel isian tiket
    // Pemindahan tiket ke grup lain setelah triase dicatat untuk dashboard (metrik "salah tim")
    // Re-index knowledge (UC-09 langkah 7): artikel KB & target visibilitasnya → indeks pencarian layanan AI
    $kb_visibility = [Entity_KnowbaseItem::class, KnowbaseItem_Profile::class, Group_KnowbaseItem::class, KnowbaseItem_User::class];
    $PLUGIN_HOOKS[Hooks::ITEM_ADD]['halosis'] = [
        Ticket::class       => [Triage::class, 'onTicketAdd'],
        Group_Ticket::class => [Reassignment::class, 'onGroupTicketAdd'],
        KnowbaseItem::class => [KnowledgeIndex::class, 'onArticleSave'],
    ] + array_fill_keys($kb_visibility, [KnowledgeIndex::class, 'onVisibilityChange']);
    $PLUGIN_HOOKS[Hooks::ITEM_UPDATE]['halosis'] = [KnowbaseItem::class => [KnowledgeIndex::class, 'onArticleSave']];
    $PLUGIN_HOOKS[Hooks::ITEM_PURGE]['halosis'] = [
        KnowbaseItem::class => [KnowledgeIndex::class, 'onArticlePurge'],
    ] + array_fill_keys($kb_visibility, [KnowledgeIndex::class, 'onVisibilityChange']);
    $PLUGIN_HOOKS[Hooks::PRE_ITIL_INFO_SECTION]['halosis'] = [TriagePanel::class, 'display'];

    // Pola insiden: tugas terjadwal didaftarkan saat install (hook.php); banner di beranda petugas
    $PLUGIN_HOOKS[Hooks::DISPLAY_CENTRAL]['halosis'] = [PatternDetector::class, 'displayCentralBanner'];

    // Tab "HaloSIS" di form Profil untuk mengatur hak akses plugin
    Plugin::registerClass(Profile::class, ['addtabon' => [\Profile::class]]);

    // Halaman konfigurasi: ikon kunci pas di Setup › Plugins dan menu Setup › AI HaloSIS
    // (menu dibutuhkan Administrator yang tidak punya akses ke Setup › Plugins)
    if (Session::haveRight(Profile::RIGHT_CONFIG, UPDATE)) {
        $PLUGIN_HOOKS[Hooks::CONFIG_PAGE]['halosis']           = 'front/config.form.php';
        $PLUGIN_HOOKS[Hooks::MENU_TOADD]['halosis']['config'] = [ConfigMenu::class];
    }
    // Dashboard kinerja AI: menu Bantuan › Kinerja AI
    if (DashboardMenu::canViewDashboard()) {
        $PLUGIN_HOOKS[Hooks::MENU_TOADD]['halosis']['helpdesk'] = [DashboardMenu::class];
    }
}

/**
 * Path aset di public/ dengan penanda waktu ubah file. GLPI memberi versi aset plugin berdasarkan versi
 * plugin saja, sehingga perubahan CSS/JS tanpa naik versi tertahan di cache browser (terlihat di Safari).
 */
function plugin_halosis_asset(string $file): string
{
    $path = __DIR__ . '/public/' . $file;
    return is_file($path) ? $file . '?m=' . filemtime($path) : $file;
}
