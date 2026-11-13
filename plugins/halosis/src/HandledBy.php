<?php

namespace GlpiPlugin\Halosis;

use Ticket;

/**
 * UC-07: "Ditangani oleh" untuk pegawai — posisi laporan dalam bahasa awam, hanya nama GRUP (bukan nama orang).
 * Dipakai sebagai kolom daftar "Laporan saya" (opsi pencarian plugin) dan info di detail tiket pegawai.
 */
final class HandledBy
{
    public const SEARCH_OPTION = 9101;

    public static function label(int $status, string $groups = ''): string
    {
        return match ($status) {
            Ticket::INCOMING => __('Awaiting Operator validation', 'halosis'),
            Ticket::ASSIGNED, Ticket::PLANNED => $groups !== '' ? $groups : __('In process by the IT team', 'halosis'),
            Ticket::WAITING => __('Awaiting your response', 'halosis'),
            Ticket::SOLVED => __('Completed, awaiting your confirmation', 'halosis'),
            Ticket::CLOSED => __('Closed', 'halosis'),
            default => '',
        };
    }

    /** Opsi pencarian terhitung (SQL) untuk daftar tiket */
    public static function searchOption(): array
    {
        global $DB;

        $groups = "(SELECT GROUP_CONCAT(DISTINCT g.name ORDER BY g.name SEPARATOR ', ') FROM glpi_groups_tickets gt"
            . ' JOIN glpi_groups g ON g.id = gt.groups_id WHERE gt.tickets_id = glpi_tickets.id AND gt.type = 2)';
        $q = static fn (string $s): string => $DB->quote($s);
        $sql = 'CASE glpi_tickets.status'
            . ' WHEN ' . Ticket::INCOMING . ' THEN ' . $q(self::label(Ticket::INCOMING))
            . ' WHEN ' . Ticket::ASSIGNED . ' THEN COALESCE(' . $groups . ', ' . $q(self::label(Ticket::ASSIGNED)) . ')'
            . ' WHEN ' . Ticket::PLANNED . ' THEN COALESCE(' . $groups . ', ' . $q(self::label(Ticket::ASSIGNED)) . ')'
            . ' WHEN ' . Ticket::WAITING . ' THEN ' . $q(self::label(Ticket::WAITING))
            . ' WHEN ' . Ticket::SOLVED . ' THEN ' . $q(self::label(Ticket::SOLVED))
            . ' WHEN ' . Ticket::CLOSED . ' THEN ' . $q(self::label(Ticket::CLOSED))
            . " ELSE '' END";

        return [
            'id'          => self::SEARCH_OPTION,
            'table'       => 'glpi_tickets',
            'field'       => 'status',
            'name'        => __('Handled by', 'halosis'),
            'datatype'    => 'string',
            'computation' => new \Glpi\DBAL\QueryExpression($sql),
            'nosearch'    => true,
            'nosort'      => true,
            'massiveaction' => false,
        ];
    }

    /**
     * Teks untuk detail tiket pegawai (dipakai ajax/ditangani.php). Null bila tiket tidak ada / bukan milik pengguna.
     */
    public static function textFor(int $ticket_id): ?string
    {
        $ticket = new Ticket();
        if (!$ticket->getFromDB($ticket_id) || !$ticket->canViewItem()) {
            return null;
        }
        $groups = [];
        foreach ((new \Group_Ticket())->find(['tickets_id' => $ticket_id, 'type' => \CommonITILActor::ASSIGN]) as $row) {
            $groups[] = (string) \Group::getById((int) $row['groups_id'])?->fields['name'];
        }
        $text = self::label((int) $ticket->fields['status'], implode(', ', array_filter($groups)));

        return $text === '' ? null : $text;
    }
}
