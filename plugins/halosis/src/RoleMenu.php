<?php

namespace GlpiPlugin\Halosis;

use Change;
use Config as CoreConfig;
use CronTask;
use Entity;
use Glpi\Event;
use Glpi\Form\Form;
use GlpiPlugin\Halosis\Controller\KandidatController;
use Group;
use ITILCategory;
use KnowbaseItem;
use Notification;
use Problem;
use Profile as CoreProfile;
use RuleTicket;
use Session;
use SLM;
use Ticket;
use User;

/**
 * Menu ringkas per peran HaloSIS (mengikuti prototipe halosis-web), lewat hook redefine_menus.
 *
 * Bagian menu bawaan GLPI TIDAK dihapus dari array menu: breadcrumb dan tombol aksi halaman daftar
 * ("Tambah", "Templat", dll.) membaca array yang sama. Bagian bawaan hanya ditandai kelas ikon
 * HIDDEN_CLASS dan disembunyikan dari sidebar oleh CSS (public/css/halosis.css). Item baru hanya
 * ditampilkan bila pengguna berhak membuka halamannya, supaya tidak ada menu yang berujung "akses ditolak".
 *
 * Super-Admin juga mendapat menu ringkas + grup "Sistem GLPI"; seluruh menu GLPI bisa dikembalikan dengan
 * mematikan fitur "Menu ringkas" di konfigurasi plugin.
 */
final class RoleMenu
{
    public const HIDDEN_CLASS = 'halosis-menu-hidden';
    /** Penanda item menu HaloSIS (dipakai public/js/menu.js untuk menyorot item aktif) */
    public const ITEM_CLASS = 'halosis-menu-item';

    /**
     * Hook redefine_menus.
     *
     * @param array<string, array<string, mixed>> $menu
     *
     * @return array<string, array<string, mixed>>
     */
    public static function redefine(array $menu): array
    {
        if (Session::getLoginUserID() === false) {
            return $menu;
        }
        if (Session::getCurrentInterface() === 'helpdesk') {
            return HelpdeskHome::redefineMenu($menu);
        }
        if (!Config::isFeatureEnabled('menu')) {
            return $menu;
        }

        $items = self::itemsForProfile((int) ($_SESSION['glpiactiveprofile']['id'] ?? 0));
        if ($items === []) {
            return $menu;
        }
        return $items + self::hideAll($menu);
    }

    /**
     * Sembunyikan bagian menu dari sidebar tanpa menghapus datanya.
     *
     * @param array<string, array<string, mixed>> $menu
     *
     * @return array<string, array<string, mixed>>
     */
    public static function hideAll(array $menu): array
    {
        foreach ($menu as $key => $section) {
            if (is_array($section)) {
                $menu[$key]['icon'] = trim(($section['icon'] ?? '') . ' ' . self::HIDDEN_CLASS);
            }
        }
        return $menu;
    }

    /**
     * @return array<string, array<string, mixed>>
     */
    private static function itemsForProfile(int $profile_id): array
    {
        $km_id = Roles::findKnowledgeManagerId();
        return match (true) {
            $profile_id === Roles::OPERATOR    => self::operator(),
            $profile_id === Roles::TIM_TEKNIS  => self::teknis(),
            $profile_id === Roles::MANAJEMEN   => self::manajemen(),
            $km_id !== null && $profile_id === $km_id => self::knowledgeManager(),
            $profile_id === Roles::ADMINISTRATOR => self::admin(false),
            $profile_id === Roles::SUPER_ADMIN   => self::admin(true),
            default => [],
        };
    }

    private static function operator(): array
    {
        return self::build([
            ['dashboard', __('Dashboard', 'halosis'), '/front/central.php', 'ti ti-layout-dashboard', true],
            ['queue', __('Validation queue', 'halosis'), self::ticketSearch([self::status('1')]), 'ti ti-sparkles', Ticket::canView()],
            ['tickets', __('All tickets', 'halosis'), '/front/ticket.php?reset=reset', 'ti ti-ticket', Ticket::canView()],
            ...self::monitoring(),
            ['knowledge', __('Search knowledge', 'halosis'), '/front/knowbaseitem.php', 'ti ti-search', KnowbaseItem::canView()],
        ]);
    }

    private static function teknis(): array
    {
        return self::build([
            ['dashboard', __('Dashboard', 'halosis'), '/front/central.php', 'ti ti-layout-dashboard', true],
            ['mytickets', __('My & team tickets', 'halosis'), self::ticketSearch([
                self::status('notold'),
                ['link' => 'AND', 'criteria' => [
                    ['field' => 5, 'searchtype' => 'equals', 'value' => 'myself'],
                    ['link' => 'OR', 'field' => 8, 'searchtype' => 'equals', 'value' => 'mygroups'],
                ]],
            ]), 'ti ti-ticket', Ticket::canView()],
            ...self::monitoring(),
            ['knowledge', __('Search knowledge', 'halosis'), '/front/knowbaseitem.php', 'ti ti-search', KnowbaseItem::canView()],
        ]);
    }

    private static function manajemen(): array
    {
        return self::build([
            ['dashboard', __('Performance dashboard', 'halosis'), '/front/dashboard_helpdesk.php', 'ti ti-chart-bar', Session::haveRight('dashboard', READ)],
            ['ai', __('AI performance', 'halosis'), DashboardMenu::PAGE, 'ti ti-robot', DashboardMenu::canViewDashboard()],
            ...self::monitoring(),
            ['reports', __('Reports', 'halosis'), '/front/stat.php', 'ti ti-report-analytics', Session::haveRight('statistic', READ)],
        ]);
    }

