<?php

namespace GlpiPlugin\Halosis;

use Glpi\Form\Form;
use Glpi\Form\Question;
use Glpi\Form\Section;

/**
 * Melokalkan dua form katalog bawaan GLPI ("Report an issue", "Request a service") dan mewajibkan Judul (UC-03).
 *
 * Isi form adalah data, bukan kode GLPI: nama yang masih bawaan diganti lewat objek Form agar hook katalog (audit &
 * sinkron indeks AI) ikut berjalan. Idempoten: form yang sudah diganti namanya oleh Administrator tidak disentuh.
 */
final class FormCatalog
{
    /** Nama & deskripsi bawaan GLPI → label Indonesia */
    private const FORMS = [
        'Report an issue'   => ['Laporkan Masalah', 'Minta bantuan tim layanan TI untuk masalah yang Anda alami.'],
        'Request a service' => ['Ajukan Permintaan', 'Minta tim layanan TI menyediakan layanan yang Anda perlukan.'],
    ];

    private const QUESTIONS = [
        'Urgency'      => 'Urgensi',
        'Category'     => 'Kategori',
        'User devices' => 'Perangkat pengguna',
        'Observers'    => 'Pengamat',
        'Location'     => 'Lokasi',
        'Title'        => 'Judul',
        'Description'  => 'Deskripsi',
        'Attachments'  => 'Lampiran',
    ];

    private const REQUIRED_QUESTION = 'Judul';

    public static function localize(): void
    {
        global $DB;

        foreach (self::FORMS as $default => [$name, $description]) {
            $form = new Form();
            if ($form->getFromDBByCrit(['name' => $default])) {
                $form->update(['id' => $form->getID(), 'name' => $name, 'description' => $description]);
            }
        }

        $forms = array_column(self::FORMS, 0);
        $sections = array_column(iterator_to_array($DB->request([
            'SELECT'     => ['s.id'],
            'FROM'       => Section::getTable() . ' AS s',
            'INNER JOIN' => [Form::getTable() . ' AS f' => ['ON' => ['s' => 'forms_forms_id', 'f' => 'id']]],
            'WHERE'      => ['f.name' => $forms],
        ])), 'id');
        if ($sections === []) {
            return;
        }
        foreach (self::QUESTIONS as $default => $label) {
            $DB->update(Question::getTable(), ['name' => $label], [
                'forms_sections_id' => $sections,
                'name'              => $default,
            ]);
        }
        $DB->update(Question::getTable(), ['is_mandatory' => 1], [
            'forms_sections_id' => $sections,
            'name'              => self::REQUIRED_QUESTION,
        ]);
    }
}
