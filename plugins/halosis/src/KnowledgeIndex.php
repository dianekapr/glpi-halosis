<?php

namespace GlpiPlugin\Halosis;

use CommonDBTM;
use Entity_KnowbaseItem;
use GlpiPlugin\Halosis\Ai\AiException;
use GlpiPlugin\Halosis\Ai\Service;
use Group_KnowbaseItem;
use KnowbaseItem;
use KnowbaseItem_Profile;
use KnowbaseItem_User;
use Session;
use Toolbox;

/**
 * Re-index knowledge otomatis (UC-09 langkah 7, BR-03): setiap artikel KB disimpan, dihapus, atau berubah
 * visibilitasnya, potongan artikel itu di indeks pencarian layanan AI diperbarui (POST /reindex/artikel).
 *
 * Artikel dianggap terbit bila FAQ atau punya target visibilitas (entitas/profil/grup/pengguna), sama dengan
 * ai/scripts/build_index.py. Kegagalan hanya dicatat: penyimpanan artikel di GLPI tetap berjalan.
 */
final class KnowledgeIndex
{
    /** Tabel target visibilitas artikel → artikel dianggap terbit */
    private const TARGETS = [Entity_KnowbaseItem::class, KnowbaseItem_Profile::class, Group_KnowbaseItem::class, KnowbaseItem_User::class];

    /**
     * Hook item_add / item_update KnowbaseItem.
     */
    public static function onArticleSave(KnowbaseItem $article): void
    {
        self::sync((int) $article->getID());
    }

    /**
     * Hook item_purge KnowbaseItem.
     */
    public static function onArticlePurge(KnowbaseItem $article): void
    {
        self::send((int) $article->getID(), '', '', 'hapus');
    }

    /**
     * Hook item_add / item_purge target visibilitas: status terbit artikelnya bisa berubah.
     */
    public static function onVisibilityChange(CommonDBTM $link): void
    {
        $kb_id = (int) ($link->fields['knowbaseitems_id'] ?? 0);
        if ($kb_id > 0) {
            self::sync($kb_id);
        }
    }

    private static function sync(int $kb_id): void
    {
        $article = new KnowbaseItem();
        if (!$article->getFromDB($kb_id)) {
            self::send($kb_id, '', '', 'hapus');
            return;
        }
        self::send($kb_id, (string) $article->fields['name'], (string) $article->fields['answer'], self::isPublished($article) ? 'simpan' : 'hapus');
    }

    public static function isPublished(KnowbaseItem $article): bool
    {
        return empty($article->fields['is_deleted'])
            && (!empty($article->fields['is_faq']) || self::hasTarget($article->getID()));
    }

    private static function hasTarget(int $kb_id): bool
    {
        foreach (self::TARGETS as $class) {
            if (countElementsInTable($class::getTable(), ['knowbaseitems_id' => $kb_id]) > 0) {
                return true;
            }
        }
        return false;
    }

    private static function send(int $kb_id, string $title, string $answer, string $action): void
    {
        if (!Service::isConfigured()) {
            return;
        }
        try {
            Service::post('/reindex/artikel', ['id' => $kb_id, 'judul' => $title, 'isi' => $answer, 'aksi' => $action]);
            Session::addMessageAfterRedirect(__s('Search index updated.', 'halosis'));
        } catch (AiException $e) {
            // Tidak menggagalkan penyimpanan artikel; layanan AI tetap memakai indeks lama
            Toolbox::logInFile('halosis', "Re-index artikel KB #{$kb_id} gagal: " . $e->getMessage() . "\n", true);
            Session::addMessageAfterRedirect(__s('Failed to update the search index; the previous index is still used.', 'halosis'), false, WARNING);
        }
    }
}
