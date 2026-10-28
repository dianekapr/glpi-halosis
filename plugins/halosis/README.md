# Plugin HaloSIS untuk GLPI 12

Modul AI untuk layanan TI BPS di atas GLPI, dengan prinsip *human-in-the-loop*: **AI memberi saran,
petugas yang memutuskan**. Semua kustomisasi lewat plugin dan palet tema; kode inti GLPI tidak diubah.

| Fitur | Siapa | Di mana |
| --- | --- | --- |
| **Tanya HaloSIS**: chatbot self-service yang menjawab hanya dari artikel Pusat Bantuan | Pegawai | Beranda Helpdesk (`/plugins/halosis/Chat`) |
| **Saran triase AI**: kategori, dampak, urgensi, prioritas, grup, keyakinan; Terima / Ubah / Tolak; Kembalikan ke operator (salah tim) | Operator (putuskan), Tim Teknis (lihat, kembalikan) | Panel "Saran AI" di form tiket |
| **Deteksi pola insiden**: tiket mirip ≥ N dalam 1 jam → Problem "Pola insiden: …" | Operator | Tugas terjadwal + banner beranda |
| **Kandidat Knowledge** (UC-09): solusi tiket selesai & solusi berulang dari indeks AI → Jadikan artikel (draf KB) / Abaikan (dengan alasan) | Knowledge Manager, Administrator, Super-Admin | Menu Kandidat knowledge (`/plugins/halosis/Kandidat`) |
| **Dashboard kinerja AI**: % diterima/diubah/ditolak, tren mingguan, salah tim, chat terbantu | Manajemen, Administrator, Super-Admin | Bantuan › Kinerja AI |
| **Konfigurasi**: penyedia AI, API key terenkripsi, ambang, toggle fitur | Administrator, Super-Admin | Setup › AI HaloSIS |

Versi 0.5.0 · GLPI 12.0.x · PHP 8.3–8.5 (syarat GLPI 12: `GLPI_MIN_PHP` 8.3, `GLPI_MAX_PHP` 8.5).
Tanpa API berbayar: AI berjalan di layanan lokal `halosis-ai`. Bila layanan itu mati dan tidak ada API key,
semua fitur berjalan dalam **mode demo** (jawaban contoh yang deterministik, tanpa internet).

## Akun demo

Password semua akun contoh: `halosis` (kecuali `glpi`). Akun dibuat oleh `seed_halosis.py` di folder induk.

| Login | Role HaloSIS | Antarmuka | Dipakai untuk |
| --- | --- | --- | --- |
| `budi`, `siti`, `maya` | Pegawai | Helpdesk | Tanya HaloSIS, buat laporan, approve solusi |
| `rina` | Operator | Standar | Validasi saran AI, banner pola insiden |
| `andi`, `yoga` | Tim Teknis (Aplikasi Statistik) | Standar | Menyelesaikan tiket; panel AI hanya-baca, *Kembalikan ke operator* bila salah tim |
| `fajar` / `dedi` | Tim Teknis (Identitas & Akses / Jaringan) | Standar | |
| `hendra` | Ketua Tim Aplikasi Statistik (Tim Teknis, supervisor grup) | Standar | Penerima "atasan" peringatan risiko SLA |
| `agus` | Ketua Tim Jaringan (Tim Teknis, supervisor grup) | Standar | Penerima "atasan" peringatan risiko SLA |
| `rudi` | Ketua Tim Perangkat (Tim Teknis, supervisor grup) | Standar | Penerima "atasan" peringatan risiko SLA |
| `wati` | Ketua Tim Identitas & Akses (Tim Teknis, supervisor grup) | Standar | Penerima "atasan" peringatan risiko SLA |
| `sri` | Manajemen | Standar (hanya-baca) | Dashboard kinerja AI |
| `lina` | Knowledge Manager | Standar | Mengelola artikel Pusat Bantuan, Kandidat knowledge |
| `dimas` | Administrator | Standar | Konfigurasi platform: katalog, SLA, tim, aturan, notifikasi, AI, audit trail |
| `glpi` / `glpi` | Super-Admin | Standar | Konfigurasi & pengelolaan sistem |

