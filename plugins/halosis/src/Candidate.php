<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;
use CronTask;

/**
 * Satu kandidat knowledge (tabel glpi_plugin_halosis_candidates). Lihat KnowledgeCandidates.
 */
final class Candidate extends CommonDBTM
{
    public const CRON_NAME = 'KnowledgeCandidates';

    public const SOURCE_TICKET = 'ticket';
    public const SOURCE_AI     = 'ai';

    public const STATUS_PENDING = 'pending';
    public const STATUS_ARTICLE = 'article';
    public const STATUS_IGNORED = 'ignored';

    public static string $rightname = Profile::RIGHT_KANDIDAT;

    public bool $dohistory = false;

    public static function cronInfo(string $name): array
    {
        return ['description' => __('HaloSIS: sync knowledge candidates from solved tickets', 'halosis')];
    }

    /** UC-06 langkah 7: kandidat dari tiket selesai tersedia tanpa menunggu halaman Kandidat dibuka */
    public static function cronKnowledgeCandidates(CronTask $task): int
    {
        $result = KnowledgeCandidates::sync();
        $added  = $result['tickets'] + $result['ai'];
        $task->log(sprintf(__('%d new knowledge candidates.', 'halosis'), $added));
        $task->setVolume($added);
        return $added > 0 ? 1 : 0;
    }

    public static function getTypeName($nb = 0)
    {
        return _n('Knowledge candidate', 'Knowledge candidates', $nb, 'halosis');
    }

    public static function getIcon()
    {
        return 'ti ti-bulb';
    }
}
