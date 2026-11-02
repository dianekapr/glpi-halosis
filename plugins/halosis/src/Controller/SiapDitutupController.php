<?php

namespace GlpiPlugin\Halosis\Controller;

use Glpi\Controller\AbstractController;
use Glpi\Http\Firewall;
use Glpi\Security\Attribute\SecurityStrategy;
use GlpiPlugin\Halosis\Closure;
use GlpiPlugin\Halosis\Config;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Exception\AccessDeniedHttpException;
use Symfony\Component\Routing\Attribute\Route;
use Ticket;

/**
 * Daftar "Siap ditutup" untuk Operator (/plugins/halosis/SiapDitutup, T21): tiket Selesai tanpa respons pemohon.
 */
final class SiapDitutupController extends AbstractController
{
    public const PAGE = '/plugins/halosis/SiapDitutup';

    #[SecurityStrategy(Firewall::STRATEGY_CENTRAL_ACCESS)]
    #[Route('/SiapDitutup', name: 'siap_ditutup', methods: 'GET')]
    public function __invoke(Request $request): Response
    {
        global $CFG_GLPI;

        if (!Closure::canClose()) {
            throw new AccessDeniedHttpException();
        }
        return $this->render('@halosis/siap_ditutup.html.twig', [
            'title'    => _x('page title', 'Ready to close', 'halosis'),
            'menu'     => ['helpdesk', Ticket::class],
            'items'    => Closure::readyToClose(),
            'hours'    => (int) Config::get('close_after_hours'),
            'ajax_url' => $CFG_GLPI['root_doc'] . '/plugins/halosis/ajax/siap_ditutup.php',
        ]);
    }
}
