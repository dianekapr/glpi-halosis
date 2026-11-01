<?php

namespace GlpiPlugin\Halosis;

use Glpi\Application\View\TemplateRenderer;
use Session;
use Ticket;

/**
 * Panel "Saran AI" di bagian atas panel isian tiket (hook pre_itil_info_section).
 * Tampil untuk pemegang hak triase (lihat); tombol keputusan hanya untuk hak triase (putuskan).
 */
final class TriagePanel
{
    public const AJAX_URL = '/plugins/halosis/ajax/triase.php';

    /**
     * @param array{item?: mixed, options?: array} $params
     */
    public static function display(array $params): void
    {
        global $CFG_GLPI;

        $ticket = $params['item'] ?? null;
        if (
            !$ticket instanceof Ticket
            || $ticket->isNewItem()
            || !Config::isFeatureEnabled('triage')
            || !Session::haveRight(Profile::RIGHT_TRIASE, READ)
        ) {
            return;
        }

        $suggestion = Suggestion::getLatestForTicket($ticket->getID());
        $can_decide = Session::haveRight(Profile::RIGHT_TRIASE, UPDATE) && $ticket->canUpdateItem();

        $decision = null;
        if ($suggestion !== null && !$suggestion->isPending()) {
            $row = Decision::getForSuggestion($suggestion->getID());
            if ($row !== null) {
                $final = json_decode((string) $row->fields['final_values'], true);
                $decision = [
                    'action' => $row->fields['action'],
                    'user'   => getUserName((int) $row->fields['users_id']),
                    'date'   => $row->fields['date_creation'],
                    'reason' => $row->fields['reason'],
                    'final'  => is_array($final) ? Suggestion::describeValues($final) : null,
                ];
            }
        }

        $context = $suggestion !== null && $can_decide && $suggestion->isPending()
            ? Triage::getContext($ticket)
            : ['categories' => [], 'groups' => []];

        TemplateRenderer::getInstance()->display('@halosis/triase_panel.html.twig', [
            'ticket_id'   => $ticket->getID(),
            'pattern'     => self::pattern($ticket->getID()),
            'suggestion'  => $suggestion?->fields,
            'values'      => $suggestion !== null ? self::describe($suggestion) : null,
            'needs_review' => $suggestion?->needsManualReview() ?? false,
            'level'       => $suggestion?->getConfidenceLevel(),
            'workload'    => $suggestion !== null ? self::workload($suggestion) : [],
            'type_hint'   => $suggestion !== null ? self::typeHint($suggestion, $ticket) : null,
            'urgency_hint' => $suggestion !== null ? self::urgencyHint($suggestion) : null,
            'impact_reason' => $suggestion !== null ? (string) ($suggestion->fields['impact_reason'] ?? '') : '',
            'threshold'   => Config::getTriageThreshold(),
            'threshold_low' => Config::getLowThreshold(),
            'is_demo'     => Config::isDemoMode(),
            'decision'    => $decision,
            'can_decide'  => $can_decide,
            'can_return'  => Reassignment::canReturn($ticket),
            'ajax_url'    => $CFG_GLPI['root_doc'] . self::AJAX_URL,
            'min_reason'  => Triage::MIN_REASON_LENGTH,
            'options'     => [
                'categories'          => array_map(static fn ($c) => $c['name'], $context['categories']),
                'groups'              => $context['groups'],
                'impact'              => self::scaleNames('getImpactName'),
                'urgency'             => self::scaleNames('getUrgencyName'),
                'priority'            => array_combine(range(1, 6), array_map([Ticket::class, 'getPriorityName'], range(1, 6))),
                'can_change_priority' => Triage::canChangePriority(),
                'priority_matrix'     => $CFG_GLPI['priority_matrix'] ?? [],
            ],
        ]);
    }

    /**
     * Kandidat tim (3 teratas dari model, atau grup saran saja) dengan jumlah tiket aktif yang sedang ditangani
     * grupnya (T5, `hitungBebanKerja()`). Hanya informasi: urutan kandidat tetap dari model.
     *
     * @return array<int, array{team: string, confidence: ?int, group: string, active: ?int}>
     */
    private static function workload(Suggestion $suggestion): array
    {
        $candidates = json_decode((string) ($suggestion->fields['candidates'] ?? ''), true);
        if (!is_array($candidates) || $candidates === []) {
            $candidates = [['team' => '', 'confidence' => null, 'groups_id' => (int) $suggestion->fields['groups_id']]];
        }
        $rows = [];
        foreach ($candidates as $c) {
            $group_id = (int) ($c['groups_id'] ?? 0);
            $rows[] = [
                'team'       => (string) ($c['team'] ?? ''),
                'confidence' => isset($c['confidence']) ? (int) $c['confidence'] : null,
                'group'      => $group_id > 0 ? Suggestion::groupName($group_id) : '',
                'active'     => $group_id > 0 ? self::activeTickets($group_id) : null,
            ];
        }
        return $rows;
    }