    private static function knowledgeManager(): array
    {
        return self::build([
            ['dashboard', __('Dashboard', 'halosis'), '/front/central.php', 'ti ti-layout-dashboard', true],
            // UC-09: solusi tiket selesai & solusi berulang dari indeks AI → draf artikel
            ['candidates', __('Knowledge candidates', 'halosis'), KandidatController::PAGE, 'ti ti-bulb', Session::haveRight(Profile::RIGHT_KANDIDAT, READ)],
            // GLPI 12: knowbaseitem.php membuka penjelajah artikel; daftar lengkap ada di ?list=1
            ['articles', __('Articles', 'halosis'), '/front/knowbaseitem.php?list=1', 'ti ti-book', KnowbaseItem::canView()],
            ['write', __('Write article', 'halosis'), '/front/knowbaseitem.form.php', 'ti ti-pencil-plus', KnowbaseItem::canCreate()],
        ]);
    }

    private static function admin(bool $super): array
    {
        $items = self::build([
            ['console', __('Admin console', 'halosis'), '/front/central.php', 'ti ti-layout-dashboard', true],
            ['catalog', __('Service catalog', 'halosis'), '/front/form/form.php', 'ti ti-folders', Form::canView()],
            ['categories', __('Service categories', 'halosis'), '/front/itilcategory.php', 'ti ti-category', ITILCategory::canView()],
            ['sla', __('SLA policy', 'halosis'), '/front/slm.php', 'ti ti-clock-hour-4', SLM::canView()],
            ['teams', __('Technical teams', 'halosis'), '/front/group.php', 'ti ti-users-group', Group::canView()],
            ['users', __('Users & roles', 'halosis'), '/front/user.php', 'ti ti-shield-check', User::canView()],
            ['rules', __('Workflow & rules', 'halosis'), '/front/ruleticket.php', 'ti ti-route', RuleTicket::canView()],
            ['ai', __('AI settings', 'halosis'), '/plugins/halosis/front/config.form.php', 'ti ti-sparkles', Session::haveRight(Profile::RIGHT_CONFIG, UPDATE)],
            ['ai-dashboard', __('AI performance', 'halosis'), DashboardMenu::PAGE, 'ti ti-robot', DashboardMenu::canViewDashboard()],
            ['candidates', __('Knowledge candidates', 'halosis'), KandidatController::PAGE, 'ti ti-bulb', Session::haveRight(Profile::RIGHT_KANDIDAT, READ)],
            // Notifikasi (hak "notification"); template notifikasi dijaga hak "config" (Super-Admin) di GLPI
            ['notifications', __('Notifications', 'halosis'), '/front/notification.php', 'ti ti-bell', Notification::canView()],
            ['audit', __('Audit trail', 'halosis'), '/front/event.php', 'ti ti-history', Event::canView()],
        ]);
        if ($super) {
            $system = array_filter([
                'config'   => [__('General setup', 'halosis'), '/front/config.form.php', 'ti ti-adjustments', CoreConfig::canView()],
                'plugins'  => [__('Plugins', 'halosis'), '/front/plugin.php', 'ti ti-puzzle', CoreConfig::canUpdate()],
                'profiles' => [__('Profiles', 'halosis'), '/front/profile.php', 'ti ti-id-badge-2', CoreProfile::canView()],
                'entities' => [__('Entities', 'halosis'), '/front/entity.php', 'ti ti-stack', Entity::canView()],
                'crontask' => [__('Automatic actions', 'halosis'), '/front/crontask.php', 'ti ti-player-play', CronTask::canView()],
                'changes'  => [__('Changes', 'halosis'), '/front/change.php', 'ti ti-clipboard-check', Change::canView()],
                'dropdown' => [__('Dropdowns', 'halosis'), '/front/dropdown.php', 'ti ti-list', CoreConfig::canView()],
            ], static fn ($i) => $i[3]);
            if ($system !== []) {
                $items['halosis-system'] = [
                    'title'   => __('GLPI system', 'halosis'),
                    'icon'    => 'ti ti-settings ' . self::ITEM_CLASS,
                    'content' => array_map(static fn ($i) => ['title' => $i[0], 'page' => $i[1], 'icon' => $i[2]], $system),
                ];
            }
        }
        return $items;
    }

    /**
     * Monitoring bersama Operator, Tim Teknis, Manajemen.
     *
     * @return array<int, array{0: string, 1: string, 2: string, 3: string, 4: bool}>
     */
    private static function monitoring(): array
    {
        return [
            ['sla', __('SLA monitoring', 'halosis'), self::ticketSearch([
                self::status('notold'),
                ['link' => 'AND', 'field' => 82, 'searchtype' => 'equals', 'value' => 1],
            ]), 'ti ti-clock-exclamation', Ticket::canView()],
            // Pola insiden dicatat sebagai Problem oleh PatternDetector
            ['patterns', __('Incident patterns', 'halosis'), '/front/problem.php', 'ti ti-topology-ring-3', Problem::canView()],
        ];
    }

    /**
     * @param array<int, array{0: string, 1: string, 2: string, 3: string, 4: bool}> $items [kunci, judul, url, ikon, boleh]
     *
     * @return array<string, array<string, mixed>>
     */
    private static function build(array $items): array
    {
        $menu = [];
        foreach ($items as [$key, $title, $url, $icon, $allowed]) {
            if ($allowed) {
                $menu['halosis-' . $key] = ['title' => $title, 'default' => $url, 'icon' => $icon . ' ' . self::ITEM_CLASS];
            }
        }
        return $menu;
    }

    private static function status(string $value): array
    {
        return ['field' => 12, 'searchtype' => 'equals', 'value' => $value];
    }

    private static function ticketSearch(array $criteria): string
    {
        return '/front/ticket.php?' . http_build_query(['criteria' => $criteria]);
    }
}