> ⚠️ `glpi`/`glpi` dan `halosis` hanya untuk demo lokal. Ganti sebelum GLPI bisa diakses dari jaringan lain.

## Instalasi

Langkah lengkap menyalakan GLPI dan data contoh ada di `README.md` folder induk. Urutannya:

```bash
docker compose up -d                                   # GLPI 12.0.0 + MySQL, http://localhost:8080
# aktifkan API (README induk langkah 3), lalu:
docker compose exec glpi php bin/console plugin:install halosis -u glpi --allow-superuser
docker compose exec glpi php bin/console plugin:activate halosis --allow-superuser
docker compose exec glpi php bin/console plugins:halosis:setup-roles --allow-superuser
.venv/bin/python seed_halosis.py http://localhost:8080 # data contoh (sekali, setelah setup-roles)
```

Folder ini di-mount ke `/var/www/glpi/plugins/halosis`, jadi perubahan kode langsung terbaca.
Atau lewat UI: **Setup › Plugins** → HaloSIS → Install → Aktifkan. Saat versi plugin naik, jalankan ulang
`plugin:install halosis -u glpi --force` lalu `plugin:activate` (install bersifat idempoten: data tetap).

**SDK Anthropic**: hanya dibutuhkan untuk memanggil Claude sungguhan. Dipasang dengan Composer ke
`vendor/` (tidak di-commit). Dari folder plugin:

```bash
docker run --rm -u "$(id -u):$(id -g)" -v "$PWD":/app -w /app composer:2 install --no-dev
```

`composer.json` me-*replace* Guzzle & paket PSR HTTP karena sudah disediakan GLPI. SDK hanya dimuat saat
API key terisi; halaman konfigurasi memperingatkan bila API key terisi tapi SDK belum terpasang.

**Uninstall** (`plugin:uninstall halosis`) menghapus semua tabel, konfigurasi, hak akses, dan tugas
terjadwal plugin. Nama profil hasil `setup-roles` tetap.

## Konfigurasi

**Setup › AI HaloSIS** (atau ikon kunci pas di Setup › Plugins). Area sensitif: GLPI meminta konfirmasi
password sebelum membukanya.

| Pengaturan | Default | Keterangan |
| --- | --- | --- |
| Penyedia AI | Anthropic (Claude) | Atau API kompatibel OpenAI |
| API key | kosong = **mode demo** | Disimpan terenkripsi dengan kunci GLPI (`glpicrypt.key`); tidak pernah dikirim ke browser |
| Model | `claude-opus-5-5` | ID model di penyedia |
| URL dasar API | kosong | Opsional, untuk gateway/proxy |
| Batas waktu | 20 detik | Jika terlewati, tiket tetap tersimpan tanpa saran |
| URL layanan AI | `http://halosis-ai:8000` | Layanan lokal `ai/service` (model history tiket + pencarian); kosong/mati → mode di atas |
| Batas waktu layanan | 8 detik | Untuk layanan AI lokal |
| Ambang keyakinan | 70% | Di bawah ambang → "Perlu penilaian manual" |
| Minimal tiket mirip | 10 | Deteksi pola insiden |
| Jendela waktu | 60 menit | Deteksi pola insiden |
| Grup Operator | bawaan "Operator Service Desk" | Penerima Problem pola insiden |
| Fitur AI | semua aktif | Saran triase, chatbot, deteksi pola, dashboard |

### Mode demo

Tanpa layanan AI lokal dan tanpa API key, semua fitur tetap bisa didemokan tanpa internet, dengan hasil yang sama untuk masukan
yang sama:

- **Saran triase**: aturan kata kunci (mis. "vpn" → Jaringan & VPN, "sso"/"login" → SSO / Login,
  "fasih"/"sinkron" → FASIH), urgensi naik bila ada "tidak bisa", "gagal", "hari ini", dampak naik bila
  ada "semua", "rekan". Model tercatat `demo-rules-v1`.
- **Chatbot**: kutipan langkah dari artikel Pusat Bantuan yang paling relevan, dengan label
  "Dari Pusat Bantuan" (label "Dijawab AI" hanya bila Claude yang merangkum).
- **Deteksi pola & dashboard** tidak memakai AI, sehingga sama di kedua mode.

