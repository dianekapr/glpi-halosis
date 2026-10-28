<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;

/**
 * Satu kandidat knowledge (tabel glpi_plugin_halosis_candidates). Lihat KnowledgeCandidates.
 */
final class Candidate extends CommonDBTM
{
    public const SOURCE_TICKET = 'ticket';
    public const SOURCE_AI     = 'ai';

    public const STATUS_PENDING = 'pending';
    public const STATUS_ARTICLE = 'article';
    public const STATUS_IGNORED = 'ignored';

    public static string $rightname = Profile::RIGHT_KANDIDAT;

    public bool $dohistory = false;

    public static function getTypeName($nb = 0)
    {
        return _n('Knowledge candidate', 'Knowledge candidates', $nb, 'halosis');
    }

    public static function getIcon()
    {
        return 'ti ti-bulb';
    }
}
