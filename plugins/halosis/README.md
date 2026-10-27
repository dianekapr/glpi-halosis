# Plugin HaloSIS untuk GLPI 12

Modul AI untuk layanan TI BPS dengan prinsip *human-in-the-loop*: AI memberi saran, petugas yang memutuskan.

> Status: kerangka plugin + halaman konfigurasi (Fase 3). Fitur AI menyusul per fase.

## Instalasi

Folder ini di-mount ke `/var/www/glpi/plugins/halosis` lewat `docker-compose.yml`. Lalu:

```bash
docker compose exec glpi php bin/console plugin:install halosis -u glpi --allow-superuser
docker compose exec glpi php bin/console plugin:activate halosis --allow-superuser
```

Atau lewat UI: **Setup › Plugins** → HaloSIS → Install → Aktifkan.

Uninstall (`plugin:uninstall halosis`) menghapus semua tabel, konfigurasi, dan hak akses plugin.

## Konfigurasi

**Setup › Plugins › HaloSIS** (ikon kunci pas), atau langsung `/plugins/halosis/front/config.form.php`.
Halaman ini termasuk area sensitif: GLPI meminta konfirmasi password sebelum membukanya.

| Pengaturan | Default | Keterangan |
| --- | --- | --- |
| Penyedia AI | Anthropic (Claude) | Atau API kompatibel OpenAI |
| API key | kosong | Disimpan terenkripsi dengan kunci GLPI (`glpicrypt.key`); tidak pernah dikirim ke browser |
| Model | `claude-opus-5-5` | ID model di penyedia |
| URL dasar API | kosong | Opsional, untuk gateway/proxy |
| Batas waktu | 20 detik | Jika terlewati, tiket tetap tersimpan tanpa saran |
| Ambang keyakinan | 70% | Di bawah ambang → "Perlu penilaian manual" |
| Fitur AI | semua aktif | Saran triase, chatbot, deteksi pola, dashboard |

**Mode demo:** jika API key kosong, semua fitur memakai jawaban contoh yang deterministik,
sehingga bisa didemokan tanpa internet.

## Role & hak akses

Role HaloSIS diterapkan ke profil GLPI dengan perintah yang aman dijalankan berulang:

```bash
docker compose exec glpi php bin/console plugins:halosis:setup-roles --allow-superuser
```

Perintah ini mengganti nama profil bawaan (berdasarkan ID, jadi pengguna yang terhubung tidak terpengaruh),
membuat profil Knowledge Manager, memastikan Manajemen hanya-baca, menerapkan hak plugin, dan menonaktifkan
akun bawaan `tech`, `normal`, `post-only`. Definisinya ada di `src/Roles.php`.

| ID | Profil GLPI asal | Role HaloSIS | Antarmuka |
| --- | --- | --- | --- |
| 1 | Self-Service | Pegawai | Helpdesk |
| 2 | Observer | Manajemen | Standar (hanya-baca) |
| 3 | Admin | Administrator | Standar |
| 4 | Super-Admin | Super-Admin (pengelola sistem) | Standar |
| 5 | Hotliner | Operator | Standar |
| 6 | Technician | Tim Teknis | Standar |
| baru | — | Knowledge Manager | Standar |

Hak plugin (bisa diubah di **Administrasi › Profil › (profil) › tab HaloSIS**). Semua pengecekan akses di
plugin memakai hak ini (`Session::haveRight`), tidak pernah nama profil.

| Hak | Nilai | Default |
| --- | --- | --- |
| `plugin_halosis_triase` | lihat (READ), putuskan (UPDATE) | Operator, Administrator, Super-Admin: lihat & putuskan; Tim Teknis: lihat |
| `plugin_halosis_chatbot` | pakai (READ) | Pegawai |
| `plugin_halosis_dashboard` | lihat (READ) | Manajemen, Administrator, Super-Admin |
| `plugin_halosis_config` | ubah (UPDATE) | Administrator, Super-Admin |

Saat plugin di-install, hak baru otomatis mendapat nilai default di atas; hak yang sudah ada tidak diubah.
Halaman konfigurasi juga muncul di menu **Setup › AI HaloSIS** bagi pemegang `plugin_halosis_config`.

## Struktur

```
setup.php            versi, syarat GLPI 12.0.x, registrasi hook
hook.php             install/uninstall: tabel, config default, hak akses
src/Config.php       baca/simpan konfigurasi, API key terenkripsi, mode demo
src/Profile.php      hak akses plugin + tab di form Profil
src/Roles.php        pemetaan 6 role HaloSIS ke profil GLPI
src/ConfigMenu.php   menu Setup › AI HaloSIS
src/Console/         perintah plugins:halosis:setup-roles
front/config.form.php  halaman konfigurasi
templates/           template Twig (@halosis/...)
public/css, public/js  aset, disajikan di /plugins/halosis/css|js/...
locales/id_ID.po     terjemahan; kompilasi: python3 tools/locales.py
```

Teks di kode memakai msgid bahasa Inggris (konvensi GLPI) dengan terjemahan `id_ID`.
Setelah menambah teks UI, jalankan `python3 tools/locales.py`: skrip ini menampilkan string
yang belum diterjemahkan lalu mengompilasi `.mo`.

## Tabel

| Tabel | Isi |
| --- | --- |
| `glpi_plugin_halosis_suggestions` | Saran triase AI per tiket (kategori, dampak, urgensi, prioritas, grup, keyakinan, penjelasan, model, status) |
| `glpi_plugin_halosis_decisions` | Log keputusan petugas: aktor, waktu, nilai saran vs final, alasan |
