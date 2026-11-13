<?php

/**
 * UC-07: teks "Ditangani oleh" untuk satu tiket milik pengguna (GET id). Dipanggil public/js/ditangani.js.
 * Hanya nama grup, bukan nama orang. Memakai `return` supaya kernel GLPI menutup request dengan normal.
 */

use GlpiPlugin\Halosis\HandledBy;

header('Content-Type: application/json; charset=UTF-8');

$text = Session::getLoginUserID() ? HandledBy::textFor((int) ($_GET['id'] ?? 0)) : null;
echo json_encode(['label' => __('Handled by', 'halosis'), 'text' => $text], JSON_UNESCAPED_UNICODE);
