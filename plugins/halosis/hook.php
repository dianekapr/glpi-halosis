<?php

/**
 * Instalasi & uninstalasi plugin HaloSIS.
 *
 * Install bersifat idempoten: dijalankan ulang saat plugin diperbarui, jadi tabel/hak/config
 * yang sudah ada tidak diubah dan yang baru ditambahkan.
 */

use GlpiPlugin\Halosis\Config;
use GlpiPlugin\Halosis\KnowledgeIndex;
use GlpiPlugin\Halosis\LoginPage;
use GlpiPlugin\Halosis\PatternDetector;
use GlpiPlugin\Halosis\ProgressReminder;
use GlpiPlugin\Halosis\Profile;
use GlpiPlugin\Halosis\TriageRetry;

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
            `candidates` text COMMENT 'JSON 3 tim teratas: tim, keyakinan, groups_id',
            `type_suggested` tinyint NOT NULL DEFAULT '0' COMMENT 'Saran jenis (T4): 1 insiden, 2 permintaan, 0 tidak ada',
            `type_confidence` tinyint unsigned NOT NULL DEFAULT '0' COMMENT 'Keyakinan saran jenis 0-100',
            `urgency_confidence` tinyint unsigned NOT NULL DEFAULT '0' COMMENT 'Keyakinan saran urgensi model 0-100; 0 = aturan',
            `impact_reason` varchar(255) NOT NULL DEFAULT '' COMMENT 'Alasan dampak naik (sinyal tiket serupa / layanan kritis)',
            `quality_ok` tinyint NOT NULL DEFAULT '1' COMMENT 'Model lolos gerbang kualitas saat saran dibuat (T32)',
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
        // Percakapan chatbot self-service pegawai: transkrip, hasil (terselesaikan/jadi tiket), rating.
        'glpi_plugin_halosis_chats' => "
            `users_id` int {$sign} NOT NULL DEFAULT '0',
            `tickets_id` int {$sign} NOT NULL DEFAULT '0' COMMENT 'Tiket yang dibuat dari percakapan',
            `status` varchar(20) NOT NULL DEFAULT 'open' COMMENT 'open|resolved|ticket|expired',
            `rating` tinyint unsigned DEFAULT NULL COMMENT '1-5, saat masalah terselesaikan',
            `message_count` int NOT NULL DEFAULT '0',
            `answered_count` int NOT NULL DEFAULT '0' COMMENT 'Jawaban yang bersumber dari artikel KB',
            `transcript` longtext COMMENT 'JSON pesan pengguna & asisten (data pribadi sudah disamarkan)',
            `date_creation` timestamp NULL DEFAULT NULL,
            `date_mod` timestamp NULL DEFAULT NULL,
            KEY `users_id` (`users_id`),
            KEY `tickets_id` (`tickets_id`),
            KEY `status` (`status`),
            KEY `date_creation` (`date_creation`)
        ",
        // Tiket yang dipindah ke grup lain setelah triase AI diterapkan (indikasi saran salah tim).
        'glpi_plugin_halosis_reassignments' => "
            `tickets_id` int {$sign} NOT NULL DEFAULT '0',
            `decisions_id` int {$sign} NOT NULL DEFAULT '0',
            `from_groups_id` int {$sign} NOT NULL DEFAULT '0' COMMENT 'Grup hasil triase',
            `to_groups_id` int {$sign} NOT NULL DEFAULT '0' COMMENT 'Grup baru yang ditugaskan (0 = dikembalikan ke operator)',
            `kind` varchar(20) NOT NULL DEFAULT 'reassign' COMMENT 'reassign|return',
            `reason` text COMMENT 'Alasan dikembalikan ke operator (UC-06)',
            `users_id` int {$sign} NOT NULL DEFAULT '0',
            `date_creation` timestamp NULL DEFAULT NULL,
            KEY `tickets_id` (`tickets_id`),
            KEY `decisions_id` (`decisions_id`),
            KEY `date_creation` (`date_creation`)
        ",
        // Pola insiden yang terdeteksi tugas terjadwal; mencegah Problem ganda untuk pola yang sama.
        'glpi_plugin_halosis_patterns' => "
            `problems_id` int {$sign} NOT NULL DEFAULT '0',
            `signature` varchar(255) NOT NULL DEFAULT '' COMMENT 'cat:<id> atau title:<kata kunci>',
            `criteria` varchar(20) NOT NULL DEFAULT '' COMMENT 'category|title',
            `label` varchar(255) NOT NULL DEFAULT '',
            `ticket_count` int NOT NULL DEFAULT '0',
            `date_creation` timestamp NULL DEFAULT NULL,
            `date_mod` timestamp NULL DEFAULT NULL,
            KEY `problems_id` (`problems_id`),
            KEY `signature` (`signature`),
            KEY `date_creation` (`date_creation`)
        ",
        // Artikel KB yang dikutip chatbot per jawaban (catatPemakaian(), hal. 176): dasar hitungan pemakaian.
        'glpi_plugin_halosis_article_uses' => "
            `knowbaseitems_id` int {$sign} NOT NULL DEFAULT '0',
            `chats_id` int {$sign} NOT NULL DEFAULT '0',
            `date_creation` timestamp NULL DEFAULT NULL,
            KEY `knowbaseitems_id` (`knowbaseitems_id`),
            KEY `chats_id` (`chats_id`),
            KEY `date_creation` (`date_creation`)
        ",
        // Umpan balik agent di Cari knowledge (KR-07): hasil membantu / tidak. Teks kueri tidak disimpan (NFR-06).
        'glpi_plugin_halosis_feedback' => "
            `users_id` int {$sign} NOT NULL DEFAULT '0',
            `source_kind` varchar(20) NOT NULL DEFAULT '' COMMENT 'kb|tiket',
            `source_ref` varchar(100) NOT NULL DEFAULT '' COMMENT 'KB-<id> atau nomor tiket historis',
            `knowbaseitems_id` int {$sign} NOT NULL DEFAULT '0',
            `score` float DEFAULT NULL COMMENT 'Skor relevansi hasil (0-1), kosong untuk kata kunci',
            `is_helpful` tinyint NOT NULL DEFAULT '0',
            `date_creation` timestamp NULL DEFAULT NULL,
            KEY `users_id` (`users_id`),
            KEY `knowbaseitems_id` (`knowbaseitems_id`),
            KEY `date_creation` (`date_creation`)
        ",
        // Percobaan ulang saran triase untuk tiket Baru tanpa saran (NFR-03, tugas TriageRetry)
        'glpi_plugin_halosis_triage_retries' => "
            `tickets_id` int {$sign} NOT NULL DEFAULT '0',
            `attempts` int NOT NULL DEFAULT '0',
            `last_error` varchar(255) NOT NULL DEFAULT '',
            `date_mod` timestamp NULL DEFAULT NULL,
            UNIQUE KEY `tickets_id` (`tickets_id`)
        ",
        // E19: pengingat progres terakhir per tiket (sekali per periode tanpa tindak lanjut).
        'glpi_plugin_halosis_progress_reminders' => "
            `tickets_id` int {$sign} NOT NULL DEFAULT '0',
            `last_activity` timestamp NULL DEFAULT NULL COMMENT 'Aktivitas terakhir saat diingatkan',
            `date_reminder` timestamp NULL DEFAULT NULL,
            `idle_days` int NOT NULL DEFAULT '0' COMMENT 'Hari kerja tanpa tindak lanjut saat diingatkan',
            UNIQUE KEY `tickets_id` (`tickets_id`)
        ",
        // Tanggal tinjau berikut per artikel KB (KR-03); tanpa baris = date_mod + kb_review_months.
        'glpi_plugin_halosis_kb_reviews' => "
            `knowbaseitems_id` int {$sign} NOT NULL DEFAULT '0',
            `date_review` date DEFAULT NULL COMMENT 'Tanggal tinjau berikut',
            `users_id` int {$sign} NOT NULL DEFAULT '0' COMMENT 'Yang mengatur tanggal',
            `date_mod` timestamp NULL DEFAULT NULL,
            UNIQUE KEY `knowbaseitems_id` (`knowbaseitems_id`),
            KEY `date_review` (`date_review`)
        ",
        // Kandidat Knowledge (UC-09): solusi tiket selesai atau solusi berulang dari indeks AI, dikurasi
        // Knowledge Manager menjadi draf artikel KB atau diabaikan dengan alasan.
        'glpi_plugin_halosis_candidates' => "
            `source` varchar(20) NOT NULL DEFAULT '' COMMENT 'ticket|ai',
            `source_ref` varchar(100) NOT NULL DEFAULT '' COMMENT 'ID tiket GLPI atau kunci klaster AI',
            `tickets_id` int {$sign} NOT NULL DEFAULT '0',
            `title` varchar(255) NOT NULL DEFAULT '',
            `problem` text COMMENT 'Masalah (tersamar)',
            `solution` text COMMENT 'Solusi (tersamar)',
            `occurrences` int NOT NULL DEFAULT '1' COMMENT 'Jumlah tiket dengan solusi serupa',
            `examples` text COMMENT 'Contoh nomor tiket history (sumber AI)',
            `is_approved` tinyint NOT NULL DEFAULT '0' COMMENT 'Solusi disetujui pemohon',
            `status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT 'pending|article|ignored',
            `knowbaseitems_id` int {$sign} NOT NULL DEFAULT '0',
            `reason` text COMMENT 'Alasan diabaikan',
            `users_id` int {$sign} NOT NULL DEFAULT '0' COMMENT 'Knowledge Manager yang memutuskan',
            `date_decision` timestamp NULL DEFAULT NULL,
            `date_creation` timestamp NULL DEFAULT NULL,
            `date_mod` timestamp NULL DEFAULT NULL,
            UNIQUE KEY `source_ref` (`source`, `source_ref`),
            KEY `status` (`status`),
            KEY `tickets_id` (`tickets_id`)
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

    // Kolom yang ditambahkan setelah versi awal (pemasangan lama tetap dimutakhirkan)
    $added = [
        'glpi_plugin_halosis_suggestions' => [
            'candidates' => 'text AFTER `explanation`',
            'type_suggested'  => "tinyint NOT NULL DEFAULT '0' AFTER `candidates`",
            'type_confidence' => "tinyint unsigned NOT NULL DEFAULT '0' AFTER `type_suggested`",
            'quality_ok'      => "tinyint NOT NULL DEFAULT '1' AFTER `type_confidence`",
            'urgency_confidence' => "tinyint unsigned NOT NULL DEFAULT '0' AFTER `type_confidence`",
            'impact_reason'      => "varchar(255) NOT NULL DEFAULT '' AFTER `urgency_confidence`",
        ],
        'glpi_plugin_halosis_reassignments' => [
            'kind'   => "varchar(20) NOT NULL DEFAULT 'reassign' AFTER `to_groups_id`",
            'reason' => 'text AFTER `kind`',
        ],
    ];
    foreach ($added as $table => $fields) {
        foreach ($fields as $field => $definition) {
            if (!$DB->fieldExists($table, $field)) {
                $DB->doQuery("ALTER TABLE `{$table}` ADD `{$field}` {$definition}");
            }
        }
    }

    Config::install();
    Profile::install();
    // Katalog layanan awal ke indeks AI (BR-03); layanan mati → dilewati, tersinkron saat kategori/form berubah
    KnowledgeIndex::syncServiceCatalog();

    // Deteksi pola insiden tiap 15 menit (tidak menimpa jadwal yang sudah diubah admin)
    CronTask::register(PatternDetector::class, PatternDetector::CRON_NAME, 15 * MINUTE_TIMESTAMP, [
        'comment' => 'HaloSIS: deteksi pola insiden',
        'mode'    => CronTask::MODE_EXTERNAL,
    ]);
    // NFR-03: saran triase yang terlewat karena AI sempat mati dicoba lagi tiap 15 menit
    CronTask::register(TriageRetry::class, TriageRetry::CRON_NAME, 15 * MINUTE_TIMESTAMP, [
        'comment' => 'HaloSIS: coba ulang saran triase yang terlewat',
        'mode'    => CronTask::MODE_EXTERNAL,
    ]);
    // E19: pengingat progres harian untuk tiket tanpa tindak lanjut + notifikasi bawaannya
    CronTask::register(ProgressReminder::class, ProgressReminder::CRON_NAME, DAY_TIMESTAMP, [
        'comment' => 'HaloSIS: pengingat progres tiket tanpa tindak lanjut',
        'mode'    => CronTask::MODE_EXTERNAL,
        'hourmin' => 7,
        'hourmax' => 17,
    ]);
    ProgressReminder::installNotification();
    // Label inti halaman login ("Sign in", …) dalam Bahasa Indonesia lewat folder terjemahan lokal GLPI
    LoginPage::installCoreLocales();

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
    ProgressReminder::uninstallNotification();
    LoginPage::uninstallCoreLocales();
    CronTask::unregister('halosis');

    return true;
}
