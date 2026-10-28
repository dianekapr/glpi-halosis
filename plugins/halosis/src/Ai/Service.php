<?php

namespace GlpiPlugin\Halosis\Ai;

use GlpiPlugin\Halosis\Config;

/**
 * Klien layanan AI HaloSIS (ai/service, FastAPI): model triase dari history tiket + pencarian Pusat Bantuan.
 *
 * Setiap kegagalan (URL kosong, layanan mati, timeout, jawaban tidak valid) dilempar sebagai AiException
 * supaya pemanggil kembali ke mode sebelumnya (dummy / AI penyedia).
 */
final class Service
{
    public static function isConfigured(): bool
    {
        return (string) Config::get('service_url') !== '';
    }

    /**
     * @param array<string, mixed> $payload
     *
     * @return array<string, mixed>
     */
    public static function post(string $path, array $payload): array
    {
        $url = (string) Config::get('service_url');
        if ($url === '') {
            throw new AiException('URL layanan AI belum diatur');
        }

        $context = stream_context_create(['http' => [
            'method'        => 'POST',
            'header'        => "Content-Type: application/json\r\nAccept: application/json\r\n",
            'content'       => json_encode($payload, JSON_UNESCAPED_UNICODE),
            'timeout'       => (int) Config::get('service_timeout'),
            'ignore_errors' => true,
        ]]);
        $body = @file_get_contents($url . $path, false, $context);
        if ($body === false) {
            throw new AiException('Layanan AI tidak bisa dihubungi');
        }

        $status = 0;
        foreach ($http_response_header ?? [] as $header) {
            if (preg_match('#^HTTP/\S+\s+(\d{3})#', $header, $m)) {
                $status = (int) $m[1];
            }
        }
        $data = json_decode($body, true);
        if ($status !== 200 || !is_array($data)) {
            throw new AiException(sprintf('Layanan AI menjawab HTTP %d', $status));
        }
        return $data;
    }
}
