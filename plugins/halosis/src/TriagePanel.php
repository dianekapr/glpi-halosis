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
