<?php

namespace GlpiPlugin\Halosis;

use Auth;
use Group;
use Group_User;
use Profile_User;
use Toolbox;
use User;

/**
 * Login SSO Keycloak dari form login HaloSIS sendiri (satu kali isi username & password).
 *
 * Password dikirim server GLPI ke Keycloak (Direct Access Grant / password grant); browser tidak pernah
 * diarahkan ke halaman login Keycloak. Bila Keycloak menerima, username hasil verifikasi diserahkan ke
 * jalur "external auth" GLPI (variabel SSO REMOTE_USER) khusus untuk request login ini, sehingga sesi,
 * log login, dan sinkron nama/email tetap ditangani inti GLPI. Sesi Keycloak langsung ditutup.
 *
 * Keycloak adalah sumber akun: setiap login, pengguna GLPI dibuat bila belum ada, lalu profilnya mengikuti
 * role realm (ROLE_PROFILES), timnya mengikuti grup Keycloak bernama sama dengan grup GLPI, dan role ketua-tim
 * menjadikannya supervisor tim. Semua ini dikerjakan sebelum GLPI memulai sesi, jadi langsung berlaku.
 *
 * Pengguna yang pernah login lewat Keycloak ditandai authtype "Other" (Auth::EXTERNAL) tanpa password lokal,
 * jadi tidak bisa lagi masuk dengan password GLPI. Akun lokal yang tidak ada di Keycloak (mis. Super-Admin
 * `glpi`) tetap login dengan password GLPI sebagai jalur darurat.
 *
 * Diaktifkan lewat environment container GLPI: HALOSIS_KEYCLOAK_URL, _REALM, _CLIENT_ID, _CLIENT_SECRET.
 */
final class KeycloakAuth
{
    /** Variabel SSO bawaan GLPI (tabel glpi_ssovariables) untuk menyerahkan username terverifikasi */
    private const SSO_VARIABLE = 'REMOTE_USER';

    /** Claim token → [kunci konfigurasi *_ssofield GLPI, variabel $_SERVER pembawa nilainya] */
    private const PROFILE_FIELDS = [
        'given_name'  => ['firstname_ssofield', 'HALOSIS_SSO_FIRSTNAME'],
        'family_name' => ['realname_ssofield', 'HALOSIS_SSO_REALNAME'],
        'email'       => ['email1_ssofield', 'HALOSIS_SSO_EMAIL'],
    ];

    /** Role realm Keycloak → profil GLPI, urut prioritas profil default (seed: satu pegawai = satu role) */
    private const ROLE_PROFILES = [
        'administrator'     => 'Administrator',
        'knowledge-manager' => 'Knowledge Manager',
        'manajemen'         => 'Manajemen',
        'operator'          => 'Operator',
        'tim-teknis'        => 'Tim Teknis',
        'pegawai'           => 'Pegawai',
    ];
    private const DEFAULT_ROLE = 'pegawai';

    /** Role realm Keycloak: supervisor di tim pengguna (penerima "atasan" peringatan risiko SLA, BR-02) */
    private const TEAM_LEADER_ROLE = 'ketua-tim';

    /** Claim ID token dari mapper client halosis-glpi (keycloak/halosis-realm.json) */
    private const ROLES_CLAIM  = 'halosis_roles';
    private const GROUPS_CLAIM = 'groups';

    private const TIMEOUT = 10;

    /** Username yang diverifikasi Keycloak pada request ini (null = bukan login Keycloak) */
    private static ?string $verified_login = null;

    /**
     * @return array{url: string, realm: string, client_id: string, client_secret: string}|null
     */
    private static function getSettings(): ?array
    {
        $settings = [
            'url'           => rtrim((string) getenv('HALOSIS_KEYCLOAK_URL'), '/'),
            'realm'         => (string) getenv('HALOSIS_KEYCLOAK_REALM'),
            'client_id'     => (string) getenv('HALOSIS_KEYCLOAK_CLIENT_ID'),
            'client_secret' => (string) getenv('HALOSIS_KEYCLOAK_CLIENT_SECRET'),
        ];
        return $settings['url'] !== '' && $settings['realm'] !== '' && $settings['client_id'] !== '' ? $settings : null;
    }

    public static function isEnabled(): bool
    {
        return self::getSettings() !== null;
    }

    /**
     * Dipanggil dari plugin_init (sebelum front/login.php dijalankan). Hanya bekerja pada POST form login.
     */
    public static function handleLoginRequest(): void
    {
        static $handled = false;
        if ($handled || !self::isLoginRequest() || ($settings = self::getSettings()) === null) {
            return;
        }
        $handled = true;

        $claims = self::verifyPassword($settings, trim((string) $_POST['login_name']), (string) $_POST['login_password']);
        if ($claims !== null) {
            self::prepareExternalLogin($claims);
        }
        // Ditolak/gagal: biarkan GLPI melanjutkan; hanya akun lokal (authtype GLPI) yang masih bisa lolos
    }