    /**
     * Saran jenis (T4) hanya bila berbeda dari jenis tiket dan keyakinannya ≥ ambang triase; selain itu null (diam).
     *
     * Keyakinan ≥ ambang: hanya bila berbeda dari jenis tiket. Keyakinan sedang (ambang rendah–ambang, TO-BE hal. 100):
     * selalu ditampilkan sebagai "perlu ditinjau" (review = true), juga bila sama dengan jenis tiket.
     *
     * @return array{suggested: string, current: string, confidence: int, review: bool}|null
     */
    private static function typeHint(Suggestion $suggestion, Ticket $ticket): ?array
    {
        $suggested  = (int) ($suggestion->fields['type_suggested'] ?? 0);
        $confidence = (int) ($suggestion->fields['type_confidence'] ?? 0);
        $review     = $confidence >= Config::getLowThreshold() && $confidence < Config::getTriageThreshold();
        if ($suggested === 0 || (!$review && ($suggested === (int) $ticket->fields['type'] || $confidence < Config::getTriageThreshold()))) {
            return null;
        }
        return [
            'suggested'  => Ticket::getTicketTypeName($suggested),
            'current'    => Ticket::getTicketTypeName((int) $ticket->fields['type']),
            'confidence' => $confidence,
            'review'     => $review,
        ];
    }

    /**
     * Urgensi dari model history (layanan hanya mengirimnya bila kelasnya lolos gerbang & di atas ambangnya); null = aturan.
     *
     * @return array{urgency: string, confidence: int}|null
     */
    private static function urgencyHint(Suggestion $suggestion): ?array
    {
        $confidence = (int) ($suggestion->fields['urgency_confidence'] ?? 0);
        if ($confidence <= 0) {
            return null;
        }
        // Kelas model (Low/Medium) dengan nama Rendah/Sedang; GLPI id_ID menamai urgensi 3 "Pertengahan"
        $urgency = (int) $suggestion->fields['urgency'];
        $label = match ($urgency) {
            2 => __('Low (model class)', 'halosis'),
            3 => __('Medium (model class)', 'halosis'),
            default => Ticket::getUrgencyName($urgency),
        };
        return ['urgency' => $label, 'confidence' => $confidence];
    }

    /**
     * Tiket belum selesai yang ditugaskan ke grup.
     */
    private static function activeTickets(int $group_id): int
    {
        global $DB;

        return (int) $DB->request([
            'COUNT'      => 'cpt',
            'FROM'       => \Group_Ticket::getTable() . ' AS gt',
            'INNER JOIN' => [Ticket::getTable() . ' AS t' => ['ON' => ['gt' => 'tickets_id', 't' => 'id']]],
            'WHERE'      => [
                'gt.groups_id'  => $group_id,
                'gt.type'       => \CommonITILActor::ASSIGN,
                't.is_deleted'  => 0,
                't.status'      => ['<', \CommonITILObject::SOLVED],
            ],
        ])->current()['cpt'];
    }

    /**
     * Pola insiden (Problem buatan HaloSIS) yang menaungi tiket ini, dengan URL-nya.
     */
    private static function pattern(int $tickets_id): ?array
    {
        $pattern = PatternDetector::getPatternForTicket($tickets_id);
        if ($pattern !== null) {
            $pattern['url'] = \Problem::getFormURLWithID($pattern['problems_id']);
        }
        return $pattern;
    }

    /**
     * Nama yang mudah dibaca untuk tiap nilai saran.
     *
     * @return array<string, string>
     */
    private static function describe(Suggestion $suggestion): array
    {
        $f = $suggestion->fields;
        return [
            'category' => Suggestion::categoryName((int) $f['itilcategories_id']),
            'impact'   => Ticket::getImpactName((int) $f['impact']),
            'urgency'  => Ticket::getUrgencyName((int) $f['urgency']),
            'priority' => Ticket::getPriorityName((int) $f['priority']),
            'group'    => Suggestion::groupName((int) $f['groups_id']),
        ];
    }

    /**
     * @return array<int, string>
     */
    private static function scaleNames(string $method): array
    {
        $names = [];
        foreach (range(1, 5) as $value) {
            $names[$value] = Ticket::$method($value);
        }
        return $names;
    }
}
