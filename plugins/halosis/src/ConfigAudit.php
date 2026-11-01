<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;
use CommonITILObject;
use Dropdown;
use Glpi\Event;
use Glpi\Form\Form;
use ITILCategory;
use Profile_Reminder;
use Reminder;
use RuleTicket;
use Session;
use SLA;
use SLM;
use Ticket;
use Toolbox;

/**
 * T20 / UC-10: jejak & pemberitahuan perubahan konfigurasi.
 *
 * - Setiap perubahan Pengaturan AI HaloSIS, aturan bisnis tiket (termasuk aturan SLA), SLA, dan kategori layanan
 *   dicatat di log sistem GLPI (Administrasi › Log; sebelum → sesudah, aktor, waktu).
 * - Administrator diberi tahu lewat Catatan (Reminder) publik untuk profil Administrator, tampil di beranda 7 hari.
 * Pratinjau dampak ambang keyakinan: previewThresholds(). Pratinjau dampak target SLA / aturan SLA pada tiket aktif:
 * previewSla(), previewSlaRule() (UC-10 langkah 5; tidak menyimpan apa pun).
 */
final class ConfigAudit
{
    /** Field yang tidak dicatat nilainya (rahasia) atau tidak bermakna */
    private const HIDDEN = [Config::API_KEY, 'date_mod', 'date_creation'];

    /** Hari tampil Catatan pemberitahuan di beranda */
    private const NOTICE_DAYS = 7;

    /** Status risiko SLA = sisa waktu ≤ 20% durasi target (sama dengan level eskalasi "Peringatan risiko SLA") */
    public const SLA_RISK_SHARE = 0.2;

    /** Satuan target SLA yang bisa dipratinjau */
    public const SLA_UNITS = ['minute', 'hour', 'day'];

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

    /**
     * Pilihan form pratinjau SLA: SLA dan aturan tiket yang menetapkan SLA.
     *
     * @return array{slas: array<int, string>, rules: array<int, string>}
     */
    public static function getSlaTargets(): array
    {
        global $DB;

        $slas = [];
        foreach ($DB->request(['SELECT' => ['id', 'name', 'type'], 'FROM' => SLA::getTable(), 'ORDER' => ['type', 'name']]) as $row) {
            $slas[(int) $row['id']] = sprintf('%s (%s)', $row['name'], (int) $row['type'] === SLM::TTO ? __('response', 'halosis') : __('resolution', 'halosis'));
        }
        $rules = [];
        foreach ($DB->request([
            'SELECT'     => ['r.id', 'r.name', 'a.value'],
            'FROM'       => 'glpi_rules AS r',
            'INNER JOIN' => ['glpi_ruleactions AS a' => ['ON' => ['a' => 'rules_id', 'r' => 'id']]],
            'WHERE'      => ['r.sub_type' => RuleTicket::class, 'r.is_active' => 1, 'a.field' => ['slas_id_ttr', 'slas_id_tto']],
            'ORDER'      => 'r.ranking',
        ]) as $row) {
            $rules[(int) $row['id']][] = $slas[(int) $row['value']] ?? '?';
        }
        $names = $DB->request(['SELECT' => ['id', 'name'], 'FROM' => 'glpi_rules', 'WHERE' => ['id' => array_keys($rules) ?: [0]]]);
        foreach ($names as $row) {
            $rules[(int) $row['id']] = sprintf('%s → %s', $row['name'], implode(', ', $rules[(int) $row['id']]));
        }
        return ['slas' => $slas, 'rules' => $rules];
    }

    /**
     * Pratinjau perubahan target satu SLA: tiket aktif yang memakai SLA itu dihitung ulang batas waktunya.
     */
    public static function previewSla(int $sla_id, int $number_time, string $definition_time): ?array
    {
        $sla = new SLA();
        if (!$sla->getFromDB($sla_id) || $number_time <= 0 || !in_array($definition_time, self::SLA_UNITS, true)) {
            return null;
        }
        $type  = (int) $sla->fields['type'] === SLM::TTO ? 'tto' : 'ttr';
        $label = sprintf(
            __('SLA "%1$s": %2$s → %3$d %4$s', 'halosis'),
            $sla->fields['name'],
            $sla->fields['number_time'] . ' ' . $sla->fields['definition_time'],
            $number_time,
            $definition_time,
        );
        $new = clone $sla;
        $new->fields['number_time']     = $number_time;
        $new->fields['definition_time'] = $definition_time;
        $tickets = array_filter(self::activeTicketsForSla(), static fn ($t) => (int) $t["slas_id_{$type}"] === $sla_id);
        return self::slaImpact($tickets, $type, $new, $label);
    }

