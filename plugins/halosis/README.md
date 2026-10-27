# Plugin HaloSIS untuk GLPI 12

Modul AI untuk layanan TI BPS dengan prinsip *human-in-the-loop*: AI memberi saran, petugas yang memutuskan.

> Status: konfigurasi, role, saran triase AI (Fase 4), dan chatbot self-service (Fase 5) sudah jalan.
> Deteksi pola insiden dan dashboard menyusul.

## Instalasi

Folder ini di-mount ke `/var/www/glpi/plugins/halosis` lewat `docker-compose.yml`. Lalu:

```bash
docker compose exec glpi php bin/console plugin:install halosis -u glpi --allow-superuser
docker compose exec glpi php bin/console plugin:activate halosis --allow-superuser
```

**SDK Anthropic** (hanya perlu untuk memanggil Claude sungguhan; mode demo jalan tanpanya).
Dipasang dengan Composer ke `vendor/` (tidak di-commit). Dari folder plugin:

```bash
docker run --rm -u "$(id -u):$(id -g)" -v "$PWD":/app -w /app composer:2 install --no-dev
```

`composer.json` me-*replace* Guzzle & paket PSR HTTP karena sudah disediakan GLPI, jadi `vendor/` hanya
berisi SDK dan dependensi yang belum ada di GLPI. SDK baru dimuat saat API key terisi.

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

## Saran triase AI (human-in-the-loop)

1. **Tiket baru disimpan** (hook `item_add` Ticket, dari antarmuka mana pun termasuk REST API) →
   plugin membuat saran: kategori ITIL, dampak, urgensi, prioritas, grup tujuan, keyakinan 0–100,
   penjelasan singkat, versi model. Disimpan di `glpi_plugin_halosis_suggestions`, **bukan** di field tiket.
   - Claude dipanggil dengan *structured output* (JSON schema); ID kategori & grup dibatasi ke daftar yang
     valid untuk entitas & tipe tiket, lalu divalidasi ulang di server. Prioritas dihitung dari matriks GLPI.
   - Mode demo: aturan kata kunci (`Triage::DEMO_KEYWORDS`), isi tiket sama → saran sama.
   - **AI gagal/timeout → tiket tetap tersimpan normal tanpa saran.** Tidak ada coba ulang, jadi waktu tunggu
     maksimal = batas waktu di konfigurasi. Penyebab dicatat di log GLPI `halosis.log`
     (di Docker: `/var/glpi/logs/halosis.log`). Petugas bisa menekan **Buat saran AI** di panel.
2. **Panel "Saran AI"** tampil di atas panel isian tiket untuk pemegang hak `plugin_halosis_triase`
   (lihat). Isinya meter keyakinan dengan garis ambang, nilai saran, penjelasan, dan model.
   Keyakinan di bawah ambang → tanda **Perlu penilaian manual**.
3. **Keputusan** (butuh hak triase *putuskan* + hak ubah tiket di GLPI):
   - **Terima** → semua nilai saran diterapkan ke tiket.
   - **Ubah** → form nilai final + **alasan wajib** (min. 5 karakter) → nilai final diterapkan.
     Tanpa hak GLPI "Ubah prioritas", prioritas mengikuti matriks urgensi × dampak.
   - **Tolak** → field tiket tidak diubah, triase manual + **alasan wajib**.
   Nilai diterapkan lewat update tiket GLPI biasa, jadi hak akses, aturan bisnis, notifikasi, dan riwayat
   field tetap berjalan. Alasan divalidasi di server, bukan hanya di browser.
4. **Pencatatan**: setiap keputusan masuk `glpi_plugin_halosis_decisions` (aktor, waktu, nilai saran vs
   final dalam JSON, alasan) **dan** tab **Riwayat** tiket (baris "HaloSIS: Saran AI diterima/diubah/ditolak…").

Pemanggilan Claude: SDK resmi `anthropic-ai/sdk`, endpoint beta Messages, `outputConfig.effort = low`
(klasifikasi), dan *server-side fallback* `fallbacks: "default"` untuk model yang mendukungnya
(`claude-opus-5-5`, `claude-opus-5`, `claude-fable-5-1`, `claude-sonnet-5-5`) bila memakai API Claude langsung.
Proxy GLPI (**Setup › Umum › Proxy**) ikut dipakai.

## Chatbot self-service pegawai (beranda "Tanya HaloSIS")

Alur *resolution-first*: Pegawai login → langsung di halaman penuh **Tanya HaloSIS**
(`/plugins/halosis/Chat`, controller `src/Controller/ChatController.php`, dirender di layout Helpdesk GLPI).
Berlaku untuk antarmuka Helpdesk + hak `plugin_halosis_chatbot` (default: Pegawai) + fitur chat aktif.

- **Halaman penuh**: percakapan memenuhi layar, input di bawah, saran pertanyaan cepat, tautan sekunder
  "Langsung buat laporan" (ke Service catalog) di kanan atas. Responsif sampai lebar HP 390px.
- **Menu Helpdesk** (hook `redefine_menus`): Tanya HaloSIS · Laporan saya · Buat laporan · Pusat bantuan (FAQ),
  lalu menu lain. Beranda Helpdesk lama disembunyikan. Menu antarmuka standar tidak diubah.
