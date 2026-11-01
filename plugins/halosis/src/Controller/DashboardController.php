<?php

namespace GlpiPlugin\Halosis\Controller;

use Glpi\Controller\AbstractController;
use Glpi\Http\Firewall;
use Glpi\Security\Attribute\SecurityStrategy;
use GlpiPlugin\Halosis\DashboardMenu;
use GlpiPlugin\Halosis\Profile;
use GlpiPlugin\Halosis\Stats;
use Session;
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
        global $CFG_GLPI;

        if (!DashboardMenu::canViewDashboard()) {
            throw new AccessDeniedHttpException();
        }

        $stats = Stats::collect(
            (int) $request->query->get('weeks', Stats::DEFAULT_WEEKS),
            (int) $request->query->get('group', 0),
            (int) $request->query->get('category', 0),
        );

        return $this->render('@halosis/dashboard.html.twig', [
            'title'   => __('AI performance', 'halosis'),
            'menu'    => ['helpdesk', DashboardMenu::class],
            'stats'   => $stats,
            'chart'   => Stats::stackedColumns($stats['weekly']),
            'periods' => Stats::ALLOWED_WEEKS,
            'options' => Stats::filterOptions(),
            'can_export' => Session::haveRight(Profile::RIGHT_CONFIG, UPDATE),
            'export_url' => $CFG_GLPI['root_doc'] . '/plugins/halosis/Dashboard/Koreksi',
            'colors'  => [
                // Palet kategori tervalidasi (validate_palette.js): diturunkan dari teal & oranye HaloSIS,
                // lolos pita kecerahan, kroma, dan pemisahan buta warna (ΔE ≥ 16).
                'accept' => '#00826F',
                'modify' => '#62C9AF',
                'reject' => '#D8652A',
            ],
        ]);
    }

    /**
     * T10: unduh keputusan Ubah/Tolak (CSV, tersamar) sebagai data koreksi untuk latih ulang model.
     * Hanya pemegang hak Pengaturan AI (plugin_halosis_config).
     */
    #[SecurityStrategy(Firewall::STRATEGY_CENTRAL_ACCESS)]
    #[Route('/Dashboard/Koreksi', name: 'dashboard_koreksi', methods: 'GET')]
    public function corrections(): Response
    {
        if (!Session::haveRight(Profile::RIGHT_CONFIG, UPDATE)) {
            throw new AccessDeniedHttpException();
        }

        $rows = Stats::corrections();
        $out = fopen('php://temp', 'r+');
        fputcsv($out, $rows !== [] ? array_keys($rows[0]) : ['tanggal', 'tiket', 'jenis', 'judul', 'deskripsi', 'keputusan', 'tim_saran', 'tim_final', 'kategori_saran', 'kategori_final', 'alasan', 'model'], escape: '');
        foreach ($rows as $row) {
            fputcsv($out, $row, escape: '');
        }
        rewind($out);

        return new Response("\xEF\xBB\xBF" . stream_get_contents($out), 200, [
            'Content-Type'        => 'text/csv; charset=UTF-8',
            'Content-Disposition' => 'attachment; filename="halosis-koreksi-' . date('Ymd') . '.csv"',
        ]);
    }
}
