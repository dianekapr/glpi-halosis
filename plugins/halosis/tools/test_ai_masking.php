<?php

/**
 * Tes: teks yang dikirim ke penyedia AI eksternal (Claude/OpenAI) sudah disamarkan (NFR-06, batas scope hal. 8).
 * Memeriksa ketiga lapisan: Triage::aiPrompt (saran triase), Chatbot::aiPrompt (perangkum chat), dan
 * Client::outgoingPrompt (jaring pengaman sebelum dikirim). Data rekaan; tidak memanggil API mana pun.
 *
 * Pakai (container GLPI): php plugins/halosis/tools/test_ai_masking.php   → keluar 0 bila lulus
 */

$src = dirname(__DIR__) . '/src';
require_once $src . '/Privacy.php';
require_once $src . '/Triage.php';
require_once $src . '/Chatbot.php';
require_once $src . '/Ai/Client.php';

use GlpiPlugin\Halosis\Ai\Client;
use GlpiPlugin\Halosis\Chatbot;
use GlpiPlugin\Halosis\Triage;

// Nilai rahasia rekaan yang TIDAK boleh muncul di payload
$secrets = ['uji.pegawai@contoh.go.id', '081234567890', '199001012020121001', 'Rahasia123'];
$raw     = 'Email uji.pegawai@contoh.go.id, HP 081234567890, NIP 199001012020121001, password: Rahasia123';

$payloads = [
    'Triage::aiPrompt'     => Triage::aiPrompt('Insiden', 'Akun terkunci ' . $raw, '<p>' . $raw . '</p>'),
    'Chatbot::aiPrompt'    => Chatbot::aiPrompt($raw, [['role' => 'user', 'text' => $raw], ['role' => 'assistant', 'text' => 'ok']],
        [['id' => 1, 'name' => 'Artikel ' . $raw, 'text' => $raw]]),
    'Client::outgoingPrompt' => Client::outgoingPrompt($raw),
];

$failed = 0;
foreach ($payloads as $name => $payload) {
    $leaks = array_filter($secrets, static fn ($s) => str_contains($payload, $s));
    $ok    = $leaks === [] && str_contains($payload, 'disamarkan');
    printf("%s %s%s\n", $ok ? 'LULUS' : 'GAGAL', $name, $leaks ? ' (bocor ' . count($leaks) . ' nilai)' : '');
    $failed += $ok ? 0 : 1;
}
exit($failed > 0 ? 1 : 0);