- **Beranda**: setelah login GLPI selalu membuka `/Helpdesk`; plugin menambahkan
  `<meta http-equiv="refresh">` (hook `add_header_tag`) **hanya** pada `GET /Helpdesk` untuk pengguna yang
  memenuhi syarat, sehingga diarahkan ke halaman chat. Operator & profil standar tidak terpengaruh;
  halaman chat ada di path lain sehingga tidak ada loop. GLPI 12 belum punya hook server-side untuk
  mengalihkan `/Helpdesk`: `RedirectException` dari `plugin_init` (saat kernel boot) maupun dari
  `redefine_menus` (di dalam render Twig) sudah dicoba dan berakhir HTTP 500.
- **Widget melayang** tetap ada di halaman Helpdesk lain (mis. detail tiket, FAQ) dengan tombol
  "buka layar penuh", tapi tidak dimuat di halaman chat. Percakapan yang sama berlanjut antara halaman
  penuh dan widget (ID di `sessionStorage`).
- **Asisten tidak tersedia** (fitur chat dimatikan): halaman menampilkan pesan + tombol "Buat laporan" yang
  menonjol. Jawaban "belum menemukan" dan galat jaringan juga menampilkan tombol "Buat laporan".
- Logika percakapan satu untuk keduanya: `Chatbot` (server), `ajax/chat.php` (endpoint),
  `templates/chat_conversation.html.twig` (isi percakapan), `public/js/chat.js` (fungsi `mount`).

- **Sumber jawaban hanya Knowledge Base yang terlihat oleh pengguna.** `KnowledgeSearch` memakai kriteria
  visibilitas GLPI (`KnowbaseItem::getVisibilityCriteria()`; di Helpdesk = FAQ yang boleh dilihat), lalu tiap
  artikel dicek ulang dengan `canViewItem()`. Artikel internal (bukan FAQ) tidak pernah dipakai.
  Peringkat: kata kunci di judul (bobot 3) dan isi (bobot 1), minimal skor 3.
- **Tidak ada artikel relevan** → "Maaf, saya belum menemukan jawabannya…". Pertanyaan pendek (≤ 2 kata kunci,
  mis. "masih gagal") dianggap lanjutan pertanyaan sebelumnya.
- **Dengan API key**: Claude merangkum *hanya* dari artikel yang ditemukan (structured output; `article_ids`
  dibatasi ke artikel tersebut). Tautan sumber dibuat server dari artikel yang ditemukan, bukan dari teks model.
  **Mode demo / AI gagal**: kutipan langkah dari artikel teratas.
- **Data pribadi**: widget menampilkan peringatan; di server, pola kata sandi (`password: …`), email, nomor HP,
  dan NIK/NIP disamarkan (`Privacy::mask`) **sebelum** dikirim ke AI maupun disimpan di transkrip.
- **Masalah terselesaikan** → rating 1–5, percakapan ditutup (status `resolved`).
- **Buat laporan** → tiket baru atas nama pegawai, memakai sesi & hak GLPI pengguna (butuh hak membuat tiket);
  judul bisa diedit, deskripsi = ringkasan percakapan. Tiket ini otomatis mendapat saran triase AI.
- Percakapan disimpan di `glpi_plugin_halosis_chats` dan hanya bisa dibaca/dilanjutkan pemiliknya;
  widget melanjutkan percakapan saat pegawai berpindah halaman.

Tampilan mengikuti prototipe `halosis-web` (komponen ChatRoom): gelembung dengan label "Dijawab AI" (atau
"Dari Pusat Bantuan" untuk kutipan mode demo), langkah bernomor, chip sumber, aksi "Apakah jawaban ini
membantu?", kartu "buat laporan" bergaris putus-putus, dan kotak input dengan saran pertanyaan.

Aset CSS/JS plugin diberi penanda waktu ubah file (`plugin_halosis_asset()` di `setup.php`), karena GLPI
hanya memberi versi aset berdasarkan versi plugin; tanpa ini perubahan tampilan tertahan di cache browser.

Catatan teknis: GLPI hanya membawa hak profil Helpdesk yang terdaftar di `Profile::$helpdesk_rights`
ke sesi, jadi plugin mendaftarkan `plugin_halosis_chatbot` di sana (`setup.php`).

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
src/Triage.php       saran triase (AI & demo) + keputusan Terima/Ubah/Tolak
src/TriagePanel.php  panel "Saran AI" di form tiket
src/Suggestion.php   model tabel saran;  src/Decision.php  model log keputusan
src/Ai/Client.php    pemanggil AI di server (SDK Anthropic / API kompatibel OpenAI)
ajax/triase.php      aksi panel (JSON)
public/js/triase.js  interaksi panel
composer.json        SDK Anthropic (vendor/ tidak di-commit)
src/Chatbot.php      jawaban chatbot, rating, buat laporan
src/HelpdeskHome.php menu Helpdesk & pengalihan beranda ke halaman chat
src/Controller/ChatController.php  halaman penuh /plugins/halosis/Chat
src/KnowledgeSearch.php  pencarian KB yang menghormati visibilitas GLPI
src/Privacy.php      penyamaran data pribadi;  src/Chat.php  model percakapan
ajax/chat.php        endpoint widget;  public/js/chat.js  widget chat
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
| `glpi_plugin_halosis_chats` | Percakapan chatbot: pemilik, transkrip (tersamarkan), status open/resolved/ticket, rating, tiket |
