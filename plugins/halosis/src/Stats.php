<?php

namespace GlpiPlugin\Halosis;

use CommonITILActor;
use CommonITILObject;
use DateTimeImmutable;
use Glpi\DBAL\QuerySubQuery;
use Group_Ticket;
use ITILCategory;
use Problem;
use Ticket;

/**
 * Angka dashboard kinerja AI, dihitung dari tabel log plugin saja:
 * keputusan (decisions), saran (suggestions), pemindahan tim (reassignments), percakapan (chats).
 */
final class Stats
{
    public const ALLOWED_WEEKS = [4, 8, 12];
    public const DEFAULT_WEEKS = 8;

    /** Bulan terakhir pada tren drift (rasio Ubah+Tolak per bulan, BP-19) */
    public const DRIFT_MONTHS = 6;

    /** Urutan seri tetap (warna mengikuti entitas, bukan peringkat) */
    public const ACTIONS = [Decision::ACTION_ACCEPT, Decision::ACTION_MODIFY, Decision::ACTION_REJECT];

    /**
     * @return array<string, mixed>
     */
    public static function collect(int $weeks, int $groups_id = 0, int $categories_id = 0): array
    {
        $weeks = in_array($weeks, self::ALLOWED_WEEKS, true) ? $weeks : self::DEFAULT_WEEKS;
        $start = self::periodStart($weeks);
        $filter = self::ticketFilter($groups_id, $categories_id);

        $decisions = self::decisions($start, $filter);
        return [
            'weeks'        => $weeks,
            'since'        => $start->format('Y-m-d'),
            'filter'       => ['groups_id' => $groups_id, 'categories_id' => $categories_id],
            'drift'        => self::drift($filter),
            'patterns'     => self::patterns($start),
            'unhelpful'    => self::unhelpfulArticles($start),
            'decisions'    => self::decisionTotals($decisions),
            'weekly'       => self::weekly($decisions, $start, $weeks),
            'by_band'      => self::byConfidenceBand($decisions),
            'reassigned'   => self::reassigned($decisions),
            'chats'        => self::chats($start),
            'articles'     => self::articleUsage($start),
            'threshold'    => Config::getTriageThreshold(),
        ];
    }

    /**
     * Awal periode: Senin pada minggu ke-(N-1) sebelum minggu ini.
     */
    private static function periodStart(int $weeks): DateTimeImmutable
    {
        $now = new DateTimeImmutable($_SESSION['glpi_currenttime'] ?? 'now');
        return $now->modify('monday this week')->setTime(0, 0)->modify('-' . ($weeks - 1) . ' weeks');
    }

    /**
     * Filter dashboard per tim (grup yang ditugaskan) dan kategori layanan (termasuk subkategori), T18.
     * Berlaku untuk angka triase (keputusan, salah tim, drift); angka chatbot & pola tidak terkait tiket.
     *
     * @return array<string, mixed> Kriteria WHERE atas d.tickets_id
     */
    private static function ticketFilter(int $groups_id, int $categories_id): array
    {
        $where = [];
        if ($groups_id > 0) {
            $where[] = ['d.tickets_id' => new QuerySubQuery([
                'SELECT' => 'tickets_id',
                'FROM'   => Group_Ticket::getTable(),
                'WHERE'  => ['groups_id' => $groups_id, 'type' => CommonITILActor::ASSIGN],
            ])];
        }
        if ($categories_id > 0) {
            $where[] = ['d.tickets_id' => new QuerySubQuery([
                'SELECT' => 'id',
                'FROM'   => Ticket::getTable(),
                'WHERE'  => ['itilcategories_id' => getSonsOf(ITILCategory::getTable(), $categories_id)],
            ])];
        }
        return $where;
    }

