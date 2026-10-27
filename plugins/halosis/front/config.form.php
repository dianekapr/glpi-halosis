<?php

/**
 * Halaman konfigurasi plugin HaloSIS.
 * Hanya untuk profil dengan hak "Konfigurasi HaloSIS" (default: Super-Admin).
 */

use Glpi\Application\View\TemplateRenderer;
use Glpi\Security\ReAuth\ReAuthManager;
use GlpiPlugin\Halosis\Ai\Client;
use GlpiPlugin\Halosis\Config;
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

Html::header(__('HaloSIS configuration', 'halosis'), '', 'config', ConfigMenu::class);

TemplateRenderer::getInstance()->display('@halosis/config.html.twig', [
    'config'         => Config::getFormValues(),
    'providers'      => Config::getProviders(),
    'features'       => Config::getFeatureLabels(),
    'is_demo'        => Config::isDemoMode(),
    'sdk_missing'    => !Client::isSdkInstalled(),
    'plugin_version' => PLUGIN_HALOSIS_VERSION,
]);
echo Html::script('/plugins/halosis/js/config.js');

Html::footer();
