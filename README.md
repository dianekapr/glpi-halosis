# Coba GLPI untuk HaloSIS

Paket ini menyalakan GLPI di laptop kamu lalu mengisinya dengan data contoh HaloSIS:
4 tim teknis, kategori layanan (SSO, FASIH, SiPecut, VPN, dll.), 10 pengguna per role,
SLA per prioritas, 12 tiket (lengkap dengan balasan, catatan internal, solusi),
5 artikel knowledge base, dan 1 "masalah" sebagai contoh pola insiden.

Di atas GLPI terpasang **plugin HaloSIS** (modul AI human-in-the-loop: chatbot Tanya HaloSIS, saran triase,
deteksi pola insiden, dashboard kinerja AI) dan palet tema HaloSIS. Cara pakai, mode demo, dan **skenario
demo langkah demi langkah** ada di [`plugins/halosis/README.md`](plugins/halosis/README.md).

## Untuk anggota tim: mulai dari link GitHub

Belum pernah pakai Git/GitHub? Ikuti bagian ini dari atas sampai bawah. Cukup sekali di langkah A–C;
langkah D dipakai setiap kali kamu bekerja.

**Istilah singkat**

| Istilah | Artinya |
| --- | --- |
| **Repo** (repository) | Folder proyek yang disimpan di GitHub, lengkap dengan riwayat perubahannya |
| **Clone** | Mengunduh repo ke laptop (sekali saja) |
| **Commit** | "Simpan titik" perubahan di laptop, dengan pesan singkat |
| **Push** | Mengirim commit dari laptop ke GitHub |
| **Pull** | Mengambil perubahan terbaru teman dari GitHub ke laptop |
| **Branch** | Jalur kerja terpisah, supaya pekerjaanmu tidak mengganggu pekerjaan teman |
| **Pull Request (PR)** | Permintaan menggabungkan branch-mu ke branch bersama, bisa dicek teman dulu |
| **Conflict** | Kamu dan teman mengubah baris yang sama; Git minta kamu memilih mana yang dipakai |

### A. Persiapan (sekali saja)

