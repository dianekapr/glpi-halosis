<?php

namespace GlpiPlugin\Halosis\Controller;

use Glpi\Controller\AbstractController;
use Glpi\Http\Firewall;
use Glpi\Security\Attribute\SecurityStrategy;
use GlpiPlugin\Halosis\DashboardMenu;
use GlpiPlugin\Halosis\Stats;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Exception\AccessDeniedHttpException;
use Symfony\Component\Routing\Attribute\Route;

/**
 * Dashboard kinerja AI (/plugins/halosis/Dashboard) untuk Manajemen (Observer), Administrator, Super-Admin.
 * Semua angka berasal dari tabel log plugin (lihat Stats).
 */
final class DashboardController extends AbstractController
{
    #[SecurityStrategy(Firewall::STRATEGY_CENTRAL_ACCESS)]
    #[Route('/Dashboard', name: 'dashboard', methods: 'GET')]
    public function __invoke(Request $request): Response
    {
        if (!DashboardMenu::canViewDashboard()) {
            throw new AccessDeniedHttpException();
        }

        $stats = Stats::collect((int) $request->query->get('weeks', Stats::DEFAULT_WEEKS));

        return $this->render('@halosis/dashboard.html.twig', [
            'title'   => __('AI performance', 'halosis'),
            'menu'    => ['helpdesk', DashboardMenu::class],
            'stats'   => $stats,
            'chart'   => Stats::stackedColumns($stats['weekly']),
            'periods' => Stats::ALLOWED_WEEKS,
            'colors'  => [
                // Palet kategori tervalidasi (validate_palette.js): diturunkan dari teal & oranye HaloSIS,
                // lolos pita kecerahan, kroma, dan pemisahan buta warna (ΔE ≥ 16).
                'accept' => '#00826F',
                'modify' => '#62C9AF',
                'reject' => '#D8652A',
            ],
        ]);
    }
}