Dengan API key, Claude dipanggil di server (SDK resmi, *structured output*, effort `low`, dan
*server-side fallback* untuk model yang mendukungnya). Bila AI gagal atau timeout, triase dilewati dan
chatbot kembali ke kutipan artikel; penyebabnya dicatat di `halosis.log` (Docker: `/var/glpi/logs/halosis.log`).

### Layanan AI HaloSIS (lokal, tanpa API key)

Bila service `halosis-ai` di docker-compose hidup, plugin memakainya **lebih dulu**:

- **Saran triase** dari model yang dilatih dari history tiket (model tercatat `triase-tfidf-lr-<tanggal>`),
  dengan top-3 tim dan nomor tiket lama yang mirip di penjelasan. Tim history dipetakan ke kategori/grup GLPI.
- **Chatbot** mencari di artikel KB + solusi tiket lama (embedding lokal); sumber tiket tampil
  "Tiket serupa <nomor>".
- Layanan mati → otomatis kembali ke mode demo / AI penyedia di atas. Cara membangun model & indeks:
  [`ai/README.md`](../../ai/README.md) (AI-3 s.d. AI-5).

## Skenario demo langkah demi langkah

Alur utama (± 10 menit), sudah diuji ujung ke ujung: **pegawai chat → buat laporan → operator validasi
saran AI → teknisi selesaikan → pegawai approve**. Pakai jendela browser terpisah (atau mode privat)
per akun.

### 1. Pegawai bertanya ke asisten (`budi`)

1. Buka http://localhost:8080 dan login `budi` / `halosis`. Anda langsung masuk ke **Tanya HaloSIS**
   (bukan beranda GLPI biasa); menu Helpdesk: Tanya HaloSIS · Laporan saya · Buat laporan · Pusat bantuan.
2. Klik chip **FASIH gagal sinkron**. Asisten menjawab dengan langkah-langkah dari artikel
   "FASIH: sinkronisasi gagal" dan chip sumber yang bisa diklik.
3. Tunjukkan peringatan privasi: kirim "password saya: abc123". Asisten memberi tahu bahwa data pribadi
   disamarkan sebelum diproses.
4. Di bawah jawaban, klik **Belum terselesaikan** → kartu oranye "Saya buatkan laporan…" → **Ya, buat laporan**.
5. Ubah judul menjadi mis. "FASIH gagal sinkron, data Susenas belum terkirim", buka **Ringkasan yang
   dilampirkan**, lalu **Kirim laporan**. Catat nomor laporan, lalu klik **Buka laporan**.

> Variasi: tanyakan "Kursi kantor saya patah" → asisten tidak menemukan artikel dan langsung menawarkan
> laporan. Atau tanyakan "VPN putus" → **Masalah terselesaikan** → beri bintang (tercatat sebagai
> "terbantu tanpa tiket" di dashboard).

### 2. Operator memvalidasi saran AI (`rina`)

1. Login `rina` / `halosis`, buka **Bantuan › Tiket**, lalu buka laporan tadi.
2. Di kanan atas ada panel **Saran AI**: kategori Aplikasi Statistik > FASIH, grup Tim Aplikasi Statistik,
   meter keyakinan dengan garis ambang, dan penjelasan.
3. Klik **Terima**. Kategori, dampak, urgensi, prioritas, dan grup langsung terisi di tiket.
   - Alternatif **Ubah**: ganti nilai + alasan wajib → **Terapkan perubahan**.
   - Alternatif **Tolak**: alasan wajib → field tiket tidak diubah, triase manual.
4. Buka tab **Historical** tiket: ada baris "HaloSIS: Saran AI diterima (keyakinan …%)" selain perubahan field.

> Untuk melihat tanda **Perlu penilaian manual**, buka tiket berjudul samar (mis. "Aplikasi error terus")
> yang keyakinannya di bawah 70%.

### 3. Tim Teknis menyelesaikan (`andi`)

1. Login `andi` / `halosis`. Tiket muncul di **Beranda › Tampilan Group** dan **Bantuan › Tiket**.
2. Panel Saran AI tampil **tanpa tombol keputusan** (Tim Teknis hanya melihat).
   - Alternatif **salah tim** (UC-06): klik **Kembalikan ke operator (salah tim)**, tulis alasan (wajib, minimal
     5 karakter). Tim & teknisi dilepas, status kembali **Baru** (antrean validasi `rina`), alasan tercatat sebagai
     tindak lanjut privat dan data evaluasi AI. `rina` lalu menugaskan tim yang benar.
