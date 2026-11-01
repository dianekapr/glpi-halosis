<?php

/**
 * Tes unit fitur penutup 🟡 tanpa basis data GLPI (data rekaan):
 *   - E15  Summary::extract — ringkasan 3 kalimat untuk deskripsi > 150 kata, tersamar, deterministik;
 *   - UC-04 Triage::workloadTiebreak — beban kerja hanya memutus seri bila selisih keyakinan < 5 poin;
 *   - UC-10 ConfigAudit::slaState — aman / berisiko (sisa ≤ 20%) / terlewati.
 * Alur yang butuh GLPI (pratinjau SLA, pola permintaan, pengingat progres) diuji di aplikasi (lihat README).
 *
 * Pakai (container GLPI): php plugins/halosis/tools/test_fitur.php   → keluar 0 bila lulus
 */

if (!function_exists('__')) {
    function __($text, $domain = null)
    {
        return $text;
    }
}

$src = dirname(__DIR__) . '/src';
foreach (['Privacy', 'KnowledgeSearch', 'Summary', 'Triage', 'ConfigAudit'] as $class) {
    require_once "{$src}/{$class}.php";
}

use GlpiPlugin\Halosis\ConfigAudit;
use GlpiPlugin\Halosis\Summary;
use GlpiPlugin\Halosis\Triage;

$checks = [];

// E15 — deskripsi panjang rekaan: keluhan utama (aplikasi survei gagal sinkron) diulang, kalimat lain pengisi
$filler = 'Kami sudah mencoba beberapa langkah umum seperti menutup dan membuka kembali perangkat di ruangan kantor. ';
$text = 'Aplikasi survei gagal sinkron sejak pagi untuk seluruh petugas lapangan di kabupaten. '
    . str_repeat($filler, 6)
    . 'Pesan galat sinkron muncul setiap kali petugas menekan tombol kirim pada aplikasi survei. '
    . 'Kontak saya uji.pegawai@contoh.go.id atau 081234567890 bila perlu konfirmasi. '
    . str_repeat('Cuaca hari ini cerah dan rapat koordinasi berjalan seperti biasa di aula. ', 4)
    . 'Mohon bantuan agar sinkron aplikasi survei kembali normal sebelum batas waktu pengiriman data.';
$long = Summary::forTicketContent('<p>' . htmlspecialchars($text) . '</p>');
$joined = implode(' ', $long['sentences'] ?? []);
$checks['E15 deskripsi > 150 kata → 3 kalimat'] = $long !== null && count($long['sentences']) === 3 && $long['words'] > 150;
$checks['E15 kalimat kunci (sinkron aplikasi survei) terpilih'] = substr_count(mb_strtolower($joined), 'sinkron') >= 2
    && !str_contains($joined, 'Cuaca hari ini');
// Kalimat kontak harus terpilih dulu agar penyamaran benar-benar teruji
$contact = Summary::forTicketContent('<p>' . htmlspecialchars('Kontak saya uji.pegawai@contoh.go.id atau 081234567890 untuk sinkron. ' . $text) . '</p>');
$contact_text = implode(' ', $contact['sentences'] ?? []);
$checks['E15 teks tersamar (tanpa email/HP)'] = str_contains($contact_text, 'disamarkan')
    && !str_contains($contact_text, '@contoh.go.id') && !str_contains($contact_text, '081234567890');
$checks['E15 deskripsi pendek → tanpa ringkasan'] = Summary::forTicketContent('<p>Printer lantai 2 macet, mohon dicek.</p>') === null;
$checks['E15 deterministik'] = Summary::forTicketContent('<p>' . htmlspecialchars($text) . '</p>') === $long;

// UC-04 — pemecah seri beban kerja
$c = [
    ['team' => 'Tim A', 'confidence' => 46, 'groups_id' => 1],
    ['team' => 'Tim B', 'confidence' => 43, 'groups_id' => 2],
    ['team' => 'Tim C', 'confidence' => 5, 'groups_id' => 3],
];
$checks['UC-04 selisih 3 poin, kandidat 2 lebih ringan → dipilih + alasan'] = str_contains((string) Triage::workloadTiebreak($c, [9, 2, 0]), 'Tim B');
$checks['UC-04 kandidat 2 tidak lebih ringan → urutan model'] = Triage::workloadTiebreak($c, [2, 2, 0]) === null;
$c[1]['confidence'] = 41;
$checks['UC-04 selisih 5 poin → urutan model'] = Triage::workloadTiebreak($c, [9, 2, 0]) === null;
$c[1]['confidence'] = 43;
$c[1]['groups_id'] = 0;
$checks['UC-04 kandidat 2 tanpa grup → urutan model'] = Triage::workloadTiebreak($c, [9, 0, 0]) === null;

// UC-10 — status SLA (mulai 08.00, batas 18.00 = 10 jam; berisiko bila sisa ≤ 2 jam)
$checks['UC-10 aman'] = ConfigAudit::slaState('2026-11-02 08:00:00', '2026-11-02 18:00:00', '2026-11-02 12:00:00') === 'ok';
$checks['UC-10 berisiko'] = ConfigAudit::slaState('2026-11-02 08:00:00', '2026-11-02 18:00:00', '2026-11-02 16:30:00') === 'risk';
$checks['UC-10 terlewati'] = ConfigAudit::slaState('2026-11-02 08:00:00', '2026-11-02 18:00:00', '2026-11-02 18:01:00') === 'overdue';

$failed = 0;
foreach ($checks as $name => $ok) {
    echo ($ok ? 'LULUS ' : 'GAGAL ') . $name . PHP_EOL;
    $failed += $ok ? 0 : 1;
}
exit($failed > 0 ? 1 : 0);
