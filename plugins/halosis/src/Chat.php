<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;
use Session;

/**
 * Satu percakapan chatbot self-service (tabel glpi_plugin_halosis_chats).
 * Hanya pemiliknya (pegawai yang memulai) yang boleh membaca atau melanjutkannya.
 */
final class Chat extends CommonDBTM
{
    public const STATUS_OPEN     = 'open';
    public const STATUS_RESOLVED = 'resolved';
    public const STATUS_TICKET   = 'ticket';

    /** Batas pesan pengguna per percakapan, mencegah transkrip tumbuh tanpa batas */
    public const MAX_USER_MESSAGES = 20;

    /** Percakapan terbuka yang diubah dalam sekian jam terakhir dilanjutkan otomatis */
    public const RESUME_HOURS = 2;

    /** Jumlah percakapan di halaman Riwayat chat */
    public const HISTORY_LIMIT = 50;

    public static string $rightname = Profile::RIGHT_CHATBOT;

    public bool $dohistory = false;

    public static function getTypeName($nb = 0)
    {
        return _n('Chat', 'Chats', $nb, 'halosis');
    }

    /**
     * Muat percakapan milik pengguna yang sedang login.
     */
    public static function getOwned(int $id): ?self
    {
        $chat = new self();
        if ($id <= 0 || !$chat->getFromDB($id) || (int) $chat->fields['users_id'] !== Session::getLoginUserID()) {
            return null;
        }
        return $chat;
    }

    /**
     * @return array<int, array<string, mixed>>
     */
    public function getMessages(): array
    {
        $messages = json_decode((string) ($this->fields['transcript'] ?? ''), true);
        return is_array($messages) ? $messages : [];
    }

    public function isOpen(): bool
    {
        return $this->fields['status'] === self::STATUS_OPEN;
    }

    public function countUserMessages(): int
    {
        return count(array_filter($this->getMessages(), static fn ($m) => ($m['role'] ?? '') === 'user'));
    }

    /**
     * Percakapan terbuka terakhir milik pengguna yang masih aktif (dilanjutkan otomatis di tab/login baru).
     *
     * @param int $skip_id Percakapan yang sengaja ditinggalkan pengguna ("Percakapan baru")
     */
    public static function getLatestOpen(int $skip_id = 0): ?self
    {
        global $DB;

        $since = date('Y-m-d H:i:s', strtotime($_SESSION['glpi_currenttime'] ?? 'now') - self::RESUME_HOURS * 3600);
        $row = $DB->request([
            'SELECT' => 'id',
            'FROM'   => self::getTable(),
            'WHERE'  => ['users_id' => Session::getLoginUserID(), 'status' => self::STATUS_OPEN, 'date_mod' => ['>=', $since]],
            'ORDER'  => ['date_mod DESC', 'id DESC'],
            'LIMIT'  => 1,
        ])->current();
        // Hanya percakapan terakhir yang dilanjutkan; jika itu yang ditinggalkan, jangan mundur ke yang lebih lama
        if (!$row || (int) $row['id'] === $skip_id) {
            return null;
        }
        return self::getOwned((int) $row['id']);
    }

    /**
     * Riwayat percakapan pengguna yang sedang login, terbaru dulu (hanya yang berisi pertanyaan).
     *
     * @return array<int, array{id: int, date: string, question: string, questions: int, status: string, rating: ?int, tickets_id: int}>
     */
    public static function getHistory(int $limit = self::HISTORY_LIMIT): array
    {
        global $DB;

        $rows = [];
        foreach ($DB->request([
            'FROM'  => self::getTable(),
            'WHERE' => ['users_id' => Session::getLoginUserID(), 'message_count' => ['>', 0]],
            'ORDER' => ['date_mod DESC', 'id DESC'],
            'LIMIT' => $limit,
        ]) as $fields) {
            $chat = new self();
            $chat->fields = $fields;
            $questions = array_values(array_filter($chat->getMessages(), static fn ($m) => ($m['role'] ?? '') === 'user'));
            $rows[] = [
                'id'         => (int) $fields['id'],
                'date'       => (string) ($fields['date_mod'] ?: $fields['date_creation']),
                'question'   => mb_strimwidth((string) ($questions[0]['text'] ?? ''), 0, 140, '…'),
                'questions'  => count($questions),
                'status'     => (string) $fields['status'],
                'rating'     => $fields['rating'] !== null ? (int) $fields['rating'] : null,
                'tickets_id' => (int) $fields['tickets_id'],
            ];
        }
        return $rows;
    }
}