3. Klik **Answer ▾ › Add a solution**, tulis solusi (mis. "Server sinkronisasi FASIH wilayah sudah
   dipulihkan. Buka FASIH lalu tekan Coba sinkron ulang."), simpan. Status menjadi **Terselesaikan**.

### 4. Pegawai menyetujui solusi (`budi`)

1. Login `budi`, buka **Laporan saya**, lalu laporan tadi.
2. Pada solusi, klik **Approve**. Status laporan menjadi **Ditutup**.
   - Alternatif **belum beres** (UC-07): tulis alasan lalu klik **Refuse**. GLPI menolak Refuse tanpa alasan;
     dengan alasan, solusi ditandai ditolak dan tiket kembali **Diproses** ke tim yang sama.

### 5. Manajemen melihat kinerja AI (`sri`)

1. Login `sri` / `halosis`, buka **Bantuan › Kinerja AI**.
2. Tunjukkan: % saran diterima apa adanya, batang komposisi Diterima/Diubah/Ditolak, **Dipindah ke tim lain
   setelah triase**, grafik keputusan per minggu (arahkan kursor ke kolom; **Tampilkan sebagai tabel**),
   keyakinan AI vs keputusan petugas, dan kartu chatbot (terbantu tanpa tiket, rating).
3. Ganti periode 4 / 8 / 12 minggu.

### Bonus: pola insiden (`glpi` + `rina`)

Deteksi butuh ≥ 10 tiket mirip dalam 60 menit. Untuk demo langsung, turunkan ambangnya:

1. Login `glpi`, **Setup › AI HaloSIS** → **Minimal tiket mirip** = 3 → Simpan.
2. Sebagai `budi`/`siti`/`maya`, buat 3 laporan cepat dengan judul mirip (mis. "Tidak bisa login SSO",
   "Login SSO gagal", "SSO error tidak bisa masuk") lewat **Langsung buat laporan**.
3. Sebagai `glpi`, buka **Setup › Tindakan otomatis › IncidentPattern** → **Jalankan** (atau tunggu
   jadwal 15 menit). Log tugas menampilkan "Pola baru: …".
4. Login `rina`, buka **Beranda**: banner **Pola insiden terdeteksi** dengan tautan ke Problem
   "Pola insiden: …" yang berisi daftar tiket dan sudah ditugaskan ke grup Operator. Panel Saran AI di tiket
   terkait menampilkan **Bagian dari pola insiden**. Operator yang memutuskan tindak lanjutnya.
5. Kembalikan **Minimal tiket mirip** ke 10.

## Detail fitur

### Saran triase AI

- Dibuat saat tiket baru disimpan (hook `item_add` Ticket, dari antarmuka mana pun termasuk REST API),
  disimpan di tabel plugin, **bukan** di field tiket. Kategori & grup dibatasi ke daftar yang valid untuk
  entitas & tipe tiket dan divalidasi ulang di server; prioritas dari matriks urgensi × dampak GLPI.
- AI gagal/timeout → tiket tetap tersimpan normal tanpa saran (tidak ada coba ulang, waktu tunggu maksimal =
  batas waktu). Petugas bisa menekan **Buat saran AI** di panel.
- Keputusan butuh hak triase *putuskan* **dan** hak ubah tiket GLPI. Nilai diterapkan lewat update tiket
  biasa, jadi aturan bisnis, notifikasi, dan riwayat field GLPI tetap berjalan. Alasan Ubah/Tolak divalidasi
  di server (minimal 5 karakter). Tanpa hak GLPI "Ubah prioritas", prioritas mengikuti matriks.
- **Kembalikan ke operator (salah tim)**, UC-06 alur alternatif: tombol hanya tampil untuk teknisi/anggota tim
  yang ditugaskan, selama tiket Diproses/Direncanakan/Menunggu. Hak dicek ulang di server. Alasan wajib.
  Hasilnya: grup & teknisi penugasan dihapus, status Baru, tindak lanjut privat "Dikembalikan ke operator
  (salah tim): …", dan baris `reassignments` dengan `kind = return`.
- Setiap keputusan tercatat di `glpi_plugin_halosis_decisions` (aktor, waktu, nilai saran vs final, alasan)
  dan tab Riwayat tiket.

### Menu ringkas per peran

Sidebar/menu mengikuti prototipe halosis-web (hook `redefine_menus`, kelas `RoleMenu`):

| Peran | Menu |
| --- | --- |
| Pegawai | Tanya HaloSIS · Buat laporan · Laporan saya · Pusat bantuan (FAQ) · Riwayat chat |
| Operator | Dashboard · Antrean validasi (tiket Baru) · Semua tiket · Monitoring SLA · Pola insiden · Cari knowledge |
| Tim Teknis | Dashboard · Tiket saya & tim · Monitoring SLA · Pola insiden · Cari knowledge |
| Manajemen | Dashboard kinerja · Kinerja AI · Monitoring SLA · Pola insiden · Laporan (statistik) |
| Knowledge Manager | Dashboard · Kandidat knowledge · Daftar artikel · Tulis artikel |
| Administrator | Admin console · Service catalog · Kategori layanan · Kebijakan SLA · Tim teknis · Pengguna & role · Workflow & aturan · Pengaturan AI · Kinerja AI · Kandidat knowledge · Notifikasi · Audit trail |
| Super-Admin | seperti Administrator + grup **Sistem GLPI** (umum, plugin, profil, entitas, aksi otomatis, perubahan, dropdown) |

- Item hanya tampil bila pengguna berhak membuka halamannya. Monitoring SLA = tiket belum selesai yang melewati
  batas waktu penyelesaian; Pola insiden = Problem yang dibuat deteksi pola.
- Menu bawaan GLPI tidak dihapus dari array menu (breadcrumb & tombol "Tambah" memakainya), hanya disembunyikan
  dari sidebar lewat CSS. Halaman lain tetap bisa dibuka lewat URL sesuai hak akses.
- Sorotan menu aktif diatur `public/js/menu.js` (detail tiket menyorot "Semua tiket"/daftar tiket peran itu).
- Matikan fitur **Menu ringkas** di konfigurasi plugin untuk kembali ke menu GLPI lengkap.

### Kandidat Knowledge (UC-09, hak `plugin_halosis_kandidat`)

Halaman `/plugins/halosis/Kandidat` (Knowledge Manager, Administrator, Super-Admin). Setiap dibuka, kandidat
baru disinkronkan dari dua sumber:

- **Tiket selesai** (Solved/Closed) dengan solusi yang tidak ditolak pemohon; yang disetujui pemohon diberi
  label *Disetujui pemohon* dan tampil lebih dulu.
- **Solusi berulang dari indeks AI**: layanan `halosis-ai` (`GET /kandidat`) mengelompokkan solusi tiket history
  yang mirip (TF-IDF, kosinus ≥ 0,75, minimal 5 tiket, solusi ≥ 10 kata). Bila layanan mati, bagian ini dilewati.

Aksi: **Jadikan artikel** membuat *draf* artikel KB (masalah + solusi + sumber, tanpa target visibilitas =
belum terbit) lalu membuka draf itu untuk disunting & diterbitkan; **Abaikan** wajib beralasan (≥ 5 karakter).
Setiap keputusan menyimpan pelaku & waktu (tabel `glpi_plugin_halosis_candidates`). Teks kandidat disamarkan.

### Tanya HaloSIS (chatbot)

- **Beranda Pegawai**: setelah login GLPI selalu membuka `/Helpdesk`; plugin menambahkan
  `<meta http-equiv="refresh">` (hook `add_header_tag`) hanya pada `GET /Helpdesk` untuk pengguna Helpdesk
  yang berhak chatbot. Operator & profil standar tidak terpengaruh; tidak ada loop. (GLPI 12 belum punya
  hook server-side untuk ini: `RedirectException` dari `plugin_init` maupun `redefine_menus` berakhir HTTP 500.)
- **Menu Helpdesk** diatur lewat hook `redefine_menus`.
- **Sumber jawaban hanya artikel KB yang terlihat oleh pengguna**: kriteria visibilitas GLPI
  (`KnowbaseItem::getVisibilityCriteria()`; di Helpdesk = FAQ yang boleh dilihat), tiap artikel dicek ulang
  dengan `canViewItem()`. Artikel internal tidak pernah dipakai. Tautan sumber dibuat server, bukan dari teks model.
- **Data pribadi** (pola kata sandi, email, nomor HP, NIK/NIP) disamarkan di server sebelum dikirim ke AI
  maupun disimpan.
- **Buat laporan** memakai sesi & hak GLPI pegawai; deskripsi = ringkasan percakapan; tiket langsung
  mendapat saran triase.
- **Widget melayang** "Tanya asisten" muncul di halaman Helpdesk lain (detail tiket, FAQ) dan melanjutkan
  percakapan yang sama; tidak dimuat di halaman chat.
- **Riwayat chat** (`/plugins/halosis/ChatHistory`, menu kedua Pegawai): 50 percakapan terbaru milik pengguna
  sendiri dengan status *Bisa dilanjutkan* / *Terselesaikan · rating* / *Laporan #id* (tertaut ke tiket).
  Item dibuka di halaman chat lewat `?chat=<id>`; id milik orang lain diabaikan (`Chat::getOwned`).
  Percakapan selesai hanya bisa dibaca.
- **Lanjut otomatis**: di tab/login baru, percakapan terbuka terakhir yang aktif dalam 2 jam
  (`Chat::RESUME_HOURS`) dimuat ulang. Setelah "Percakapan baru", percakapan itu tidak dilanjutkan otomatis lagi
  (diingat di `localStorage` browser) dan tetap bisa dibuka dari Riwayat chat.
- Fitur chat dimatikan → halaman menampilkan "Asisten sedang tidak tersedia" + tombol Buat laporan.

### Deteksi pola insiden

Tugas terjadwal **`IncidentPattern`** (tiap 15 menit, mode CLI; penjadwal container menjalankan
`front/cron.php` tiap menit). Manual: `docker compose exec glpi php front/cron.php --force IncidentPattern`.

1. Tiket yang dibuat dalam jendela waktu, belum dihapus, belum selesai.
2. Dikelompokkan per **kategori** (tiket tanpa kategori memakai kategori saran triase AI), sisanya per
   **judul mirip** (≥ 2 kata kunci sama dan overlap ≥ 0,5).
3. Kelompok ≥ N tiket → Problem **"Pola insiden: …"** (daftar tiket & kriteria), ditautkan ke tiketnya,
   ditugaskan ke grup Operator. Tidak ada penyelesaian/penerusan otomatis.
4. Pola yang sama dengan Problem masih terbuka (≤ 24 jam) tidak dibuat ulang; tiket baru ditautkan ke sana.

Notifikasi: penugasan ke grup Operator (notifikasi GLPI standar terkirim bila email dikonfigurasi), banner
di beranda pemegang hak triase *putuskan*, dan catatan di panel Saran AI tiket terkait.

### Dashboard kinerja AI

Semua angka dari tabel log plugin (`src/Stats.php`):

| Angka | Sumber |
| --- | --- |
| % saran diterima / diubah / ditolak, keputusan per minggu | `decisions` |
| Keyakinan AI vs keputusan (di atas / di bawah ambang) | `decisions` + `suggestions` |
| % tiket dipindah ke tim lain setelah triase ("salah tim"), termasuk yang dikembalikan Tim Teknis | `reassignments` ÷ tiket dengan keputusan Terima/Ubah |
| Chat terbantu tanpa tiket, jadi laporan, rata-rata rating | `chats` |

GLPI tidak punya aksi "kembalikan karena salah tim", jadi plugin mencatat dua hal: tombol **Kembalikan ke
operator** (`kind = return`, beserta alasan) dan setiap kali tiket yang triasenya sudah diterapkan lalu
ditugaskan ke grup lain (`kind = reassign`, hook `item_add` Group_Ticket). Grafik dirender server
sebagai SVG tanpa pustaka luar. Warna seri divalidasi untuk buta warna (Diterima `#00826F`, Diubah `#62C9AF`,
Ditolak `#D8652A`, turunan teal & oranye HaloSIS), dan nilai selalu tertulis sebagai teks.

## Role & hak akses

`plugins:halosis:setup-roles` (aman dijalankan berulang) mengganti nama profil bawaan berdasarkan ID,
membuat Knowledge Manager, memastikan Manajemen hanya-baca, menerapkan hak plugin, dan menonaktifkan akun
bawaan `tech`, `normal`, `post-only`. Definisi di `src/Roles.php`.

| ID | Profil GLPI asal | Role HaloSIS | Antarmuka |
| --- | --- | --- | --- |
| 1 | Self-Service | Pegawai | Helpdesk |
| 2 | Observer | Manajemen | Standar (hanya-baca) |
| 3 | Admin | Administrator | Standar |
| 4 | Super-Admin | Super-Admin (pengelola sistem) | Standar |
| 5 | Hotliner | Operator | Standar |
| 6 | Technician | Tim Teknis | Standar |
| baru | — | Knowledge Manager | Standar |

Hak plugin (ubah di **Administrasi › Profil › (profil) › tab HaloSIS**). Semua pengecekan akses memakai
hak ini, tidak pernah nama profil.

| Hak | Nilai | Default |
| --- | --- | --- |
| `plugin_halosis_triase` | lihat (READ), putuskan (UPDATE) | Operator, Administrator, Super-Admin: lihat & putuskan; Tim Teknis: lihat |
| `plugin_halosis_chatbot` | pakai (READ) | Pegawai |
| `plugin_halosis_dashboard` | lihat (READ) | Manajemen, Administrator, Super-Admin |
| `plugin_halosis_kandidat` | lihat (READ), putuskan (UPDATE: jadikan artikel / abaikan) | Knowledge Manager, Administrator, Super-Admin: lihat & putuskan |
| `plugin_halosis_config` | ubah (UPDATE) | Administrator, Super-Admin |

GLPI hanya membawa hak profil Helpdesk yang terdaftar di `Profile::$helpdesk_rights` ke sesi, jadi plugin
mendaftarkan `plugin_halosis_chatbot` di sana (`setup.php`).

## Pemecahan masalah

| Gejala | Penyebab & solusi |
| --- | --- |
| Tampilan chatbot/panel berantakan setelah update | Cache browser lama. Aset plugin sudah diberi penanda waktu ubah file (`plugin_halosis_asset()`), cukup muat ulang (Safari: Cmd+Option+R). |
| "An unexpected error occurred" setelah login | Bug GLPI 12.0.0 pada "Remember me" (token ganda). "Remember me" sudah dimatikan (`login_remember_time = 0`); lihat README induk. |
| `ERROR_NOT_ALLOWED_IP` saat menjalankan seed | Klien API untuk IP gateway Docker belum ada; lihat README induk langkah 3. |
| Tiket baru tidak mendapat saran AI | Cek fitur triase aktif dan `/var/glpi/logs/halosis.log` (AI gagal/timeout, SDK belum terpasang). Klik **Buat saran AI** di panel. |
| Pegawai tidak diarahkan ke Tanya HaloSIS | Pastikan profil Helpdesk punya hak chatbot (tab HaloSIS) dan fitur chat aktif; login ulang. |
| Pola insiden tidak terbentuk | Butuh ≥ N tiket mirip dalam jendela waktu; lihat log tugas di Setup › Tindakan otomatis › IncidentPattern. |

## Batasan yang diketahui

- **Belum diuji dengan API key Claude asli.** Jalur SDK, jaringan, timeout, dan penanganan galat sudah
  terbukti (request sampai ke API dan ditolak karena key uji palsu), tapi isi request belum divalidasi oleh
  API dengan key sungguhan. Uji sekali dengan key asli sebelum dipakai.
- AI dipanggil saat tiket disimpan, jadi pegawai menunggu sampai saran jadi (maksimal = batas waktu).
- **Mode demo saja** (layanan `halosis-ai` mati): pencarian artikel memakai pencocokan kata kunci, jadi sinonim
  (mis. "lemot" vs "lambat") belum dikenali; cukup untuk KB kecil. Dengan `halosis-ai`, pencarian chatbot
  memakai embedding (`intfloat/multilingual-e5-base`) sehingga makna serupa tetap ditemukan.
- Deteksi pola insiden mengelompokkan judul dengan kata kunci di semua mode (tidak memakai layanan AI).
- Sebagian menu GLPI masih berbahasa Inggris (terjemahan `id_ID` bawaan GLPI 12 belum lengkap).
- Notifikasi email pola insiden bergantung pada konfigurasi email GLPI.

## Pengembangan

```
setup.php                 versi, syarat GLPI 12.0.x, registrasi hook, penanda versi aset
hook.php                  install/uninstall: tabel, config default, hak akses, tugas terjadwal
src/Config.php            konfigurasi, API key terenkripsi, mode demo
src/Profile.php           hak akses plugin + tab di form Profil;  src/Roles.php  role HaloSIS & hak inti GLPI
src/RoleMenu.php          menu ringkas per peran (hook redefine_menus)
src/Console/              perintah plugins:halosis:setup-roles
src/Ai/Client.php         pemanggil AI di server (SDK Anthropic / API kompatibel OpenAI)
src/Ai/Service.php        klien layanan lokal halosis-ai (/triage, /chat, /kandidat);  src/Ai/AiException.php
src/Triage.php            saran triase (AI & demo) + keputusan;  src/TriagePanel.php  panel di form tiket
src/Suggestion.php        model saran;  src/Decision.php  model keputusan
src/Chatbot.php           jawaban chatbot, rating, buat laporan;  src/Chat.php  model percakapan
src/KnowledgeSearch.php   pencarian KB yang menghormati visibilitas GLPI;  src/Privacy.php  penyamaran data
src/HelpdeskHome.php      menu Helpdesk & pengalihan beranda ke halaman chat
src/PatternDetector.php   tugas terjadwal pola insiden + banner
src/Stats.php             angka dashboard;  src/Reassignment.php  pemindahan tim & Kembalikan ke operator
src/KnowledgeCandidates.php  sinkron, daftar, Jadikan artikel / Abaikan;  src/Candidate.php  model kandidat
src/Controller/           ChatController (/plugins/halosis/Chat, /plugins/halosis/ChatHistory),
                          DashboardController (/plugins/halosis/Dashboard), KandidatController (/plugins/halosis/Kandidat)
src/ConfigMenu.php, src/DashboardMenu.php  entri menu
ajax/triase.php, ajax/chat.php, ajax/kandidat.php  endpoint JSON panel triase, chatbot, kandidat knowledge
front/config.form.php     halaman konfigurasi
templates/                template Twig (@halosis/...)
public/css, public/js     aset, disajikan di /plugins/halosis/css|js/... (chat, config, dashboard, kandidat,
                          menu, triase)
locales/id_ID.po          terjemahan;  tools/locales.py  cek string belum diterjemahkan + kompilasi .mo
composer.json             SDK Anthropic (vendor/ tidak di-commit)
```

Teks di kode memakai msgid bahasa Inggris (konvensi GLPI) dengan terjemahan `id_ID`. Setelah menambah teks
UI, jalankan `python3 tools/locales.py`.

### Tabel

| Tabel | Isi |
| --- | --- |
| `glpi_plugin_halosis_suggestions` | Saran triase AI per tiket (kategori, dampak, urgensi, prioritas, grup, keyakinan, penjelasan, model, status) |
| `glpi_plugin_halosis_decisions` | Keputusan petugas: aktor, waktu, nilai saran vs final, alasan |
| `glpi_plugin_halosis_reassignments` | Tiket yang dipindah ke grup lain (`reassign`) atau dikembalikan ke operator dengan alasan (`return`) setelah triase AI diterapkan |
| `glpi_plugin_halosis_patterns` | Pola insiden: tanda pola, kriteria (kategori/judul), Problem, jumlah tiket |
| `glpi_plugin_halosis_chats` | Percakapan chatbot: pemilik, transkrip (tersamarkan), status, rating, tiket |
| `glpi_plugin_halosis_candidates` | Kandidat Knowledge (UC-09): sumber (tiket selesai / klaster AI), masalah & solusi (tersamarkan), jumlah kemunculan, status (`pending` / `article` / `ignored`), artikel KB yang dibuat, alasan diabaikan, Knowledge Manager & waktu keputusan |
