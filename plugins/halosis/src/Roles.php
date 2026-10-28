<?php

namespace GlpiPlugin\Halosis;

use CommonITILObject;
use CommonITILTask;
use ITILFollowup;
use KnowbaseItem;
use Profile as CoreProfile;
use ProfileRight;
use User;

/**
 * Pemetaan 6 role HaloSIS ke profil GLPI.
 *
 * Profil bawaan GLPI dikenali dari ID-nya (stabil sejak instalasi), bukan dari nama, sehingga
 * aman diganti nama. Profil "Knowledge Manager" tidak ada di GLPI dan dibuat oleh plugin.
 * Dipakai oleh perintah `plugins:halosis:setup-roles` dan oleh instalasi plugin (hak default).
 */
final class Roles
{
    // ID profil bawaan instalasi GLPI
    public const PEGAWAI       = 1; // Self-Service, antarmuka Helpdesk
    public const MANAJEMEN     = 2; // Observer
    public const ADMINISTRATOR = 3; // Admin
    public const SUPER_ADMIN   = 4; // Super-Admin, khusus akun pengelola sistem
    public const OPERATOR      = 5; // Hotliner
    public const TIM_TEKNIS    = 6; // Technician

    public const KNOWLEDGE_MANAGER_NAME = 'Knowledge Manager';

    /** Akun bawaan GLPI yang tidak dipakai HaloSIS dan dinonaktifkan */
    public const DEFAULT_ACCOUNTS = ['tech', 'normal', 'post-only'];

    /**
     * Nama baru profil bawaan (Super-Admin sengaja tidak diganti).
     *
     * @return array<int, string>
     */
    public static function getProfileNames(): array
    {
        return [
            self::PEGAWAI       => 'Pegawai',
            self::MANAJEMEN     => 'Manajemen',
            self::ADMINISTRATOR => 'Administrator',
            self::OPERATOR      => 'Operator',
            self::TIM_TEKNIS    => 'Tim Teknis',
        ];
    }

    /**
     * Hak plugin per profil. Profil yang tidak disebut mendapat 0 untuk semua hak plugin.
     *
     * @return array<int, array<string, int>>
     */
    public static function getPluginRights(): array
    {
        $rights = [
            self::PEGAWAI => [
                Profile::RIGHT_CHATBOT => READ,
            ],
            self::OPERATOR => [
                Profile::RIGHT_TRIASE => READ | UPDATE,
            ],
            self::TIM_TEKNIS => [
                Profile::RIGHT_TRIASE => READ,
            ],
            self::MANAJEMEN => [
                Profile::RIGHT_DASHBOARD => READ,
            ],
            self::ADMINISTRATOR => [
                Profile::RIGHT_TRIASE    => READ | UPDATE,
                Profile::RIGHT_DASHBOARD => READ,
                Profile::RIGHT_CONFIG    => UPDATE,
                Profile::RIGHT_KANDIDAT  => READ | UPDATE,
            ],
            // Akun pengelola sistem (di luar aktor dokumen): semua hak plugin
            self::SUPER_ADMIN => [
                Profile::RIGHT_TRIASE    => READ | UPDATE,
                Profile::RIGHT_DASHBOARD => READ,
                Profile::RIGHT_CONFIG    => UPDATE,
                Profile::RIGHT_KANDIDAT  => READ | UPDATE,
            ],
        ];
        // Knowledge Manager dibuat oleh plugin (ID tidak tetap): UC-09 kurasi kandidat knowledge
        if (($km_id = self::findKnowledgeManagerId()) !== null) {
            $rights[$km_id] = [Profile::RIGHT_KANDIDAT => READ | UPDATE];
        }
        return $rights;
    }

