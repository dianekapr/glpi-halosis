<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;
use CommonITILActor;
use Group_Ticket;
use Session;
use Throwable;
use Toolbox;

/**
 * Pemindahan tiket ke grup lain SETELAH triase AI diterapkan (Terima/Ubah) — indikasi saran salah tim.
 * Dicatat lewat hook item_add Group_Ticket (tabel glpi_plugin_halosis_reassignments); dipakai dashboard
 * kinerja AI untuk metrik "% tiket dipindah ke tim lain setelah triase".
 */
final class Reassignment extends CommonDBTM
{
    public static string $rightname = Profile::RIGHT_DASHBOARD;

    public bool $dohistory = false;

    public static function getTypeName($nb = 0)
    {
        return _n('Team reassignment', 'Team reassignments', $nb, 'halosis');
    }

    /**
     * Hook item_add Group_Ticket. Saat Terima/Ubah, grup ditambahkan SEBELUM keputusan tercatat,
     * jadi penugasan oleh triase itu sendiri tidak terhitung sebagai pemindahan.
     */
    public static function onGroupTicketAdd(Group_Ticket $link): void
    {
        try {
            if ((int) $link->fields['type'] !== CommonITILActor::ASSIGN) {
                return;
            }
            $tickets_id = (int) $link->fields['tickets_id'];
            $groups_id  = (int) $link->fields['groups_id'];

            $decision = new Decision();
            $found = $decision->getFromDBByRequest([
                'WHERE' => ['tickets_id' => $tickets_id, 'action' => [Decision::ACTION_ACCEPT, Decision::ACTION_MODIFY]],
                'ORDER' => 'id DESC',
                'LIMIT' => 1,
            ]);
            if (!$found) {
                return;
            }
            $final = json_decode((string) $decision->fields['final_values'], true);
            $triaged_group = (int) ($final['groups_id'] ?? 0);
            if ($triaged_group === 0 || $triaged_group === $groups_id) {
                return;
            }

            (new self())->add([
                'tickets_id'     => $tickets_id,
                'decisions_id'   => $decision->getID(),
                'from_groups_id' => $triaged_group,
                'to_groups_id'   => $groups_id,
                'users_id'       => (int) Session::getLoginUserID(),
            ]);
        } catch (Throwable $e) {
            // Pencatatan metrik tidak boleh mengganggu penugasan tiket
            Toolbox::logInFile('halosis', 'Gagal mencatat pemindahan tim: ' . $e->getMessage() . "\n", true);
        }
    }
}