1. **Pasang aplikasi:**
   - **Git**: Mac → buka Terminal, ketik `git --version` (kalau belum ada, macOS menawarkan untuk memasang);
     Windows → https://git-scm.com/download/win (pilih opsi bawaan saja).
   - **Docker Desktop**: https://www.docker.com/products/docker-desktop, lalu buka aplikasinya sampai ikon paus
     di menu bar/taskbar berhenti bergerak.
   - **Python 3**: Mac biasanya sudah ada (`python3 --version`); Windows → https://www.python.org/downloads
     (centang **Add python.exe to PATH** saat instalasi).
   - Disarankan: **VS Code** (https://code.visualstudio.com) untuk membuka & mengedit kode.
2. **Kenalkan dirimu ke Git** (nama & email yang tercatat di setiap commit):
   ```bash
   git config --global user.name "Nama Kamu"
   git config --global user.email "email-github-kamu@contoh.com"
   ```
3. **Login GitHub dari laptop.** GitHub tidak menerima password biasa untuk push. Pilih salah satu:
   - Paling mudah: pasang **GitHub Desktop** (https://desktop.github.com) dan login di sana; Git di laptop ikut
     memakai login itu.
   - Atau GitHub CLI: pasang dari https://cli.github.com lalu jalankan `gh auth login` (pilih *GitHub.com* →
     *HTTPS* → *Login with a web browser*).

### B. Ambil kode (clone)

Buka Terminal (Mac) atau **Git Bash** (Windows), lalu:
```bash
cd ~/Downloads                     # pindah ke folder tempat proyek mau disimpan
git clone https://github.com/dianekapr/glpi-halosis.git
cd glpi-halosis
git checkout dev                   # kerja tim ada di branch dev
cp .env.example .env               # Windows (cmd): copy .env.example .env
```
File `.env` berisi pengaturan lokal dan sengaja tidak ikut ke GitHub.

### C. Jalankan di laptop

Ikuti bagian **Langkah** di bawah (1 s.d. 7). Catatan untuk anggota tim:

- `docker compose up -d` pertama kali juga membangun layanan AI (`halosis-ai`) dan mengunduh beberapa GB;
  bisa 10–20 menit. Selanjutnya cepat.
- **Data history tiket, model AI, dan indeks pencarian TIDAK ada di GitHub** (berisi data pribadi, lihat
  [`ai/README.md`](ai/README.md)). Siapa perlu apa:

  | Kebutuhan | Yang diperlukan |
  | --- | --- |
  | Menjalankan & menguji GLPI + plugin | Tidak perlu data apa pun. `seed_halosis.py` mengisi data contoh; tanpa model AI, plugin otomatis memakai **mode demo** |
  | **Menguji end-to-end dengan AI sungguhan** (saran triase dari model, chatbot dari solusi tiket lama) | Folder `ai/models/` dan `ai/index/` dari pemilik repo. **Tidak perlu file Excel** |
  | Melatih ulang model dari Excel | Hanya 1–2 orang yang mengurus AI; ikuti [`ai/README.md`](ai/README.md) |

  Cara memasangnya ada di bagian **C2** di bawah.
- Windows: ganti `.venv/bin/python` dengan `.venv\Scripts\python` dan `.venv/bin/pip` dengan `.venv\Scripts\pip`.

### C2. Pasang model AI dari Google Drive (untuk penguji)

> ⚠️ Isi folder ini diturunkan dari history tiket BPS (sudah disamarkan, tetapi tetap **data internal**).
> Jangan unggah ulang, jangan kirim ke orang lain/grup chat, dan jangan di-commit ke GitHub.

**Syarat:** Langkah 1–6 di bawah sudah selesai (GLPI menyala, plugin terpasang, data contoh sudah diisi
sekali di database kosong). Indeks chatbot merujuk artikel Knowledge Base hasil `seed_halosis.py`, jadi
langkah 5 wajib dijalankan dulu.

**1. Unduh dua folder dari Google Drive** (login dengan akun Google yang diberi akses oleh pemilik repo):

| Folder | Link | Isi |
| --- | --- | --- |
| `models` | [Buka di Google Drive](https://drive.google.com/drive/folders/1S_Cpm0qa0OoqGSC4-SFt-ZZfhaw9X87Y?usp=share_link) | `triage.joblib` (±40 MB) |
| `index` | [Buka di Google Drive](https://drive.google.com/drive/folders/1S_Cpm0qa0OoqGSC4-SFt-ZZfhaw9X87Y?usp=share_link) | `chunks.parquet`, `vectors.npy` |

Di Drive: klik kanan folder → **Download**. Drive mengemasnya jadi file `.zip` (namanya bisa seperti
`models-20261028T…-001.zip`). Ekstrak: Mac → klik dua kali file zip; Windows → klik kanan → **Extract All**.

**2. Taruh di folder proyek** sehingga susunannya **persis** seperti ini (nama huruf kecil semua):
```text
glpi-halosis/
└── ai/
    ├── models/
    │   └── triage.joblib
    └── index/
        ├── chunks.parquet
        └── vectors.npy
```
Hati-hati folder dobel hasil ekstrak, mis. `ai/models/models/triage.joblib`. Kalau begitu, pindahkan file-nya
naik satu tingkat. Cek dari folder proyek:
```bash
ls ai/models ai/index          # Mac/Linux
dir ai\models ai\index         # Windows (cmd)
```
Harus terlihat tepat tiga file di atas.

**3. Nyalakan ulang layanan AI**
```bash
docker compose restart halosis-ai
```
(Kalau layanan belum pernah dibuat: `docker compose up -d --build halosis-ai`.)

**4. Cek layanan siap.** Buka http://localhost:8001/health. Saat pertama kali, layanan mengunduh model bahasa
(±1 GB), jadi bisa 2–5 menit; muat ulang halaman sampai muncul:
```text
{"status":"ok","triase":true,"versi_model":"triase-tfidf-lr-…","pencarian":true, …}
```

| Yang muncul | Artinya | Yang dilakukan |
| --- | --- | --- |
| `"status":"ok"` | Model & indeks terbaca | Lanjut ke langkah 5 |
| `"status":"sebagian"`, `"triase":false` | `triage.joblib` tidak ditemukan | Cek susunan folder (langkah 2), lalu ulangi langkah 3 |
| `"status":"sebagian"`, `"pencarian":false` | `chunks.parquet`/`vectors.npy` tidak ditemukan | Cek susunan folder (langkah 2), lalu ulangi langkah 3 |
| Halaman tidak bisa dibuka | Layanan masih menyiapkan diri (mengunduh model bahasa) atau belum menyala | Tunggu beberapa menit lalu muat ulang. Bila tetap: `docker compose ps` (harus ada `halosis-ai` *Up*) dan `docker compose logs --tail 30 halosis-ai` (siap bila ada baris `Application startup complete`) |

**5. Pastikan GLPI memakai layanan ini.** Login `glpi` → menu **Pengaturan AI** → bagian *Layanan AI HaloSIS*:
URL harus `http://halosis-ai:8000` (bawaan). Jangan diganti `localhost:8001`: GLPI berjalan di dalam Docker
dan memanggil layanan lewat nama `halosis-ai`.

**6. Uji cepat**
- Login `budi` → tanya *"kuota email saya penuh"* → jawaban punya sumber **"Tiket serupa …"**
  (tanpa model: jawaban dari artikel FAQ saja).
- Login `budi` → tanya *"resep nasi goreng"* → asisten menjawab belum menemukan jawaban.
- Buat tiket *"tidak bisa login SSO"* → login `rina` → buka tiketnya → panel **Saran AI** menyebut model
  `triase-tfidf-lr-…` beserta 3 tim teratas (tanpa model: `demo-rules-v1`).

Lalu jalankan skenario lengkap di
[`plugins/halosis/README.md`](plugins/halosis/README.md#skenario-demo-langkah-demi-langkah).

**7. Setelah selesai menguji**
- `git status` tidak boleh menampilkan `ai/models` atau `ai/index` (sudah di-`.gitignore`). Kalau muncul,
  jangan commit; kabari pemilik repo.
- Bila tidak dipakai lagi, hapus kedua folder dan file zip unduhannya.

### D. Alur kerja harian (biar tidak bentrok)

Branch di repo ini:

| Branch | Isi | Siapa yang mengubah |
| --- | --- | --- |
| `master` | Versi stabil untuk demo/pengumpulan | Hanya lewat PR dari `dev`, disepakati bersama |
| `dev` | Gabungan pekerjaan tim yang sudah dicek | Hanya lewat Pull Request |
| `fitur/<nama>-<topik>` | Pekerjaanmu sendiri, mis. `fitur/rina-dashboard` | Kamu |

**1. Sebelum mulai kerja: ambil yang terbaru**
```bash
git checkout dev
git pull
```

**2. Buat branch untuk tugasmu** (sekali per tugas)
```bash
git checkout -b fitur/namamu-topik
```

**3. Kerjakan, lalu simpan (commit)**
```bash
git status                         # lihat file apa saja yang berubah
git add plugins/halosis/src/Stats.php   # pilih file yang memang mau disimpan
git commit -m "Tambah grafik tren mingguan di dashboard"
```
Commit sering-sering dengan pesan yang jelas. Hindari `git add .` kalau belum yakin isi `git status`.

**4. Kirim ke GitHub (push)**
```bash
git push -u origin fitur/namamu-topik      # pertama kali untuk branch ini
git push                                   # berikutnya cukup ini
```

**5. Buat Pull Request ke `dev`.** Buka repo di GitHub → muncul tombol **Compare & pull request** → pastikan
*base: `dev`* ← *compare: branch-mu* → tulis apa yang diubah & cara mengeceknya → **Create pull request**. Minta
satu teman mengecek, lalu klik **Merge pull request**.

**6. Setelah PR digabung**
```bash
git checkout dev
git pull
git branch -d fitur/namamu-topik           # hapus branch lama di laptop
```

**Kalau `dev` sudah berubah saat kamu masih bekerja** (teman sudah merge duluan), gabungkan dulu ke branch-mu
supaya conflict ketahuan lebih awal:
```bash
git checkout dev && git pull
git checkout fitur/namamu-topik
git merge dev
```

**Kalau muncul conflict.** Git menandai bagian yang bentrok di dalam file:
```text
<<<<<<< HEAD
versi kamu
=======
versi dari dev
>>>>>>> dev
```
Buka file itu (VS Code menampilkan tombol *Accept Current / Incoming / Both*), sisakan versi yang benar,
hapus tanda `<<<<<<<`, `=======`, `>>>>>>>`, lalu:
```bash
git add nama-file-yang-bentrok
git commit -m "Selesaikan conflict dengan dev"
```
Ragu memilih? Tanya teman yang mengubah bagian itu sebelum commit.

**Aturan emas**
- **Jangan pernah commit** `data/`, `.env`, `ai/models/`, `ai/index/`, file `.xlsx`/`.parquet` (data pribadi &
  rahasia). Semuanya sudah ada di `.gitignore`; tetap cek `git status` sebelum commit.
- Jangan kerja langsung di `dev`/`master`; selalu lewat branch + PR.
- Selalu `git pull` di `dev` sebelum membuat branch baru.
- Jangan pakai `git push --force` ke `dev`/`master`.
- Bagi tugas per bagian/berkas di grup supaya jarang mengubah file yang sama bersamaan.

**Masalah yang sering muncul**

| Pesan | Artinya & solusinya |
| --- | --- |
| `! [rejected] … (fetch first)` / `non-fast-forward` | Di GitHub ada perubahan yang belum kamu ambil → `git pull`, selesaikan conflict bila ada, lalu `git push` lagi |
| `Your local changes … would be overwritten` | Ada perubahan yang belum di-commit → commit dulu, atau simpan sementara dengan `git stash` lalu `git stash pop` setelah pull |
| `Permission denied` / `403` | Belum login (langkah A.3), atau akunmu belum punya akses tulis ke repo → minta ke pemilik repo |
| `Authentication failed` | Pakai login GitHub Desktop / `gh auth login`, bukan password akun |
| Terlanjur commit file data (belum push) | `git reset --soft HEAD~1`, keluarkan file itu dari commit, lalu kabari pemilik repo |
| Terlanjur **push** file data/`.env` | Jangan push lagi; segera kabari pemilik repo (riwayat GitHub harus dibersihkan & password diganti) |

## Yang dibutuhkan
- Docker Desktop (Mac/Windows) atau Docker Engine (Linux)
- Python 3 (untuk skrip pengisi data)
- Git (untuk mengambil & mengirim kode, lihat bagian di atas)

## Langkah

**1. Nyalakan GLPI** (pastikan file `.env` sudah ada: `cp .env.example .env`)
```bash
docker compose up -d
```
Tunggu 1–3 menit (pertama kali GLPI menginstal dirinya sendiri). Cek dengan `docker compose logs -f glpi`.

**2. Buka** http://localhost:8080 dan login `glpi` / `glpi` (akun super-admin bawaan).

**3. Aktifkan API** (dibutuhkan skrip pengisi data dan nanti oleh Next.js)
```bash
docker compose exec glpi php bin/console config:set enable_api 1 --allow-superuser
docker compose exec glpi php bin/console config:set enable_api_login_credentials 1 --allow-superuser
```
Kalau perintah di atas gagal karena path, ganti `bin/console` dengan `/var/www/glpi/bin/console`.
Atau lewat UI: **Setup › General › API** → aktifkan "Enable Rest API" dan "Enable login with credentials".

Di Docker Desktop (Mac), request dari laptop terlihat berasal dari `192.168.65.1`, bukan `127.0.0.1`,
sehingga API menolak dengan `ERROR_NOT_ALLOWED_IP`. Tambahkan klien API untuk rentang gateway Docker:
```bash
docker compose exec -T db mysql -uglpi -pglpi glpi -e "INSERT INTO glpi_apiclients (entities_id,is_recursive,name,date_creation,is_active,ipv4_range_start,ipv4_range_end,dolog_method) VALUES (0,1,'HaloSIS lokal (host Docker Desktop)',NOW(),1,INET_ATON('192.168.65.0'),INET_ATON('192.168.65.255'),0);"
```
(Atau lewat UI: **Setup › General › API › Add API client**.)

**4. Pasang plugin HaloSIS & terapkan role**
```bash
docker compose exec glpi php bin/console plugin:install halosis -u glpi --allow-superuser
docker compose exec glpi php bin/console plugin:activate halosis --allow-superuser
docker compose exec glpi php bin/console plugins:halosis:setup-roles --allow-superuser
```
Perintah `setup-roles` aman dijalankan berulang. Yang dilakukannya:
- ganti nama profil bawaan GLPI sesuai role HaloSIS (ID tetap, pengguna yang terhubung tidak terpengaruh);
- buat profil **Knowledge Manager**; pastikan **Manajemen** hanya-baca;
- terapkan hak plugin HaloSIS (triase, chatbot, dashboard, konfigurasi);
- nonaktifkan akun bawaan GLPI `tech`, `normal`, `post-only`.

**5. Isi data contoh HaloSIS** (jalankan sekali saja, setelah langkah 4)
```bash
python3 -m venv .venv && .venv/bin/pip install requests
.venv/bin/python seed_halosis.py http://localhost:8080
```

**6. Login sebagai role berbeda** (password semua: `halosis`)

| Login | Nama | Profil GLPI (role HaloSIS) | Antarmuka | Keterangan |
| --- | --- | --- | --- | --- |
| budi, siti, maya | Budi Santoso, dkk. | Pegawai | Helpdesk (sederhana) | Lapor & pantau tiket, chatbot |
| rina | Rina Wulandari | Operator | Standar | Validasi & triase tiket (saran AI) |
| andi, yoga | Andi Pratama, Yoga Saputra | Tim Teknis | Standar | Tim Aplikasi Statistik |
| fajar | Fajar Nugroho | Tim Teknis | Standar | Tim Identitas & Akses |
| dedi | Dedi Kurniawan | Tim Teknis | Standar | Tim Jaringan |
| sri | Sri Handayani | Manajemen | Standar | Hanya-baca: tiket, dashboard, statistik |
| lina | Lina Marlina | Knowledge Manager | Standar | Kelola Knowledge Base; tiket hanya-baca |
| glpi | — | Super-Admin | Standar | Pengelola sistem (bukan role bisnis) |

Profil **Administrator** (bekas "Admin") disiapkan untuk admin bisnis HaloSIS, tapi belum ada pengguna contohnya.

Hak plugin HaloSIS (bisa diubah di **Administrasi › Profil › (profil) › tab HaloSIS**):

| Hak | Pegawai | Operator | Tim Teknis | Manajemen | Knowledge Manager | Administrator | Super-Admin |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Chatbot | ✓ | | | | | | |
| Saran triase AI | | lihat & putuskan | lihat | | | lihat & putuskan | lihat & putuskan |
| Dashboard kinerja AI | | | | ✓ | | ✓ | ✓ |
| Konfigurasi plugin | | | | | | ✓ | ✓ |

> ⚠️ **Keamanan.** Akun `glpi` / `glpi` adalah Super-Admin dengan password bawaan yang diketahui umum.
> Ganti password-nya (**klik avatar › Preferensi › Password**) sebelum GLPI bisa diakses dari jaringan lain,
> dan jangan gunakan akun ini untuk pekerjaan sehari-hari. Password contoh `halosis` juga hanya untuk demo.
> Perintah `setup-roles` menampilkan peringatan selama masih ada akun dengan password bawaan.

> ⚠️ **"Remember me" dimatikan** (`login_remember_time = 0`, semula 604800 = 7 hari) karena bug GLPI 12.0.0:
> mengirim form login saat browser masih login dengan "Remember me" (tab login lama, tombol Back) berakhir
> "An unexpected error occurred" (`Duplicate entry … glpi_usertokens.token_uid`), dan tugas pembersih token
> GLPI juga gagal. Aktifkan lagi bila GLPI merilis perbaikan:
> ```bash
> docker compose exec glpi php bin/console config:set login_remember_time 604800 --allow-superuser
> ```
> Untuk instalasi baru, matikan dengan nilai `0`.

> **Aksi otomatis → mode CLI.** Container GLPI sudah menjalankan `front/cron.php` tiap 60 detik, jadi semua
> aksi otomatis di-set ke mode CLI (Setup › Aksi otomatis). Mode "GLPI" bawaan memicu peringatan "Automatic actions
> may not be running as expected". Untuk instalasi baru:
> ```bash
> docker compose exec db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" -e "UPDATE glpi_crontasks SET mode=2 WHERE mode=1"'
> ```

**7. Tampilan HaloSIS** (palet, logo, bahasa, teks login)

Palet ada di `themes/halosis.scss` (di-mount ke folder tema kustom GLPI `/var/glpi/files/_themes`).
Jadikan default untuk semua pengguna:
```bash
docker compose exec glpi php bin/console config:set palette halosis --allow-superuser
docker compose exec glpi php bin/console config:set language id_ID --allow-superuser
docker compose exec glpi php bin/console config:set text_login '<p style="text-align:center">Selamat datang di <strong>HaloSIS</strong>, layanan TI BPS.<br>Masuk dengan akun dinas Anda.</p>' --allow-superuser
```
Judul beranda Helpdesk: **Administrasi › Entitas › BPS › Helpdesk** → judul kustom "Halo, ada yang bisa kami bantu?".

Catatan palet: GLPI memakai variabel `secondary` juga sebagai warna teks, jadi variabelnya diisi versi gelap
`#4F7D72` agar terbaca; `#77B8A8` dipakai sebagai latar (tombol sekunder, `.bg-secondary`). Badge memakai
accent `#FF965A` dengan teks `#203332`. Logo HaloSIS berupa SVG inline di variabel `--glpi-logo-*`.

## Peta HaloSIS → menu GLPI

| Halaman HaloSIS | Di GLPI |
| --- | --- |
| Laporan Saya, Detail Laporan (pegawai) | Login pegawai → **Tiket** (antarmuka sederhana/Helpdesk) |
| Buat Laporan | **Service catalog** / Create a ticket |
| Pusat Bantuan | **FAQ** (artikel KB yang ditandai FAQ) |
| Konfirmasi "sudah beres / belum beres" | Tombol **Approve / Refuse** pada solusi tiket |
| Antrean validasi & Semua tiket (operator) | **Bantuan › Tiket** (filter status Baru) |
| Tiket saya & tim (Tim Teknis) | Beranda **Tampilan Personal / Tampilan Group** |
| Komentar publik / catatan internal | **Answer › Followup** (centang *Private* untuk internal), **Task** |
| Monitoring SLA | Kolom "Waktu untuk menyelesaikan" + **Setup › Service levels** |
| Pola insiden | **Bantuan › Masalah** (tiket ditautkan ke masalah) |
| Knowledge base (KM) | **Tools › Basisdata pengetahuan** |
| Dashboard manajemen, laporan | **Bantuan › Dashboard**, **Bantuan › Statistik** |
| Service catalog, tim, pengguna & role | **Setup › Dropdowns › ITIL categories**, **Administrasi › Groups / Users / Profil** (nama profil = role HaloSIS) |
| Workflow & aturan otomatis | **Administrasi › Rules › Business rules for tickets** |
| Audit trail | Tab **Riwayat** di setiap tiket/objek |

**Tidak ada di GLPI** (tetap dibangun sendiri di HaloSIS): chatbot AI, saran triase + keyakinan,
alur Terima/Ubah/Tolak saran AI, deteksi pola otomatis, dan dashboard kinerja AI.

## Mematikan / mengulang dari nol
```bash
docker compose down          # matikan (data tetap)
docker compose down -v       # hapus semua data, lalu ulangi dari langkah 1
```

Folder `screenshot/` berisi contoh tampilan hasil akhirnya (GLPI 12 dengan data ini).