    /**
     * Pilihan filter: grup yang bisa ditugaskan & kategori layanan.
     *
     * @return array{groups: array<int, string>, categories: array<int, string>}
     */
    public static function filterOptions(): array
    {
        global $DB;

        $options = ['groups' => [], 'categories' => []];
        foreach ($DB->request(['SELECT' => ['id', 'name'], 'FROM' => \Group::getTable(), 'WHERE' => ['is_assign' => 1], 'ORDER' => 'name']) as $row) {
            $options['groups'][(int) $row['id']] = (string) $row['name'];
        }
        foreach ($DB->request(['SELECT' => ['id', 'completename'], 'FROM' => ITILCategory::getTable(), 'ORDER' => 'completename']) as $row) {
            $options['categories'][(int) $row['id']] = (string) $row['completename'];
        }
        return $options;
    }

    /**
     * Keputusan dalam periode, dengan keyakinan saran terkait.
     *
     * @return array<int, array{action: string, date: string, tickets_id: int, confidence: int}>
     */
    private static function decisions(DateTimeImmutable $start, array $filter = []): array
    {
        global $DB;

        $rows = [];
        foreach ($DB->request([
            'SELECT'    => ['d.action', 'd.date_creation', 'd.tickets_id', 's.confidence'],
            'FROM'      => Decision::getTable() . ' AS d',
            'LEFT JOIN' => [
                Suggestion::getTable() . ' AS s' => ['ON' => ['d' => 'suggestions_id', 's' => 'id']],
            ],
            'WHERE'     => ['d.date_creation' => ['>=', $start->format('Y-m-d H:i:s')]] + $filter,
            'ORDER'     => 'd.id',
        ]) as $row) {
            $rows[] = [
                'action'     => (string) $row['action'],
                'date'       => (string) $row['date_creation'],
                'tickets_id' => (int) $row['tickets_id'],
                'confidence' => (int) $row['confidence'],
            ];
        }
        return $rows;
    }

    /**
     * Jumlah & persentase per keputusan.
     */
    private static function decisionTotals(array $decisions): array
    {
        $counts = array_fill_keys(self::ACTIONS, 0);
        foreach ($decisions as $decision) {
            if (isset($counts[$decision['action']])) {
                $counts[$decision['action']]++;
            }
        }
        $total = array_sum($counts);
        $percent = [];
        foreach ($counts as $action => $count) {
            $percent[$action] = $total > 0 ? round($count * 100 / $total) : 0;
        }
        return ['total' => $total, 'counts' => $counts, 'percent' => $percent];
    }

    /**
     * Keputusan per minggu (Senin–Minggu), termasuk minggu tanpa data.
     *
     * @return array<int, array{start: string, label: string, counts: array<string, int>, total: int}>
     */
    private static function weekly(array $decisions, DateTimeImmutable $start, int $weeks): array
    {
        $buckets = [];
        for ($i = 0; $i < $weeks; $i++) {
            $week = $start->modify("+{$i} weeks");
            $buckets[$week->format('Y-m-d')] = [
                'start'  => $week->format('Y-m-d'),
                'label'  => $week->format('d/m'),
                'counts' => array_fill_keys(self::ACTIONS, 0),
                'total'  => 0,
            ];
        }
        foreach ($decisions as $decision) {
            $key = (new DateTimeImmutable($decision['date']))->modify('monday this week')->format('Y-m-d');
            if (isset($buckets[$key]['counts'][$decision['action']])) {
                $buckets[$key]['counts'][$decision['action']]++;
                $buckets[$key]['total']++;
            }
        }
        return array_values($buckets);
    }

    /**
     * Keputusan per pita keyakinan (di atas / di bawah ambang): apakah keyakinan AI selaras dengan petugas?
     */
    private static function byConfidenceBand(array $decisions): array
    {
        $threshold = Config::getTriageThreshold();
        $bands = ['above' => [], 'below' => []];
        foreach ($decisions as $decision) {
            $bands[$decision['confidence'] >= $threshold ? 'above' : 'below'][] = $decision;
        }
        return array_map([self::class, 'decisionTotals'], $bands);
    }

