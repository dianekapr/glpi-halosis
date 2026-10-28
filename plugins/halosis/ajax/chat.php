<?php

/**
 * Endpoint widget chatbot self-service (public/js/chat.js).
 *   GET  action=widget            → HTML widget (kosong jika chatbot tidak tersedia untuk pengguna)
 *   GET  action=history&chat_id   → riwayat percakapan milik pengguna
 *   GET  action=latest[&skip]     → id percakapan terbuka terakhir yang masih aktif (0 = tidak ada)
 *   POST action=message|resolve|ticket
 * Memakai `return` (bukan exit) supaya kernel GLPI tetap menutup request dengan normal.
 */

use Glpi\Application\View\TemplateRenderer;
use GlpiPlugin\Halosis\Chat;
use GlpiPlugin\Halosis\Chatbot;

global $CFG_GLPI;

$action = (string) ($_REQUEST['action'] ?? '');

if ($action === 'widget') {
    header('Content-Type: text/html; charset=UTF-8');
    if (Chatbot::isAvailable()) {
        TemplateRenderer::getInstance()->display('@halosis/chat_widget.html.twig', [
            'ajax_url'    => $CFG_GLPI['root_doc'] . '/plugins/halosis/ajax/chat.php',
            'page_url'    => Chatbot::getPageUrl(),
            'report_url'  => \Glpi\Form\ServiceCatalog\ServiceCatalog::getSearchURL(),
            'max_length'  => Chatbot::MAX_MESSAGE_LENGTH,
            'user_name'   => $_SESSION['glpifirstname'] ?? '',
        ]);
    }
    return;
}

header('Content-Type: application/json; charset=UTF-8');
$respond = static function (int $status, array $data): void {
    http_response_code($status);
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
};

if (!Chatbot::isAvailable()) {
    $respond(403, ['ok' => false, 'message' => __('The chatbot is not available for your account.', 'halosis')]);
    return;
}

$chat_id = (int) ($_REQUEST['chat_id'] ?? 0);
$chat    = $chat_id > 0 ? Chat::getOwned($chat_id) : null;
if ($chat_id > 0 && $chat === null) {
    $respond(404, ['ok' => false, 'message' => __('Conversation not found.', 'halosis')]);
    return;
}

if ($action === 'latest') {
    // Percakapan terbuka terakhir untuk dilanjutkan (tab/login baru); skip = yang sengaja ditinggalkan
    $respond(200, ['ok' => true, 'chat_id' => Chat::getLatestOpen((int) ($_GET['skip'] ?? 0))?->getID() ?? 0]);
    return;
}

if ($action === 'history') {
    $respond(200, [
        'ok'       => true,
        'status'   => $chat?->fields['status'],
        'messages' => array_map(
            static fn ($m) => [
                'role'    => $m['role'],
                'text'    => $m['text'],
                'sources' => $m['sources'] ?? [],
                'found'   => (bool) ($m['found'] ?? false),
                'ai'      => Chatbot::isAiModel($m['model'] ?? null),
            ],
            $chat?->getMessages() ?? [],
        ),
    ]);
    return;
}

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    $respond(405, ['ok' => false, 'message' => 'POST required']);
    return;
}

switch ($action) {
    case 'message':
        $result = Chatbot::ask($chat, (string) ($_POST['text'] ?? ''));
        $respond($result['ok'] ? 200 : 422, $result);
        return;

    case 'resolve':
        if ($chat === null) {
            $respond(404, ['ok' => false, 'message' => __('Conversation not found.', 'halosis')]);
            return;
        }
        $error = Chatbot::resolve($chat, (int) ($_POST['rating'] ?? 0));
        $respond($error === null ? 200 : 422, $error === null
            ? ['ok' => true, 'message' => __('Thank you! Glad your problem is solved.', 'halosis')]
            : ['ok' => false, 'message' => $error]);
        return;

    case 'ticket':
        if ($chat === null) {
            $respond(404, ['ok' => false, 'message' => __('Conversation not found.', 'halosis')]);
            return;
        }
        $result = Chatbot::createTicket($chat, (string) ($_POST['title'] ?? ''));
        if ($result['ok']) {
            $result['message'] = sprintf(__('Report #%d has been created. An officer will follow it up.', 'halosis'), $result['ticket_id']);
        }
        $respond($result['ok'] ? 200 : 422, $result);
        return;

    default:
        $respond(400, ['ok' => false, 'message' => 'Unknown action']);
}
