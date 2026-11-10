<?php

namespace GlpiPlugin\Halosis;

use CommonITILValidation;
use GlpiPlugin\Halosis\Ai\AiException;
use GlpiPlugin\Halosis\Ai\Service;
use ITILSolution;
use KnowbaseItem;
use Session;
use Ticket;
use Toolbox;

/**
 * Kandidat Knowledge (UC-09 didukung AI, BP-16 knowledge feedback loop).
 *
 * Sumber kandidat:
 * - Tiket GLPI yang selesai (Solved/Closed) dengan solusi yang tidak ditolak pemohon; solusi yang
 *   disetujui pemohon ditandai "Disetujui pemohon" dan diurutkan lebih dulu.
 * - Solusi yang sering berulang di history tiket (klaster dari indeks AI, layanan ai/service /kandidat).
 *
 * Knowledge Manager memutuskan: "Jadikan artikel" membuat DRAF artikel KB (belum terbit, tanpa target
 * visibilitas) berisi masalah + solusi, atau "Abaikan" dengan alasan. Teks selalu disamarkan (Privacy).
 */
final class KnowledgeCandidates
{
    /** Minimal panjang solusi (karakter) agar layak jadi kandidat */
    private const MIN_SOLUTION_LENGTH = 20;
    private const AI_MIN_OCCURRENCES  = 5;
    private const AI_LIMIT            = 20;

    /**
     * Tambahkan kandidat baru dari kedua sumber. Kandidat yang sudah ada tidak diubah.
     *
     * @return array{tickets: int, ai: int, ai_available: bool}
     */
    public static function sync(): array
    {
        $tickets = self::syncTickets();
        $ai      = self::syncAi();
        return ['tickets' => $tickets, 'ai' => (int) $ai, 'ai_available' => $ai !== null];
    }

    private static function existingRefs(string $source): array
    {
        global $DB;
        return array_flip(array_column(iterator_to_array($DB->request([
            'SELECT' => ['source_ref'],
            'FROM'   => Candidate::getTable(),
            'WHERE'  => ['source' => $source],
        ])), 'source_ref'));
    }

    private static function syncTickets(): int
    {
        global $DB;

        $known = self::existingRefs(Candidate::SOURCE_TICKET);
        $added = 0;
        foreach ($DB->request([
            'SELECT' => ['id', 'name', 'content'],
            'FROM'   => Ticket::getTable(),
            // Tiket demo ([DEMO]) tidak menjadi kandidat artikel
            'WHERE'  => ['status' => [Ticket::SOLVED, Ticket::CLOSED], 'is_deleted' => 0, 'NOT' => ['name' => ['LIKE', '[DEMO]%']]],
            'ORDER'  => 'id DESC',
        ]) as $ticket) {
            if (isset($known[(string) $ticket['id']])) {
                continue;
            }
            $solution = $DB->request([
                'SELECT' => ['content', 'status'],
                'FROM'   => ITILSolution::getTable(),
                'WHERE'  => [
                    'itemtype' => Ticket::class,
                    'items_id' => $ticket['id'],
                    'NOT'      => ['status' => CommonITILValidation::REFUSED],
                ],
                'ORDER'  => 'id DESC',
                'LIMIT'  => 1,
            ])->current();
            $solution_text = $solution ? KnowledgeSearch::plainText((string) $solution['content']) : '';
            if (mb_strlen($solution_text) < self::MIN_SOLUTION_LENGTH) {
                continue;
            }

            $candidate = new Candidate();
            $candidate->add([
                'source'      => Candidate::SOURCE_TICKET,
                'source_ref'  => (string) $ticket['id'],
                'tickets_id'  => (int) $ticket['id'],
                'title'       => mb_substr(Privacy::mask((string) $ticket['name'])['text'], 0, 255),
                'problem'     => Privacy::mask(KnowledgeSearch::plainText((string) $ticket['content']))['text'],
                'solution'    => Privacy::mask($solution_text)['text'],
                'is_approved' => (int) ((int) $solution['status'] === CommonITILValidation::ACCEPTED),
                'status'      => Candidate::STATUS_PENDING,
            ]);
            $added++;
        }
        return $added;
    }

    /**
     * @return int|null Jumlah kandidat baru, null jika layanan AI tidak dapat dihubungi
     */
    private static function syncAi(): ?int
    {
        if (!Service::isConfigured()) {
            return null;
        }
        try {
            $data = Service::get(sprintf('/kandidat?min=%d&limit=%d', self::AI_MIN_OCCURRENCES, self::AI_LIMIT));
        } catch (AiException $e) {
            Toolbox::logInFile('halosis', 'Kandidat knowledge: layanan AI gagal. ' . $e->getMessage() . "\n", true);
            return null;
        }

        $known = self::existingRefs(Candidate::SOURCE_AI);
        $added = 0;
        foreach ((array) ($data['kandidat'] ?? []) as $item) {
            $key = (string) ($item['kunci'] ?? '');
            if ($key === '' || isset($known[$key])) {
                continue;
            }
            $candidate = new Candidate();
            $candidate->add([
                'source'      => Candidate::SOURCE_AI,
                'source_ref'  => mb_substr($key, 0, 100),
                'title'       => mb_substr(Privacy::mask((string) ($item['judul'] ?? ''))['text'], 0, 255),
                'problem'     => Privacy::mask((string) ($item['masalah'] ?? ''))['text'],
                'solution'    => Privacy::mask((string) ($item['solusi'] ?? ''))['text'],
                'occurrences' => max(1, (int) ($item['jumlah'] ?? 1)),
                'examples'    => implode(', ', array_slice(array_map('strval', (array) ($item['contoh_tiket'] ?? [])), 0, 5)),
                'status'      => Candidate::STATUS_PENDING,
            ]);
            $added++;
        }
        return $added;
    }