    /**
     * Tiket yang triasenya diterapkan (Terima/Ubah) lalu dipindah ke grup lain atau dikembalikan ke operator.
     */
    private static function reassigned(array $decisions): array
    {
        global $DB;

        $applied = array_values(array_unique(array_column(array_filter(
            $decisions,
            static fn ($d) => in_array($d['action'], [Decision::ACTION_ACCEPT, Decision::ACTION_MODIFY], true),
        ), 'tickets_id')));

        $moved = $returned = 0;
        if ($applied !== []) {
            $count = static fn (array $where) => (int) ($DB->request([
                'SELECT' => ['COUNT DISTINCT' => 'tickets_id AS cpt'],
                'FROM'   => Reassignment::getTable(),
                'WHERE'  => ['tickets_id' => $applied] + $where,
            ])->current()['cpt'] ?? 0);
            $moved = $count([]);
            // UC-06: dikembalikan Tim Teknis ke operator (bagian dari "salah tim")
            $returned = $count(['kind' => Reassignment::KIND_RETURN]);
        }

        return [
            'applied'  => count($applied),
            'moved'    => $moved,
            'returned' => $returned,
            'percent' => count($applied) > 0 ? round($moved * 100 / count($applied)) : 0,
        ];
    }

    /**
     * Indikator drift (BP-19): rasio Ubah+Tolak per bulan kalender, DRIFT_MONTHS bulan terakhir.
     *
     * @return array<int, array{label: string, total: int, overridden: int, percent: ?int}>
     */
    private static function drift(array $filter): array
    {
        $now = new DateTimeImmutable($_SESSION['glpi_currenttime'] ?? 'now');
        $first = $now->modify('first day of this month')->setTime(0, 0)->modify('-' . (self::DRIFT_MONTHS - 1) . ' months');
        $months = [];
        for ($i = 0; $i < self::DRIFT_MONTHS; $i++) {
            $month = $first->modify("+{$i} months");
            $months[$month->format('Y-m')] = ['label' => $month->format('m/Y'), 'total' => 0, 'overridden' => 0, 'percent' => null];
        }
        foreach (self::decisions($first, $filter) as $decision) {
            $key = substr($decision['date'], 0, 7);
            if (!isset($months[$key]) || !in_array($decision['action'], self::ACTIONS, true)) {
                continue;
            }
            $months[$key]['total']++;
            $months[$key]['overridden'] += (int) ($decision['action'] !== Decision::ACTION_ACCEPT);
        }
        foreach ($months as &$month) {
            $month['percent'] = $month['total'] > 0 ? (int) round($month['overridden'] * 100 / $month['total']) : null;
        }
        return array_values($months);
    }

    /**
     * Pola insiden dalam periode (BP-17): terdeteksi, dikonfirmasi (Problem sudah ditangani: status lepas dari
     * Baru), ditutup (Selesai/Ditutup atau dihapus sebagai pola palsu).
     *
     * @return array{detected: int, confirmed: int, closed: int}
     */
    private static function patterns(DateTimeImmutable $start): array
    {
        global $DB;

        $counts = ['detected' => 0, 'confirmed' => 0, 'closed' => 0];
        foreach ($DB->request([
            'SELECT'    => ['pr.status', 'pr.is_deleted'],
            'FROM'      => PatternDetector::getTable() . ' AS p',
            'LEFT JOIN' => [Problem::getTable() . ' AS pr' => ['ON' => ['p' => 'problems_id', 'pr' => 'id']]],
            'WHERE'     => ['p.date_creation' => ['>=', $start->format('Y-m-d H:i:s')]],
        ]) as $row) {
            $counts['detected']++;
            $status = (int) $row['status'];
            if ($row['status'] === null || (int) $row['is_deleted'] === 1 || in_array($status, [CommonITILObject::SOLVED, CommonITILObject::CLOSED], true)) {
                $counts['closed']++;
            } elseif ($status !== CommonITILObject::INCOMING) {
                $counts['confirmed']++;
            }
        }
        return $counts;
    }

