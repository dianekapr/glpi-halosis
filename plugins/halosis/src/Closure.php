<?php

namespace GlpiPlugin\Halosis;

use CommonITILActor;
use CommonITILObject;
use ITILFollowup;
use Session;
use Ticket;
use Ticket_User;

/**
 * T21: rekomendasi penutupan (5.1 Activity Elimination/Duration, 5.2.3.2). Tiket Selesai yang tidak direspons
 * pemohon lebih dari `close_after_hours` jam masuk daftar "Siap ditutup" untuk Operator. Tidak ada penutupan
 * otomatis: Operator menutup per tiket atau massal, dan alasannya tercatat sebagai tindak lanjut privat.
 */
final class Closure
{
    /**
     * @return array<int, array{id: int, name: string, solvedate: string, hours: int, requesters: string, url: string}>
     */
    public static function readyToClose(int $limit = 200): array
    {
        global $DB;

        $hours = max(1, (int) Config::get('close_after_hours'));
        $now   = strtotime($_SESSION['glpi_currenttime'] ?? 'now');
        $rows  = [];
        foreach ($DB->request([
            'SELECT' => ['id', 'name', 'solvedate'],
            'FROM'   => Ticket::getTable(),
            'WHERE'  => [
                'is_deleted' => 0,
                'status'     => CommonITILObject::SOLVED,
                'solvedate'  => ['<', date('Y-m-d H:i:s', $now - $hours * 3600)],
                'NOT'        => ['entities_id' => Config::getArchiveEntityIds() ?: [-1]],
            ],
            'ORDER'  => 'solvedate',
            'LIMIT'  => $limit,
        ]) as $ticket) {
            $requesters = array_map('intval', array_column((new Ticket_User())->find([
                'tickets_id' => $ticket['id'], 'type' => CommonITILActor::REQUESTER,
            ]), 'users_id'));
            // Respons pemohon setelah solusi (balasan) → bukan "tanpa respons"
            if ($requesters !== [] && countElementsInTable(ITILFollowup::getTable(), [
                'itemtype' => Ticket::class, 'items_id' => $ticket['id'],
                'users_id' => $requesters, 'date' => ['>', $ticket['solvedate']],
            ]) > 0) {
                continue;
            }
            $rows[] = [
                'id'         => (int) $ticket['id'],
                'name'       => (string) $ticket['name'],
                'solvedate'  => (string) $ticket['solvedate'],
                'hours'      => (int) floor(($now - strtotime($ticket['solvedate'])) / 3600),
                'requesters' => implode(', ', array_map('getUserName', $requesters)),
                'url'        => Ticket::getFormURLWithID((int) $ticket['id']),
            ];
        }
        return $rows;
    }

    /**
     * Tutup tiket yang masih memenuhi syarat daftar; tindak lanjut privat mencatat alasannya.
     *
     * @param int[] $ids
     * @return array{closed: int, skipped: int}
     */
    public static function close(array $ids): array
    {
        $eligible = array_column(self::readyToClose(1000), 'id');
        $closed = $skipped = 0;
        foreach (array_unique(array_map('intval', $ids)) as $id) {
            $ticket = new Ticket();
            if (!in_array($id, $eligible, true) || !$ticket->getFromDB($id) || !$ticket->canUpdateItem()) {
                $skipped++;
                continue;
            }
            (new ITILFollowup())->add([
                'itemtype'   => Ticket::class,
                'items_id'   => $id,
                'is_private' => 1,
                'content'    => htmlescape(sprintf(
                    __('Closed by the Operator: no response from the requester within %d hours after the solution (HaloSIS closure recommendation).', 'halosis'),
                    (int) Config::get('close_after_hours'),
                )),
            ]);
            if ($ticket->update(['id' => $id, 'status' => CommonITILObject::CLOSED])) {
                $closed++;
            } else {
                $skipped++;
            }
        }
        return ['closed' => $closed, 'skipped' => $skipped];
    }

    public static function canClose(): bool
    {
        return Session::haveRight(Profile::RIGHT_TRIASE, UPDATE) && Session::haveRight(Ticket::$rightname, UPDATE);
    }
}
