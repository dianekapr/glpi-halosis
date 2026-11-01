<?php

namespace GlpiPlugin\Halosis;

/**
 * E15: ringkasan ekstraktif deskripsi tiket panjang untuk panel Saran AI, tanpa LLM.
 *
 * Deskripsi > MIN_WORDS kata disamarkan dulu (Privacy::mask), dipecah per kalimat, lalu tiap kalimat diberi skor
 * = jumlah frekuensi kata kuncinya di seluruh deskripsi ÷ √(banyak kata kunci kalimat) (kalimat yang memuat kata
 * yang sering diulang = inti keluhan), kalimat pertama mendapat bonus posisi. SENTENCES kalimat berskor tertinggi
 * ditampilkan sesuai urutan aslinya. Deterministik: isi sama → ringkasan sama.
 */
final class Summary
{
    /** Deskripsi dengan kata lebih dari ini diringkas */
    public const MIN_WORDS = 150;

    /** Banyak kalimat ringkasan */
    public const SENTENCES = 3;

    /** Bonus skor kalimat pertama (biasanya berisi keluhan utama) */
    private const FIRST_SENTENCE_BONUS = 1.2;

    /** Kalimat ringkasan dipotong agar panel tetap ringkas */
    private const MAX_SENTENCE_CHARS = 300;

    /**
     * Ringkasan deskripsi tiket (HTML GLPI) atau null bila deskripsi tidak panjang.
     *
     * @return array{sentences: string[], words: int}|null
     */
    public static function forTicketContent(?string $html): ?array
    {
        $text = (string) $html;
        // Batas blok HTML (paragraf, baris, butir) juga batas kalimat
        $text = preg_replace('#<(br|/p|/div|/li|/h[1-6]|/tr)\b[^>]*>#i', "\n", $text) ?? $text;
        $text = html_entity_decode(strip_tags($text), ENT_QUOTES | ENT_HTML5, 'UTF-8');
        return self::extract(Privacy::mask($text)['text']);
    }

    /**
     * @return array{sentences: string[], words: int}|null
     */
    public static function extract(string $text, int $count = self::SENTENCES): ?array
    {
        $words = self::wordCount($text);
        if ($words <= self::MIN_WORDS) {
            return null;
        }

        $sentences = [];
        foreach (preg_split('/(?<=[.!?])\s+|\R+/u', $text) ?: [] as $sentence) {
            $sentence = trim(preg_replace('/\s+/u', ' ', $sentence) ?? '');
            // Kalimat yang diulang (salin-tempel) dihitung sekali agar tidak mendominasi frekuensi kata
            if (self::wordCount($sentence) >= 3 && !in_array(mb_strtolower($sentence), array_map('mb_strtolower', $sentences), true)) {
                $sentences[] = $sentence;
            }
        }
        if (count($sentences) <= $count) {
            return null; // sedikit kalimat panjang: ringkasan tidak menambah apa-apa
        }

        $tokens    = array_map([KnowledgeSearch::class, 'tokens'], $sentences);
        $frequency = array_count_values(array_merge(...$tokens));
        $scores    = [];
        foreach ($tokens as $index => $sentence_tokens) {
            if ($sentence_tokens === []) {
                $scores[$index] = 0.0;
                continue;
            }
            $sum = array_sum(array_map(static fn ($t) => $frequency[$t], $sentence_tokens));
            $scores[$index] = $sum / sqrt(count($sentence_tokens)) * ($index === 0 ? self::FIRST_SENTENCE_BONUS : 1.0);
        }
        // Skor sama → kalimat lebih awal didahulukan (urutan stabil)
        uksort($scores, static fn ($a, $b) => [$scores[$b], $a] <=> [$scores[$a], $b]);
        $chosen = array_slice(array_keys($scores), 0, $count);
        sort($chosen);

        return [
            'sentences' => array_map(static fn ($i) => mb_strimwidth($sentences[$i], 0, self::MAX_SENTENCE_CHARS, '…'), $chosen),
            'words'     => $words,
        ];
    }

    private static function wordCount(string $text): int
    {
        return count(preg_split('/[^\p{L}\p{N}]+/u', $text, -1, PREG_SPLIT_NO_EMPTY) ?: []);
    }
}