    /**
     * UC-08 & FR-04 (Tabel 6.1): Operator mewarisi pemantauan SLA & pola insiden dari Petugas Layanan TI dan
     * boleh mengubah Masalah (konfirmasi/tutup pola, tautkan tiket).
     *
     * @return array<string, int>
     */
    public static function getOperatorCoreRights(): array
    {
        return [
            'problem' => CommonITILObject::READALL | CommonITILObject::READMY | UPDATE,
        ];
    }

    /**
     * UC-10: Administrator Sistem mengonfigurasi service catalog (form) dan aturan notifikasi, serta membaca
     * audit trail; hak ini tidak termasuk bawaan profil Admin GLPI. Template notifikasi tetap hak `config`.
     *
     * @return array<string, int>
     */
    public static function getAdministratorCoreRights(): array
    {
        return [
            'form'         => READ | UPDATE | CREATE | DELETE | PURGE,
            'notification' => READ | UPDATE | CREATE | PURGE,
            // Audit trail (log sistem GLPI, halaman Event); hak `logs` hanya untuk tab Riwayat per objek
            'system_logs'  => READ,
        ];
    }

    /**
     * UC-08: Tim Teknis mewarisi pemantauan SLA & pola insiden, tetapi Masalah hanya-baca.
     *
     * @return array<string, int>
     */
    public static function getTimTeknisCoreRights(): array
    {
        return [
            'problem' => CommonITILObject::READALL | CommonITILObject::READMY,
        ];
    }

    /**
     * Hak inti GLPI yang ditegaskan untuk Manajemen: hanya melihat (tiket, dashboard, statistik).
     * Hak lain mengikuti bawaan profil Observer.
     *
     * @return array<string, int>
     */
    public static function getManajemenCoreRights(): array
    {
        return [
            'ticket'           => CommonITILObject::READALL | CommonITILObject::READMY,
            'followup'         => ITILFollowup::SEEPUBLIC,
            'task'             => CommonITILTask::SEEPUBLIC,
            'ticketvalidation' => 0,
            'ticketcost'       => READ,
            'problem'          => READ | CommonITILObject::READALL,
            'dashboard'        => READ,
            'statistic'        => READ,
            'reports'          => READ,
        ];
    }

    /**
     * Hak profil Knowledge Manager: penuh di Knowledge Base, tiket hanya baca, tanpa konfigurasi.
     * Hak yang tidak disebut bernilai 0.
     *
     * @return array<string, int>
     */
    public static function getKnowledgeManagerRights(): array
    {
        return [
            'knowbase' => READ | UPDATE | CREATE | PURGE
                | KnowbaseItem::KNOWBASEADMIN | KnowbaseItem::READFAQ
                | KnowbaseItem::PUBLISHFAQ | KnowbaseItem::COMMENTS,
            // Lihat semua tiket + balasan/tugas (termasuk catatan internal) untuk mengambil solusi
            'ticket'          => CommonITILObject::READALL | CommonITILObject::READMY,
            'followup'        => ITILFollowup::SEEPUBLIC | ITILFollowup::SEEPRIVATE,
            'task'            => CommonITILTask::SEEPUBLIC | CommonITILTask::SEEPRIVATE,
            'problem'         => READ | CommonITILObject::READALL,
            'document'        => READ,
            'user'            => READ,
            'reminder_public' => READ,
            'rssfeed_public'  => READ,
            'personalization' => READ | UPDATE,
            'password_update' => 1,
        ];
    }

    public static function findKnowledgeManagerId(): ?int
    {
        $profile = new CoreProfile();
        return $profile->getFromDBByCrit(['name' => self::KNOWLEDGE_MANAGER_NAME]) ? $profile->getID() : null;
    }