    /**
     * Artikel dengan umpan balik "tidak membantu" terbanyak (BP-13): percakapan chatbot yang mengutip artikel
     * lalu berakhir jadi laporan atau rating ≤ 2, ditambah penilaian "Tidak membantu" agent di Cari knowledge.
     *
     * @return array<int, array{name: string, url: string, chat: int, agent: int, total: int}>
     */
    private static function unhelpfulArticles(DateTimeImmutable $start, int $limit = 5): array
    {
        global $DB;

        $since = $start->format('Y-m-d H:i:s');
        $counts = [];
        foreach ($DB->request([
            'SELECT'     => ['au.knowbaseitems_id', 'COUNT DISTINCT' => 'au.chats_id AS cpt'],
            'FROM'       => 'glpi_plugin_halosis_article_uses AS au',
            'INNER JOIN' => [Chat::getTable() . ' AS c' => ['ON' => ['au' => 'chats_id', 'c' => 'id']]],
            'WHERE'      => [
                'au.date_creation' => ['>=', $since],
                'OR'               => ['c.status' => Chat::STATUS_TICKET, 'c.rating' => ['<=', 2]],
            ],
            'GROUPBY'    => 'au.knowbaseitems_id',
        ]) as $row) {
            $counts[(int) $row['knowbaseitems_id']]['chat'] = (int) $row['cpt'];
        }
        foreach ($DB->request([
            'SELECT'  => ['knowbaseitems_id', 'COUNT' => 'id AS cpt'],
            'FROM'    => 'glpi_plugin_halosis_feedback',
            'WHERE'   => ['is_helpful' => 0, 'knowbaseitems_id' => ['>', 0], 'date_creation' => ['>=', $since]],
            'GROUPBY' => 'knowbaseitems_id',
        ]) as $row) {
            $counts[(int) $row['knowbaseitems_id']]['agent'] = (int) $row['cpt'];
        }

        $rows = [];
        foreach ($counts as $kb_id => $c) {
            $article = new \KnowbaseItem();
            if (!$article->getFromDB($kb_id)) {
                continue;
            }
            $chat = $c['chat'] ?? 0;
            $agent = $c['agent'] ?? 0;
            $rows[] = ['name' => (string) $article->fields['name'], 'url' => \KnowbaseItem::getFormURLWithID($kb_id), 'chat' => $chat, 'agent' => $agent, 'total' => $chat + $agent];
        }
        usort($rows, static fn ($a, $b) => $b['total'] <=> $a['total']);
        return array_slice($rows, 0, $limit);
    }

    /**
     * Artikel KB yang paling sering dikutip chatbot dalam periode.
     *
     * @return array<int, array{name: string, url: string, uses: int}>
     */
    private static function articleUsage(DateTimeImmutable $start, int $limit = 5): array
    {
        global $DB;

        $rows = [];
        foreach ($DB->request([
            'SELECT'  => ['knowbaseitems_id', 'COUNT' => 'id AS uses'],
            'FROM'    => 'glpi_plugin_halosis_article_uses',
            'WHERE'   => ['date_creation' => ['>=', $start->format('Y-m-d H:i:s')]],
            'GROUPBY' => 'knowbaseitems_id',
            'ORDER'   => 'uses DESC',
            'LIMIT'   => $limit,
        ]) as $row) {
            $article = new \KnowbaseItem();
            if ($article->getFromDB((int) $row['knowbaseitems_id'])) {
                $rows[] = ['name' => (string) $article->fields['name'], 'url' => \KnowbaseItem::getFormURLWithID($article->getID()), 'uses' => (int) $row['uses']];
            }
        }
        return $rows;
    }

