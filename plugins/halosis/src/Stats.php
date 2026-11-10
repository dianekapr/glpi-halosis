<?php

namespace GlpiPlugin\Halosis;

use CommonITILActor;
use CommonITILObject;
use DateTimeImmutable;
use Glpi\DBAL\QuerySubQuery;
use Group_Ticket;
use ITILCategory;
use ITILFollowup;
use Problem;
use ProblemTask;
use Problem_Ticket;
use Ticket;
use Ticket_User;
use TicketSatisfaction;

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
            'kpi'          => self::serviceKpi($start, $categories_id),
            'baseline'     => self::baseline(),
            'volume'       => self::ticketVolume(),
            'patterns'     => self::patterns($start),
            'pattern_trend' => self::patternTrend(),
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
     * Baseline pembanding (`ai/scripts/baseline.py` → baseline.json): angka dokumen (overall 27,59% / respons 42,62%)
     * dan history ESTIM versi baru (overall_sla_result_extended & response_sla_final_result MET ÷ MET + OVERDUE,
     * termasuk jumlah hasil berimputasi) & kepuasan (% rating ≥ 4, cakupan rating). Beda metode: `metode` di JSON.
     * Null bila berkas belum dibuat.
     *
     * @return array<string, mixed>|null
     */
    public static function baseline(): ?array
    {
        $path = dirname(__DIR__) . '/baseline.json';
        $data = is_readable($path) ? json_decode((string) file_get_contents($path), true) : null;
        return is_array($data) && isset($data['sla'], $data['kepuasan']) ? $data : null;
    }

    /**
     * Kepuasan pemohon dari survei GLPI (tiket dibuka dalam periode, survei sudah dijawab): % skor ≥ 4 dari 5,
     * sebanding baseline rating ESTIM.
     *
     * @return array{answered: int, satisfied_pct: ?float}
     */
    private static function satisfaction(DateTimeImmutable $start, int $categories_id = 0): array
    {
        global $DB;

        $where = ['t.is_deleted' => 0, 't.date' => ['>=', $start->format('Y-m-d H:i:s')], 'NOT' => ['s.date_answered' => null]];
        if ($categories_id > 0) {
            $where['t.itilcategories_id'] = getSonsOf(ITILCategory::getTable(), $categories_id);
        }
        $answered = $satisfied = 0;
        foreach ($DB->request([
            'SELECT'     => ['s.satisfaction', 's.satisfaction_scaled_to_5'],
            'FROM'       => TicketSatisfaction::getTable() . ' AS s',
            'INNER JOIN' => [Ticket::getTable() . ' AS t' => ['ON' => ['s' => 'tickets_id', 't' => 'id']]],
            'WHERE'      => $where,
        ]) as $row) {
            $score = $row['satisfaction_scaled_to_5'] !== null ? (float) $row['satisfaction_scaled_to_5'] : (float) $row['satisfaction'];
            if ($score > 0) {
                $answered++;
                $satisfied += (int) ($score >= 4);
            }
        }
        return ['answered' => $answered, 'satisfied_pct' => $answered > 0 ? round($satisfied * 100 / $answered, 1) : null];
    }

    /**
     * KPI layanan tabel 1.3 (T24) untuk tiket yang dibuka dalam periode: % pelanggaran SLA respons (TTO) &
     * penyelesaian (TTR), median waktu sampai diambil/ditugaskan, % diselesaikan Operator tanpa eskalasi ke tim.
     *
     * @return array{tickets: int, tto_breach: ?float, tto_n: int, ttr_breach: ?float, ttr_n: int, assign_median_min: ?int, l1_pct: ?float, solved: int}
     */
    private static function serviceKpi(DateTimeImmutable $start, int $categories_id = 0): array
    {
        global $DB;

        $now = $_SESSION['glpi_currenttime'] ?? date('Y-m-d H:i:s');
        $where = ['is_deleted' => 0, 'date' => ['>=', $start->format('Y-m-d H:i:s')]];
        if ($categories_id > 0) {
            $where['itilcategories_id'] = getSonsOf(ITILCategory::getTable(), $categories_id);
        }
        if (($archive = Config::getArchiveEntityIds()) !== []) {
            $where[] = ['NOT' => ['entities_id' => $archive]];
        }
        $operator = PatternDetector::getOperatorGroupId();
        $k = ['tickets' => 0, 'tto_n' => 0, 'tto_b' => 0, 'ttr_n' => 0, 'ttr_b' => 0, 'solved' => 0, 'l1' => 0, 'delays' => [],
            'pass' => 0, 'breach' => 0];
        foreach ($DB->request([
            'SELECT' => ['id', 'date', 'status', 'time_to_own', 'time_to_resolve', 'takeintoaccountdate', 'solvedate'],
            'FROM'   => Ticket::getTable(),
            'WHERE'  => $where,
        ]) as $t) {
            $k['tickets']++;
            if ($t['time_to_own']) {
                $k['tto_n']++;
                $k['tto_b'] += (int) (($t['takeintoaccountdate'] ?: $now) > $t['time_to_own']);
            }
            if ($t['time_to_resolve']) {
                $k['ttr_n']++;
                $k['ttr_b'] += (int) (($t['solvedate'] ?: $now) > $t['time_to_resolve']);
            }
            // Kepatuhan keseluruhan, sebanding baseline ESTIM overall_sla_result_extended (MET ÷ (MET + OVERDUE)):
            // BREACH bila respons atau penyelesaian terlampaui; PASS bila selesai tanpa terlampaui; sisanya berjalan
            $breached = ($t['time_to_own'] && ($t['takeintoaccountdate'] ?: $now) > $t['time_to_own'])
                || ($t['time_to_resolve'] && ($t['solvedate'] ?: $now) > $t['time_to_resolve']);
            if ($t['time_to_own'] || $t['time_to_resolve']) {
                if ($breached) {
                    $k['breach']++;
                } elseif ((int) $t['status'] >= CommonITILObject::SOLVED) {
                    $k['pass']++;
                }
            }
            if ($t['takeintoaccountdate']) {
                $k['delays'][] = (strtotime($t['takeintoaccountdate']) - strtotime($t['date'])) / 60;
            }
            if ((int) $t['status'] >= CommonITILObject::SOLVED) {
                $k['solved']++;
                $groups = array_column(iterator_to_array($DB->request([
                    'SELECT' => 'groups_id', 'FROM' => Group_Ticket::getTable(),
                    'WHERE'  => ['tickets_id' => $t['id'], 'type' => CommonITILActor::ASSIGN],
                ])), 'groups_id');
                // L1: diselesaikan tanpa ditugaskan ke tim selain grup Operator (KPI first-line, UC-03 alur L1)
                $k['l1'] += (int) (array_diff(array_map('intval', $groups), [$operator]) === []);
            }
        }
        sort($k['delays']);
        $median = $k['delays'] === [] ? null : (int) round($k['delays'][intdiv(count($k['delays']), 2)]);
        $pct = static fn (int $a, int $b) => $b > 0 ? round($a * 100 / $b, 1) : null;
        return [
            'tickets' => $k['tickets'], 'tto_n' => $k['tto_n'], 'tto_breach' => $pct($k['tto_b'], $k['tto_n']),
            'ttr_n' => $k['ttr_n'], 'ttr_breach' => $pct($k['ttr_b'], $k['ttr_n']),
            'assign_median_min' => $median, 'solved' => $k['solved'], 'l1_pct' => $pct($k['l1'], $k['solved']),
            'pass_pct' => $pct($k['pass'], $k['pass'] + $k['breach']), 'decided' => $k['pass'] + $k['breach'],
            'satisfaction' => self::satisfaction($start, $categories_id),
        ];
    }

    /**
     * Volume tiket per minggu, 12 minggu (T25): per jenis (Insiden/Permintaan) dan 5 kategori teratas.
     *
     * @return array{weeks: array<int, string>, types: array<string, array<int, int>>, categories: array<int, array{label: string, counts: array<int, int>, total: int}>}
     */
    private static function ticketVolume(): array
    {
        global $DB;

        $start = self::periodStart(12);
        $keys = [];
        for ($i = 0; $i < 12; $i++) {
            $keys[$start->modify("+{$i} weeks")->format('Y-m-d')] = $i;
        }
        $where = ['is_deleted' => 0, 'date' => ['>=', $start->format('Y-m-d H:i:s')]];
        if (($archive = Config::getArchiveEntityIds()) !== []) {
            $where[] = ['NOT' => ['entities_id' => $archive]];
        }
        $types = [__('Incident') => array_fill(0, 12, 0), __('Request') => array_fill(0, 12, 0)];
        $cats = [];
        foreach ($DB->request(['SELECT' => ['date', 'type', 'itilcategories_id'], 'FROM' => Ticket::getTable(), 'WHERE' => $where]) as $t) {
            $w = $keys[(new DateTimeImmutable($t['date']))->modify('monday this week')->format('Y-m-d')] ?? null;
            if ($w === null) {
                continue;
            }
            $types[(int) $t['type'] === Ticket::DEMAND_TYPE ? __('Request') : __('Incident')][$w]++;
            $label = (int) $t['itilcategories_id'] > 0 ? Suggestion::categoryName((int) $t['itilcategories_id']) : __('(uncategorised)', 'halosis');
            $cats[$label] ??= ['label' => $label, 'counts' => array_fill(0, 12, 0), 'total' => 0];
            $cats[$label]['counts'][$w]++;
            $cats[$label]['total']++;
        }
        usort($cats, static fn ($a, $b) => $b['total'] <=> $a['total']);
        return [
            'weeks'      => array_map(static fn ($k) => (new DateTimeImmutable($k))->format('d/m'), array_keys($keys)),
            'types'      => $types,
            'categories' => array_slice($cats, 0, 5),
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
     * Pola insiden dalam periode (BP-17): terdeteksi, dikonfirmasi (ada tindakan manusia pada Problem: perubahan
     * status/tautan tiket oleh pengguna, bukan tugas otomatis `cron_*`, atau tindak lanjut/tugas), ditutup
     * (Selesai/Ditutup atau dihapus sebagai pola palsu). Status awal "Ditugaskan" hasil pembuatan otomatis tidak dihitung. KPI Tabel 1.3 "waktu untuk mengetahui masalah"
     * & "jumlah pengguna terdampak": median menit dari tiket pertama pola sampai pola dibuat, dan pemohon unik per pola
     * (median) serta total pemohon unik.
     *
     * @return array{detected: int, confirmed: int, closed: int, detect_median_min: ?float, requesters_median: ?float, requesters_total: int}
     */
    private static function patterns(DateTimeImmutable $start): array
    {
        global $DB;

        $counts = ['detected' => 0, 'confirmed' => 0, 'closed' => 0];
        $created = $open = [];
        foreach ($DB->request([
            'SELECT'    => ['p.problems_id', 'p.date_creation', 'pr.status', 'pr.is_deleted'],
            'FROM'      => PatternDetector::getTable() . ' AS p',
            'LEFT JOIN' => [Problem::getTable() . ' AS pr' => ['ON' => ['p' => 'problems_id', 'pr' => 'id']]],
            'WHERE'     => ['p.date_creation' => ['>=', $start->format('Y-m-d H:i:s')]],
        ]) as $row) {
            $counts['detected']++;
            $status = (int) $row['status'];
            if ($row['status'] === null || (int) $row['is_deleted'] === 1 || in_array($status, [CommonITILObject::SOLVED, CommonITILObject::CLOSED], true)) {
                $counts['closed']++;
            } else {
                $open[] = (int) $row['problems_id'];
            }
            if ((int) $row['problems_id'] > 0) {
                $created[(int) $row['problems_id']] = strtotime((string) $row['date_creation']);
            }
        }
        $counts['confirmed'] = count(self::humanTouchedProblems($open));

        $first = $requesters = $all = [];
        if ($created !== []) {
            foreach ($DB->request([
                'SELECT'    => ['pt.problems_id', 't.date', 'tu.users_id'],
                'FROM'      => Problem_Ticket::getTable() . ' AS pt',
                'INNER JOIN' => [Ticket::getTable() . ' AS t' => ['ON' => ['pt' => 'tickets_id', 't' => 'id']]],
                'LEFT JOIN' => [Ticket_User::getTable() . ' AS tu' => ['ON' => ['tu' => 'tickets_id', 't' => 'id', [
                    'AND' => ['tu.type' => CommonITILActor::REQUESTER],
                ]]]],
                'WHERE'     => ['pt.problems_id' => array_keys($created)],
            ]) as $row) {
                $pid  = (int) $row['problems_id'];
                $time = strtotime((string) $row['date']);
                $first[$pid] = min($first[$pid] ?? $time, $time);
                if ((int) $row['users_id'] > 0) {
                    $requesters[$pid][(int) $row['users_id']] = true;
                    $all[(int) $row['users_id']] = true;
                }
            }
        }
        $delays = [];
        foreach ($first as $pid => $time) {
            $delays[] = max(0, ($created[$pid] - $time) / 60);
        }
        return $counts + [
            'detect_median_min' => self::median($delays),
            'requesters_median' => self::median(array_map('count', array_values($requesters))),
            'requesters_total'  => count($all),
        ];
    }

    /**
     * Problem yang sudah disentuh manusia: log dari pengguna (bukan tugas otomatis `cron_*`) atau tindak lanjut/tugas.
     *
     * @param array<int, int> $problem_ids
     * @return array<int, true>
     */
    private static function humanTouchedProblems(array $problem_ids): array
    {
        global $DB;

        $problem_ids = array_values(array_filter($problem_ids));
        if ($problem_ids === []) {
            return [];
        }
        $touched = [];
        foreach ($DB->request([
            'SELECT' => ['items_id'],
            'FROM'   => 'glpi_logs',
            'WHERE'  => [
                'itemtype' => Problem::getType(),
                'items_id' => $problem_ids,
                'NOT'      => ['user_name' => ['LIKE', 'cron_%']],
                ['NOT' => ['user_name' => '']],
            ],
        ]) as $row) {
            $touched[(int) $row['items_id']] = true;
        }
        foreach ($DB->request(['SELECT' => ['items_id'], 'FROM' => ITILFollowup::getTable(),
            'WHERE' => ['itemtype' => Problem::getType(), 'items_id' => $problem_ids]]) as $row) {
            $touched[(int) $row['items_id']] = true;
        }
        foreach ($DB->request(['SELECT' => ['problems_id'], 'FROM' => ProblemTask::getTable(),
            'WHERE' => ['problems_id' => $problem_ids]]) as $row) {
            $touched[(int) $row['problems_id']] = true;
        }
        return $touched;
    }

    /**
     * @param array<int, int|float> $values
     */
    private static function median(array $values): ?float
    {
        if ($values === []) {
            return null;
        }
        sort($values);
        $mid = intdiv(count($values), 2);
        return round(count($values) % 2 ? (float) $values[$mid] : ($values[$mid - 1] + $values[$mid]) / 2, 1);
    }

    /**
     * Tren pola insiden (BP-21): jumlah tiket yang tertaut ke pola per minggu per topik, 12 minggu terakhir
     * (tidak mengikuti filter periode). Topik = label pola (kategori atau judul wakil); 5 topik terbanyak.
     *
     * @return array{weeks: array<int, string>, topics: array<int, array{label: string, counts: array<int, int>, total: int}>}
     */
    private static function patternTrend(int $limit = 5): array
    {
        global $DB;

        $weeks = 12;
        $start = self::periodStart($weeks);
        $keys = [];
        for ($i = 0; $i < $weeks; $i++) {
            $keys[$start->modify("+{$i} weeks")->format('Y-m-d')] = $i;
        }
        $topics = [];
        foreach ($DB->request([
            'SELECT' => ['label', 'ticket_count', 'date_creation'],
            'FROM'   => PatternDetector::getTable(),
            'WHERE'  => ['date_creation' => ['>=', $start->format('Y-m-d H:i:s')]],
        ]) as $row) {
            $week = (new DateTimeImmutable($row['date_creation']))->modify('monday this week')->format('Y-m-d');
            if (!isset($keys[$week])) {
                continue;
            }
            $label = mb_strimwidth((string) $row['label'], 0, 60, '…');
            $topics[$label] ??= ['label' => $label, 'counts' => array_fill(0, $weeks, 0), 'total' => 0];
            $topics[$label]['counts'][$keys[$week]] += max(1, (int) $row['ticket_count']);
            $topics[$label]['total'] += max(1, (int) $row['ticket_count']);
        }
        usort($topics, static fn ($a, $b) => $b['total'] <=> $a['total']);
        return [
            'weeks'  => array_map(static fn ($k) => (new DateTimeImmutable($k))->format('d/m'), array_keys($keys)),
            'topics' => array_slice($topics, 0, $limit),
        ];
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
            // Percakapan yang diakhiri "Tidak, terima kasih" (resolved tanpa rating) bukan "terbantu"
            $declined = $row['status'] === Chat::STATUS_RESOLVED && $row['rating'] === null;
            if (!$declined && isset($counts[$row['status']])) {
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
            // Data demo ([DEMO], scripts/seed_demo.py) tidak ikut diekspor sebagai bahan koreksi
            'WHERE'      => ['d.action' => [Decision::ACTION_MODIFY, Decision::ACTION_REJECT], 'NOT' => ['t.name' => ['LIKE', '[DEMO]%']]],
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
