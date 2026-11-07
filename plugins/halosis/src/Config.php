<?php

namespace GlpiPlugin\Halosis;

use Config as CoreConfig;
use GLPIKey;
use GlpiPlugin\Halosis\Ai\AiException;
use GlpiPlugin\Halosis\Ai\Service;
use Toolbox;

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

    public const FEATURES = ['triage', 'chat', 'pattern', 'dashboard', 'menu'];

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
        // Ambang bawah (TO-BE hal. 100): di bawahnya penilaian manual; antara keduanya pilih dari 3 kandidat
        'ai_threshold_low' => 40,
        // Deteksi pola insiden: minimal N tiket mirip dalam jendela waktu (menit); 0 = grup Operator bawaan
        'pattern_min_tickets' => 3, // PoC hal. 56: minimum 3 incident
        'pattern_window'      => 60,
        'pattern_group_id'    => 0,
        // Metode semantik di /pola: average (rakus rata-rata kemiripan, bawaan) atau dbscan (PoC hal. 56)
        'pattern_method'      => 'average',
        'pattern_threshold'   => '0.50',
        'pattern_eps'         => '0.50',
        'pattern_min_samples' => 3,
        // FR-04: permintaan layanan (REQ) ikut dikelompokkan menjadi pola; bawaan mati (PoC hal. 56: pola dari INC)
        'pattern_include_requests' => 0,
        // Sinyal dampak saran triase: kategori layanan yang namanya memuat salah satu kata ini → dampak naik 1 tingkat
        'critical_services'   => 'SSO, Email, Jaringan',
        // Jabatan pejabat (awal kata, wawancara PM & operator): pemohon dimasukkan ke grup OFFICIAL_GROUP saat login SSO
        // → RuleTicket (setup_pejabat_rules.py) & saran triase menaikkan urgensi satu tingkat
        'official_titles'     => 'Kepala, Direktur, Deputi, Sekretaris Utama',
        // Artikel terbit yang tidak diubah selama N bulan masuk tab "Perlu ditinjau" (tinjau berkala, hal. 139)
        'kb_review_months'    => 6,
        // T21: tiket Selesai tanpa respons pemohon lebih dari N jam masuk daftar "Siap ditutup"
        'close_after_hours'   => 48,
        // E19: tiket Diproses/Menunggu tanpa tindak lanjut lebih dari N hari kerja → pengingat progres ke teknisi & grup
        'progress_reminder_days' => 5,
        'feature_triage'    => 1,
        'feature_chat'      => 1,
        'feature_pattern'   => 1,
        'feature_dashboard' => 1,
        // Sidebar petugas ringkas per peran (RoleMenu); 0 = menu GLPI lengkap
        'feature_menu'      => 1,
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
            'menu'      => __('Compact menu per HaloSIS role (off = full GLPI menu)', 'halosis'),
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
     * Pilihan metode deteksi pola semantik untuk form.
     *
     * @return array<string, string>
     */
    public static function getPatternMethods(): array
    {
        return [
            'average' => __('Average similarity (default)', 'halosis'),
            'dbscan'  => __('DBSCAN (as in the PoC)', 'halosis'),
        ];
    }

    /** Entitas arsip migrasi history (ai/scripts/migrate_sample.py): bukan tiket operasional */
    public const ARCHIVE_ENTITY = 'Arsip ESTIM';

    /**
     * ID entitas arsip beserta sub-entitasnya; tugas terjadwal plugin tidak menyentuh tiket di sini.
     *
     * @return int[]
     */
    public static function getArchiveEntityIds(): array
    {
        $entity = new \Entity();
        if (!$entity->getFromDBByCrit(['name' => self::ARCHIVE_ENTITY])) {
            return [];
        }
        return array_map('intval', array_values(getSonsOf(\Entity::getTable(), $entity->getID())));
    }

    /**
     * Kata kunci kategori layanan kritis (sinyal dampak saran triase), mis. ["SSO", "Email", "Jaringan"].
     *
     * @return string[]
     */
    public static function getCriticalServices(): array
    {
        return self::parseList((string) self::get('critical_services'));
    }

    /** Grup GLPI pemohon pejabat (dibuat setup_pejabat_rules.py, keanggotaan dari jabatan Keycloak) */
    public const OFFICIAL_GROUP = 'Pejabat';

    /**
     * Kata jabatan pejabat yang cocok dengan awal jabatan (tanpa beda huruf besar), mis. "Kepala" untuk
     * "Kepala BPS Kabupaten …"; null bila bukan pejabat.
     */
    public static function matchOfficialTitle(?string $title): ?string
    {
        $title = trim((string) $title);
        foreach (self::parseList((string) self::get('official_titles')) as $word) {
            if ($title !== '' && preg_match('/^' . preg_quote($word, '/') . '\\b/iu', $title)) {
                return $word;
            }
        }
        return null;
    }

    /**
     * "a, b ,, c" → ["a", "b", "c"] (unik, maks. 20 butir, masing-masing maks. 60 karakter).
     *
     * @return string[]
     */
    private static function parseList(string $value): array
    {
        $items = array_filter(array_map(static fn ($v) => mb_substr(trim($v), 0, 60), explode(',', $value)), 'strlen');
        return array_slice(array_values(array_unique($items)), 0, 20);
    }

    /**
     * Gerbang pada nilai aktif (tata_kelola_ai.md §2) → pesan peringatan; pola tidak pernah memblokir.
     *
     * @return string[]
     */
    public static function gateWarnings(): array
    {
        if (!Service::isConfigured()) {
            return [];
        }
        try {
            $gates = Service::post('/gerbang', [
                'ambang_triase' => self::getTriageThreshold() / 100,
                'ambang'        => (float) self::get('pattern_threshold'),
                'min_anggota'   => max(2, (int) self::get('pattern_min_tickets')),
                'jendela_menit' => max(15, (int) self::get('pattern_window')),
                'metode'        => self::get('pattern_method') === 'dbscan' ? 'dbscan' : 'rata',
                'eps'           => (float) self::get('pattern_eps'),
                'min_sampel'    => (int) self::get('pattern_min_samples'),
            ]);
        } catch (AiException $e) {
            Toolbox::logInFile('halosis', 'Pemeriksaan gerbang AI gagal: ' . $e->getMessage() . "\n", true);
            return [__('The AI quality gates could not be checked.', 'halosis')];
        }
        Toolbox::logInFile('halosis', 'Gerbang AI: ' . json_encode($gates, JSON_UNESCAPED_UNICODE) . "\n", true);

        $warnings = [];
        foreach (['triase' => __('Triage gate at the active threshold: %s', 'halosis'), 'pola' => __('Pattern gate (warning only): %s', 'halosis')] as $gate => $message) {
            if (($gates[$gate]['lolos'] ?? false) !== true) {
                $warnings[] = sprintf($message, implode('; ', (array) ($gates[$gate]['alasan'] ?? [])));
            }
        }
        return $warnings;
    }

    public static function getLowThreshold(): int
    {
        return min((int) self::get('ai_threshold_low'), self::getTriageThreshold());
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
        $values['ai_threshold_low'] = max(0, min($values['triage_threshold'], (int) ($input['ai_threshold_low'] ?? self::DEFAULTS['ai_threshold_low'])));

        $values['pattern_min_tickets'] = max(2, min(500, (int) ($input['pattern_min_tickets'] ?? self::DEFAULTS['pattern_min_tickets'])));
        $values['pattern_window']      = max(15, min(1440, (int) ($input['pattern_window'] ?? self::DEFAULTS['pattern_window'])));
        $group_id = (int) ($input['pattern_group_id'] ?? 0);
        $values['pattern_group_id'] = $group_id > 0 && (new \Group())->getFromDB($group_id) ? $group_id : 0;
        $values['pattern_method'] = in_array($input['pattern_method'] ?? '', ['average', 'dbscan'], true) ? $input['pattern_method'] : 'average';
        $values['pattern_threshold'] = number_format(max(0.05, min(0.95, (float) str_replace(',', '.', (string) ($input['pattern_threshold'] ?? self::DEFAULTS['pattern_threshold'])))), 2, '.', '');
        $values['pattern_eps'] = number_format(max(0.05, min(1.5, (float) str_replace(',', '.', (string) ($input['pattern_eps'] ?? self::DEFAULTS['pattern_eps'])))), 2, '.', '');
        $values['pattern_min_samples'] = max(2, min(50, (int) ($input['pattern_min_samples'] ?? self::DEFAULTS['pattern_min_samples'])));
        $values['pattern_include_requests'] = (int) !empty($input['pattern_include_requests']);
        $values['critical_services'] = implode(', ', self::parseList((string) ($input['critical_services'] ?? '')));
        $values['official_titles'] = implode(', ', self::parseList((string) ($input['official_titles'] ?? '')));
        $values['close_after_hours'] = max(1, min(720, (int) ($input['close_after_hours'] ?? self::DEFAULTS['close_after_hours'])));
        $values['progress_reminder_days'] = max(1, min(60, (int) ($input['progress_reminder_days'] ?? self::DEFAULTS['progress_reminder_days'])));
        $values['kb_review_months'] = max(1, min(36, (int) ($input['kb_review_months'] ?? self::DEFAULTS['kb_review_months'])));

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

        $before = CoreConfig::getConfigurationValues(self::CONTEXT, array_keys($values));
        CoreConfig::setConfigurationValues(self::CONTEXT, $values);
        self::$values = null;
        ConfigAudit::onConfigSaved($before, $values);

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
