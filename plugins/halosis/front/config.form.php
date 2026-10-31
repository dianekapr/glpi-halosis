<?php

/**
 * Halaman konfigurasi plugin HaloSIS.
 * Hanya untuk profil dengan hak "Konfigurasi HaloSIS" (default: Super-Admin).
 */

use Glpi\Application\View\TemplateRenderer;
use Glpi\Security\ReAuth\ReAuthManager;
use GlpiPlugin\Halosis\Ai\Client;
use GlpiPlugin\Halosis\Config;
use GlpiPlugin\Halosis\ConfigAudit;
use GlpiPlugin\Halosis\ConfigMenu;
use GlpiPlugin\Halosis\Profile;

Session::checkRight(Profile::RIGHT_CONFIG, UPDATE);

// Area sensitif (API key): minta konfirmasi password seperti halaman Profil/Pengguna di GLPI
ReAuthManager::getInstance()->checkReAuthenticationOrRedirect();

if (isset($_POST['update'])) {
    $errors = Config::saveFromForm($_POST);
    foreach ($errors as $error) {
        Session::addMessageAfterRedirect(htmlescape($error), false, ERROR);
    }
    if ($errors === []) {
        Session::addMessageAfterRedirect(__s('HaloSIS configuration saved.', 'halosis'));
    }
    Html::back();
}

// T20: pratinjau dampak ambang baru tanpa menyimpan
$config  = Config::getFormValues();
$preview = null;
if (isset($_POST['preview'])) {
    $config['triage_threshold'] = max(0, min(100, (int) ($_POST['triage_threshold'] ?? $config['triage_threshold'])));
    $config['ai_threshold_low'] = max(0, min($config['triage_threshold'], (int) ($_POST['ai_threshold_low'] ?? $config['ai_threshold_low'])));
    $preview = ConfigAudit::previewThresholds($config['triage_threshold'], $config['ai_threshold_low']);
}

Html::header(__('HaloSIS configuration', 'halosis'), '', 'config', ConfigMenu::class);

TemplateRenderer::getInstance()->display('@halosis/config.html.twig', [
    'preview'        => $preview,
    'config'         => $config,
    'providers'      => Config::getProviders(),
    'pattern_methods' => Config::getPatternMethods(),
    'features'       => Config::getFeatureLabels(),
    'is_demo'        => Config::isDemoMode(),
    'sdk_missing'    => !Client::isSdkInstalled(),
    'plugin_version' => PLUGIN_HALOSIS_VERSION,
]);
echo Html::script('/plugins/halosis/js/config.js');

Html::footer();
