<?php

namespace GlpiPlugin\Halosis;

use CommonGLPI;
use Html;
use Profile as CoreProfile;
use ProfileRight;
use Session;

/**
 * Hak akses plugin HaloSIS, diatur lewat tab "HaloSIS" di form Profil GLPI.
 * Semua pengecekan akses di plugin memakai hak ini (Session::haveRight), bukan nama profil.
 */
final class Profile extends CommonGLPI
{
    /** UPDATE = membuka & menyimpan halaman konfigurasi plugin */
    public const RIGHT_CONFIG = 'plugin_halosis_config';
    /** READ = melihat panel Saran AI di tiket, UPDATE = memutuskan Terima/Ubah/Tolak */
    public const RIGHT_TRIASE = 'plugin_halosis_triase';
    /** READ = memakai chatbot self-service */
    public const RIGHT_CHATBOT = 'plugin_halosis_chatbot';
    /** READ = melihat dashboard kinerja AI */
    public const RIGHT_DASHBOARD = 'plugin_halosis_dashboard';
    /** READ = melihat Kandidat Knowledge (UC-09), UPDATE = Jadikan artikel / Abaikan */
    public const RIGHT_KANDIDAT = 'plugin_halosis_kandidat';

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
     * Definisi baris matriks hak akses (Profile::displayRightsChoiceMatrix).
     * Profil Helpdesk hanya relevan dengan chatbot; profil standar dengan fitur petugas.
     *
     * @param string|null $interface 'helpdesk', 'central', atau null untuk semua
     */
    public static function getAllRights(?string $interface = null): array
    {
        $helpdesk = [
            [
                'itemtype' => self::class,
                'label'    => __('Self-service chatbot', 'halosis'),
                'field'    => self::RIGHT_CHATBOT,
                'rights'   => [READ => __('Use')],
            ],
        ];
        $central = [
            [
                'itemtype' => self::class,
                'label'    => __('AI triage suggestions', 'halosis'),
                'field'    => self::RIGHT_TRIASE,
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
            [
                'itemtype' => self::class,
                'label'    => __('Knowledge candidates', 'halosis'),
                'field'    => self::RIGHT_KANDIDAT,
                'rights'   => [
                    READ   => __('Read'),
                    UPDATE => __('Decide (make article / dismiss)', 'halosis'),
                ],
            ],
            [
                'itemtype' => Config::class,
                'label'    => __('HaloSIS configuration', 'halosis'),
                'field'    => self::RIGHT_CONFIG,
                'rights'   => [UPDATE => __('Update')],
            ],
        ];

        return match ($interface) {
            'helpdesk' => $helpdesk,
            'central'  => $central,
            default    => array_merge($helpdesk, $central),
        };
    }

    /**
     * @return string[]
     */
    public static function getRightNames(): array
    {
        return array_column(self::getAllRights(), 'field');
    }

    public function getTabNameForItem(CommonGLPI $item, $withtemplate = 0)
    {
        if ($item instanceof CoreProfile) {
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
        $profile->displayRightsChoiceMatrix(self::getAllRights($profile->fields['interface']), [
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
     * Terapkan hak plugin ke semua profil.
     *
     * @param array<int, array<string, int>> $rights_by_profile Hak per ID profil; yang tidak disebut = 0
     * @param bool                           $override          true = timpa semua hak plugin;
     *                                                          false = hanya hak di $only_names
     * @param string[]                       $only_names        Dipakai jika $override = false
     */
    public static function applyRights(array $rights_by_profile, bool $override, array $only_names = []): void
    {
        global $DB;

        $names = $override ? self::getRightNames() : $only_names;
        if ($names === []) {
            return;
        }

        foreach ($DB->request(['SELECT' => ['id'], 'FROM' => CoreProfile::getTable()]) as $row) {
            $profiles_id = (int) $row['id'];
            $rights = [];
            foreach ($names as $name) {
                $rights[$name] = $rights_by_profile[$profiles_id][$name] ?? 0;
            }
            ProfileRight::updateProfileRights($profiles_id, $rights);

            // Berlaku langsung untuk sesi yang sedang aktif dengan profil ini (tanpa perlu login ulang)
            if (($_SESSION['glpiactiveprofile']['id'] ?? null) == $profiles_id) {
                foreach ($rights as $name => $value) {
                    $_SESSION['glpiactiveprofile'][$name] = $value;
                }
            }
        }
    }

    /**
     * Daftarkan hak plugin di semua profil dan beri nilai default untuk hak yang baru ditambahkan.
     * Hak yang sudah ada tidak diubah, supaya pengaturan admin tetap terjaga saat plugin diperbarui.
     * Hak plugin lama yang tidak dipakai lagi dihapus.
     */
    public static function install(): void
    {
        global $DB;

        $all_names = self::getRightNames();
        $existing  = array_column(iterator_to_array($DB->request([
            'SELECT'   => ['name'],
            'DISTINCT' => true,
            'FROM'     => ProfileRight::getTable(),
            'WHERE'    => ['name' => ['LIKE', 'plugin_halosis_%']],
        ])), 'name');

        $obsolete = array_values(array_diff($existing, $all_names));
        if ($obsolete !== []) {
            ProfileRight::deleteProfileRights($obsolete);
        }

        $new_names = array_values(array_diff($all_names, $existing));
        if ($new_names !== []) {
            ProfileRight::addProfileRights($new_names);
            self::applyRights(Roles::getPluginRights(), false, $new_names);
        }
    }

    public static function uninstall(): void
    {
        global $DB;

        // Termasuk hak dari versi plugin sebelumnya yang mungkin masih tersisa
        $names = array_column(iterator_to_array($DB->request([
            'SELECT'   => ['name'],
            'DISTINCT' => true,
            'FROM'     => ProfileRight::getTable(),
            'WHERE'    => ['name' => ['LIKE', 'plugin_halosis_%']],
        ])), 'name');
        ProfileRight::deleteProfileRights($names);
        foreach ($names as $name) {
            unset($_SESSION['glpiactiveprofile'][$name]);
        }
    }
}