    /**
     * Percakapan chatbot: terbantu tanpa tiket, jadi laporan, rating rata-rata.
     */
    private static function chats(DateTimeImmutable $start): array
    {
        global $DB;

        Chat::expireIdle();
        $counts = ['total' => 0, Chat::STATUS_RESOLVED => 0, Chat::STATUS_TICKET => 0, Chat::STATUS_OPEN => 0];
        $ratings = [];
        foreach ($DB->request([
            'SELECT' => ['status', 'rating'],
            'FROM'   => Chat::getTable(),
            'WHERE'  => ['date_creation' => ['>=', $start->format('Y-m-d H:i:s')]],
        ]) as $row) {
            $counts['total']++;
            if (isset($counts[$row['status']])) {
                $counts[$row['status']]++;
            }
            if ($row['rating'] !== null) {
                $ratings[] = (int) $row['rating'];
            }
        }

        $resolved = $counts[Chat::STATUS_RESOLVED];
        return [
            'total'          => $counts['total'],
            'resolved'       => $resolved,
            'ticket'         => $counts[Chat::STATUS_TICKET],
            'open'           => $counts[Chat::STATUS_OPEN],
            'resolved_pct'   => $counts['total'] > 0 ? round($resolved * 100 / $counts['total']) : 0,
            'rating_avg'     => $ratings !== [] ? round(array_sum($ratings) / count($ratings), 1) : null,
            'rating_count'   => count($ratings),
        ];
    }

    /**
     * Geometri kolom bertumpuk untuk SVG (dihitung di server, tanpa pustaka grafik).
     * Spesifikasi: kolom ≤ 24px, ujung atas membulat 4px & rata di garis dasar, celah 2px antar-segmen.
     */
    public static function stackedColumns(array $weekly, int $width = 720, int $height = 240): array
    {
        $pad = ['top' => 24, 'right' => 8, 'bottom' => 28, 'left' => 36];
        $plot_w = $width - $pad['left'] - $pad['right'];
        $plot_h = $height - $pad['top'] - $pad['bottom'];

        $max  = max(1, ...array_column($weekly, 'total'));
        $step = self::niceStep($max / 4);
        $top  = (int) (ceil($max / $step) * $step);

        $ticks = [];
        for ($v = 0; $v <= $top; $v += $step) {
            $ticks[] = ['value' => $v, 'y' => round($pad['top'] + $plot_h - $v / $top * $plot_h, 1)];
        }

        $band  = $plot_w / max(1, count($weekly));
        $bar_w = min(24, $band * 0.5);
        $gap   = 2;
        $columns = [];
        foreach ($weekly as $i => $week) {
            $x = $pad['left'] + $band * $i + ($band - $bar_w) / 2;
            $y = $pad['top'] + $plot_h;
            $segments = [];
            $visible = array_values(array_filter(self::ACTIONS, static fn ($a) => $week['counts'][$a] > 0));
            foreach ($visible as $j => $action) {
                $h = $week['counts'][$action] / $top * $plot_h;
                $y -= $h;
                $is_top = $j === count($visible) - 1;
                // Celah 2px di atas tiap segmen kecuali yang paling atas
                $segments[] = [
                    'action' => $action,
                    'path'   => self::columnPath($x, $y + ($is_top ? 0 : $gap), $bar_w, max(1, $h - ($is_top ? 0 : $gap)), $is_top ? 4 : 0),
                ];
            }
            $columns[] = [
                'x'        => round($x, 1),
                'center'   => round($x + $bar_w / 2, 1),
                'top'      => round($y, 1),
                'band_x'   => round($pad['left'] + $band * $i, 1),
                'band_w'   => round($band, 1),
                'segments' => $segments,
                'week'     => $week,
            ];
        }

        return [
            'width'    => $width,
            'height'   => $height,
            'plot'     => ['left' => $pad['left'], 'right' => $width - $pad['right'], 'top' => $pad['top'], 'bottom' => $pad['top'] + $plot_h],
            'ticks'    => $ticks,
            'columns'  => $columns,
            'baseline' => $pad['top'] + $plot_h,
        ];
    }

