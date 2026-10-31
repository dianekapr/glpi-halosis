<?php

/**
 * Tutup tiket dari daftar "Siap ditutup" (T21), per tiket atau massal. Dipanggil public/js/closure.js; balasan JSON.
 */

use GlpiPlugin\Halosis\Closure;

header('Content-Type: application/json; charset=UTF-8');

$respond = static function (int $status, array $data): void {
    http_response_code($status);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
};

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    $respond(405, ['ok' => false, 'message' => 'POST required']);
    return;
}
if (!Closure::canClose()) {
    $respond(403, ['ok' => false, 'message' => __('You are not allowed to close tickets.', 'halosis')]);
    return;
}
$result = Closure::close((array) ($_POST['ids'] ?? []));
Session::addMessageAfterRedirect(htmlescape(sprintf(__('%1$d ticket(s) closed, %2$d skipped.', 'halosis'), $result['closed'], $result['skipped'])));
$respond(200, ['ok' => true] + $result);
