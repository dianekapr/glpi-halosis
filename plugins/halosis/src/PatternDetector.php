<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;
use CommonITILObject;
use CronTask;
use GlpiPlugin\Halosis\Ai\AiException;
use GlpiPlugin\Halosis\Ai\Service;
use Group;
use Problem;
use Problem_Ticket;
use Session;
use Ticket;
use Toolbox;

/**
 * Deteksi pola insiden (tugas terjadwal GLPI, tiap 15 menit).
 *
 * Tiket yang dibuat dalam jendela waktu terakhir dikelompokkan:
 *   1. per kategori — tiket tanpa kategori memakai kategori dari saran triase AI;
 *   2. sisanya per kemiripan judul: ≥ TITLE_MIN_SHARED kata kunci sama dan overlap ≥ TITLE_SIMILARITY
 *      (kata sama ÷ jumlah kata judul yang lebih pendek; judul tiket pendek & panjangnya beragam).
 * Kelompok dengan ≥ N tiket menjadi Problem "Pola insiden: …" yang ditautkan ke tiketnya dan ditugaskan
 * ke grup Operator. Problem dibiarkan berstatus Baru: petugas yang memutuskan tindak lanjut.
 * Pola yang sama dan Problem-nya masih terbuka tidak dibuat ulang; tiket barunya ditautkan ke Problem itu.
 * Hanya tiket Insiden yang dihitung (PoC hal. 56: pola dari tiket INC); permintaan layanan tidak membentuk pola.
 *
 * Tabel glpi_plugin_halosis_patterns mencatat pola yang terdeteksi.
 */
final class PatternDetector extends CommonDBTM
{
    public const CRON_NAME = 'IncidentPattern';

    /** Nama grup Operator bila tidak diatur di konfigurasi (data contoh HaloSIS) */
    public const DEFAULT_OPERATOR_GROUP = 'Operator Service Desk';

    /** Kemiripan judul minimal (overlap coefficient kata kunci) untuk satu kelompok */
    public const TITLE_SIMILARITY = 0.5;

    /** Minimal kata kunci yang sama, supaya judul yang hanya berbagi satu kata umum tidak digabung */
    public const TITLE_MIN_SHARED = 2;

    /** Problem pola yang masih terbuka dan lebih muda dari ini dipakai ulang untuk pola yang sama */
    private const REUSE_HOURS = 24;

    public static string $rightname = Profile::RIGHT_TRIASE;

    public bool $dohistory = false;

    public static function getTable($classname = null)
    {
        return 'glpi_plugin_halosis_patterns';
    }

    public static function getTypeName($nb = 0)
    {
        return _n('Incident pattern', 'Incident patterns', $nb, 'halosis');
    }

    /**
     * Keterangan tugas di Setup › Tindakan otomatis.
     */
    public static function cronInfo(string $name): array
    {
        return [
            'description' => __('HaloSIS: detect incident patterns from similar new tickets', 'halosis'),
        ];
    }

    /**
     * Dipanggil GLPI sesuai jadwal. 1 = ada pekerjaan, 0 = tidak ada.
     */
    public static function cronIncidentPattern(CronTask $task): int
    {
        if (!Config::isFeatureEnabled('pattern')) {
            $task->log(__('Incident pattern detection is disabled in the HaloSIS configuration.', 'halosis'));
            return 0;
        }

        $results = self::detect();
        $linked  = 0;
        foreach ($results as $result) {
            $linked += $result['linked'];
            $task->log(sprintf(
                '%s: %s (%d %s, Problem #%d, %s)',
                $result['created'] ? __('New pattern', 'halosis') : __('Pattern updated', 'halosis'),
                $result['label'],
                $result['count'],
                _n('ticket', 'tickets', $result['count']),
                $result['problems_id'],
                sprintf(__('%d newly linked', 'halosis'), $result['linked']),
            ));
        }
        $task->setVolume($linked);

        return $results === [] ? 0 : 1;
    }

    /**
     * Jalankan deteksi sekarang.
     *
     * @return array<int, array{label: string, count: int, problems_id: int, created: bool, linked: int}>
     */
    public static function detect(): array
    {
        $min     = max(2, (int) Config::get('pattern_min_tickets'));
        $window  = max(15, (int) Config::get('pattern_window'));
        $tickets = self::getRecentTickets($window);

        // Semantik lewat layanan AI bila tersedia; gagal/tidak dikonfigurasi → metode kata kunci
        $patterns = self::groupSemantic($tickets, $min, $window) ?? self::group($tickets, $min);

        $results = [];
        foreach ($patterns as $pattern) {
            $results[] = self::upsertProblem($pattern, $window);
        }
        return $results;
    }

