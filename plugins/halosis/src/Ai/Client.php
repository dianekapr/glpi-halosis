<?php

namespace GlpiPlugin\Halosis\Ai;

use Anthropic\Client as AnthropicClient;
use Anthropic\Core\Exceptions\APIException;
use GlpiPlugin\Halosis\Config;
use GLPIKey;
use GuzzleHttp\Client as GuzzleClient;
use Throwable;

/**
 * Pemanggil AI di sisi server. API key dibaca dari konfigurasi terenkripsi dan hanya dipakai di sini;
 * tidak pernah dikirim ke browser.
 */
final class Client
{
    /** Model Claude yang mendukung server-side fallback mode "default" */
    private const FALLBACK_MODELS = ['claude-opus-5-5', 'claude-opus-5', 'claude-fable-5-1', 'claude-sonnet-5-5'];
    private const FALLBACK_BETA   = 'server-side-fallback-2026-07-01';

    /**
     * Minta jawaban JSON yang mengikuti skema.
     *
     * @param array<string, mixed> $schema JSON Schema objek jawaban
     *
     * @return array{data: array<string, mixed>, model: string}
     *
     * @throws AiException
     */
    public static function completeJson(string $system, string $prompt, array $schema, int $max_tokens = 4000): array
    {
        if (Config::isDemoMode()) {
            throw new AiException('Mode demo aktif: pemanggilan AI tidak dilakukan.');
        }

        try {
            return match (Config::get('ai_provider')) {
                Config::PROVIDER_OPENAI => self::callOpenAiCompatible($system, $prompt, $schema, $max_tokens),
                default                 => self::callAnthropic($system, $prompt, $schema, $max_tokens),
            };
        } catch (AiException $e) {
            throw $e;
        } catch (Throwable $e) {
            throw new AiException(sprintf('%s: %s', $e::class, $e->getMessage()), 0, $e);
        }
    }

    /**
     * Claude lewat SDK resmi Anthropic, dengan structured output (JSON schema).
     */
    private static function callAnthropic(string $system, string $prompt, array $schema, int $max_tokens): array
    {
        self::loadSdk();

        $model    = (string) Config::get('ai_model');
        $base_url = (string) Config::get('api_base_url');

        $client = new AnthropicClient(
            apiKey: Config::getApiKey(),
            baseUrl: $base_url !== '' ? $base_url : null,
            requestOptions: [
                'transporter' => self::httpClient(),
                'timeout'     => self::timeout(),
                // Tanpa coba ulang: tiket sedang menunggu disimpan, jadi waktu tunggu maksimal = batas waktu
                'maxRetries'  => 0,
            ],
        );

        // Fallback server-side saat permintaan ditolak classifier keamanan (hanya API Claude langsung)
        $fallback = in_array($model, self::FALLBACK_MODELS, true) && $base_url === '';

        try {
            $message = $client->beta->messages->create(
                maxTokens: $max_tokens,
                messages: [['role' => 'user', 'content' => $prompt]],
                model: $model,
                system: $system,
                // Klasifikasi tidak butuh penalaran panjang: effort rendah = cepat & hemat
                outputConfig: [
                    'effort' => 'low',
                    'format' => ['type' => 'json_schema', 'schema' => $schema],
                ],
                fallbacks: $fallback ? 'default' : null,
                betas: $fallback ? [self::FALLBACK_BETA] : null,
            );
        } catch (APIException $e) {
            throw new AiException('Claude API: ' . $e->getMessage(), 0, $e);
        }

        if ($message->stopReason === 'refusal') {
            throw new AiException('Claude menolak permintaan: ' . ($message->stopDetails?->category ?? 'tanpa kategori'));
        }
        if ($message->stopReason === 'max_tokens') {
            throw new AiException('Jawaban Claude terpotong (max_tokens).');
        }

        foreach ($message->content as $block) {
            if ($block->type === 'text') {
                return ['data' => self::decode($block->text), 'model' => (string) $message->model];
            }
        }
        throw new AiException('Jawaban Claude tidak berisi teks.');
    }

    /**
     * Gateway kompatibel OpenAI (Chat Completions dengan response_format json_schema).
     */
    private static function callOpenAiCompatible(string $system, string $prompt, array $schema, int $max_tokens): array
    {
        $base_url = (string) Config::get('api_base_url');
        $url      = ($base_url !== '' ? $base_url : 'https://api.openai.com/v1') . '/chat/completions';
        $model    = (string) Config::get('ai_model');

        $response = self::httpClient()->post($url, [
            'headers' => ['Authorization' => 'Bearer ' . Config::getApiKey()],
            'json'    => [
                'model'           => $model,
                'max_tokens'      => $max_tokens,
                'messages'        => [
                    ['role' => 'system', 'content' => $system],
                    ['role' => 'user', 'content' => $prompt],
                ],
                'response_format' => [
                    'type'        => 'json_schema',
                    'json_schema' => ['name' => 'halosis', 'strict' => true, 'schema' => $schema],
                ],
            ],
        ]);

        $body = json_decode((string) $response->getBody(), true);
        $text = $body['choices'][0]['message']['content'] ?? null;
        if (!is_string($text)) {
            throw new AiException('Jawaban API kompatibel OpenAI tidak berisi teks.');
        }
        return ['data' => self::decode($text), 'model' => (string) ($body['model'] ?? $model)];
    }

    /**
     * @return array<string, mixed>
     */
    private static function decode(string $text): array
    {
        $data = json_decode($text, true);
        if (!is_array($data)) {
            throw new AiException('Jawaban AI bukan JSON yang valid.');
        }
        return $data;
    }

    private static function timeout(): float
    {
        return (float) Config::get('ai_timeout');
    }

    /**
     * Klien HTTP dengan batas waktu dari konfigurasi dan proxy GLPI (Setup › Umum › Proxy),
     * mengikuti aturan yang sama dengan Glpi\Toolbox\HttpClient.
     */
    private static function httpClient(): GuzzleClient
    {
        global $CFG_GLPI;

        $options = [
            'timeout'         => self::timeout(),
            'connect_timeout' => 5,
            'http_errors'     => true,
        ];
        if (!empty($CFG_GLPI['proxy_name']) && !in_array(self::class, $CFG_GLPI['proxy_exclusions'] ?? [], true)) {
            $credentials = '';
            if (!empty($CFG_GLPI['proxy_user'])) {
                $credentials = sprintf(
                    '%s:%s@',
                    rawurlencode($CFG_GLPI['proxy_user']),
                    rawurlencode((new GLPIKey())->decrypt($CFG_GLPI['proxy_passwd']) ?: '')
                );
            }
            $options['proxy'] = sprintf('http://%s%s:%d', $credentials, $CFG_GLPI['proxy_name'], $CFG_GLPI['proxy_port']);
        }
        return new GuzzleClient($options);
    }

    /**
     * SDK Anthropic dipasang lewat Composer di folder plugin (vendor/). Dimuat hanya saat dibutuhkan,
     * supaya mode demo tetap berjalan tanpa SDK.
     */
    private static function loadSdk(): void
    {
        if (class_exists(AnthropicClient::class)) {
            return;
        }
        $autoload = dirname(__DIR__, 2) . '/vendor/autoload.php';
        if (!is_file($autoload)) {
            throw new AiException('SDK Anthropic belum terpasang. Jalankan composer install di folder plugin.');
        }
        require_once $autoload;
    }

    public static function isSdkInstalled(): bool
    {
        return is_file(dirname(__DIR__, 2) . '/vendor/autoload.php');
    }
}
