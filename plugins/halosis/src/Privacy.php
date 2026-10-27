<?php

namespace GlpiPlugin\Halosis;

/**
 * Penyamaran data pribadi di pesan chat, dilakukan di server SEBELUM dikirim ke AI maupun disimpan.
 * Lapisan pengaman tambahan; widget tetap memperingatkan pegawai agar tidak mengirim data pribadi.
 */
final class Privacy
{
    /**
     * @return array{text: string, masked: bool}
     */
    public static function mask(string $text): array
    {
        $patterns = [
            // "password saya: abc123", "kata sandi = ...", "PIN adalah 1234"
            '/\b(password|passwd|kata ?sandi|sandi|pin|otp)(\s+(saya|ku|nya))?\s*(adalah|:|=)\s*\S+/iu' => '$1$2 $4 [disamarkan]',
            // Email
            '/[\w.+-]+@[\w-]+(\.[\w-]+)+/u' => '[email disamarkan]',
            // Nomor HP Indonesia
            '/(\+62|\b62|\b0)8\d{7,11}\b/u' => '[nomor HP disamarkan]',
            // NIK (16 digit) / NIP (18 digit) / nomor panjang lain
            '/\b\d{15,18}\b/u' => '[nomor identitas disamarkan]',
        ];

        $masked = preg_replace(array_keys($patterns), array_values($patterns), $text) ?? $text;
        return ['text' => $masked, 'masked' => $masked !== $text];
    }
}
