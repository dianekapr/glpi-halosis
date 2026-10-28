<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;
use CommonITILActor;
use Group_Ticket;
use ITILFollowup;
use Session;
use Ticket;
use Ticket_User;
use Throwable;
use Toolbox;

/**
 * Pemindahan tiket ke grup lain SETELAH triase AI diterapkan (Terima/Ubah) — indikasi saran salah tim.
 * Dicatat lewat hook item_add Group_Ticket (tabel glpi_plugin_halosis_reassignments); dipakai dashboard
 * kinerja AI untuk metrik "% tiket dipindah ke tim lain setelah triase".
 *
 * UC-06 alur alternatif: Tim Teknis dapat mengembalikan tiket ke operator karena salah tim (alasan wajib).
 * Dicatat dengan kind = return dan to_groups_id = 0, sehingga ikut dihitung sebagai saran salah tim.
 */
final class Reassignment extends CommonDBTM
{
    public static string $rightname = Profile::RIGHT_DASHBOARD;

    public const KIND_REASSIGN = 'reassign';
    public const KIND_RETURN   = 'return';

    /** Status tiket yang boleh dikembalikan: sudah ditugaskan, belum diselesaikan */
    private const RETURNABLE_STATUS = [Ticket::ASSIGNED, Ticket::PLANNED, Ticket::WAITING];

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
                'kind'           => self::KIND_REASSIGN,
                'users_id'       => (int) Session::getLoginUserID(),
            ]);
        } catch (Throwable $e) {
            // Pencatatan metrik tidak boleh mengganggu penugasan tiket
            Toolbox::logInFile('halosis', 'Gagal mencatat pemindahan tim: ' . $e->getMessage() . "\n", true);
        }
    }

    /**
     * Pengguna aktif termasuk tim yang ditugaskan (teknisi atau anggota grup) dan boleh mengubah tiket.
     */
    public static function canReturn(Ticket $ticket): bool
    {
        if (
            !in_array((int) $ticket->fields['status'], self::RETURNABLE_STATUS, true)
            || !$ticket->canUpdateItem()
        ) {
            return false;
        }
        $users_id = (int) Session::getLoginUserID();
        return $ticket->isUser(CommonITILActor::ASSIGN, $users_id)
            || $ticket->haveAGroup(CommonITILActor::ASSIGN, $_SESSION['glpigroups'] ?? []);
    }

    /**
     * Kembalikan tiket ke antrean validasi operator: grup & teknisi dilepas, status kembali Baru,
     * alasan dicatat sebagai tindak lanjut privat dan data evaluasi AI.
     *
     * @return string|null pesan kesalahan, null bila berhasil
     */
    public static function returnToOperator(Ticket $ticket, string $reason): ?string
    {
        $reason = trim($reason);
        if (!self::canReturn($ticket)) {
            return __('Only the assigned team can return this ticket while it is in progress.', 'halosis');
        }
        if (mb_strlen($reason) < Triage::MIN_REASON_LENGTH) {
            return sprintf(__('A reason of at least %d characters is required.', 'halosis'), Triage::MIN_REASON_LENGTH);
        }

        $tickets_id = $ticket->getID();
        $groups = array_column($ticket->getGroups(CommonITILActor::ASSIGN), 'groups_id');

        $followup = new ITILFollowup();
        $followup->add([
            'itemtype'   => Ticket::class,
            'items_id'   => $tickets_id,
            'is_private' => 1,
            'users_id'   => (int) Session::getLoginUserID(),
            'content'    => sprintf(__('Returned to operator (wrong team): %s', 'halosis'), $reason),
        ]);

        (new Group_Ticket())->deleteByCriteria(['tickets_id' => $tickets_id, 'type' => CommonITILActor::ASSIGN]);
        (new Ticket_User())->deleteByCriteria(['tickets_id' => $tickets_id, 'type' => CommonITILActor::ASSIGN]);
        $ticket->update(['id' => $tickets_id, 'status' => Ticket::INCOMING]);

        $decision = new Decision();
        $has_decision = $decision->getFromDBByRequest([
            'WHERE' => ['tickets_id' => $tickets_id, 'action' => [Decision::ACTION_ACCEPT, Decision::ACTION_MODIFY]],
            'ORDER' => 'id DESC',
            'LIMIT' => 1,
        ]);
        (new self())->add([
            'tickets_id'     => $tickets_id,
            'decisions_id'   => $has_decision ? $decision->getID() : 0,
            'from_groups_id' => (int) ($groups[0] ?? 0),
            'to_groups_id'   => 0,
            'kind'           => self::KIND_RETURN,
            'reason'         => $reason,
            'users_id'       => (int) Session::getLoginUserID(),
        ]);
        return null;
    }
}
