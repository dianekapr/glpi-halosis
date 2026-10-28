<?php

/**
 * Aksi halaman Kandidat Knowledge: Jadikan artikel (draf KB) / Abaikan (dengan alasan).
 * Dipanggil lewat fetch() dari public/js/kandidat.js; selalu membalas JSON.
 * Memakai `return` (bukan exit) supaya kernel GLPI tetap menutup request dengan normal.
 */

use GlpiPlugin\Halosis\Candidate;
use GlpiPlugin\Halosis\KnowledgeCandidates;
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
if (!Session::haveRight(Profile::RIGHT_KANDIDAT, UPDATE)) {
    $respond(403, ['ok' => false, 'message' => __('You are not allowed to decide on knowledge candidates.', 'halosis')]);
    return;
}

$candidate = new Candidate();
if (!$candidate->getFromDB((int) ($_POST['id'] ?? 0))) {
    $respond(404, ['ok' => false, 'message' => __('Candidate not found.', 'halosis')]);
    return;
}

$result = match ((string) ($_POST['action'] ?? '')) {
    'article' => KnowledgeCandidates::makeArticle($candidate),
    'ignore'  => KnowledgeCandidates::ignore($candidate, (string) ($_POST['reason'] ?? '')),
    default   => ['ok' => false, 'message' => 'Unknown action'],
};
if ($result['ok']) {
    Session::addMessageAfterRedirect(isset($result['url'])
        ? __s('Draft article created. Review it, then publish it to make it visible.', 'halosis')
        : __s('Candidate dismissed.', 'halosis'));
}
$respond($result['ok'] ? 200 : 422, $result);
