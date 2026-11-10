<?php
/**
 * ALAT DEMO (bukan bagian layanan AI): langkah sisi-plugin untuk scripts/seed_demo.py.
 * Jalankan lewat:  docker compose exec -T glpi php /var/www/glpi/plugins/halosis/tools/seed_demo_plugin.php <langkah> [arg]
 * Langkah: survei | keputusan | pola | chat <n_total> <n_rating> | mundurkan | hapus
 * Semua operasi dibatasi ketat pada data bertanda "[DEMO]" (tiket bernama "[DEMO]%", chat dengan pesan pertama
 * "[DEMO]…", pola/Problem berlabel "[DEMO]…"). Tidak menyentuh data latih atau indeks AI.
 */
use GlpiPlugin\Halosis\{Triage, Suggestion, PatternDetector, Chat};

require '/var/www/glpi/vendor/autoload.php';
(new Glpi\Kernel\Kernel('production'))->boot();
global $DB;
mt_srand(42);

const TAG = '[DEMO]';
const CHAT_PREFIX = '[{"role":"user","text":"[DEMO]';

function masuk(string $login): void
{
    $u = new User();
    if (!$u->getFromDBbyName($login)) {
        fwrite(STDERR, "akun {$login} tidak ada\n"); exit(1);
    }
    $auth = new Auth(); $auth->auth_succeded = true; $auth->user = $u;
    Session::init($auth, true);
}
function demoTickets(): array
{
    global $DB;
    $r = [];
    foreach ($DB->request(['FROM' => 'glpi_tickets', 'WHERE' => ['name' => ['LIKE', TAG . '%'], 'is_deleted' => 0]]) as $t) {
        $r[(int) $t['id']] = $t;
    }
    return $r;
}
function demoChats(): array
{
    global $DB;
    $r = [];
    foreach ($DB->request(['FROM' => 'glpi_plugin_halosis_chats', 'WHERE' => ['transcript' => ['LIKE', CHAT_PREFIX . '%']], 'ORDER' => 'id']) as $c) {
        $r[(int) $c['id']] = $c;
    }
    return $r;
}
function demoPatterns(): array
{
    global $DB;
    return iterator_to_array($DB->request(['FROM' => 'glpi_plugin_halosis_patterns', 'WHERE' => ['label' => ['LIKE', '%' . TAG . '%']]]), false);
}
$fmt = fn (int $ts) => date('Y-m-d H:i:s', $ts);

