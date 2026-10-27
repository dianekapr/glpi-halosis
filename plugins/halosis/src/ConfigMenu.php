<?php

namespace GlpiPlugin\Halosis;

use CommonGLPI;
use Session;

/**
 * Entri menu Setup › "AI HaloSIS" menuju halaman konfigurasi plugin.
 * Diperlukan karena Administrator berhak mengatur plugin tanpa hak konfigurasi GLPI
 * (sehingga tidak bisa membuka Setup › Plugins).
 */
final class ConfigMenu extends CommonGLPI
{
    public const PAGE = '/plugins/halosis/front/config.form.php';

    public static string $rightname = Profile::RIGHT_CONFIG;

    public static function getTypeName($nb = 0)
    {
        return __('HaloSIS AI', 'halosis');
    }

    public static function getIcon()
    {
        return 'ti ti-sparkles';
    }

    public static function getMenuContent()
    {
        if (!Session::haveRight(Profile::RIGHT_CONFIG, UPDATE)) {
            return false;
        }

        return [
            'title' => self::getTypeName(),
            'page'  => self::PAGE,
            'icon'  => self::getIcon(),
        ];
    }
}
