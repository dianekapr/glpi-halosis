<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;

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
}