    private static function isLoginRequest(): bool
    {
        global $CFG_GLPI;

        if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST' || !isset($_SERVER['REQUEST_URI'])) {
            return false;
        }
        $path = (string) parse_url((string) $_SERVER['REQUEST_URI'], PHP_URL_PATH);
        if ($path !== ($CFG_GLPI['root_doc'] ?? '') . '/front/login.php') {
            return false;
        }
        // Langkah MFA atau form tidak lengkap: bukan urusan Keycloak. Field "auth" (dropdown Sumber login) diabaikan:
        // pilihannya hanya sumber GLPI dan nilainya selalu "local" bila dropdown tampil.
        if (isset($_POST['totp_code']) || isset($_SESSION['mfa_pre_auth'])) {
            return false;
        }
        if (!is_string($_POST['login_name'] ?? null) || !is_string($_POST['login_password'] ?? null)
            || trim($_POST['login_name']) === '' || $_POST['login_password'] === '') {
            return false;
        }
        return self::isSameOrigin();
    }

    /**
     * Cek CSRF yang sama dengan GLPI (CheckCsrfListener), tetapi lebih awal: plugin_init berjalan sebelum
     * pengecekan GLPI, dan POST lintas situs tidak boleh sampai memicu percobaan password ke Keycloak.
     */
    private static function isSameOrigin(): bool
    {
        $fetch_site = $_SERVER['HTTP_SEC_FETCH_SITE'] ?? null;
        if ($fetch_site !== null) {
            return in_array($fetch_site, ['same-origin', 'none'], true);
        }
        $origin = $_SERVER['HTTP_ORIGIN'] ?? null;
        $host   = $_SERVER['HTTP_HOST'] ?? null;
        if ($origin !== null && $host !== null) {
            $origin_host = (string) parse_url($origin, PHP_URL_HOST);
            $origin_port = parse_url($origin, PHP_URL_PORT);
            return (is_int($origin_port) ? "$origin_host:$origin_port" : $origin_host) === $host;
        }
        return true;
    }

    /**
     * Periksa username & password ke Keycloak, lalu tutup lagi sesi Keycloak-nya.
     *
     * @param array{url: string, realm: string, client_id: string, client_secret: string} $settings
     *
     * @return array<string, mixed>|null claim ID token, null bila ditolak atau Keycloak tidak bisa dihubungi
     */
    private static function verifyPassword(array $settings, string $login, string $password): ?array
    {
        $base   = $settings['url'] . '/realms/' . rawurlencode($settings['realm']) . '/protocol/openid-connect';
        $client = ['client_id' => $settings['client_id'], 'client_secret' => $settings['client_secret']];

        [$status, $tokens] = self::post($base . '/token', $client + [
            'grant_type' => 'password',
            'scope'      => 'openid',
            'username'   => $login,
            'password'   => $password,
        ]);
        if ($status === 0) {
            Toolbox::logInFile('halosis', "Keycloak tidak bisa dihubungi ({$settings['url']}); login SSO dilewati\n", true);
            return null;
        }
        if ($status !== 200 || !is_string($tokens['id_token'] ?? null)) {
            // 401 invalid_grant = password salah / akun nonaktif; selain itu kemungkinan salah konfigurasi
            if ($status !== 401) {
                Toolbox::logInFile('halosis', sprintf("Keycloak menolak login (HTTP %d, %s)\n", $status, $tokens['error'] ?? '-'), true);
            }
            return null;
        }

        if (is_string($tokens['refresh_token'] ?? null)) {
            self::post($base . '/logout', $client + ['refresh_token' => $tokens['refresh_token']]);
        }

        // ID token diterima langsung dari endpoint token Keycloak lewat kanal server-ke-server, jadi isinya
        // bisa dipakai tanpa verifikasi tanda tangan (OpenID Connect Core §3.1.3.7)
        $parts  = explode('.', $tokens['id_token']);
        $claims = json_decode((string) base64_decode(strtr($parts[1] ?? '', '-_', '+/')), true);
        if (!is_array($claims) || !is_string($claims['preferred_username'] ?? null) || $claims['preferred_username'] === '') {
            Toolbox::logInFile('halosis', "ID token Keycloak tanpa preferred_username; login SSO dilewati\n", true);
            return null;
        }
        return $claims;
    }

    /**
     * Hook init_session. GLPI mencatat glpi_remote_user untuk login external auth dan menganggap sesi kedaluwarsa
     * bila request berikutnya tidak membawa REMOTE_USER yang sama (SSO di web server). Keycloak di sini hanya
     * memeriksa password saat login, jadi penanda itu dilepas dan sesi berjalan seperti login biasa.
     */
    public static function onInitSession(): void
    {
        if (self::$verified_login !== null) {
            unset($_SESSION['glpi_remote_user']);
        }
    }

    /**
     * @param array<string, string> $form
     *
     * @return array{0: int, 1: array<string, mixed>} [status HTTP (0 = tidak terhubung), isi JSON]
     */
    private static function post(string $url, array $form): array
    {
        $context = stream_context_create(['http' => [
            'method'        => 'POST',
            'header'        => "Content-Type: application/x-www-form-urlencoded\r\nAccept: application/json\r\n",
            'content'       => http_build_query($form),
            'timeout'       => self::TIMEOUT,
            'ignore_errors' => true,
        ]]);
        $body = @file_get_contents($url, false, $context);
        if ($body === false) {
            return [0, []];
        }

        $status = 0;
        foreach ($http_response_header ?? [] as $header) {
            if (preg_match('#^HTTP/\S+\s+(\d{3})#', $header, $m)) {
                $status = (int) $m[1];
            }
        }
        $data = json_decode($body, true);
        return [$status, is_array($data) ? $data : []];
    }

    /**
     * Serahkan pengguna terverifikasi ke jalur external auth GLPI. Semua perubahan konfigurasi hanya berlaku
     * di memori untuk request ini; konfigurasi GLPI di database tidak berubah.
     *
     * @param array<string, mixed> $claims
     */
    private static function prepareExternalLogin(array $claims): void
    {
        global $CFG_GLPI, $DB;

        $variable = $DB->request([
            'SELECT' => 'id',
            'FROM'   => 'glpi_ssovariables',
            'WHERE'  => ['name' => self::SSO_VARIABLE],
        ])->current();
        if ($variable === null) {
            Toolbox::logInFile('halosis', 'Variabel SSO ' . self::SSO_VARIABLE . " tidak ada di glpi_ssovariables\n", true);
            return;
        }

        $login = $claims['preferred_username'];
        self::$verified_login = $login;
        $CFG_GLPI['ssovariables_id'] = $variable['id'];
        $CFG_GLPI['existing_auth_server_field_clean_domain'] = 0;
        $_SERVER[self::SSO_VARIABLE] = $login;
        foreach (self::PROFILE_FIELDS as $claim => [$config_key, $server_key]) {
            if (is_string($claims[$claim] ?? null) && $claims[$claim] !== '') {
                $CFG_GLPI[$config_key] = $server_key;
                $_SERVER[$server_key]  = $claims[$claim];
            }
        }

        // Form login selalu mengirim noAUTO ("0", atau "1" setelah logout) dan GLPI menganggap keberadaannya saja
        // = lewati SSO. noAUTO mencegah login otomatis REMOTE_USER setelah logout; di sini pengguna sendiri yang
        // mengetik password dan Keycloak sudah menerimanya, jadi penanda itu tidak berlaku.
        unset($_POST['noAUTO'], $_GET['noAUTO'], $_REQUEST['noAUTO']);

        $user = self::provisionUser($claims);
        if ($user !== null) {
            self::syncProfiles($user, self::getClaimList($claims, self::ROLES_CLAIM));
            self::syncTeams($user, self::getClaimList($claims, self::GROUPS_CLAIM), in_array(self::TEAM_LEADER_ROLE, self::getClaimList($claims, self::ROLES_CLAIM), true));
        }
    }

    /**
     * @param array<string, mixed> $claims
     *
     * @return array<int, string>
     */
    private static function getClaimList(array $claims, string $name): array
    {
        $values = is_array($claims[$name] ?? null) ? $claims[$name] : [];
        // Nama grup bisa berupa path ("/Tim Jaringan") bila mapper Keycloak memakai full path
        return array_values(array_map(static fn ($v) => ltrim($v, '/'), array_filter($values, 'is_string')));
    }

    /**
     * Pengguna GLPI untuk akun Keycloak: dibuat bila belum ada (sebelum login GLPI, agar profil & tim sudah
     * terpasang saat sesi dimulai). Akun lokal yang sekarang dikelola Keycloak kehilangan password GLPI-nya.
     *
     * @param array<string, mixed> $claims
     */
    private static function provisionUser(array $claims): ?User
    {
        global $DB;

        $login = $claims['preferred_username'];
        $user  = new User();
        if (!$user->getFromDBbyName($login)) {
            $input = ['name' => $login, 'authtype' => Auth::EXTERNAL, 'is_active' => 1, '_extauth' => 1];
            foreach (['given_name' => 'firstname', 'family_name' => 'realname'] as $claim => $field) {
                if (is_string($claims[$claim] ?? null)) {
                    $input[$field] = $claims[$claim];
                }
            }
            if (is_string($claims['email'] ?? null) && $claims['email'] !== '') {
                $input['_useremails'] = ['-1' => $claims['email']];
            }
            if (!$user->add($input)) {
                Toolbox::logInFile('halosis', "Gagal membuat pengguna GLPI untuk akun Keycloak {$login}\n", true);
                return null;
            }
            return $user;
        }

        if ((int) $user->fields['authtype'] === Auth::DB_GLPI) {
            $DB->update(User::getTable(), [
                'authtype' => Auth::EXTERNAL,
                'auths_id' => 0,
                'password' => '',
            ], ['id' => $user->getID()]);
        }
        return $user;
    }

    /**
     * Profil HaloSIS mengikuti role Keycloak. Profil di luar ROLE_PROFILES (mis. Super-Admin yang diberi manual)
     * tidak disentuh. Tanpa role HaloSIS sama sekali → Pegawai.
     *
     * @param array<int, string> $roles
     */
    private static function syncProfiles(User $user, array $roles): void
    {
        global $DB;

        $profiles = [];
        foreach ($DB->request(['SELECT' => ['id', 'name'], 'FROM' => \Profile::getTable(), 'WHERE' => ['name' => array_values(self::ROLE_PROFILES)]]) as $row) {
            $profiles[$row['name']] = (int) $row['id'];
        }
        $wanted = [];
        foreach (self::ROLE_PROFILES as $role => $profile_name) {
            if (in_array($role, $roles, true) && isset($profiles[$profile_name])) {
                $wanted[] = $profiles[$profile_name];
            }
        }
        if ($wanted === [] && isset($profiles[self::ROLE_PROFILES[self::DEFAULT_ROLE]])) {
            $wanted[] = $profiles[self::ROLE_PROFILES[self::DEFAULT_ROLE]];
        }
        if ($wanted === []) {
            Toolbox::logInFile('halosis', "Profil HaloSIS tidak ditemukan di GLPI; profil {$user->fields['name']} tidak disinkronkan\n", true);
            return;
        }

        $link = new Profile_User();
        $current = [];
        foreach ($link->find(['users_id' => $user->getID(), 'profiles_id' => array_values($profiles)]) as $row) {
            if (in_array((int) $row['profiles_id'], $wanted, true) && !isset($current[$row['profiles_id']])) {
                $current[$row['profiles_id']] = true;
            } else {
                $link->delete(['id' => $row['id']], true);
            }
        }
        foreach ($wanted as $profiles_id) {
            if (!isset($current[$profiles_id])) {
                $link->add(['users_id' => $user->getID(), 'profiles_id' => $profiles_id, 'entities_id' => 0, 'is_recursive' => 1]);
            }
        }

        // Profil default = role HaloSIS dengan prioritas tertinggi (menentukan antarmuka setelah login)
        $DB->update(User::getTable(), ['profiles_id' => $wanted[0]], ['id' => $user->getID()]);
    }

    /**
     * Keanggotaan tim (grup GLPI) mengikuti grup Keycloak bernama sama; role ketua-tim = supervisor di timnya.
     *
     * @param array<int, string> $teams
     */
    private static function syncTeams(User $user, array $teams, bool $is_leader): void
    {
        global $DB;

        $groups = [];
        if ($teams !== []) {
            foreach ($DB->request(['SELECT' => ['id', 'name'], 'FROM' => Group::getTable(), 'WHERE' => ['name' => $teams]]) as $row) {
                $groups[(int) $row['id']] = $row['name'];
            }
        }
        $unknown = array_diff($teams, $groups);
        if ($unknown !== []) {
            Toolbox::logInFile('halosis', sprintf("Grup Keycloak %s milik %s tidak ada di GLPI; dilewati\n", implode(', ', $unknown), $user->fields['name']), true);
        }

        $link = new Group_User();
        $current = [];
        foreach ($link->find(['users_id' => $user->getID()]) as $row) {
            if (!isset($groups[$row['groups_id']]) || isset($current[$row['groups_id']])) {
                $link->delete(['id' => $row['id']], true);
                continue;
            }
            $current[$row['groups_id']] = true;
            if ((bool) $row['is_manager'] !== $is_leader) {
                $link->update(['id' => $row['id'], 'is_manager' => (int) $is_leader]);
            }
        }
        foreach (array_keys($groups) as $groups_id) {
            if (!isset($current[$groups_id])) {
                $link->add(['users_id' => $user->getID(), 'groups_id' => $groups_id, 'is_manager' => (int) $is_leader]);
            }
        }
    }
}
