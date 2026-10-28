<?php

namespace GlpiPlugin\Halosis;

use Config as CoreConfig;
use GLPIKey;

/**
 * Konfigurasi plugin HaloSIS, disimpan di glpi_configs dengan konteks "plugin:halosis".
 *
 * API key dienkripsi otomatis oleh GLPI saat disimpan (terdaftar lewat hook secured_configs)
 * dan hanya didekripsi di sisi server lewat getApiKey(). Jika API key kosong, plugin berjalan
 * dalam mode demo: semua fitur AI memakai jawaban contoh yang deterministik.
 */
final class Config
{
    public const CONTEXT = 'plugin:halosis';
    public const API_KEY = 'api_key';

    public const PROVIDER_ANTHROPIC = 'anthropic';
    public const PROVIDER_OPENAI    = 'openai';

    public const FEATURES = ['triage', 'chat', 'pattern', 'dashboard'];

    private const DEFAULTS = [
        'ai_provider'      => self::PROVIDER_ANTHROPIC,
        self::API_KEY      => '',
        'api_base_url'     => '',
        'ai_model'         => 'claude-opus-5-5',
        'ai_timeout'       => 20,
        // Layanan AI lokal (ai/service, docker-compose): dipanggil lebih dulu, gagal → mode di atas
        'service_url'      => 'http://halosis-ai:8000',
        'service_timeout'  => 8,
        'triage_threshold' => 70,
        // Deteksi pola insiden: minimal N tiket mirip dalam jendela waktu (menit); 0 = grup Operator bawaan
        'pattern_min_tickets' => 10,
        'pattern_window'      => 60,
        'pattern_group_id'    => 0,
        'feature_triage'    => 1,
        'feature_chat'      => 1,
        'feature_pattern'   => 1,
        'feature_dashboard' => 1,
    ];

    /** Cache nilai config per request */
    private static ?array $values = null;

    /**
     * Nama penyedia AI untuk pilihan di form.
     *
     * @return array<string, string>
     */
    public static function getProviders(): array
    {
        return [
            self::PROVIDER_ANTHROPIC => __('Anthropic (Claude)', 'halosis'),
            self::PROVIDER_OPENAI    => __('OpenAI-compatible API', 'halosis'),
        ];
    }

    /**
     * Label tiap fitur AI untuk toggle di form.
     *
     * @return array<string, string>
     */
    public static function getFeatureLabels(): array
    {
        return [
            'triage'    => __('AI triage suggestions on new tickets', 'halosis'),
            'chat'      => __('Self-service chatbot for employees', 'halosis'),
            'pattern'   => __('Incident pattern detection', 'halosis'),
            'dashboard' => __('AI performance dashboard', 'halosis'),
        ];
    }

    public static function get(string $name): mixed
    {
        if (self::$values === null) {
            self::$values = array_merge(self::DEFAULTS, CoreConfig::getConfigurationValues(self::CONTEXT));
        }
        return self::$values[$name] ?? null;
    }

    /**
     * API key dalam bentuk asli. HANYA untuk pemanggilan AI di server, jangan pernah dikirim ke template/JS.
     */
    public static function getApiKey(): string
    {
        $encrypted = (string) self::get(self::API_KEY);
        if ($encrypted === '') {
            return '';
        }
        return (string) (new GLPIKey())->decrypt($encrypted);
    }

    public static function hasApiKey(): bool
    {
        return (string) self::get(self::API_KEY) !== '';
    }

    public static function isDemoMode(): bool
    {
        return !self::hasApiKey();
    }

    public static function isFeatureEnabled(string $feature): bool
    {
        return (int) self::get('feature_' . $feature) === 1;
    }

    public static function getTriageThreshold(): int
    {
        return (int) self::get('triage_threshold');
    }

    /**
     * Nilai untuk ditampilkan di form konfigurasi. API key tidak ikut, hanya status tersimpan/tidak.
     */
    public static function getFormValues(): array
    {
        $values = [];
        foreach (array_keys(self::DEFAULTS) as $name) {
            if ($name !== self::API_KEY) {
                $values[$name] = self::get($name);
            }
        }
        $values['has_api_key'] = self::hasApiKey();
        return $values;
    }

    /**
     * Validasi & simpan input dari form konfigurasi.
     *
     * @return string[] Daftar pesan galat (kosong jika semua tersimpan)
     */
    public static function saveFromForm(array $input): array
    {
        $errors = [];
        $values = [];

        $provider = (string) ($input['ai_provider'] ?? '');
        if (array_key_exists($provider, self::getProviders())) {
            $values['ai_provider'] = $provider;
        }

        $base_url = trim((string) ($input['api_base_url'] ?? ''));
        if ($base_url === '' || preg_match('#^https?://[^\s]+$#i', $base_url) === 1) {
            $values['api_base_url'] = rtrim($base_url, '/');
        } else {
            $errors[] = __('API base URL must start with http:// or https://.', 'halosis');
        }

        $service_url = trim((string) ($input['service_url'] ?? ''));
        if ($service_url === '' || preg_match('#^https?://[^\s]+$#i', $service_url) === 1) {
            $values['service_url'] = rtrim($service_url, '/');
        } else {
            $errors[] = __('AI service URL must start with http:// or https://.', 'halosis');
        }
        $values['service_timeout'] = max(1, min(60, (int) ($input['service_timeout'] ?? self::DEFAULTS['service_timeout'])));

        $model = trim((string) ($input['ai_model'] ?? ''));
        $values['ai_model'] = $model !== '' ? $model : self::DEFAULTS['ai_model'];

        $values['ai_timeout']       = max(5, min(120, (int) ($input['ai_timeout'] ?? self::DEFAULTS['ai_timeout'])));
        $values['triage_threshold'] = max(0, min(100, (int) ($input['triage_threshold'] ?? self::DEFAULTS['triage_threshold'])));

        $values['pattern_min_tickets'] = max(2, min(500, (int) ($input['pattern_min_tickets'] ?? self::DEFAULTS['pattern_min_tickets'])));
        $values['pattern_window']      = max(15, min(1440, (int) ($input['pattern_window'] ?? self::DEFAULTS['pattern_window'])));
        $group_id = (int) ($input['pattern_group_id'] ?? 0);
        $values['pattern_group_id'] = $group_id > 0 && (new \Group())->getFromDB($group_id) ? $group_id : 0;

        foreach (self::FEATURES as $feature) {
            $values['feature_' . $feature] = (int) !empty($input['feature_' . $feature]);
        }

        // API key: kosong = tidak diubah; centang "hapus" = kosongkan (kembali ke mode demo)
        $api_key = trim((string) ($input[self::API_KEY] ?? ''));
        if (!empty($input['_clear_api_key'])) {
            $values[self::API_KEY] = '';
        } elseif ($api_key !== '') {
            $values[self::API_KEY] = $api_key; // dienkripsi oleh CoreConfig karena terdaftar di secured_configs
        }

        CoreConfig::setConfigurationValues(self::CONTEXT, $values);
        self::$values = null;

        return $errors;
    }

    /**
     * Isi nilai default untuk config yang belum ada (tidak menimpa nilai yang sudah diatur).
     */
    public static function install(): void
    {
        $existing = CoreConfig::getConfigurationValues(self::CONTEXT);
        $missing  = array_diff_key(self::DEFAULTS, $existing);
        if ($missing !== []) {
            CoreConfig::setConfigurationValues(self::CONTEXT, $missing);
        }
        self::$values = null;
    }

    public static function uninstall(): void
    {
        CoreConfig::deleteConfigurationValues(self::CONTEXT, array_keys(self::DEFAULTS));
        self::$values = null;
    }
}