switch ($argv[1] ?? '') {
    case 'keputusan':
        masuk('rina');
        $w = ['accept' => 70, 'modify' => 15, 'reject' => 15];
        $n = ['accept' => 0, 'modify' => 0, 'reject' => 0, 'gagal' => 0];
        $ids = array_keys(demoTickets());
        foreach ($DB->request(['FROM' => Suggestion::getTable(), 'WHERE' => ['tickets_id' => $ids ?: [-1], 'status' => 'pending'], 'ORDER' => 'id']) as $row) {
            $s = new Suggestion();
            $s->getFromDB($row['id']);
            $r = mt_rand(1, 100);
            // Tiket L1 (hanya ditugaskan ke grup Operator) tidak boleh ditambah grup tim oleh saran: saran ditolak
            $grup = array_map('intval', array_column(iterator_to_array($DB->request(['SELECT' => 'groups_id', 'FROM' => 'glpi_groups_tickets', 'WHERE' => ['tickets_id' => $row['tickets_id'], 'type' => 2]]), false), 'groups_id'));
            $l1 = $grup !== [] && array_diff($grup, [PatternDetector::getOperatorGroupId()]) === [];
            if ($l1) { $r = 100; }
            $aksi = $r <= $w['accept'] ? 'accept' : ($r <= $w['accept'] + $w['modify'] ? 'modify' : 'reject');
            $input = ['reason' => TAG . ' alasan koreksi untuk data demo'];
            if ($aksi === 'modify') {
                $ticket = new Ticket(); $ticket->getFromDB((int) $row['tickets_id']);
                $groups = array_keys(Triage::getContext($ticket)['groups']);
                $other = array_values(array_diff($groups, [(int) $row['groups_id']]));
                $input += $s->getValues();
                $input['groups_id'] = $other ? $other[array_rand($other)] : (int) $row['groups_id'];
                $input['urgency'] = max(1, min(5, (int) $row['urgency'] + (mt_rand(0, 1) ? 1 : -1)));
                $input['priority'] = Ticket::computePriority($input['urgency'], (int) $input['impact']);
            }
            $err = Triage::decide($s, $aksi, $input);
            $err === null ? $n[$aksi]++ : $n['gagal']++;
        }
        echo 'keputusan: ' . json_encode($n) . "\n";
        break;

    case 'survei':
        // Kelas TicketSatisfaction hanya mengizinkan pemohon & tidak bisa dimuat lewat CLI; survei diisi lewat DB layer GLPI,
        // terbatas pada baris milik tiket [DEMO] berstatus Ditutup (baris survei dibuat GLPI saat tiket ditutup).
        $maks = (int) ($argv[2] ?? 33); $isi = 0;
        foreach (demoTickets() as $id => $t) {
            if ((int) $t['status'] !== 6 || $isi >= $maks) { continue; }
            $nilai = [3, 4, 4, 5, 5, 2][mt_rand(0, 5)];
            $DB->update('glpi_ticketsatisfactions', ['satisfaction' => $nilai, 'comment' => TAG, 'date_answered' => date('Y-m-d H:i:s')], ['tickets_id' => $id]);
            $isi++;
        }
        echo "survei terisi: {$isi}\n";
        break;

    case 'pola':
        masuk('dimas');
        $hasil = PatternDetector::detect();
        echo 'pola terdeteksi/diperbarui: ' . count($hasil) . ' | berlabel [DEMO]: ' . count(demoPatterns()) . "\n";
        break;

    case 'geser_pola':
        // pola historis: tiket "Presensi online error 500" ([DEMO]) dipindah 6 minggu ke belakang (rentang 40 menit)
        $i = 0; $base = time() - 6 * 7 * 86400;
        foreach (demoTickets() as $id => $t) {
            if (str_contains($t['name'], 'Presensi online error 500')) {
                $DB->update('glpi_tickets', ['date' => $fmt($base + 300 * $i++)], ['id' => $id, 'name' => ['LIKE', TAG . '%']]);
            }
        }
        echo "tiket pola digeser: {$i}\n";
        break;

    case 'chat':
        masuk('budi');
        [$total, $rated] = [(int) ($argv[2] ?? 40), (int) ($argv[3] ?? 18)];
        $kb = array_column(iterator_to_array($DB->request(['SELECT' => ['id', 'name'], 'FROM' => 'glpi_knowbaseitems', 'WHERE' => ['is_faq' => 1], 'LIMIT' => 6]), false), 'name', 'id');
        $kbIds = array_keys($kb);
        $tikets = array_keys(demoTickets());
        $pertanyaan = ['Wi-Fi tidak bisa tersambung', 'Cara reset kata sandi', 'Printer tidak mencetak', 'VPN gagal masuk', 'Email tidak terkirim', 'Aplikasi lambat dibuka'];
        // komposisi: ber-rating (resolved), jadi tiket, ditolak (resolved tanpa rating), kedaluwarsa
        $jenis = array_merge(array_fill(0, $rated, 'rating'), array_fill(0, 8, 'ticket'), array_fill(0, 8, 'tolak'),
            array_fill(0, max(0, $total - $rated - 16), 'expired'));
        $dibuat = 0;
        foreach ($jenis as $i => $j) {
            $kb_id = $kbIds[$i % count($kbIds)];
            $q = TAG . ' ' . $pertanyaan[$i % count($pertanyaan)];
            $now = date('Y-m-d H:i:s');
            $msgs = [
                ['role' => 'user', 'text' => $q, 'at' => $now],
                ['role' => 'assistant', 'text' => 'Jawaban demo dari artikel panduan.', 'found' => true,
                    'sources' => [['id' => $kb_id, 'title' => $kb[$kb_id], 'type' => 'kb']], 'model' => 'demo', 'out_of_scope' => false, 'at' => $now],
            ];
            $rating = $j === 'rating' ? [5, 5, 4, 4, 3, 2, 1][mt_rand(0, 6)] : null;
            $chat = new Chat();
            $id = $chat->add([
                'users_id' => Session::getLoginUserID(), 'tickets_id' => $j === 'ticket' ? $tikets[array_rand($tikets)] : 0,
                'status' => $j === 'ticket' ? 'ticket' : ($j === 'expired' ? 'expired' : 'resolved'),
                'rating' => $rating, 'message_count' => 2, 'answered_count' => 1,
                'transcript' => json_encode($msgs, JSON_UNESCAPED_UNICODE),
            ]);
            if ($id && ($j === 'ticket' || $rating !== null && $rating <= 2 || $i % 2 === 0)) {
                $DB->insert('glpi_plugin_halosis_article_uses', ['knowbaseitems_id' => $kb_id, 'chats_id' => $id, 'date_creation' => $now]);
            }
            $dibuat += (int) (bool) $id;
        }
        echo "chat dibuat: {$dibuat}\n";
        break;

    case 'mundurkan':
        // SATU-SATUNYA langkah yang mengubah tanggal. WHERE ketat: id tiket/chat/pola [DEMO] saja.
        $tk = demoTickets();
        $ids = array_keys($tk);
        if (!$ids) { echo "tidak ada tiket [DEMO]\n"; break; }
        $now = time();
        $ke = 0;
        foreach ($tk as $id => $t) {
            $d = strtotime($tk[$id]['date']);
            $set = ['date_creation' => $fmt($d), 'date_mod' => $fmt($d + 3600)];
            if ($t['takeintoaccountdate']) { $set['takeintoaccountdate'] = $fmt($d + mt_rand(5, 240) * 60); }
            if ((int) $t['status'] >= 5) {
                $solve = $d + mt_rand(2, 80) * 3600;
                $set['solvedate'] = $fmt($solve); $set['date_mod'] = $fmt($solve);
                if ((int) $t['status'] === 6) { $set['closedate'] = $fmt($solve + 86400); $set['date_mod'] = $fmt($solve + 86400); }
                $DB->update('glpi_itilfollowups', ['date' => $fmt($d + 3600), 'date_creation' => $fmt($d + 3600), 'date_mod' => $fmt($d + 3600)], ['itemtype' => 'Ticket', 'items_id' => $id]);
                $DB->update('glpi_itilsolutions', ['date_creation' => $fmt($solve), 'date_mod' => $fmt($solve), 'date_approval' => null], ['itemtype' => 'Ticket', 'items_id' => $id]);
                $DB->update('glpi_ticketsatisfactions', ['date_begin' => $fmt($solve + 86400), 'date_answered' => $DB->request(['SELECT' => 'satisfaction', 'FROM' => 'glpi_ticketsatisfactions', 'WHERE' => ['tickets_id' => $id, 'NOT' => ['satisfaction' => null]]])->count() ? $fmt($solve + 86400 + mt_rand(1, 40) * 3600) : null], ['tickets_id' => $id]);
            }
            $DB->update('glpi_tickets', $set, ['id' => $id, 'name' => ['LIKE', TAG . '%']]);
            // saran, keputusan, penugasan ulang mengikuti tanggal tiketnya
            $DB->update('glpi_plugin_halosis_suggestions', ['date_creation' => $fmt($d + 60), 'date_mod' => $fmt($d + 60)], ['tickets_id' => $id]);
            $DB->update('glpi_plugin_halosis_decisions', ['date_creation' => $fmt($d + mt_rand(10, 180) * 60)], ['tickets_id' => $id]);
            $DB->update('glpi_plugin_halosis_reassignments', ['date_creation' => $fmt($d + 3600)], ['tickets_id' => $id]);
            $ke++;
        }
        // chat: sebar rata 12 minggu ke belakang (urutan id)
        $chats = demoChats(); $i = 0; $n = max(1, count($chats));
        foreach ($chats as $cid => $c) {
            $t = $now - (int) ((($n - $i) / $n) * 12 * 7 * 86400) + mt_rand(0, 40000);
            $DB->update('glpi_plugin_halosis_chats', ['date_creation' => $fmt($t), 'date_mod' => $fmt($t + 600)], ['id' => $cid, 'transcript' => ['LIKE', CHAT_PREFIX . '%']]);
            $DB->update('glpi_plugin_halosis_article_uses', ['date_creation' => $fmt($t)], ['chats_id' => $cid]);
            $i++;
        }
        // pola berlabel [DEMO]: tanggal Problem & pola mengikuti tiket anggota pertamanya
        foreach (demoPatterns() as $p) {
            $first = null;
            foreach ($DB->request(['SELECT' => 'tickets_id', 'FROM' => 'glpi_problems_tickets', 'WHERE' => ['problems_id' => $p['problems_id']]]) as $pt) {
                if (isset($tk[(int) $pt['tickets_id']])) { $first = min($first ?? PHP_INT_MAX, strtotime($tk[(int) $pt['tickets_id']]['date'])); }
            }
            if ($first !== null) {
                $DB->update('glpi_plugin_halosis_patterns', ['date_creation' => $fmt($first + 1800), 'date_mod' => $fmt($first + 1800)], ['id' => $p['id'], 'label' => ['LIKE', '%' . TAG . '%']]);
                $DB->update('glpi_problems', ['date' => $fmt($first + 1800), 'date_creation' => $fmt($first + 1800), 'date_mod' => $fmt($first + 1800)], ['id' => $p['problems_id']]);
            }
        }
        echo "tanggal dimundurkan: {$ke} tiket, " . count($chats) . ' chat, ' . count(demoPatterns()) . " pola\n";
        break;

    case 'hapus':
        masuk('dimas');
        $ids = array_keys(demoTickets());
        $ids && array_map(fn ($t) => $DB->delete($t, ['tickets_id' => $ids]), ['glpi_plugin_halosis_decisions', 'glpi_plugin_halosis_suggestions', 'glpi_plugin_halosis_reassignments']);
        foreach (demoChats() as $cid => $_) {
            $DB->delete('glpi_plugin_halosis_article_uses', ['chats_id' => $cid]);
            $DB->delete('glpi_plugin_halosis_chats', ['id' => $cid, 'transcript' => ['LIKE', CHAT_PREFIX . '%']]);
        }
        $p = 0;
        foreach (demoPatterns() as $row) {
            $DB->delete('glpi_plugin_halosis_patterns', ['id' => $row['id']]);
            (new Problem())->delete(['id' => (int) $row['problems_id']], true); $p++;
        }
        echo 'baris plugin [DEMO] dihapus; pola/Problem: ' . $p . "\n";
        break;

    default:
        fwrite(STDERR, "langkah: keputusan | pola | chat | mundurkan | hapus\n"); exit(1);
}
