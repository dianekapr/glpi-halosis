<?php

/**
 * Umpan balik agent di Cari knowledge (KR-07): satu hasil ditandai membantu / tidak membantu.
 * Dipanggil lewat fetch() dari public/js/feedback.js; selalu membalas JSON. Teks kueri tidak dikirim/disimpan.
 */

use GlpiPlugin\Halosis\Profile;

header('Content-Type: application/json; charset=UTF-8');

$respond = static function (int $status, array $data): void {
    http_response_code($status);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
};

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    $respond(405, ['ok' => false, 'message' => 'POST required']);
    return;
}
if (!Session::haveRight(Profile::RIGHT_TRIASE, READ)) {
    $respond(403, ['ok' => false, 'message' => __('You are not allowed to search knowledge.', 'halosis')]);
    return;
}

$ref = mb_substr(trim((string) ($_POST['ref'] ?? '')), 0, 100);
if (preg_match('/^[A-Za-z0-9._-]{1,100}$/', $ref) !== 1) {
    $respond(422, ['ok' => false, 'message' => 'Invalid source']);
    return;
}
$kb_id = preg_match('/^KB-(\d+)$/', $ref, $m) ? (int) $m[1] : 0;
$score = is_numeric($_POST['score'] ?? null) ? max(0.0, min(1.0, (float) $_POST['score'])) : null;

global $DB;
$DB->insert('glpi_plugin_halosis_feedback', [
    'users_id'         => Session::getLoginUserID(),
    'source_kind'      => $kb_id > 0 ? 'kb' : 'tiket',
    'source_ref'       => $ref,
    'knowbaseitems_id' => $kb_id,
    'score'            => $score,
    'is_helpful'       => (int) !empty($_POST['helpful']),
    'date_creation'    => $_SESSION['glpi_currenttime'] ?? date('Y-m-d H:i:s'),
]);
$respond(200, ['ok' => true]);