    /**
     * Tiket Insiden yang dibuat dalam jendela waktu, belum dihapus, belum selesai.
     *
     * @return array<int, array{id: int, name: string, entities_id: int, urgency: int, category: int}>
     */
    private static function getRecentTickets(int $window_minutes): array
    {
        global $DB;

        $since = date('Y-m-d H:i:s', strtotime(($_SESSION['glpi_currenttime'] ?? date('Y-m-d H:i:s')) . " -{$window_minutes} minutes"));

        $tickets = [];
        foreach ($DB->request([
            'SELECT' => ['id', 'name', 'content', 'date', 'entities_id', 'urgency', 'itilcategories_id'],
            'FROM'   => Ticket::getTable(),
            'WHERE'  => [
                'is_deleted' => 0,
                'type'       => Ticket::INCIDENT_TYPE,
                'date'       => ['>=', $since],
                'status'     => ['<', CommonITILObject::SOLVED],
            ],
            'ORDER'  => 'id',
        ]) as $row) {
            $tickets[(int) $row['id']] = [
                'id'          => (int) $row['id'],
                'name'        => (string) $row['name'],
                'content'     => mb_substr(trim(html_entity_decode(strip_tags((string) $row['content']))), 0, 300),
                'date'        => (string) $row['date'],
                'entities_id' => (int) $row['entities_id'],
                'urgency'     => (int) $row['urgency'],
                'category'    => (int) $row['itilcategories_id'],
            ];
        }

        // Tiket pegawai sering belum berkategori: pakai kategori saran triase AI
        $uncategorized = array_keys(array_filter($tickets, static fn ($t) => $t['category'] === 0));
        if ($uncategorized !== []) {
            foreach ($DB->request([
                'SELECT' => ['tickets_id', 'itilcategories_id'],
                'FROM'   => Suggestion::getTable(),
                'WHERE'  => ['tickets_id' => $uncategorized, 'itilcategories_id' => ['>', 0]],
                'ORDER'  => 'id',
            ]) as $row) {
                $tickets[(int) $row['tickets_id']]['category'] = (int) $row['itilcategories_id'];
            }
        }

        return $tickets;
    }

    /**
     * Kelompokkan tiket berdasarkan kemiripan makna (POST /pola layanan AI HaloSIS).
     * Null bila layanan tidak dikonfigurasi atau gagal, supaya pemanggil memakai metode kata kunci.
     *
     * @return array<int, array{criteria: string, signature: string, label: string, category: int, tickets: array}>|null
     */
    private static function groupSemantic(array $tickets, int $min, int $window): ?array
    {
        if (!Service::isConfigured() || count($tickets) < $min) {
            return Service::isConfigured() ? [] : null;
        }
        try {
            $response = Service::post('/pola', [
                'tiket'         => array_map(static fn ($t) => [
                    'id' => $t['id'], 'judul' => $t['name'], 'deskripsi' => $t['content'], 'waktu' => $t['date'],
                ], array_values($tickets)),
                'min_anggota'   => $min,
                'jendela_menit' => $window,
            ]);
        } catch (AiException $e) {
            Toolbox::logInFile('halosis', 'Deteksi pola semantik gagal, memakai kata kunci: ' . $e->getMessage() . "\n", true);
            return null;
        }

        $patterns = [];
        foreach ($response['kelompok'] ?? [] as $group) {
            $members = array_values(array_filter(array_map(static fn ($id) => $tickets[(int) $id] ?? null, $group['ids'] ?? [])));
            if (count($members) < $min) {
                continue;
            }
            // Kategori terbanyak di antara anggota (0 bila belum berkategori)
            $categories = array_count_values(array_filter(array_column($members, 'category')));
            arsort($categories);
            $patterns[] = [
                'criteria'  => 'semantic',
                // Anggota tertua stabil antar-jalannya cron selama pola masih terbuka
                'signature' => 'sem:' . min(array_column($members, 'id')),
                'label'     => (string) ($group['judul_wakil'] ?? $members[0]['name']),
                'category'  => (int) (array_key_first($categories) ?? 0),
                'score'     => (float) ($group['skor_rata'] ?? 0),
                'tickets'   => $members,
            ];
        }
        return $patterns;
    }

