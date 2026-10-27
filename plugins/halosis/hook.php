<?php

/**
 * Instalasi & uninstalasi plugin HaloSIS.
 *
 * Install bersifat idempoten: dijalankan ulang saat plugin diperbarui, jadi tabel/hak/config
 * yang sudah ada tidak diubah dan yang baru ditambahkan.
 */

use GlpiPlugin\Halosis\Config;
use GlpiPlugin\Halosis\Profile;

/**
 * Daftar tabel plugin beserta definisi kolomnya (tanpa kolom id).
 *
 * @return array<string, string>
 */
function plugin_halosis_tables(): array
{
    $sign = DBConnection::getDefaultPrimaryKeySignOption();

    return [
        // Saran triase AI per tiket. Disimpan di tabel plugin, bukan di field tiket.
        'glpi_plugin_halosis_suggestions' => "
            `tickets_id` int {$sign} NOT NULL DEFAULT '0',
            `itilcategories_id` int {$sign} NOT NULL DEFAULT '0',
            `impact` tinyint NOT NULL DEFAULT '3',
            `urgency` tinyint NOT NULL DEFAULT '3',
            `priority` tinyint NOT NULL DEFAULT '3',
            `groups_id` int {$sign} NOT NULL DEFAULT '0',
            `confidence` tinyint unsigned NOT NULL DEFAULT '0' COMMENT 'Keyakinan 0-100',
            `explanation` text,
            `model` varchar(255) NOT NULL DEFAULT '',
            `is_demo` tinyint NOT NULL DEFAULT '0',
            `status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT 'pending|accepted|modified|rejected',
            `date_creation` timestamp NULL DEFAULT NULL,
            `date_mod` timestamp NULL DEFAULT NULL,
            KEY `tickets_id` (`tickets_id`),
            KEY `status` (`status`),
            KEY `date_creation` (`date_creation`)
        ",
        // Log keputusan petugas atas saran AI (Terima / Ubah / Tolak), dasar dashboard kinerja AI.
        'glpi_plugin_halosis_decisions' => "
            `suggestions_id` int {$sign} NOT NULL DEFAULT '0',
            `tickets_id` int {$sign} NOT NULL DEFAULT '0',
            `users_id` int {$sign} NOT NULL DEFAULT '0',
            `action` varchar(20) NOT NULL DEFAULT '' COMMENT 'accept|modify|reject',
            `suggested_values` longtext COMMENT 'JSON nilai saran AI',
            `final_values` longtext COMMENT 'JSON nilai final yang diterapkan',
            `reason` text,
            `date_creation` timestamp NULL DEFAULT NULL,
            KEY `suggestions_id` (`suggestions_id`),
            KEY `tickets_id` (`tickets_id`),
            KEY `users_id` (`users_id`),
            KEY `action` (`action`),
            KEY `date_creation` (`date_creation`)
        ",
    ];
}

function plugin_halosis_install(): bool
{
    global $DB;

    $charset   = DBConnection::getDefaultCharset();
    $collation = DBConnection::getDefaultCollation();
    $sign      = DBConnection::getDefaultPrimaryKeySignOption();

    foreach (plugin_halosis_tables() as $table => $columns) {
        if ($DB->tableExists($table)) {
            continue;
        }
        $DB->doQuery("
            CREATE TABLE `{$table}` (
                `id` int {$sign} NOT NULL AUTO_INCREMENT,
                {$columns},
                PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET={$charset} COLLATE={$collation} ROW_FORMAT=DYNAMIC
        ");
    }

    Config::install();
    Profile::install();

    return true;
}

function plugin_halosis_uninstall(): bool
{
    global $DB;

    foreach (array_keys(plugin_halosis_tables()) as $table) {
        $DB->dropTable($table, true);
    }

    Config::uninstall();
    Profile::uninstall();

    return true;
}
