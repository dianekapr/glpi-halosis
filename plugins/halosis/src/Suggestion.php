<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;
use Group;
use ITILCategory;
use Ticket;

/**
 * Saran triase AI untuk satu tiket (tabel glpi_plugin_halosis_suggestions).
 * Nilai saran disimpan di sini, bukan di field tiket; baru diterapkan ke tiket setelah petugas memutuskan.
 */
final class Suggestion extends CommonDBTM
{
    public const STATUS_PENDING  = 'pending';
    public const STATUS_ACCEPTED = 'accepted';
    public const STATUS_MODIFIED = 'modified';
    public const STATUS_REJECTED = 'rejected';

    /** Field triase yang disarankan AI dan bisa diterapkan ke tiket */
    public const VALUE_FIELDS = ['itilcategories_id', 'impact', 'urgency', 'priority', 'groups_id'];

    public static string $rightname = Profile::RIGHT_TRIASE;

    public bool $dohistory = false;

    public static function getTypeName($nb = 0)
    {
        return _n('AI suggestion', 'AI suggestions', $nb, 'halosis');
    }

    /**
     * Saran terbaru untuk tiket, atau null jika belum ada.
     */
    public static function getLatestForTicket(int $tickets_id): ?self
    {
        $suggestion = new self();
        $found = $suggestion->getFromDBByRequest([
            'WHERE' => ['tickets_id' => $tickets_id],
            'ORDER' => 'id DESC',
            'LIMIT' => 1,
        ]);
        return $found ? $suggestion : null;
    }

    /**
     * Nilai triase saran ini sebagai array (untuk log keputusan & pembandingan).
     *
     * @return array<string, int>
     */
    public function getValues(): array
    {
        $values = [];
        foreach (self::VALUE_FIELDS as $field) {
            $values[$field] = (int) $this->fields[$field];
        }
        return $values;
    }

    public function isPending(): bool
    {
        return $this->fields['status'] === self::STATUS_PENDING;
    }

    public function needsManualReview(): bool
    {
        return (int) $this->fields['confidence'] < Config::getTriageThreshold();
    }

    /**
     * Tingkat keyakinan (TO-BE hal. 100): high = saran utama, medium = pilih dari 3 kandidat, low = manual.
     */
    public function getConfidenceLevel(): string
    {
        $confidence = (int) $this->fields['confidence'];
        return match (true) {
            $confidence >= Config::getTriageThreshold() => 'high',
            $confidence >= Config::getLowThreshold()    => 'medium',
            default                                     => 'low',
        };
    }

    /**
     * Uraian nilai triase yang mudah dibaca, mis. untuk riwayat tiket.
     *
     * @param array<string, int> $values
     */
    public static function describeValues(array $values): string
    {
        return sprintf(
            '%s: %s; %s: %s; %s: %s; %s: %s; %s: %s',
            __('Category'),
            self::categoryName((int) ($values['itilcategories_id'] ?? 0)),
            __('Impact'),
            Ticket::getImpactName((int) ($values['impact'] ?? 0)),
            __('Urgency'),
            Ticket::getUrgencyName((int) ($values['urgency'] ?? 0)),
            __('Priority'),
            Ticket::getPriorityName((int) ($values['priority'] ?? 0)),
            Group::getTypeName(1),
            self::groupName((int) ($values['groups_id'] ?? 0)),
        );
    }

    public static function categoryName(int $id): string
    {
        $category = new ITILCategory();
        return $id > 0 && $category->getFromDB($id) ? $category->fields['completename'] : '-';
    }

    public static function groupName(int $id): string
    {
        $group = new Group();
        return $id > 0 && $group->getFromDB($id) ? $group->fields['completename'] : '-';
    }
}
