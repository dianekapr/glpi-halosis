<?php

namespace GlpiPlugin\Halosis;

use Calendar;
use CommonDBTM;
use CommonITILObject;
use CronTask;
use Entity;
use ITILFollowup;
use Notification;
use Notification_NotificationTemplate;
use NotificationEvent;
use NotificationTarget;
use NotificationTargetTicket;
use NotificationTemplate;
use NotificationTemplateTranslation;
use Ticket;
use TicketTask;
use Toolbox;

/**
 * E19: tugas terjadwal "ProgressReminder" (Pengingat progres).
 *
 * Tiket Diproses (ditugaskan/direncanakan) atau Menunggu yang tidak mendapat tindak lanjut/tugas lebih dari N hari
 * kerja (Pengaturan AI `progress_reminder_days`, bawaan 5) → notifikasi GLPI "HaloSIS: Pengingat progres" ke teknisi
 * & grup yang ditugaskan (email + browser). Aktivitas terakhir = tindak lanjut/tugas terakhir, waktu diambil, atau
 * waktu dibuat. Sekali per periode: pengingat berikutnya baru dikirim setelah N hari kerja lagi tanpa aktivitas.
 * Hari kerja mengikuti kalender entitas tiket (libur ikut), cadangan Senin–Jumat.
 */
final class ProgressReminder extends CommonDBTM
{
    public const CRON_NAME = 'ProgressReminder';

    /** Event notifikasi GLPI untuk tiket (didaftarkan lewat hook item_get_events) */
    public const EVENT = 'halosis_progress';

    /** Status yang diingatkan: Diproses (ditugaskan, direncanakan) dan Menunggu */
    public const STATUSES = [CommonITILObject::ASSIGNED, CommonITILObject::PLANNED, CommonITILObject::WAITING];

    /** Tiket per jalannya tugas */
    public const BATCH = 200;

    public bool $dohistory = false;

    public static function getTable($classname = null)
    {
        return 'glpi_plugin_halosis_progress_reminders';
    }

    public static function cronInfo(string $name): array
    {
        return ['description' => __('HaloSIS: remind assigned technicians of tickets without progress', 'halosis')];
    }

    public static function cronProgressReminder(CronTask $task): int
    {
        $result = self::run();
        foreach ($result['log'] as $line) {
            $task->log($line);
        }
        $task->setVolume($result['sent']);
        return $result['sent'] > 0 ? 1 : 0;
    }

    /**
     * @return array{checked: int, sent: int, log: string[]}
     */
    public static function run(?string $now = null): array
    {
        global $DB;

        $now  = $now ?? ($_SESSION['glpi_currenttime'] ?? date('Y-m-d H:i:s'));
        $days = max(1, (int) Config::get('progress_reminder_days'));

        $checked = $sent = 0;
        $log = [];
        foreach ($DB->request([
            'SELECT'    => ['t.id', 't.entities_id', 't.date', 't.takeintoaccountdate', 'r.date_reminder'],
            'FROM'      => Ticket::getTable() . ' AS t',
            'LEFT JOIN' => [self::getTable() . ' AS r' => ['ON' => ['t' => 'id', 'r' => 'tickets_id']]],
            'WHERE'     => [
                't.is_deleted' => 0,
                't.status'     => self::STATUSES,
                ['NOT' => ['t.entities_id' => Config::getArchiveEntityIds() ?: [-1]]],
            ],
            'ORDER'     => 't.id',
            'LIMIT'     => self::BATCH,
        ]) as $row) {
            $checked++;
            $last = self::lastActivity((int) $row['id'], [(string) $row['date'], (string) $row['takeintoaccountdate']]);
            $calendar = self::calendarId((int) $row['entities_id']);
            $idle = self::workingDaysBetween($last, $now, $calendar);
            if ($idle <= $days) {
                continue;
            }
            // Sekali per periode: sudah diingatkan setelah aktivitas terakhir dan belum lewat N hari kerja lagi
            $previous = (string) ($row['date_reminder'] ?? '');
            if ($previous !== '' && $previous >= $last && self::workingDaysBetween($previous, $now, $calendar) <= $days) {
                continue;
            }

            $ticket = new Ticket();
            if (!$ticket->getFromDB((int) $row['id'])) {
                continue;
            }
            NotificationEvent::raiseEvent(self::EVENT, $ticket, ['halosis_idle_days' => $idle, 'halosis_days' => $days]);
            $DB->updateOrInsert(self::getTable(), [
                'last_activity' => $last,
                'date_reminder' => $now,
                'idle_days'     => $idle,
            ], ['tickets_id' => $ticket->getID()]);
            $sent++;
            $line = sprintf(__('Ticket #%1$d: progress reminder sent (%2$d working days without follow-up)', 'halosis'), $ticket->getID(), $idle);
            $log[] = $line;
            Toolbox::logInFile('halosis', "ProgressReminder: {$line}\n", true);
        }
        return ['checked' => $checked, 'sent' => $sent, 'log' => $log];
    }

    /**
     * Waktu aktivitas terakhir: tindak lanjut / tugas terakhir, atau tanggal cadangan (dibuat, diambil) yang terbaru.
     *
     * @param string[] $fallback
     */
    public static function lastActivity(int $tickets_id, array $fallback): string
    {
        global $DB;

        $dates = array_filter($fallback);
        foreach ([
            [ITILFollowup::getTable(), ['itemtype' => Ticket::class, 'items_id' => $tickets_id]],
            [TicketTask::getTable(), ['tickets_id' => $tickets_id]],
        ] as [$table, $where]) {
            $max = $DB->request(['SELECT' => ['MAX' => 'date_creation AS last'], 'FROM' => $table, 'WHERE' => $where])->current()['last'] ?? null;
            if ($max) {
                $dates[] = (string) $max;
            }
        }
        return $dates === [] ? date('Y-m-d H:i:s') : max($dates);
    }