    /**
     * Metode kata kunci: kelompokkan tiket menjadi pola (≥ $min tiket).
     *
     * @return array<int, array{criteria: string, signature: string, label: string, category: int, tickets: array}>
     */
    private static function group(array $tickets, int $min): array
    {
        $patterns = [];

        // 1. Kategori sama
        $by_category = [];
        foreach ($tickets as $ticket) {
            if ($ticket['category'] > 0) {
                $by_category[$ticket['category']][] = $ticket;
            }
        }
        $grouped = [];
        foreach ($by_category as $category_id => $members) {
            if (count($members) < $min) {
                continue;
            }
            $patterns[] = [
                'criteria'  => 'category',
                'signature' => 'cat:' . $category_id,
                'label'     => Suggestion::categoryName($category_id),
                'category'  => $category_id,
                'tickets'   => $members,
            ];
            foreach ($members as $member) {
                $grouped[$member['id']] = true;
            }
        }

        // 2. Judul mirip, di antara tiket yang belum masuk pola kategori
        $clusters = [];
        foreach ($tickets as $ticket) {
            if (isset($grouped[$ticket['id']])) {
                continue;
            }
            $tokens = KnowledgeSearch::tokens($ticket['name']);
            if ($tokens === []) {
                continue;
            }
            // Berbasis indeks, bukan referensi foreach: referensi yang tertinggal setelah `continue`
            // akan ditimpa oleh foreach berikutnya dan merusak isi kelompok.
            foreach (array_keys($clusters) as $index) {
                if (self::isSimilarTitle($tokens, $clusters[$index]['tokens'])) {
                    $clusters[$index]['tickets'][] = $ticket;
                    $clusters[$index]['counts'] = self::addCounts($clusters[$index]['counts'], $tokens);
                    continue 2;
                }
            }
            $clusters[] = ['tokens' => $tokens, 'tickets' => [$ticket], 'counts' => self::addCounts([], $tokens)];
        }

        foreach ($clusters as $cluster) {
            if (count($cluster['tickets']) < $min) {
                continue;
            }
            // Kata kunci yang paling sering muncul menjadi tanda pola (stabil antar-jalannya cron)
            arsort($cluster['counts']);
            $keywords = array_slice(array_keys($cluster['counts']), 0, 3);
            sort($keywords);
            $patterns[] = [
                'criteria'  => 'title',
                'signature' => 'title:' . implode(' ', $keywords),
                'label'     => $cluster['tickets'][0]['name'],
                'category'  => 0,
                'tickets'   => $cluster['tickets'],
            ];
        }

        return $patterns;
    }

    /**
     * Buat Problem baru untuk pola, atau tautkan tiket baru ke Problem pola yang masih terbuka.
     */
    private static function upsertProblem(array $pattern, int $window): array
    {
        // Tanda pola bisa bergeser antar-jalannya cron (mis. anggota tertua sudah selesai): anggota yang sudah
        // tertaut ke Problem pola yang masih terbuka membawa tiket mirip yang baru ke Problem itu
        $record  = self::findOpenRecord($pattern['signature'])
            ?? self::findOpenRecordForTickets(array_column($pattern['tickets'], 'id'));
        $created = $record === null;
        $problem = new Problem();

        if ($created) {
            $urgency = max(array_column($pattern['tickets'], 'urgency')) ?: 3;
            $impact  = 4; // banyak pengguna terdampak
            $input = [
                'name'              => sprintf(__('Incident pattern: %s', 'halosis'), mb_substr($pattern['label'], 0, 200)),
                'content'           => self::describe($pattern, $window),
                'entities_id'       => $pattern['tickets'][0]['entities_id'],
                'urgency'           => $urgency,
                'impact'            => $impact,
                'priority'          => Problem::computePriority($urgency, $impact),
                'itilcategories_id' => $pattern['category'],
                'status'            => CommonITILObject::INCOMING,
            ];
            if (($group_id = self::getOperatorGroupId()) > 0) {
                // Ditugaskan ke grup Operator: muncul di antrean mereka & memicu notifikasi GLPI ke grup tsb.
                $input['_groups_id_assign'] = $group_id;
            }
            $problems_id = (int) $problem->add($input);

            $record = new self();
            $record->add([
                'problems_id'  => $problems_id,
                'signature'    => $pattern['signature'],
                'criteria'     => $pattern['criteria'],
                'label'        => mb_substr($pattern['label'], 0, 255),
                'ticket_count' => 0,
            ]);
        } else {
            $problems_id = (int) $record->fields['problems_id'];
        }

        // Tautkan tiket yang belum tertaut ke Problem ini (relasi dicatat di Riwayat tiket & Problem)
        $linked = 0;
        foreach ($pattern['tickets'] as $ticket) {
            $exists = countElementsInTable(Problem_Ticket::getTable(), [
                'problems_id' => $problems_id,
                'tickets_id'  => $ticket['id'],
            ]) > 0;
            if (!$exists && (new Problem_Ticket())->add(['problems_id' => $problems_id, 'tickets_id' => $ticket['id']])) {
                $linked++;
            }
        }

        $total = countElementsInTable(Problem_Ticket::getTable(), ['problems_id' => $problems_id]);
        $record->update(['id' => $record->getID(), 'ticket_count' => $total]);

        return [
            'label'       => $pattern['label'],
            'count'       => $total,
            'problems_id' => $problems_id,
            'created'     => $created,
            'linked'      => $linked,
        ];
    }

