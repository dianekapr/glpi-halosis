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
}
