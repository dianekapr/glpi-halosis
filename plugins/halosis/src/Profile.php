<?php

namespace GlpiPlugin\Halosis;

use CommonGLPI;
use Html;
use Profile as CoreProfile;
use ProfileRight;
use Session;

/**
 * Hak akses plugin HaloSIS, diatur lewat tab "HaloSIS" di form Profil GLPI.
 */
final class Profile extends CommonGLPI
{
    /** Membuka & menyimpan halaman konfigurasi plugin */
    public const RIGHT_CONFIG = 'plugin_halosis_config';
    /** READ = melihat panel Saran AI di tiket, UPDATE = memutuskan Terima/Ubah/Tolak */
    public const RIGHT_TRIAGE = 'plugin_halosis_triage';
    /** READ = melihat dashboard kinerja AI */
    public const RIGHT_DASHBOARD = 'plugin_halosis_dashboard';

    /**
     * Hak default saat instalasi, berdasarkan nama profil bawaan GLPI.
     * Peran HaloSIS: Admin = Super-Admin, Operator = Hotliner, Manajemen = Observer.
     */
    private const DEFAULT_RIGHTS = [
        'Super-Admin' => [
            self::RIGHT_CONFIG    => UPDATE,
            self::RIGHT_TRIAGE    => READ | UPDATE,
            self::RIGHT_DASHBOARD => READ,
        ],
        'Hotliner' => [
            self::RIGHT_TRIAGE => READ | UPDATE,
        ],
        'Observer' => [
            self::RIGHT_DASHBOARD => READ,
        ],
    ];

    public static string $rightname = 'profile';

    public static function getTypeName($nb = 0)
    {
        return 'HaloSIS';
    }

    public static function getIcon()
    {
        return 'ti ti-sparkles';
    }

    /**
     * Definisi baris untuk matriks hak akses (Profile::displayRightsChoiceMatrix).
     */
    public static function getAllRights(): array
    {
        return [
            [
                'itemtype' => Config::class,
                'label'    => __('HaloSIS configuration', 'halosis'),
                'field'    => self::RIGHT_CONFIG,
                'rights'   => [UPDATE => __('Update')],
            ],
            [
                'itemtype' => self::class,
                'label'    => __('AI triage suggestions', 'halosis'),
                'field'    => self::RIGHT_TRIAGE,
                'rights'   => [
                    READ   => __('Read'),
                    UPDATE => __('Decide (accept / modify / reject)', 'halosis'),
                ],
            ],
            [
                'itemtype' => self::class,
                'label'    => __('AI performance dashboard', 'halosis'),
                'field'    => self::RIGHT_DASHBOARD,
                'rights'   => [READ => __('Read')],
            ],
        ];
    }

    public function getTabNameForItem(CommonGLPI $item, $withtemplate = 0)
    {
        if ($item instanceof CoreProfile && $item->getField('interface') === 'central') {
            return self::createTabEntry(self::getTypeName());
        }
        return '';
    }

    public static function displayTabContentForItem(CommonGLPI $item, $tabnum = 1, $withtemplate = 0)
    {
        if (!$item instanceof CoreProfile) {
            return false;
        }

        $profile = new CoreProfile();
        $profile->getFromDB($item->getID());
        $canedit = Session::haveRight(self::$rightname, UPDATE);

        echo '<form method="post" action="' . htmlescape(CoreProfile::getFormURL()) . '">';
        echo '<div class="spaced">';
        $profile->displayRightsChoiceMatrix(self::getAllRights(), [
            'canedit' => $canedit,
            'title'   => __('HaloSIS AI module', 'halosis'),
        ]);
        if ($canedit) {
            echo '<div class="text-center mt-3">';
            echo Html::hidden('id', ['value' => $item->getID()]);
            echo Html::submit(_x('button', 'Save'), ['name' => 'update', 'class' => 'btn btn-primary']);
            echo '</div>';
        }
        echo '</div>';
        Html::closeForm();

        return true;
    }

    /**
     * Tambahkan hak plugin ke semua profil (nilai 0), lalu beri hak default ke profil bawaan.
     * Hak yang sudah ada tidak diubah, supaya pengaturan admin tetap terjaga saat plugin diperbarui.
     */
    public static function install(): void
    {
        global $DB;

        $all_names = array_column(self::getAllRights(), 'field');
        $existing  = array_column(iterator_to_array($DB->request([
            'SELECT'   => ['name'],
            'DISTINCT' => true,
            'FROM'     => ProfileRight::getTable(),
            'WHERE'    => ['name' => $all_names],
        ])), 'name');
        $new_names = array_values(array_diff($all_names, $existing));
        if ($new_names === []) {
            return;
        }

        ProfileRight::addProfileRights($new_names);

        foreach (self::DEFAULT_RIGHTS as $profile_name => $rights) {
            $rights = array_intersect_key($rights, array_flip($new_names));
            $profile = new CoreProfile();
            if ($rights === [] || !$profile->getFromDBByCrit(['name' => $profile_name])) {
                continue;
            }
            ProfileRight::updateProfileRights($profile->getID(), $rights);

            // Berlaku langsung untuk sesi yang sedang aktif dengan profil ini (tanpa perlu login ulang)
            if (($_SESSION['glpiactiveprofile']['id'] ?? null) == $profile->getID()) {
                foreach ($rights as $name => $value) {
                    $_SESSION['glpiactiveprofile'][$name] = $value;
                }
            }
        }
    }

    public static function uninstall(): void
    {
        $names = array_column(self::getAllRights(), 'field');
        ProfileRight::deleteProfileRights($names);
        foreach ($names as $name) {
            unset($_SESSION['glpiactiveprofile'][$name]);
        }
    }
}
