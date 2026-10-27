<?php

namespace GlpiPlugin\Halosis;

use CommonGLPI;
use Session;

/**
 * Entri menu Bantuan › "Kinerja AI" menuju dashboard kinerja AI (pemegang hak dashboard, fitur aktif).
 */
final class DashboardMenu extends CommonGLPI
{
    public const PAGE = '/plugins/halosis/Dashboard';

    public static string $rightname = Profile::RIGHT_DASHBOARD;

    public static function getTypeName($nb = 0)
    {
        return __('AI performance', 'halosis');
    }

    public static function getIcon()
    {
        return 'ti ti-chart-bar';
    }

    public static function canViewDashboard(): bool
    {
        return Config::isFeatureEnabled('dashboard') && Session::haveRight(Profile::RIGHT_DASHBOARD, READ);
    }

    public static function getMenuContent()
    {
        if (!self::canViewDashboard()) {
            return false;
        }

        return [
            'title' => self::getTypeName(),
            'page'  => self::PAGE,
            'icon'  => self::getIcon(),
        ];
    }
}