    /**
     * Catatan pola dengan tanda yang sama, Problem-nya belum selesai & belum dihapus, masih baru.
     */
    private static function findOpenRecord(string $signature): ?self
    {
        global $DB;

        $since = date('Y-m-d H:i:s', strtotime(($_SESSION['glpi_currenttime'] ?? date('Y-m-d H:i:s')) . ' -' . self::REUSE_HOURS . ' hours'));
        $row = $DB->request([
            'SELECT'     => ['p.id'],
            'FROM'       => self::getTable() . ' AS p',
            'INNER JOIN' => [
                Problem::getTable() . ' AS pr' => ['ON' => ['p' => 'problems_id', 'pr' => 'id']],
            ],
            'WHERE'      => [
                'p.signature'     => $signature,
                'p.date_creation' => ['>=', $since],
                'pr.is_deleted'   => 0,
                'pr.status'       => ['<', CommonITILObject::SOLVED],
            ],
            'ORDER'      => 'p.id DESC',
            'LIMIT'      => 1,
        ])->current();

        $record = new self();
        return $row !== null && $record->getFromDB((int) $row['id']) ? $record : null;
    }

    /**
     * Catatan pola yang Problem-nya masih terbuka dan sudah menaungi salah satu tiket ini.
     *
     * @param int[] $tickets_ids
     */
    private static function findOpenRecordForTickets(array $tickets_ids): ?self
    {
        global $DB;

        if ($tickets_ids === []) {
            return null;
        }
        $row = $DB->request([
            'SELECT'     => ['p.id'],
            'FROM'       => self::getTable() . ' AS p',
            'INNER JOIN' => [
                Problem::getTable() . ' AS pr'           => ['ON' => ['p' => 'problems_id', 'pr' => 'id']],
                Problem_Ticket::getTable() . ' AS pt' => ['ON' => ['p' => 'problems_id', 'pt' => 'problems_id']],
            ],
            'WHERE'      => [
                'pt.tickets_id' => $tickets_ids,
                'pr.is_deleted' => 0,
                'pr.status'     => ['<', CommonITILObject::SOLVED],
            ],
            'ORDER'      => 'p.id DESC',
            'LIMIT'      => 1,
        ])->current();

        $record = new self();
        return $row !== null && $record->getFromDB((int) $row['id']) ? $record : null;
    }

    /**
     * Grup Operator penerima pola: dari konfigurasi, atau grup "Operator Service Desk".
     */
    public static function getOperatorGroupId(): int
    {
        $configured = (int) Config::get('pattern_group_id');
        if ($configured > 0) {
            return $configured;
        }
        $group = new Group();
        return $group->getFromDBByCrit(['name' => self::DEFAULT_OPERATOR_GROUP]) ? $group->getID() : 0;
    }

    /**
     * Deskripsi Problem (HTML ter-escape).
     */
    private static function describe(array $pattern, int $window): string
    {
        $criteria = match ($pattern['criteria']) {
            'category' => sprintf(__('same category (%s)', 'halosis'), $pattern['label']),
            'semantic' => sprintf(__('similar meaning (average similarity %s)', 'halosis'), number_format($pattern['score'] ?? 0, 2)),
            default    => __('similar titles', 'halosis'),
        };
        $method = $pattern['criteria'] === 'semantic' ? __('semantic', 'halosis') : __('keyword', 'halosis');

        $items = [];
        foreach ($pattern['tickets'] as $ticket) {
            $items[] = sprintf('<li>#%d — %s</li>', $ticket['id'], htmlescape($ticket['name']));
        }

        return sprintf(
            '<p>%s</p><p>%s</p><p>%s</p><ul>%s</ul><p><em>%s</em></p>',
            htmlescape(sprintf(
                __('HaloSIS detected %1$d new tickets within the last %2$d minutes with %3$s.', 'halosis'),
                count($pattern['tickets']),
                $window,
                $criteria,
            )),
            htmlescape(sprintf(__('Detection method: %s', 'halosis'), $method)),
            htmlescape(__('Linked tickets:', 'halosis')),
            implode('', $items),
            htmlescape(__('Detected automatically. An officer decides the follow-up (investigate, assign a team, or close if unrelated).', 'halosis')),
        );
    }