    /**
     * Pratinjau aturan SLA yang menetapkan SLA lain: jenis SLA pengganti (respons/penyelesaian) menentukan aksi aturan
     * yang diganti; tiket aktif yang cocok dengan kriteria aturan dan kini memakai SLA aksi itu dihitung ulang.
     */
    public static function previewSlaRule(int $rule_id, int $new_sla_id): ?array
    {
        $rule = new RuleTicket();
        if (!$rule->getRuleWithCriteriasAndActions($rule_id, true, true)) {
            return null;
        }
        $new = new SLA();
        if (!$new->getFromDB($new_sla_id)) {
            return null;
        }
        $type   = (int) $new->fields['type'] === SLM::TTO ? 'tto' : 'ttr';
        $action = null;
        foreach ($rule->actions as $candidate) {
            if ($candidate->fields['field'] === "slas_id_{$type}") {
                $action = $candidate->fields;
            }
        }
        if ($action === null) {
            return ['error' => __('The replacement SLA must be of the same kind (response or resolution) as the rule action.', 'halosis')];
        }
        $old_sla = (int) $action['value'];
        $label   = sprintf(__('Rule "%1$s": SLA %2$s → %3$s', 'halosis'), $rule->fields['name'], Dropdown::getDropdownName(SLA::getTable(), $old_sla), $new->fields['name']);
        $tickets = array_filter(
            self::activeTicketsForSla(),
            static fn ($t) => (int) $t["slas_id_{$type}"] === $old_sla && $rule->checkCriterias($t),
        );
        return self::slaImpact($tickets, $type, $new, $label);
    }

    /**
     * Tiket aktif (Baru s.d. Menunggu) di luar entitas arsip, dengan field yang dipakai SLA & kriteria aturan.
     *
     * @return array<int, array<string, mixed>>
     */
    private static function activeTicketsForSla(): array
    {
        global $DB;

        $rows = [];
        foreach ($DB->request([
            'SELECT' => [
                'id', 'date', 'type', 'itilcategories_id', 'priority', 'urgency', 'impact', 'entities_id', 'status',
                'slas_id_ttr', 'slas_id_tto', 'time_to_resolve', 'time_to_own', 'sla_waiting_duration', 'takeintoaccount_delay_stat',
            ],
            'FROM'   => Ticket::getTable(),
            'WHERE'  => [
                'is_deleted' => 0,
                'status'     => ['<', CommonITILObject::SOLVED],
                'NOT'        => ['entities_id' => Config::getArchiveEntityIds() ?: [-1]],
            ],
        ]) as $row) {
            $rows[(int) $row['id']] = $row;
        }
        return $rows;
    }

    /**
     * Status SLA sekarang vs bila target baru diterapkan, per tiket: aman / berisiko / terlewati.
     *
     * @param array<int, array<string, mixed>> $tickets
     * @return array{label: string, total: int, current: array<string, int>, new: array<string, int>, changed: int, worse: int, better: int}
     */
    private static function slaImpact(array $tickets, string $type, SLA $new, string $label): array
    {
        $now    = $_SESSION['glpi_currenttime'] ?? date('Y-m-d H:i:s');
        $empty  = ['ok' => 0, 'risk' => 0, 'overdue' => 0];
        $result = ['label' => $label, 'total' => 0, 'current' => $empty, 'new' => $empty, 'changed' => 0, 'worse' => 0, 'better' => 0];
        $rank   = ['ok' => 0, 'risk' => 1, 'overdue' => 2];
        foreach ($tickets as $ticket) {
            // SLA respons hanya berlaku sampai tiket diambil
            if ($type === 'tto' && (int) $ticket['takeintoaccount_delay_stat'] > 0) {
                continue;
            }
            $due_now = (string) ($type === 'ttr' ? $ticket['time_to_resolve'] : $ticket['time_to_own']);
            $due_new = (string) $new->computeDate($ticket['date'], $type === 'ttr' ? (int) $ticket['sla_waiting_duration'] : 0);
            $from = self::slaState((string) $ticket['date'], $due_now !== '' ? $due_now : $due_new, $now);
            $to   = self::slaState((string) $ticket['date'], $due_new, $now);
            $result['total']++;
            $result['current'][$from]++;
            $result['new'][$to]++;
            if ($from !== $to) {
                $result['changed']++;
                $result[$rank[$to] > $rank[$from] ? 'worse' : 'better']++;
            }
        }
        return $result;
    }

    /**
     * terlewati = lewat batas; berisiko = sisa ≤ SLA_RISK_SHARE durasi target; selain itu aman.
     */
    public static function slaState(string $start, string $due, string $now): string
    {
        $start_ts = strtotime($start);
        $due_ts   = strtotime($due);
        $now_ts   = strtotime($now);
        if ($due_ts === false || $start_ts === false || $now_ts === false) {
            return 'ok';
        }
        if ($now_ts > $due_ts) {
            return 'overdue';
        }
        return $due_ts - $now_ts <= self::SLA_RISK_SHARE * max(0, $due_ts - $start_ts) ? 'risk' : 'ok';
    }
}
