<?php

/**
 * Aksi panel "Saran AI": buat saran, Terima, Ubah, Tolak, dan Kembalikan ke operator (Tim Teknis, UC-06).
 * Dipanggil lewat fetch() dari public/js/triase.js; selalu membalas JSON.
 * Memakai `return` (bukan exit) supaya kernel GLPI tetap menutup request dengan normal.
 */

use GlpiPlugin\Halosis\Decision;
use GlpiPlugin\Halosis\Profile;
use GlpiPlugin\Halosis\Reassignment;
use GlpiPlugin\Halosis\Suggestion;
use GlpiPlugin\Halosis\Triage;

header('Content-Type: application/json; charset=UTF-8');

$respond = static function (int $status, ?string $error = null): void {
    http_response_code($status);
    echo json_encode($error === null ? ['ok' => true] : ['ok' => false, 'message' => $error]);
};

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    $respond(405, 'POST required');
    return;
}

$action = (string) ($_POST['action'] ?? '');

// Tim Teknis hanya berhak membaca triase; hak mengembalikan diperiksa per tiket (tim yang ditugaskan)
if ($action === 'return') {
    $ticket = new Ticket();
    if (!Session::haveRight(Profile::RIGHT_TRIASE, READ) || !$ticket->getFromDB((int) ($_POST['ticket_id'] ?? 0))) {
        $respond(403, __('You are not allowed to update this ticket.', 'halosis'));
        return;
    }
    $error = Reassignment::returnToOperator($ticket, (string) ($_POST['reason'] ?? ''));
    if ($error !== null) {
        $respond(422, $error);
        return;
    }
    Session::addMessageAfterRedirect(__s('Ticket returned to the operator validation queue.', 'halosis'));
    $respond(200);
    return;
}

if (!Session::haveRight(Profile::RIGHT_TRIASE, UPDATE)) {
    $respond(403, __('You are not allowed to decide on AI suggestions.', 'halosis'));
    return;
}

if ($action === 'generate') {
    $ticket = new Ticket();
    if (!$ticket->getFromDB((int) ($_POST['ticket_id'] ?? 0)) || !$ticket->canUpdateItem()) {
        $respond(403, __('You are not allowed to update this ticket.', 'halosis'));
        return;
    }
    if (Triage::generate($ticket, true) === null) {
        $respond(502, __('The AI could not produce a suggestion. The ticket is unchanged; check files/_log/halosis.log.', 'halosis'));
        return;
    }
    Session::addMessageAfterRedirect(__s('AI suggestion created.', 'halosis'));
    $respond(200);
    return;
}

$suggestion = new Suggestion();
if (!$suggestion->getFromDB((int) ($_POST['suggestion_id'] ?? 0))) {
    $respond(404, __('Suggestion not found.', 'halosis'));
    return;
}

$error = Triage::decide($suggestion, $action, $_POST);
if ($error !== null) {
    $respond(422, $error);
    return;
}

Session::addMessageAfterRedirect(match ($action) {
    Decision::ACTION_ACCEPT => __s('AI suggestion accepted and applied to the ticket.', 'halosis'),
    Decision::ACTION_MODIFY => __s('Modified values applied to the ticket.', 'halosis'),
    default                 => __s('AI suggestion rejected. Please triage the ticket manually.', 'halosis'),
});
$respond(200);
