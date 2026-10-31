<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;
use CommonITILObject;
use CronTask;
use Glpi\DBAL\QuerySubQuery;
use Ticket;
use Throwable;
use Toolbox;

/**
 * NFR-03: tugas terjadwal "TriageRetry" membuat saran triase untuk tiket Baru yang belum punya saran (mis. layanan AI
 * sempat mati saat tiket disimpan). Idempoten: Triage::generate() tidak membuat saran kedua bila sudah ada.
 * Percobaan per tiket dicatat di glpi_plugin_halosis_triage_retries dan dibatasi MAX_ATTEMPTS.
 */
final class TriageRetry extends CommonDBTM
{
    public const CRON_NAME = 'TriageRetry';

    /** Percobaan maksimal per tiket; setelahnya tiket ditriase manual oleh Operator */
    public const MAX_ATTEMPTS = 5;

    /** Hanya tiket yang dibuat dalam sekian hari terakhir (tiket lama sudah ditangani manual) */
    public const MAX_AGE_DAYS = 3;

    /** Tiket per jalannya tugas, supaya satu putaran tidak membebani layanan AI */
    public const BATCH = 20;

    public bool $dohistory = false;

    public static function getTable($classname = null)
    {
        return 'glpi_plugin_halosis_triage_retries';
    }

    public static function cronInfo(string $name): array
    {
        return ['description' => __('HaloSIS: create missing AI triage suggestions for new tickets', 'halosis')];
    }

    public static function cronTriageRetry(CronTask $task): int
    {
        if (!Config::isFeatureEnabled('triage')) {
            $task->log(__('AI triage is disabled in the HaloSIS configuration.', 'halosis'));
            return 0;
        }
        $result = self::run();
        foreach ($result['log'] as $line) {
            $task->log($line);
        }
        $task->setVolume($result['created']);
        return $result['tried'] > 0 ? 1 : 0;
    }

    /**
     * @return array{tried: int, created: int, log: string[]}
     */
    public static function run(): array
    {
        global $DB;

        $since = date('Y-m-d H:i:s', strtotime(($_SESSION['glpi_currenttime'] ?? 'now') . ' -' . self::MAX_AGE_DAYS . ' days'));
        $iterator = $DB->request([
            'SELECT'    => ['t.id', 'r.attempts'],
            'FROM'      => Ticket::getTable() . ' AS t',
            'LEFT JOIN' => [self::getTable() . ' AS r' => ['ON' => ['t' => 'id', 'r' => 'tickets_id']]],
            'WHERE'     => [
                't.is_deleted' => 0,
                't.status'     => CommonITILObject::INCOMING,
                't.date'       => ['>=', $since],
                // Belum punya saran & bukan entitas arsip (dua NOT terpisah; satu NOT berisi dua kunci = NOT(a DAN b))
                ['NOT' => ['t.id' => new QuerySubQuery(['SELECT' => 'tickets_id', 'FROM' => Suggestion::getTable()])]],
                ['NOT' => ['t.entities_id' => Config::getArchiveEntityIds() ?: [-1]]],
                'OR'           => [['r.attempts' => null], ['r.attempts' => ['<', self::MAX_ATTEMPTS]]],
            ],
            'ORDER'     => 't.id',
            'LIMIT'     => self::BATCH,
        ]);

        $tried = $created = 0;
        $log = [];
        foreach ($iterator as $row) {
            $ticket = new Ticket();
            if (!$ticket->getFromDB((int) $row['id'])) {
                continue;
            }
            $tried++;
            $error = '';
            try {
                $suggestion = Triage::generate($ticket);
            } catch (Throwable $e) {
                $suggestion = null;
                $error = mb_substr($e->getMessage(), 0, 255);
            }
            if ($suggestion !== null) {
                $created++;
                $DB->delete(self::getTable(), ['tickets_id' => $ticket->getID()]);
                $log[] = sprintf(__('Ticket #%d: AI suggestion created', 'halosis'), $ticket->getID());
                continue;
            }
            $attempts = (int) $row['attempts'] + 1;
            $DB->updateOrInsert(self::getTable(), [
                'attempts'   => $attempts,
                'last_error' => $error !== '' ? $error : 'AI tidak memberi saran',
                'date_mod'   => $_SESSION['glpi_currenttime'] ?? date('Y-m-d H:i:s'),
            ], ['tickets_id' => $ticket->getID()]);
            $line = sprintf(__('Ticket #%1$d: no suggestion yet (attempt %2$d of %3$d)', 'halosis'), $ticket->getID(), $attempts, self::MAX_ATTEMPTS);
            $log[] = $line;
            Toolbox::logInFile('halosis', "TriageRetry: {$line}\n", true);
        }
        return ['tried' => $tried, 'created' => $created, 'log' => $log];
    }
}
