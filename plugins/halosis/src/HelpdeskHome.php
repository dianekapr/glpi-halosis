<?php

namespace GlpiPlugin\Halosis;

use Session;

/**
 * Menjadikan "Tanya HaloSIS" beranda Pegawai (alur resolution-first), tanpa mengubah core GLPI.
 *
 * - Menu Helpdesk diatur ulang lewat hook redefine_menus.
 * - Beranda Helpdesk (/Helpdesk, tujuan GLPI setelah login) dialihkan ke halaman chat lewat tag
 *   <meta http-equiv="refresh"> dari hook add_header_tag. Tag hanya ditambahkan bila server memutuskan
 *   request ini GET /Helpdesk dari pengguna Helpdesk yang berhak chatbot; profil antarmuka standar
 *   (Operator, dll.) tidak pernah mendapatkannya, dan halaman chat ada di path lain sehingga tidak ada loop.
 *
 * Catatan: GLPI 12 belum punya hook server-side untuk mengalihkan /Helpdesk. RedirectException dari
 * plugin_init (dijalankan saat kernel boot) maupun dari redefine_menus (di dalam render Twig) sudah
 * diuji dan berakhir HTTP 500, jadi tidak dipakai.
 */
final class HelpdeskHome
{
    public const MENU_KEY = 'halosis-chat';
    public const MENU_HISTORY_KEY = 'halosis-chat-history';
    public const HISTORY_PATH = '/plugins/halosis/ChatHistory';

    /**
     * Hook redefine_menus (antarmuka Helpdesk), urutan prototipe: Tanya HaloSIS, Buat laporan, Laporan saya,
     * Pusat bantuan (FAQ), Riwayat chat. Menu Helpdesk lain (Reservasi, dll.) disembunyikan dari navigasi.
     *
     * @param array<string, array<string, mixed>> $menu
     *
     * @return array<string, array<string, mixed>>
     */
    public static function redefineMenu(array $menu): array
    {
        if (!Chatbot::isAvailable()) {
            return $menu;
        }

        $item = static fn (string $title, string $path, string $icon): array => [
            'default' => $path,
            'title'   => $title,
            'icon'    => $icon . ' ' . RoleMenu::ITEM_CLASS,
        ];
        $ordered = [self::MENU_KEY => $item(__('Ask HaloSIS', 'halosis'), Chatbot::PAGE_PATH, 'ti ti-message-chatbot')];
        $renames = [
            'create_ticket' => __('Create report', 'halosis'),
            'tickets'       => __('My reports', 'halosis'),
            'faq'           => __('Help center (FAQ)', 'halosis'),
        ];
        foreach ($renames as $key => $title) {
            if (isset($menu[$key])) {
                $ordered[$key] = array_merge($menu[$key], [
                    'title' => $title,
                    'icon'  => trim(($menu[$key]['icon'] ?? '') . ' ' . RoleMenu::ITEM_CLASS),
                ]);
                unset($menu[$key]);
            }
        }
        $ordered[self::MENU_HISTORY_KEY] = $item(__('Chat history', 'halosis'), self::HISTORY_PATH, 'ti ti-history');

        // Beranda Helpdesk lama digantikan halaman chat; menu lain disembunyikan (datanya tetap untuk breadcrumb)
        unset($menu['home']);
        return $ordered + RoleMenu::hideAll($menu);
    }

    /**
     * Request ini membuka beranda Helpdesk GLPI?
     */
    public static function isHelpdeskHomeRequest(): bool
    {
        global $CFG_GLPI;

        if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'GET' || !isset($_SERVER['REQUEST_URI'])) {
            return false;
        }
        $path = (string) parse_url((string) $_SERVER['REQUEST_URI'], PHP_URL_PATH);
        return rtrim($path, '/') === ($CFG_GLPI['root_doc'] ?? '') . '/Helpdesk';
    }

    /**
     * Tag <head> pengalih beranda Helpdesk ke halaman chat (dipakai hanya bila isHelpdeskHomeRequest()).
     *
     * @return array<int, array{tag: string, properties: array<string, string>}>
     */
    public static function getRedirectHeaderTags(): array
    {
        return [[
            'tag'        => 'meta',
            'properties' => ['http-equiv' => 'refresh', 'content' => '0;url=' . Chatbot::getPageUrl()],
        ]];
    }

    public static function shouldRedirectHome(): bool
    {
        return Session::getLoginUserID() !== false && self::isHelpdeskHomeRequest() && Chatbot::isAvailable();
    }
}
