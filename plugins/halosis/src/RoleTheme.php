<?php

namespace GlpiPlugin\Halosis;

use Session;

/**
 * Warna aksen per peran (cara 1: hanya aksen; latar, warna semantik, grafik, dan logo tetap).
 *
 * Peran dibaca dari ID profil AKTIF (seperti RoleMenu), bukan dari nama pengguna, jadi ikut berubah saat pengguna
 * mengganti profil. Peran dikirim ke halaman lewat tag <meta name="halosis-role"> (hook add_header_tag, tersedia
 * sejak awal render sehingga warna tidak berkedip); public/js/role.js memasang kelas `hs-role-<peran>` di <body>
 * dan lencana nama peran di header. Variabel warna: public/css/halosis.css, pemakaian: themes/halosis.scss.
 * Halaman login (anonim) tidak mendapat peran → tetap teal netral.
 */
final class RoleTheme
{
    public const META_NAME = 'halosis-role';

    /**
     * Kunci peran untuk profil aktif; null bila tidak login atau profil di luar 6 peran HaloSIS.
     */
    public static function currentRole(): ?string
    {
        if (Session::getLoginUserID() === false) {
            return null;
        }
        $profile_id = (int) ($_SESSION['glpiactiveprofile']['id'] ?? 0);
        return match ($profile_id) {
            Roles::PEGAWAI    => 'pegawai',
            Roles::OPERATOR   => 'operator',
            // Ketua tim memakai profil Tim Teknis (pengelola grup), jadi warnanya sama
            Roles::TIM_TEKNIS => 'tim-teknis',
            Roles::MANAJEMEN  => 'manajemen',
            // Super-Admin = Administrator
            Roles::ADMINISTRATOR, Roles::SUPER_ADMIN => 'administrator',
            0       => null,
            default => $profile_id === Roles::findKnowledgeManagerId() ? 'knowledge-manager' : null,
        };
    }

    /**
     * Tag header untuk hook add_header_tag (kosong bila tanpa peran).
     *
     * @return array<int, array{tag: string, properties: array<string, string>}>
     */
    public static function getHeaderTags(): array
    {
        $role = self::currentRole();
        if ($role === null) {
            return [];
        }
        return [[
            'tag'        => 'meta',
            'properties' => [
                'name'       => self::META_NAME,
                'content'    => $role,
                // Teks lencana: nama profil aktif apa adanya (mis. "Super-Admin" tetap tertulis Super-Admin)
                'data-label' => (string) ($_SESSION['glpiactiveprofile']['name'] ?? ''),
            ],
        ]];
    }
}