    /**
     * Pola terbuka yang terdeteksi dalam 48 jam terakhir (untuk banner petugas).
     *
     * @return array<int, array{problems_id: int, label: string, ticket_count: int, date: string}>
     */
    public static function getRecentOpenPatterns(): array
    {
        global $DB;

        $since = date('Y-m-d H:i:s', strtotime(($_SESSION['glpi_currenttime'] ?? date('Y-m-d H:i:s')) . ' -48 hours'));
        $patterns = [];
        foreach ($DB->request([
            'SELECT'     => ['p.problems_id', 'p.label', 'p.ticket_count', 'p.date_creation'],
            'FROM'       => self::getTable() . ' AS p',
            'INNER JOIN' => [
                Problem::getTable() . ' AS pr' => ['ON' => ['p' => 'problems_id', 'pr' => 'id']],
            ],
            'WHERE'      => [
                'p.date_creation' => ['>=', $since],
                'pr.is_deleted'   => 0,
                'pr.status'       => ['<', CommonITILObject::SOLVED],
            ],
            'ORDER'      => 'p.date_creation DESC',
            'LIMIT'      => 5,
        ]) as $row) {
            $patterns[] = [
                'problems_id'  => (int) $row['problems_id'],
                'label'        => (string) $row['label'],
                'ticket_count' => (int) $row['ticket_count'],
                'date'         => (string) $row['date_creation'],
            ];
        }
        return $patterns;
    }

    /**
     * Problem pola yang menaungi tiket ini (untuk panel Saran AI), atau null.
     *
     * @return array{problems_id: int, label: string, ticket_count: int}|null
     */
    public static function getPatternForTicket(int $tickets_id): ?array
    {
        global $DB;

        $row = $DB->request([
            'SELECT'     => ['p.problems_id', 'p.label', 'p.ticket_count'],
            'FROM'       => self::getTable() . ' AS p',
            'INNER JOIN' => [
                Problem_Ticket::getTable() . ' AS pt' => ['ON' => ['p' => 'problems_id', 'pt' => 'problems_id']],
            ],
            'WHERE'      => ['pt.tickets_id' => $tickets_id],
            'ORDER'      => 'p.id DESC',
            'LIMIT'      => 1,
        ])->current();

        return $row === null ? null : [
            'problems_id'  => (int) $row['problems_id'],
            'label'        => (string) $row['label'],
            'ticket_count' => (int) $row['ticket_count'],
        ];
    }

    /**
     * Hook display_central: banner pola insiden untuk petugas yang memutuskan triase.
     */
    public static function displayCentralBanner(): void
    {
        if (
            Session::getCurrentInterface() !== 'central'
            || !Config::isFeatureEnabled('pattern')
            || !Session::haveRight(Profile::RIGHT_TRIASE, UPDATE)
        ) {
            return;
        }
        $patterns = self::getRecentOpenPatterns();
        if ($patterns === []) {
            return;
        }
        foreach ($patterns as &$pattern) {
            $pattern['url'] = Problem::getFormURLWithID($pattern['problems_id']);
        }
        unset($pattern);

        \Glpi\Application\View\TemplateRenderer::getInstance()->display('@halosis/pattern_banner.html.twig', [
            'patterns' => $patterns,
        ]);
    }

    /**
     * @param string[] $a
     * @param string[] $b
     */
    private static function isSimilarTitle(array $a, array $b): bool
    {
        $shared = count(array_intersect($a, $b));
        return $shared >= self::TITLE_MIN_SHARED && $shared / min(count($a), count($b)) >= self::TITLE_SIMILARITY;
    }

    /**
     * @param array<string, int> $counts
     * @param string[]           $tokens
     *
     * @return array<string, int>
     */
    private static function addCounts(array $counts, array $tokens): array
    {
        foreach ($tokens as $token) {
            $counts[$token] = ($counts[$token] ?? 0) + 1;
        }
        return $counts;
    }
}
