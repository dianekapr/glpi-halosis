<?php

namespace GlpiPlugin\Halosis\Controller;

use Glpi\Controller\AbstractController;
use Glpi\Http\Firewall;
use Glpi\Security\Attribute\SecurityStrategy;
use GlpiPlugin\Halosis\Candidate;
use GlpiPlugin\Halosis\KnowledgeCandidates;
use GlpiPlugin\Halosis\Profile;
use KnowbaseItem;
use Session;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Exception\AccessDeniedHttpException;
use Symfony\Component\Routing\Attribute\Route;
use Ticket;

/**
 * Halaman Kandidat Knowledge (/plugins/halosis/Kandidat) untuk Knowledge Manager & Administrator (UC-09).
 * Setiap kali dibuka, kandidat baru disinkronkan dari tiket selesai dan layanan AI.
 */
final class KandidatController extends AbstractController
{
    public const PAGE = '/plugins/halosis/Kandidat';

    #[SecurityStrategy(Firewall::STRATEGY_CENTRAL_ACCESS)]
    #[Route('/Kandidat', name: 'kandidat', methods: 'GET')]
    public function __invoke(Request $request): Response
    {
        global $CFG_GLPI;

        if (!Session::haveRight(Profile::RIGHT_KANDIDAT, READ)) {
            throw new AccessDeniedHttpException();
        }

        $sync   = KnowledgeCandidates::sync();
        $status = (string) $request->query->get('status', Candidate::STATUS_PENDING);
        if (!in_array($status, [Candidate::STATUS_PENDING, Candidate::STATUS_ARTICLE, Candidate::STATUS_IGNORED], true)) {
            $status = Candidate::STATUS_PENDING;
        }

        $items = array_map(static fn (array $c) => $c + [
            'ticket_url'  => $c['tickets_id'] > 0 ? Ticket::getFormURLWithID((int) $c['tickets_id']) : '',
            'article_url' => $c['knowbaseitems_id'] > 0 ? KnowbaseItem::getFormURLWithID((int) $c['knowbaseitems_id']) : '',
        ], KnowledgeCandidates::list($status));

        return $this->render('@halosis/kandidat.html.twig', [
            'title'      => __('Knowledge candidates', 'halosis'),
            'menu'       => ['tools', KnowbaseItem::class],
            'status'     => $status,
            'counts'     => KnowledgeCandidates::counts(),
            'items'      => $items,
            'sync'       => $sync,
            'can_decide' => Session::haveRight(Profile::RIGHT_KANDIDAT, UPDATE),
            'ajax_url'   => $CFG_GLPI['root_doc'] . '/plugins/halosis/ajax/kandidat.php',
            'min_reason' => \GlpiPlugin\Halosis\Triage::MIN_REASON_LENGTH,
        ]);
    }
}
