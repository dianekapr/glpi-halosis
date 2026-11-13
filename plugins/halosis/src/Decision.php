<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;
use ITILSolution;
use Session;
use Ticket;

/**
 * Log keputusan petugas atas saran AI (tabel glpi_plugin_halosis_decisions):
 * aktor, waktu, nilai saran vs nilai final, dan alasan. Dasar dashboard kinerja AI.
 */
final class Decision extends CommonDBTM
{
    public const ACTION_ACCEPT = 'accept';
    public const ACTION_MODIFY = 'modify';
    public const ACTION_REJECT = 'reject';

    public static string $rightname = Profile::RIGHT_TRIASE;

    public bool $dohistory = false;

    public static function getTypeName($nb = 0)
    {
        return _n('AI decision', 'AI decisions', $nb, 'halosis');
    }

    /**
     * Keputusan terakhir untuk sebuah saran, atau null.
     */
    public static function getForSuggestion(int $suggestions_id): ?self
    {
        $decision = new self();
        $found = $decision->getFromDBByRequest([
            'WHERE' => ['suggestions_id' => $suggestions_id],
            'ORDER' => 'id DESC',
            'LIMIT' => 1,
        ]);
        return $found ? $decision : null;
    }

    /**
     * UC-05 A5: setelah keputusan atau solusi, tiket tidak lagi tampil di daftar tersaring "Menunggu keputusan".
     * Beri petugas pesan yang menjelaskan hal itu, lengkap dengan tautan ke tiket.
     */
    public static function flashLeftQueue(int $tickets_id, bool $solved = false): void
    {
        $url  = htmlescape(Ticket::getFormURLWithID($tickets_id));
        $link = '<a href="' . $url . '">' . __s('Open ticket', 'halosis') . '</a>';
        $msg  = $solved
            ? sprintf(__s('Solution saved. Ticket #%1$d is now Solved and moved out of the validation queue.', 'halosis'), $tickets_id)
            : sprintf(__s('Decision saved. Ticket #%1$d was moved out of the validation queue.', 'halosis'), $tickets_id);
        Session::addMessageAfterRedirect($msg . ' ' . $link);
    }

    /** Hook item_add ITILSolution: solusi level 1 oleh petugas triase (UC-05 5c). */
    public static function onSolutionAdd(ITILSolution $solution): void
    {
        if (
            ($solution->fields['itemtype'] ?? '') === Ticket::class
            && Session::haveRight(Profile::RIGHT_TRIASE, UPDATE)
        ) {
            self::flashLeftQueue((int) $solution->fields['items_id'], true);
        }
    }
}
