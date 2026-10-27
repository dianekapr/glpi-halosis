<?php

namespace GlpiPlugin\Halosis\Controller;

use Glpi\Controller\AbstractController;
use Glpi\Form\ServiceCatalog\ServiceCatalog;
use Glpi\Http\Firewall;
use Glpi\Security\Attribute\SecurityStrategy;
use GlpiPlugin\Halosis\Chatbot;
use GlpiPlugin\Halosis\Config;
use GlpiPlugin\Halosis\HelpdeskHome;
use KnowbaseItem;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Exception\AccessDeniedHttpException;
use Symfony\Component\Routing\Attribute\Route;

/**
 * Halaman penuh "Tanya HaloSIS" (/plugins/halosis/Chat), beranda Pegawai di antarmuka Helpdesk.
 * Dirender di layout Helpdesk GLPI; logika percakapan dipakai bersama dengan widget (Chatbot, ajax/chat.php).
 */
final class ChatController extends AbstractController
{
    #[SecurityStrategy(Firewall::STRATEGY_HELPDESK_ACCESS)]
    #[Route('/Chat', name: 'chat', methods: 'GET')]
    public function __invoke(Request $request): Response
    {
        global $CFG_GLPI;

        if (!Chatbot::canUse()) {
            throw new AccessDeniedHttpException();
        }

        return $this->render('@halosis/chat_page.html.twig', [
            'title'       => __('Ask HaloSIS', 'halosis'),
            'menu'        => [HelpdeskHome::MENU_KEY],
            // Hak ada tapi fitur chat dimatikan admin → tampilkan pesan + tombol buat laporan
            'available'   => Config::isFeatureEnabled('chat'),
            'ajax_url'    => $CFG_GLPI['root_doc'] . '/plugins/halosis/ajax/chat.php',
            'max_length'  => Chatbot::MAX_MESSAGE_LENGTH,
            'user_name'   => $_SESSION['glpifirstname'] ?? '',
            'report_url'  => ServiceCatalog::getSearchURL(),
            'faq_url'     => KnowbaseItem::getSearchURL(),
            'suggestions' => [
                __('Forgot my SSO password', 'halosis'),
                __('FASIH fails to sync', 'halosis'),
                __('VPN keeps disconnecting', 'halosis'),
                __('Email attachment is too large', 'halosis'),
            ],
        ]);
    }
}
