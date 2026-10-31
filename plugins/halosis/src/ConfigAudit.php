<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;
use Glpi\Event;
use Glpi\Form\Form;
use ITILCategory;
use Profile_Reminder;
use Reminder;
use Session;
use Toolbox;

/**
 * T20 / UC-10: jejak & pemberitahuan perubahan konfigurasi.
 *
 * - Setiap perubahan Pengaturan AI HaloSIS, aturan bisnis tiket (termasuk aturan SLA), SLA, dan kategori layanan
 *   dicatat di log sistem GLPI (Administrasi › Log; sebelum → sesudah, aktor, waktu).
 * - Administrator diberi tahu lewat Catatan (Reminder) publik untuk profil Administrator, tampil di beranda 7 hari.
 * Pratinjau dampak ambang keyakinan: previewThresholds().
 */
final class ConfigAudit
{
    /** Field yang tidak dicatat nilainya (rahasia) atau tidak bermakna */
    private const HIDDEN = [Config::API_KEY, 'date_mod', 'date_creation'];

    /** Hari tampil Catatan pemberitahuan di beranda */
    private const NOTICE_DAYS = 7;

    /**
     * Hook item_add / item_update / item_purge untuk aturan tiket, SLA, kategori layanan, dan form katalog.
     * Kategori & form juga menyinkronkan katalog layanan ke indeks AI (BR-03).
     */
    public static function onItemAdd(CommonDBTM $item): void
    {
        self::onItemChange($item, __('created', 'halosis'));
    }

    public static function onItemUpdate(CommonDBTM $item): void
    {
        self::onItemChange($item, __('updated', 'halosis'));
    }

    public static function onItemPurge(CommonDBTM $item): void
    {
        self::onItemChange($item, __('deleted', 'halosis'));
    }

    private static function onItemChange(CommonDBTM $item, string $action): void
    {
        if ($item instanceof ITILCategory || $item instanceof Form) {
            KnowledgeIndex::onCatalogChange($item);
        }
        if ($item instanceof Form) {
            return;
        }
        $changes = [];
        foreach ($item->updates ?? [] as $field) {
            if (!in_array($field, self::HIDDEN, true)) {
                $changes[$field] = [$item->oldvalues[$field] ?? null, $item->fields[$field] ?? null];
            }
        }
        if ($action === __('updated', 'halosis') && $changes === []) {
            return;
        }
        self::record(sprintf('%s "%s" (#%d) %s', $item::getTypeName(1), $item->fields['name'] ?? '', $item->getID(), $action), $changes);
    }

    /**
     * Pengaturan AI HaloSIS disimpan: catat field yang berubah (API key hanya "diubah", tanpa nilai).
     *
     * @param array<string, mixed> $before
     * @param array<string, mixed> $after
     */
    public static function onConfigSaved(array $before, array $after): void
    {
        $changes = [];
        foreach ($after as $field => $value) {
            if ((string) ($before[$field] ?? '') === (string) $value) {
                continue;
            }
            $changes[$field] = $field === Config::API_KEY ? ['***', '***'] : [$before[$field] ?? null, $value];
        }
        if ($changes !== []) {
            self::record(__('HaloSIS AI settings updated', 'halosis'), $changes);
        }
    }

    /**
     * @param array<string, array{0: mixed, 1: mixed}> $changes
     */
    private static function record(string $title, array $changes): void
    {
        $lines = array_map(
            static fn ($field, $pair) => sprintf('%s: %s → %s', $field, self::short($pair[0]), self::short($pair[1])),
            array_keys($changes),
            $changes,
        );
        $actor = Session::getLoginUserID() ? getUserName(Session::getLoginUserID()) : 'cron/CLI';
        $text  = $title . ($lines !== [] ? ' — ' . implode('; ', $lines) : '') . ' — ' . $actor;
        Event::log(0, 'system', 4, 'setup', mb_substr($text, 0, 1000));
        Toolbox::logInFile('halosis', "Konfigurasi: {$text}\n", true);

        $now = $_SESSION['glpi_currenttime'] ?? date('Y-m-d H:i:s');
        $reminder = new Reminder();
        $id = $reminder->add([
            'name'            => mb_substr('HaloSIS: ' . $title, 0, 255),
            'text'            => '<p>' . htmlescape($title) . '</p><ul>' . implode('', array_map(
                static fn ($l) => '<li>' . htmlescape($l) . '</li>',
                $lines,
            )) . '</ul><p>' . htmlescape(sprintf(__('By %1$s at %2$s', 'halosis'), $actor, $now)) . '</p>',
            'begin_view_date' => $now,
            'end_view_date'   => date('Y-m-d H:i:s', strtotime($now . ' +' . self::NOTICE_DAYS . ' days')),
            'users_id'        => Session::getLoginUserID() ?: 0,
        ]);
        if ($id) {
            (new Profile_Reminder())->add([
                'reminders_id' => $id,
                'profiles_id'  => Roles::ADMINISTRATOR,
                'entities_id'  => 0,
                'is_recursive' => 1,
            ]);
        }
    }

    private static function short(mixed $value): string
    {
        $text = is_scalar($value) || $value === null ? (string) $value : json_encode($value);
        return $text === '' ? '∅' : mb_strimwidth($text, 0, 60, '…');
    }

    /**
     * Pratinjau dampak ambang baru: saran 30 hari terakhir per tingkat (tinggi/sedang/rendah) dengan ambang sekarang
     * vs ambang baru, dan berapa yang berpindah tingkat.
     *
     * @return array{total: int, current: array<string, int>, new: array<string, int>, moved: int, moves: array<string, int>}
     */
    public static function previewThresholds(int $high, int $low): array
    {
        global $DB;

        $low = min($low, $high);
        $level = static fn (int $c, int $h, int $l) => $c >= $h ? 'high' : ($c >= $l ? 'medium' : 'low');
        $result = ['total' => 0, 'current' => ['high' => 0, 'medium' => 0, 'low' => 0], 'new' => ['high' => 0, 'medium' => 0, 'low' => 0], 'moved' => 0, 'moves' => []];
        $since = date('Y-m-d H:i:s', strtotime(($_SESSION['glpi_currenttime'] ?? 'now') . ' -30 days'));
        foreach ($DB->request(['SELECT' => 'confidence', 'FROM' => Suggestion::getTable(), 'WHERE' => ['date_creation' => ['>=', $since]]]) as $row) {
            $c = (int) $row['confidence'];
            $from = $level($c, Config::getTriageThreshold(), Config::getLowThreshold());
            $to   = $level($c, $high, $low);
            $result['total']++;
            $result['current'][$from]++;
            $result['new'][$to]++;
            if ($from !== $to) {
                $result['moved']++;
                $result['moves']["{$from}→{$to}"] = ($result['moves']["{$from}→{$to}"] ?? 0) + 1;
            }
        }
        return $result;
    }
}
