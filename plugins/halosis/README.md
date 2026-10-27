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

## Hak akses

Diatur di **Administrasi › Profil › (profil) › tab HaloSIS**. Default saat instalasi:

| Hak | Super-Admin | Hotliner (Operator) | Observer (Manajemen) |
| --- | --- | --- | --- |
| Konfigurasi HaloSIS | ✓ | | |
| Saran triase AI (lihat / putuskan) | ✓ / ✓ | ✓ / ✓ | |
| Dashboard kinerja AI | ✓ | | ✓ |

## Struktur

```
setup.php            versi, syarat GLPI 12.0.x, registrasi hook
hook.php             install/uninstall: tabel, config default, hak akses
src/Config.php       baca/simpan konfigurasi, API key terenkripsi, mode demo
src/Profile.php      hak akses plugin + tab di form Profil
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