    /**
     * @return array<int, array<string, mixed>>
     */
    public static function list(string $status): array
    {
        global $DB;
        return iterator_to_array($DB->request([
            'FROM'  => Candidate::getTable(),
            'WHERE' => ['status' => $status],
            'ORDER' => $status === Candidate::STATUS_PENDING
                ? ['is_approved DESC', 'occurrences DESC', 'id DESC']
                : ['date_decision DESC', 'id DESC'],
            'LIMIT' => 100,
        ]), false);
    }

    /** Tanggal tinjau berikut per artikel (KR-03) */
    public const REVIEW_TABLE = 'glpi_plugin_halosis_kb_reviews';

    /**
     * Artikel terbit yang jatuh tempo ditinjau (hal. 139), terlama dulu. Tanggal tinjau berikut = tanggal yang diatur
     * Knowledge Manager (KR-03) atau, bila belum diatur, `date_mod` + `kb_review_months`. Menyunting artikel di KB
     * memajukan date_mod; mengatur tanggal baru menjadwalkan tinjauan berikutnya.
     *
     * @return array<int, array{id: int, name: string, date_mod: string, next_review: string, explicit: bool, url: string}>
     */
    public static function dueForReview(): array
    {
        global $DB;

        $months = max(1, (int) Config::get('kb_review_months'));
        $today  = date('Y-m-d', strtotime($_SESSION['glpi_currenttime'] ?? 'now'));
        $items = [];
        foreach ($DB->request([
            'SELECT'    => [KnowbaseItem::getTable() . '.*', 'r.date_review'],
            'FROM'      => KnowbaseItem::getTable(),
            'LEFT JOIN' => [self::REVIEW_TABLE . ' AS r' => ['ON' => ['r' => 'knowbaseitems_id', KnowbaseItem::getTable() => 'id']]],
            'ORDER'     => ['date_mod ASC', 'id ASC'],
        ]) as $fields) {
            $explicit = !empty($fields['date_review']);
            $next = $explicit ? (string) $fields['date_review'] : date('Y-m-d', strtotime($fields['date_mod'] . " +{$months} months"));
            if ($next > $today) {
                continue;
            }
            $article = new KnowbaseItem();
            $article->fields = $fields;
            if (!KnowledgeIndex::isPublished($article)) {
                continue;
            }
            $items[] = [
                'id'          => (int) $fields['id'],
                'name'        => (string) $fields['name'],
                'date_mod'    => (string) $fields['date_mod'],
                'next_review' => $next,
                'explicit'    => $explicit,
                'url'         => KnowbaseItem::getFormURLWithID((int) $fields['id']),
            ];
        }
        return $items;
    }

    /**
     * Atur tanggal tinjau berikut satu artikel (KR-03): artikel keluar dari "Perlu ditinjau" sampai tanggal itu.
     *
     * @return array{ok: bool, message?: string}
     */
    public static function setReviewDate(int $kb_id, string $date): array
    {
        global $DB;

        $parsed = \DateTimeImmutable::createFromFormat('!Y-m-d', $date);
        $today  = date('Y-m-d', strtotime($_SESSION['glpi_currenttime'] ?? 'now'));
        if ($parsed === false || $parsed->format('Y-m-d') !== $date || $date <= $today) {
            return ['ok' => false, 'message' => __('Choose a review date after today.', 'halosis')];
        }
        if (!(new KnowbaseItem())->getFromDB($kb_id)) {
            return ['ok' => false, 'message' => __('Article not found.', 'halosis')];
        }
        $DB->updateOrInsert(self::REVIEW_TABLE, [
            'date_review' => $date,
            'users_id'    => Session::getLoginUserID(),
            'date_mod'    => $_SESSION['glpi_currenttime'] ?? date('Y-m-d H:i:s'),
        ], ['knowbaseitems_id' => $kb_id]);
        return ['ok' => true];
    }

    /**
     * @return array<string, int> Jumlah kandidat per status
     */
    public static function counts(): array
    {
        global $DB;
        $counts = [Candidate::STATUS_PENDING => 0, Candidate::STATUS_ARTICLE => 0, Candidate::STATUS_IGNORED => 0];
        foreach ($DB->request([
            'SELECT'  => ['status', 'COUNT' => 'id AS total'],
            'FROM'    => Candidate::getTable(),
            'GROUPBY' => 'status',
        ]) as $row) {
            $counts[$row['status']] = (int) $row['total'];
        }
        return $counts;
    }

