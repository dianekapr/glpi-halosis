<?php

namespace GlpiPlugin\Halosis;

use KnowbaseItem;

/**
 * Pencarian artikel Knowledge Base untuk chatbot, HANYA di antara artikel yang boleh dilihat pengguna:
 * query memakai kriteria visibilitas GLPI (di antarmuka Helpdesk = FAQ yang terlihat), lalu setiap
 * artikel dicek ulang dengan KnowbaseItem::canViewItem() (visibilitas, jendela tayang).
 */
final class KnowledgeSearch
{
    /** Skor minimum agar artikel dianggap relevan (1 kata di judul = 3, 1 kata di isi = 1) */
    public const MIN_SCORE = 3;

    private const MAX_TEXT_LENGTH = 4000;

    private const STOPWORDS = [
        'yang', 'dan', 'atau', 'dari', 'untuk', 'dengan', 'pada', 'karena', 'ini', 'itu', 'ada', 'apa', 'bagaimana',
        'gimana', 'kenapa', 'mengapa', 'cara', 'saya', 'aku', 'kami', 'kita', 'anda', 'kamu', 'tidak', 'tdk', 'gak',
        'bisa', 'sudah', 'belum', 'juga', 'akan', 'mau', 'ingin', 'tolong', 'mohon', 'bantu', 'dong', 'saja', 'lagi',
        'terus', 'sejak', 'kalau', 'jika', 'agar', 'supaya', 'masih', 'sangat', 'banyak', 'semua', 'kok', 'nya',
        'the', 'and', 'for', 'error',
    ];

    /**
     * @return array<int, array{id: int, name: string, text: string, url: string, score: int}>
     */
    public static function search(string $question, int $limit = 3): array
    {
        global $DB;

        $tokens = self::tokens($question);
        if ($tokens === []) {
            return [];
        }

        $table      = KnowbaseItem::getTable();
        $visibility = KnowbaseItem::getVisibilityCriteria();
        $likes      = [];
        foreach ($tokens as $token) {
            $likes[] = ["$table.name" => ['LIKE', "%$token%"]];
            $likes[] = ["$table.answer" => ['LIKE', "%$token%"]];
        }

        $candidates = $DB->request([
            'SELECT'    => ["$table.id"],
            'DISTINCT'  => true,
            'FROM'      => $table,
            'LEFT JOIN' => $visibility['LEFT JOIN'],
            'WHERE'     => [$visibility['WHERE'], ['OR' => $likes]],
            'LIMIT'     => 50,
        ]);

        $results = [];
        foreach ($candidates as $row) {
            $item = new KnowbaseItem();
            if (!$item->getFromDB((int) $row['id']) || !$item->canViewItem()) {
                continue;
            }
            $name  = (string) $item->fields['name'];
            $text  = self::plainText((string) $item->fields['answer']);
            $score = self::score($tokens, mb_strtolower($name), mb_strtolower($text));
            if ($score < self::MIN_SCORE) {
                continue;
            }
            $results[] = [
                'id'    => $item->getID(),
                'name'  => $name,
                'text'  => mb_substr($text, 0, self::MAX_TEXT_LENGTH),
                'url'   => KnowbaseItem::getFormURLWithID($item->getID()),
                'score' => $score,
            ];
        }

        // Skor tertinggi dulu; seri → id terkecil (hasil deterministik)
        usort($results, static fn ($a, $b) => [$b['score'], $a['id']] <=> [$a['score'], $b['id']]);
        return array_slice($results, 0, $limit);
    }

    /**
     * Kata kunci bermakna dari pertanyaan (huruf kecil, tanpa kata umum, minimal 3 huruf).
     *
     * @return string[]
     */
    public static function tokens(string $text): array
    {
        $words = preg_split('/[^\p{L}\p{N}]+/u', mb_strtolower($text), -1, PREG_SPLIT_NO_EMPTY) ?: [];
        $words = array_filter($words, static fn ($w) => mb_strlen($w) >= 3 && !in_array($w, self::STOPWORDS, true));
        return array_values(array_unique($words));
    }

    /**
     * @param string[] $tokens
     */
    private static function score(array $tokens, string $name, string $text): int
    {
        $score = 0;
        foreach ($tokens as $token) {
            if (str_contains($name, $token)) {
                $score += 3;
            } elseif (str_contains($text, $token)) {
                $score += 1;
            }
        }
        return $score;
    }

    public static function plainText(string $html): string
    {
        $html = preg_replace('#<li[^>]*>#i', "\n- ", $html) ?? $html;
        $html = str_ireplace(['<br>', '<br/>', '<br />', '</p>', '</li>', '</ol>', '</ul>'], "\n", $html);
        $text = html_entity_decode(strip_tags($html), ENT_QUOTES | ENT_HTML5, 'UTF-8');
        $text = preg_replace("/[ \t]+/", ' ', $text) ?? $text;
        return trim(preg_replace("/\n\s*\n+/", "\n", $text) ?? $text);
    }
}