    /**
     * Path batang: ujung atas membulat (r), dasar persegi.
     */
    private static function columnPath(float $x, float $y, float $w, float $h, float $r): string
    {
        $r = min($r, $w / 2, $h);
        $f = static fn (float $n): string => (string) round($n, 2);
        return sprintf(
            'M%s %s V%s Q%s %s %s %s H%s Q%s %s %s %s V%s Z',
            $f($x), $f($y + $h),
            $f($y + $r), $f($x), $f($y), $f($x + $r), $f($y),
            $f($x + $w - $r), $f($x + $w), $f($y), $f($x + $w), $f($y + $r),
            $f($y + $h),
        );
    }

    private static function niceStep(float $raw): int
    {
        foreach ([1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000] as $step) {
            if ($raw <= $step) {
                return $step;
            }
        }
        return (int) (ceil($raw / 1000) * 1000);
    }

    /**
     * Keputusan Ubah/Tolak sebagai data koreksi untuk melatih ulang model (T10, tata_kelola_ai.md §2 langkah 1b).
     * Judul, deskripsi, dan alasan disamarkan (Privacy); tim final = grup final keputusan, atau grup yang kini
     * ditugaskan pada tiket (Tolak = triase manual).
     *
     * @return array<int, array<string, string|int>>
     */
    public static function corrections(): array
    {
        global $DB;

        $rows = [];
        foreach ($DB->request([
            'SELECT'     => ['d.date_creation', 'd.tickets_id', 'd.action', 'd.final_values', 'd.reason', 's.groups_id', 's.itilcategories_id', 's.model', 't.name', 't.content', 't.type'],
            'FROM'       => Decision::getTable() . ' AS d',
            'INNER JOIN' => [Ticket::getTable() . ' AS t' => ['ON' => ['d' => 'tickets_id', 't' => 'id']]],
            'LEFT JOIN'  => [Suggestion::getTable() . ' AS s' => ['ON' => ['d' => 'suggestions_id', 's' => 'id']]],
            'WHERE'      => ['d.action' => [Decision::ACTION_MODIFY, Decision::ACTION_REJECT]],
            'ORDER'      => 'd.id',
        ]) as $row) {
            $final = json_decode((string) $row['final_values'], true) ?: [];
            $group = (int) ($final['groups_id'] ?? 0) ?: (int) ($DB->request([
                'SELECT' => 'groups_id',
                'FROM'   => Group_Ticket::getTable(),
                'WHERE'  => ['tickets_id' => $row['tickets_id'], 'type' => CommonITILActor::ASSIGN],
                'ORDER'  => 'id DESC',
                'LIMIT'  => 1,
            ])->current()['groups_id'] ?? 0);
            $rows[] = [
                'tanggal'        => (string) $row['date_creation'],
                'tiket'          => (int) $row['tickets_id'],
                'jenis'          => (int) $row['type'] === Ticket::DEMAND_TYPE ? 'REQ' : 'INC',
                'judul'          => Privacy::mask((string) $row['name'])['text'],
                'deskripsi'      => mb_substr(Privacy::mask(KnowledgeSearch::plainText((string) $row['content']))['text'], 0, 2000),
                'keputusan'      => (string) $row['action'],
                'tim_saran'      => Suggestion::groupName((int) $row['groups_id']),
                'tim_final'      => $group > 0 ? Suggestion::groupName($group) : '',
                'kategori_saran' => Suggestion::categoryName((int) $row['itilcategories_id']),
                'kategori_final' => isset($final['itilcategories_id']) ? Suggestion::categoryName((int) $final['itilcategories_id']) : '',
                'alasan'         => Privacy::mask((string) $row['reason'])['text'],
                'model'          => (string) $row['model'],
            ];
        }
        return $rows;
    }
}
