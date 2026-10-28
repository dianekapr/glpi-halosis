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
        return self::request('POST', $path, $payload);
    }

    /**
     * @return array<string, mixed>
     */
    public static function get(string $path): array
    {
        return self::request('GET', $path, null);
    }

    /**
     * @param array<string, mixed>|null $payload
     *
     * @return array<string, mixed>
     */
    private static function request(string $method, string $path, ?array $payload): array
    {
        $url = (string) Config::get('service_url');
        if ($url === '') {
            throw new AiException('URL layanan AI belum diatur');
        }

        $http = [
            'method'        => $method,
            'header'        => "Accept: application/json\r\n",
            'timeout'       => (int) Config::get('service_timeout'),
            'ignore_errors' => true,
        ];
        if ($payload !== null) {
            $http['header']  .= "Content-Type: application/json\r\n";
            $http['content']  = json_encode($payload, JSON_UNESCAPED_UNICODE);
        }
        $context = stream_context_create(['http' => $http]);
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