    /**
     * Hari kerja sesudah hari $from sampai dengan hari $to (Senin → Senin berikutnya = 5).
     */
    public static function workingDaysBetween(string $from, string $to, int $calendars_id = 0): int
    {
        $start = strtotime(date('Y-m-d', strtotime($from)) . ' +1 day');
        $end   = strtotime(date('Y-m-d', strtotime($to)));
        if ($start === false || $end === false || $start > $end) {
            return 0;
        }
        $calendar = null;
        if ($calendars_id > 0) {
            $calendar = new Calendar();
            if (!$calendar->getFromDB($calendars_id) || !$calendar->hasAWorkingDay()) {
                $calendar = null;
            }
        }
        $days = 0;
        for ($day = $start; $day <= $end; $day = strtotime('+1 day', $day)) {
            $working = $calendar !== null ? $calendar->isAWorkingDay($day) : (int) date('N', $day) <= 5;
            $days += (int) $working;
        }
        return $days;
    }

    private static function calendarId(int $entities_id): int
    {
        $id = Entity::getUsedConfig('calendars_strategy', $entities_id, 'calendars_id', 0);
        return is_numeric($id) ? max(0, (int) $id) : 0;
    }

    /**
     * Hook item_get_events: daftarkan event pengingat pada notifikasi tiket (Setup › Notifikasi).
     */
    public static function addEvent(NotificationTarget $target): void
    {
        if ($target instanceof NotificationTargetTicket) {
            $target->events[self::EVENT] = __('HaloSIS: progress reminder', 'halosis');
        }
    }

    /**
     * Hook item_get_datas: tag templat ##halosis.idle_days## dan ##halosis.reminder_days##.
     */
    public static function addTemplateData(NotificationTarget $target): void
    {
        if ($target instanceof NotificationTargetTicket && $target->raiseevent === self::EVENT) {
            $target->data['##halosis.idle_days##']     = (string) ($target->options['halosis_idle_days'] ?? '');
            $target->data['##halosis.reminder_days##'] = (string) ($target->options['halosis_days'] ?? Config::get('progress_reminder_days'));
        }
    }

    /**
     * Uninstall: hapus notifikasi & templat pengingat (penerima & mode ikut terhapus bersama notifikasi).
     */
    public static function uninstallNotification(): void
    {
        $notification = new Notification();
        foreach ($notification->find(['itemtype' => Ticket::class, 'event' => self::EVENT]) as $row) {
            $notification->delete(['id' => $row['id']], true);
        }
        $template = new NotificationTemplate();
        foreach ($template->find(['itemtype' => Ticket::class, 'name' => 'HaloSIS: Pengingat progres']) as $row) {
            $template->delete(['id' => $row['id']], true);
        }
    }

    /**
     * Notifikasi + templat bawaan (idempoten; tidak menimpa yang sudah diubah admin): penerima teknisi & grup yang
     * ditugaskan, mode email & browser.
     */
    public static function installNotification(): void
    {
        $notification = new Notification();
        if ($notification->getFromDBByCrit(['itemtype' => Ticket::class, 'event' => self::EVENT])) {
            return;
        }

        $template = new NotificationTemplate();
        $template_id = (int) $template->add(['name' => 'HaloSIS: Pengingat progres', 'itemtype' => Ticket::class]);
        (new NotificationTemplateTranslation())->add([
            'notificationtemplates_id' => $template_id,
            'language'                 => '',
            'subject'                  => '[HaloSIS] Pengingat progres tiket ##ticket.id##',
            'content_text'             => "Tiket ##ticket.id## (##ticket.status##) belum mendapat tindak lanjut selama "
                . "##halosis.idle_days## hari kerja (batas ##halosis.reminder_days## hari kerja).\n"
                . "Mohon perbarui progres atau beri tindak lanjut kepada pemohon.\n##ticket.url##",
            'content_html'             => '<p>Tiket ##ticket.id## (##ticket.status##) belum mendapat tindak lanjut selama '
                . '##halosis.idle_days## hari kerja (batas ##halosis.reminder_days## hari kerja).</p>'
                . '<p>Mohon perbarui progres atau beri tindak lanjut kepada pemohon.</p>'
                . '<p><a href="##ticket.url##">##ticket.url##</a></p>',
        ]);

        $notification_id = (int) $notification->add([
            'name'         => 'HaloSIS: Pengingat progres',
            'itemtype'     => Ticket::class,
            'event'        => self::EVENT,
            'entities_id'  => 0,
            'is_recursive' => 1,
            'is_active'    => 1,
        ]);
        foreach (['mailing', 'ajax'] as $mode) {
            (new Notification_NotificationTemplate())->add([
                'notifications_id'         => $notification_id,
                'notificationtemplates_id' => $template_id,
                'mode'                     => $mode,
            ]);
        }
        foreach ([Notification::ASSIGN_TECH, Notification::ASSIGN_GROUP] as $recipient) {
            (new \NotificationTarget())->add([
                'notifications_id' => $notification_id,
                'type'             => Notification::USER_TYPE,
                'items_id'         => $recipient,
            ]);
        }
    }
}