    /**
     * Terapkan semua role HaloSIS. Aman dijalankan berulang (nilai akhir selalu sama).
     *
     * @return string[] Log langkah yang dikerjakan
     */
    public static function apply(): array
    {
        $log = [];

        // 1. Ganti nama profil bawaan (ID tetap, pengguna yang terhubung tidak terpengaruh)
        foreach (self::getProfileNames() as $id => $name) {
            $profile = new CoreProfile();
            if (!$profile->getFromDB($id)) {
                $log[] = "Profil #{$id} tidak ditemukan, dilewati";
                continue;
            }
            $old = $profile->fields['name'];
            if ($old !== $name) {
                $profile->update(['id' => $id, 'name' => $name]);
                $log[] = "Profil #{$id}: \"{$old}\" → \"{$name}\"";
            } else {
                $log[] = "Profil #{$id}: \"{$name}\" (sudah sesuai)";
            }
        }

        // 2. Manajemen: pastikan hanya-baca (termasuk Masalah/pola insiden, UC-08)
        ProfileRight::updateProfileRights(self::MANAJEMEN, self::getManajemenCoreRights());
        $log[] = 'Manajemen: hak tiket/followup/tugas/masalah diset hanya-baca, dashboard & statistik dapat dilihat';

        // 2b. Petugas Layanan TI (UC-08): Operator boleh mengubah Masalah (FR-04), Tim Teknis hanya melihat
        ProfileRight::updateProfileRights(self::OPERATOR, self::getOperatorCoreRights());
        ProfileRight::updateProfileRights(self::TIM_TEKNIS, self::getTimTeknisCoreRights());
        $log[] = 'Operator: Masalah lihat + ubah (konfirmasi/tutup pola, tautkan tiket); Tim Teknis: Masalah hanya-baca';

        // Profil Operator berasal dari "Hotliner" GLPI yang membuka form tiket baru saat login; Operator HaloSIS
        // mulai dari dashboard & antrean validasi
        $operator = new CoreProfile();
        if ($operator->getFromDB(self::OPERATOR) && (int) $operator->fields['create_ticket_on_login'] !== 0) {
            $operator->update(['id' => self::OPERATOR, 'create_ticket_on_login' => 0]);
            $log[] = 'Operator: tidak lagi membuka form tiket baru saat login';
        }

        // 2c. Administrator Sistem (UC-10): service catalog, aturan notifikasi, audit trail
        ProfileRight::updateProfileRights(self::ADMINISTRATOR, self::getAdministratorCoreRights());
        $log[] = 'Administrator: kelola service catalog (form) & notifikasi, baca audit trail';

        // 3. Knowledge Manager: buat jika belum ada, lalu set hak (semua hak lain = 0)
        $km_id = self::findKnowledgeManagerId();
        if ($km_id === null) {
            $km_id = (int) (new CoreProfile())->add([
                'name'      => self::KNOWLEDGE_MANAGER_NAME,
                'interface' => 'central',
                'comment'   => 'Role HaloSIS: kelola Knowledge Base, tiket hanya baca',
            ]);
            $log[] = "Profil Knowledge Manager dibuat (#{$km_id})";
        } else {
            $log[] = "Profil Knowledge Manager sudah ada (#{$km_id})";
        }
        $km_rights = array_fill_keys(array_keys(ProfileRight::getAllPossibleRights()), 0);
        ProfileRight::updateProfileRights($km_id, array_merge($km_rights, self::getKnowledgeManagerRights()));
        $log[] = 'Knowledge Manager: hak penuh Knowledge Base, tiket hanya baca, tanpa konfigurasi';

        // 4. Hak plugin HaloSIS ditegaskan ke nilai default untuk semua profil
        Profile::applyRights(self::getPluginRights(), true);
        $log[] = 'Hak plugin HaloSIS diterapkan ke semua profil';

        // 5. Nonaktifkan akun bawaan yang tidak dipakai
        foreach (self::DEFAULT_ACCOUNTS as $login) {
            $user = new User();
            if ($user->getFromDBbyName($login) && $user->fields['is_active']) {
                $user->update(['id' => $user->getID(), 'is_active' => 0]);
                $log[] = "Akun bawaan \"{$login}\" dinonaktifkan";
            }
        }

        return $log;
    }
}
