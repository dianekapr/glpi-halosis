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
            'WHERE'  => ['status' => [Ticket::SOLVED, Ticket::CLOSED], 'is_deleted' => 0],
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
        $answer = sprintf(
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
            'name'     => $candidate->fields['title'] ?: __('Knowledge candidate', 'halosis'),
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