    /**
     * Buat draf artikel KB (belum terbit) dari kandidat.
     *
     * @return array{ok: bool, message?: string, url?: string}
     */
    public static function makeArticle(Candidate $candidate): array
    {
        if ($candidate->fields['status'] !== Candidate::STATUS_PENDING) {
            return ['ok' => false, 'message' => __('This candidate has already been decided.', 'halosis')];
        }

        $source = $candidate->fields['source'] === Candidate::SOURCE_TICKET
            ? sprintf(__('Source: solution of ticket #%d.', 'halosis'), $candidate->fields['tickets_id'])
            : sprintf(__('Source: recurring solution in %d historical tickets (AI index).', 'halosis'), $candidate->fields['occurrences']);
        $ai     = self::aiDraft($candidate, $source);
        $answer = $ai['html'] ?? sprintf(
            '<h3>%s</h3><p>%s</p><h3>%s</h3><p>%s</p><p><em>%s %s</em></p>',
            htmlescape(__('Problem', 'halosis')),
            nl2br(htmlescape((string) $candidate->fields['problem'])),
            htmlescape(__('Solution', 'halosis')),
            nl2br(htmlescape((string) $candidate->fields['solution'])),
            htmlescape($source),
            htmlescape(__('Draft from Knowledge candidates; review before publishing.', 'halosis')),
        );

        // Tanpa target visibilitas = draf (belum terbit); Knowledge Manager menerbitkan setelah meninjau
        $article = new KnowbaseItem();
        $article_id = $article->add([
            'name'     => ($ai['title'] ?? '') ?: ($candidate->fields['title'] ?: __('Knowledge candidate', 'halosis')),
            'answer'   => $answer,
            'is_faq'   => 0,
            'users_id' => Session::getLoginUserID(),
        ]);
        if (!$article_id) {
            return ['ok' => false, 'message' => __('The draft article could not be created.', 'halosis')];
        }

        $candidate->update([
            'id'               => $candidate->getID(),
            'status'           => Candidate::STATUS_ARTICLE,
            'knowbaseitems_id' => $article_id,
            'users_id'         => Session::getLoginUserID(),
            'date_decision'    => $_SESSION['glpi_currenttime'],
        ]);
        return ['ok' => true, 'url' => KnowbaseItem::getFormURLWithID($article_id)];
    }

    /**
     * Draf berbahasa formal dari layanan halosis-ai (LLM): judul + HTML. null = LLM none/gagal → pakai templat lama.
     */
    private static function aiDraft(Candidate $candidate, string $source): ?array
    {
        if (!Service::isConfigured()) {
            return null;
        }
        $refs = $candidate->fields['source'] === Candidate::SOURCE_TICKET
            ? ['#' . (int) $candidate->fields['tickets_id']]
            : array_values(array_filter(array_map('trim', explode(',', (string) $candidate->fields['examples']))));
        try {
            $data = Service::post('/kandidat/draf', [
                'judul'   => (string) $candidate->fields['title'],
                'masalah' => (string) $candidate->fields['problem'],
                'solusi'  => (string) $candidate->fields['solution'],
                'sumber'  => $refs,
            ]);
        } catch (AiException $e) {
            Toolbox::logInFile('halosis', 'Draf artikel AI gagal, memakai templat. ' . $e->getMessage() . "\n", true);
            return null;
        }
        $draft = $data['draf'] ?? null;
        if (!is_array($draft) || empty($draft['gejala']) || empty($draft['langkah'])) {
            return null;
        }
        $html = sprintf(
            '<h3>%s</h3><p>%s</p><h3>%s</h3><p>%s</p><p><em>%s</em></p><p><em>%s</em></p>',
            htmlescape(__('Symptoms', 'halosis')),
            nl2br(htmlescape((string) $draft['gejala'])),
            htmlescape(__('Resolution steps', 'halosis')),
            nl2br(htmlescape((string) $draft['langkah'])),
            htmlescape($source),
            htmlescape('Disusun AI, wajib ditinjau Knowledge Manager'),
        );
        return ['title' => mb_substr(Privacy::mask((string) ($draft['judul'] ?? ''))['text'], 0, 255), 'html' => $html];
    }

    /**
     * @return array{ok: bool, message?: string}
     */
    public static function ignore(Candidate $candidate, string $reason): array
    {
        if ($candidate->fields['status'] !== Candidate::STATUS_PENDING) {
            return ['ok' => false, 'message' => __('This candidate has already been decided.', 'halosis')];
        }
        $reason = trim($reason);
        if (mb_strlen($reason) < Triage::MIN_REASON_LENGTH) {
            return ['ok' => false, 'message' => sprintf(__('Please give a reason of at least %d characters.', 'halosis'), Triage::MIN_REASON_LENGTH)];
        }
        $candidate->update([
            'id'            => $candidate->getID(),
            'status'        => Candidate::STATUS_IGNORED,
            'reason'        => mb_substr(Privacy::mask($reason)['text'], 0, 1000),
            'users_id'      => Session::getLoginUserID(),
            'date_decision' => $_SESSION['glpi_currenttime'],
        ]);
        return ['ok' => true];
    }
}
