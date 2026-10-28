# GLPI - HaloSIS

Paket ini menyalakan GLPI di laptop kamu lalu mengisinya dengan data contoh HaloSIS:
4 tim teknis, kategori layanan (SSO, FASIH, SiPecut, VPN, dll.), 15 pengguna contoh (lihat langkah 6),
SLA per prioritas, 12 tiket (lengkap dengan balasan, catatan internal, solusi),
5 artikel knowledge base, dan 1 "masalah" sebagai contoh pola insiden.

Di atas GLPI terpasang **plugin HaloSIS** (modul AI human-in-the-loop: chatbot Tanya HaloSIS, saran triase,
deteksi pola insiden, kandidat knowledge, dashboard kinerja AI) dan palet tema HaloSIS. Cara pakai, mode demo,
dan **skenario demo langkah demi langkah** ada di [`plugins/halosis/README.md`](plugins/halosis/README.md).

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

**Syarat:** Langkah 1–6 di bawah sudah selesai (GLPI menyala, plugin terpasang, data contoh sudah diisi).
Indeks chatbot merujuk artikel Knowledge Base hasil `seed_halosis.py`, jadi langkah 5 wajib dijalankan dulu.

**1. [Unduh folder `models` dan `index` dari sini](https://drive.google.com/drive/folders/1S_Cpm0qa0OoqGSC4-SFt-ZZfhaw9X87Y?usp=share_link)**
(login dengan akun Google yang diberi akses oleh pemilik repo). Isinya: `models/triage.joblib` (±40 MB) dan
`index/chunks.parquet` + `index/vectors.npy`.

Di Drive: pilih kedua folder (atau folder induknya) → klik kanan → **Download**. Drive mengemasnya jadi file
`.zip` (namanya bisa seperti `drive-download-20261028T…-001.zip`). Ekstrak: Mac → klik dua kali file zip;
Windows → klik kanan → **Extract All**.

> 🔒 **Untuk pemilik repo:** bagikan folder Drive ini **hanya ke akun Google anggota tim** (Bagikan › tambahkan
> email satu per satu, peran *Pelihat*). Jangan pakai akses umum "Siapa saja yang memiliki link": link di README
> ini bisa terbaca siapa pun yang membuka repo, dan isinya diturunkan dari data internal.

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

**3. Aktifkan API** (dibutuhkan skrip pengisi data dan layanan AI)
```bash
docker compose exec glpi php bin/console config:set enable_api 1 --allow-superuser
docker compose exec glpi php bin/console config:set enable_api_login_credentials 1 --allow-superuser
```
Kalau perintah di atas gagal karena path, ganti `bin/console` dengan `/var/www/glpi/bin/console`.
Atau lewat UI: **Setup › General › API** → aktifkan "Enable Rest API" dan "Enable login with credentials".

Request dari laptop masuk lewat gateway Docker, bukan `127.0.0.1`, sehingga API bisa menolak dengan
`ERROR_NOT_ALLOWED_IP`. Alamat gateway berbeda per sistem:

| Sistem | Alamat yang biasa terlihat |
| --- | --- |
| Docker Desktop Mac | `192.168.65.1` (rentang `192.168.65.0`–`192.168.65.255`, dipakai perintah di bawah) |
| Linux (Docker Engine) | umumnya `172.17.0.1` atau `172.18.x.x` (jaringan compose) |
| Windows (Docker Desktop) | bisa berbeda; jangan menebak |

**Lihat IP yang tercantum di pesan error** (mis. `ERROR_NOT_ALLOWED_IP ... 172.18.0.1`), lalu sesuaikan
rentang `INET_ATON('…')` awal & akhir pada perintah berikut (atau isian rentang IPv4 di UI API client) agar
mencakup IP itu. Contoh untuk Mac:
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

**5. Isi data contoh HaloSIS** (setelah langkah 4; aman dijalankan berulang)
```bash
python3 -m venv .venv && .venv/bin/pip install requests
.venv/bin/python seed_halosis.py http://localhost:8080
```
Tim, kategori, pengguna, dan SLA dicari dulu menurut nama lalu dibuat bila belum ada, jadi pengguna contoh baru
(mis. ketua tim) bisa ditambahkan ke database lama cukup dengan menjalankan ulang skrip ini. Tiket, artikel KB,
dan masalah contoh hanya dibuat pada run pertama.

**5b. SLA otomatis & peringatan risiko SLA** (BR-02, UC-08; aman dijalankan berulang)
```bash
.venv/bin/python setup_sla_alerts.py http://localhost:8080
docker compose exec glpi php bin/console config:set use_notifications 1 --allow-superuser
docker compose exec glpi php bin/console config:set notifications_ajax 1 --allow-superuser
```
Skrip ini hanya memakai fitur bawaan GLPI (lewat API, tanpa mengubah kode inti):
- **Aturan bisnis "SLA Kritis/Tinggi/Sedang/Rendah"** memasang SLA waktu penyelesaian menurut prioritas, saat tiket
  dibuat maupun saat prioritas diubah (mis. operator menerima saran triase). Tanpa aturan ini, laporan baru tidak
  punya SLA. Bisa diubah Administrator di menu **Workflow & aturan**.
- **Level eskalasi "Peringatan risiko SLA"** di tiap SLA, berjalan **sebelum** batas waktu: 1 jam (Kritis),
  1,5 jam (Tinggi), 4 jam (Sedang), 24 jam (Rendah).
- **Notifikasi "Ticket Recall"** dikirim ke teknisi & tim yang ditugaskan serta **supervisor tim (atasan)**, lewat
  notifikasi browser (tanpa server email) dan email (bila SMTP diatur).
- Penerima "atasan" adalah **ketua tim** masing-masing (`hendra`, `agus`, `rudi`, `wati`), yaitu supervisor grup
  yang dibuat `seed_halosis.py`. Skrip memperingatkan bila ada tim tanpa supervisor. Di produksi, tandai ketua
  tim sungguhan di **Tim teknis › (tim) › Pengguna › Supervisor**.

Aksi otomatis `slaticket` yang mengirim peringatan; cron container memeriksanya tiap menit. Untuk menguji tanpa
menunggu batas waktu, majukan jadwalnya lalu tunggu ±1 menit:
`UPDATE glpi_slalevels_tickets SET date = NOW() WHERE tickets_id = <id>`. Peringatan muncul di
`glpi_queuednotifications` (event `recall`) untuk teknisi & anggota tim serta ketua timnya.

**5c. Kolom daftar yang ringkas & warna prioritas/SLA** (konfigurasi GLPI, tanpa kode; aman dijalankan berulang)
```bash
.venv/bin/python setup_list_columns.py http://localhost:8080
docker compose exec glpi php bin/console config:set priority_6 '#c92a2a' --allow-superuser   # Mayor
docker compose exec glpi php bin/console config:set priority_5 '#e03131' --allow-superuser   # Sangat tinggi
docker compose exec glpi php bin/console config:set priority_4 '#f76707' --allow-superuser   # Tinggi
docker compose exec glpi php bin/console config:set priority_3 '#f59f00' --allow-superuser   # Sedang
docker compose exec glpi php bin/console config:set priority_2 '#868e96' --allow-superuser   # Rendah
docker compose exec glpi php bin/console config:set priority_1 '#adb5bd' --allow-superuser   # Sangat rendah
docker compose exec glpi php bin/console config:set duedateok_color '#2f9e44' --allow-superuser
docker compose exec glpi php bin/console config:set duedatewarning_color '#f76707' --allow-superuser
docker compose exec glpi php bin/console config:set duedatecritical_color '#e03131' --allow-superuser
```
Warna di atas menjadi **titik** pada pill prioritas/SLA di tabel (palet membuat pill lembut + titik).

`setup_list_columns.py` menulis *Display preferences* global (Administrasi › … › ikon "pilih kolom"). GLPI selalu
menambahkan kolom **ID** dan **nama/judul**; berikut kolom tambahannya (kiri → kanan):

| Daftar (menu) | Kolom tambahan | Dibuang (alasan) |
| --- | --- | --- |
| Tiket — Antrean validasi & Semua tiket (Operator) | Status, Prioritas, Kategori, Pemohon, Grup teknisi, Waktu untuk menyelesaikan, Terakhir diperbarui | Tanggal buka (dobel tanggal), Teknisi (Operator menugaskan ke tim) |
| Tiket — Tiket saya & tim (kolom pribadi tiap pengguna Tim Teknis) | Status, Prioritas, Kategori, Pemohon, Teknisi, Waktu untuk menyelesaikan, Terakhir diperbarui | Grup teknisi (sudah tersaring ke tim sendiri), Tanggal buka |
| Tiket — Laporan saya (Pegawai, Helpdesk) | Status, Kategori, Terakhir diperbarui | Tanggal buka (dobel tanggal) |
| Masalah / pola insiden | Status, Prioritas, Kategori, Jumlah tiket, Tanggal buka | Deskripsi (panjang), Waktu untuk menyelesaikan (kosong untuk pola) |
| Knowledge Base (Daftar artikel) | Kategori, FAQ, Pengguna (penulis), Tampilan, Terakhir diperbarui | Parent article, Unsur terkait (kosong) |
| Pengguna | Nama depan, Nama belakang, Email, Profil (Entitas), Grup, Aktif, Terakhir login | Telepon, Lokasi (kosong) |
| Tim (Grup) | Manager (ketua tim), Jumlah pengguna, Bisa ditugaskan | Komentar (kosong) |
| Kategori layanan (ITIL) | Grup, Jumlah tiket, Terlihat untuk insiden / permintaan / antarmuka sederhana | — |
| SLA / SLM | SLM, Tipe, Waktu / Kalender | — |
| Workflow & aturan (aturan tiket) | Kolom tetap bawaan GLPI (Nama, Deskripsi, Dipakai untuk, Kriteria, Tindakan, Aktif, Posisi) | Daftar aturan bukan mesin pencarian, kolomnya tidak bisa diatur preferensi |

Urutan default **Antrean validasi, Tiket saya & tim, Monitoring SLA**: "Waktu untuk menyelesaikan" terdekat dulu
(URL menu ringkas di `plugins/halosis/src/RoleMenu.php`).

Batasan GLPI: preferensi kolom berlaku per *itemtype* (dan per pengguna), **bukan per URL pencarian**. Antrean
validasi dan Semua tiket sama-sama daftar Tiket milik Operator, jadi kolom Status tetap tampil di antrean
(isinya selalu "Baru") karena dibutuhkan di Semua tiket. Pengguna yang berhak (hak *Search config*) tetap bisa
mengubah kolomnya sendiri; menjalankan ulang skrip menimpa kolom global & kolom pribadi Tim Teknis.

**6. Login sebagai role berbeda** (password semua: `halosis`)

Role mengikuti aktor pada dokumen perancangan (Tabel 6.1, UC-01 s.d. UC-10):

| Login | Nama | Profil GLPI (role HaloSIS) | Aktor dokumen | Use case | Antarmuka | Keterangan |
| --- | --- | --- | --- | --- | --- | --- |
| budi, siti, maya | Budi Santoso, dkk. | Pegawai | Pegawai BPS (Requester) | UC-01, UC-03, UC-07 | Helpdesk (sederhana) | Chatbot, lapor & pantau tiket |
| rina | Rina Wulandari | Operator | Operator HaloSIS ⊂ Petugas Layanan TI | UC-05, UC-08 | Standar | Validasi saran AI & teruskan tiket; ubah Masalah (pola insiden) |
| andi, yoga | Andi Pratama, Yoga Saputra | Tim Teknis | Tim Teknis (Resolver) ⊂ Petugas Layanan TI | UC-06, UC-08 | Standar | Tim Aplikasi Statistik |
| fajar | Fajar Nugroho | Tim Teknis | Tim Teknis (Resolver) ⊂ Petugas Layanan TI | UC-06, UC-08 | Standar | Tim Identitas & Akses |
| dedi | Dedi Kurniawan | Tim Teknis | Tim Teknis (Resolver) ⊂ Petugas Layanan TI | UC-06, UC-08 | Standar | Tim Jaringan |
| hendra | Hendra Wijaya | Tim Teknis | Tim Teknis (Resolver) ⊂ Petugas Layanan TI | UC-06, UC-08 | Standar | **Ketua Tim Aplikasi Statistik** (supervisor grup); penerima "atasan" peringatan risiko SLA (BR-02) |
| agus | Agus Setiawan | Tim Teknis | Tim Teknis (Resolver) ⊂ Petugas Layanan TI | UC-06, UC-08 | Standar | **Ketua Tim Jaringan** (supervisor grup); penerima "atasan" peringatan risiko SLA (BR-02) |
| rudi | Rudi Hermawan | Tim Teknis | Tim Teknis (Resolver) ⊂ Petugas Layanan TI | UC-06, UC-08 | Standar | **Ketua Tim Perangkat** (supervisor grup); penerima "atasan" peringatan risiko SLA (BR-02) |
| wati | Wati Susanti | Tim Teknis | Tim Teknis (Resolver) ⊂ Petugas Layanan TI | UC-06, UC-08 | Standar | **Ketua Tim Identitas & Akses** (supervisor grup); penerima "atasan" peringatan risiko SLA (BR-02) |
| sri | Sri Handayani | Manajemen | Manajemen / Pimpinan | UC-08 | Standar | Hanya-baca: tiket, Masalah, dashboard, statistik |
| lina | Lina Marlina | Knowledge Manager | Knowledge Manager | UC-09 | Standar | Kelola Knowledge Base & Kandidat Knowledge; tiket hanya-baca |
| dimas | Dimas Aditya | Administrator | Administrator Sistem | UC-10 | Standar | Konfigurasi platform (katalog, SLA, tim, aturan, AI) |
| — | — | — | Petugas Layanan TI (abstrak) | UC-08 | — | Aktor induk Operator + Tim Teknis, tanpa akun sendiri: kemampuan bersama Monitoring SLA & Masalah (pola insiden) |
| — | — | — | AI Engine (aktor sistem) | UC-02, UC-04 | — | Layanan `halosis-ai` (lihat [`ai/README.md`](ai/README.md)) |
| glpi | — | Super-Admin | **Di luar aktor dokumen** | — | Standar | Akun pengelola sistem (instalasi, plugin, profil); bukan role bisnis |

Database yang diisi dengan versi seed lama (belum ada `dimas` atau ketua tim): jalankan ulang langkah 5
lalu 5b; hanya pengguna yang belum ada yang dibuat.

Hak inti GLPI untuk UC-08 (diatur `setup-roles`):

| Hak | Operator | Tim Teknis | Manajemen |
| --- | --- | --- | --- |
| Monitoring SLA (tiket melewati batas waktu) | lihat | lihat | lihat |
| Masalah / pola insiden | lihat & ubah (konfirmasi/tutup pola, tautkan tiket, FR-04) | lihat | lihat |

Untuk UC-10, `setup-roles` juga memberi **Administrator** hak service catalog (form) dan notifikasi (`notification`:
lihat, ubah, buat, hapus), serta **audit trail** (`system_logs`: lihat log sistem); semuanya tidak termasuk hak
bawaan profil Admin GLPI.

**Notifikasi untuk Administrator (UC-10) — apa yang bisa & tidak.** GLPI 12 hanya memisahkan *aturan notifikasi*
dari hak `config`. Template dan pengaturan pengiriman tetap dijaga `config` di kode inti GLPI
(`NotificationTemplate::$rightname = 'config'`, `NotificationSetting::$rightname = 'config'`, dan halaman pengaturan
email/browser memeriksa `config` UPDATE). Hak `config` penuh **tidak** diberikan ke Administrator karena juga membuka
Setup › Umum, plugin, autentikasi, dan seluruh konfigurasi sistem.

| Yang dikonfigurasi | `dimas` (Administrator) | Hak GLPI |
| --- | --- | --- |
| Daftar notifikasi: aktif/nonaktif, event, penerima (teknisi, grup, supervisor, profil…), template mana yang dipakai | ✓ ubah | `notification` |
| Isi template notifikasi (subjek & isi email/browser) | — (Super-Admin) | `config` |
| Pengaturan pengiriman: notifikasi aktif, SMTP, notifikasi browser | — (Super-Admin) | `config` |

Opsi bila Administrator perlu mengubah isi template atau mengaktifkan saluran tanpa `config`: halaman
**"Pengaturan notifikasi" ringkas di plugin HaloSIS** (dijaga hak plugin sendiri) yang hanya membuka subjek/isi
template HaloSIS (mis. Ticket Recall) dan sakelar email/browser; plugin yang menyimpannya di sisi server. Belum dibuat.

Hak plugin HaloSIS (bisa diubah di **Administrasi › Profil › (profil) › tab HaloSIS**):

| Hak | Pegawai | Operator | Tim Teknis | Manajemen | Knowledge Manager | Administrator | Super-Admin |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Chatbot | ✓ | | | | | | |
| Saran triase AI | | lihat & putuskan | lihat | | | lihat & putuskan | lihat & putuskan |
| Dashboard kinerja AI | | | | ✓ | | ✓ | ✓ |
| Kandidat Knowledge (UC-09) | | | | | lihat & putuskan | lihat & putuskan | lihat & putuskan |
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

Palet ada di `themes/halosis.scss` (di-mount ke `/var/glpi-themes`, folder tema kustom GLPI lewat variabel
`GLPI_THEMES_DIR` di `docker-compose.yml`).
Jadikan default untuk semua pengguna:
```bash
docker compose exec glpi php bin/console config:set palette halosis --allow-superuser
docker compose exec glpi php bin/console config:set language id_ID --allow-superuser
docker compose exec glpi php bin/console config:set text_login '<p style="text-align:center">Selamat datang di <strong>HaloSIS</strong>, layanan TI BPS.<br>Masuk dengan akun dinas Anda.</p>' --allow-superuser
```
Judul beranda Helpdesk: **Administrasi › Entitas › BPS › Helpdesk** → judul kustom "Halo, ada yang bisa kami bantu?".

Catatan palet: GLPI memakai variabel `secondary` juga sebagai warna teks, jadi variabelnya diisi versi gelap
`#4C786E` agar terbaca (kontras ≥ 4,5:1 di putih maupun latar `#F5F8F6`); `#77B8A8` dipakai sebagai latar
(tombol sekunder, `.bg-secondary`). Badge memakai accent `#FF965A` dengan teks `#203332`.

**Logo:** tanda logo dari `plugins/halosis/public/logo/` (file asli `logo-sidebar.webp` & `logo-loginwebp` berlatar
pola kotak-kotak tercetak, jadi dibuat versi transparan tanpa mengubah bentuk: `halosis-logo-light.png` putih
untuk sidebar primary, `halosis-logo-dark.png` hitam untuk login & header Helpdesk, PNG 192px). Dipasang lewat
variabel `--glpi-logo-*`; tulisan "HaloSIS" ditambahkan dengan CSS `::after` (font Plus Jakarta Sans). Sidebar
diciutkan: hanya tanda logo. **Favicon tidak bisa diganti** tanpa mengubah GLPI: tautannya ditulis langsung di
template inti (`templates/layout/parts/head.html.twig` → `/pics/favicon.ico`), dan tema/CSS tidak bisa mengatur
favicon.

Tampilan mengikuti prototipe `halosis-web` **tanpa mengubah GLPI** (NFR-10): hanya palet ini + CSS/aset plugin.
- Judul Plus Jakarta Sans (di-host lokal di `plugins/halosis/public/fonts`, lisensi OFL, tanpa CDN); teks Inter
  bawaan GLPI. Kartu 16px, tombol & input 10px, badge pill, bayangan halus, tabel daftar lebih lega.
- Antarmuka Helpdesk (Pegawai) memakai header putih seperti prototipe; sidebar petugas tetap primary.
- Header notifikasi info & peringatan GLPI disesuaikan agar kontras teks memenuhi WCAG AA.
- **Semua tabel daftar** (tiket, masalah, KB, pengguna, grup, kategori, SLA, aturan, log): kartu membulat, header
  11px huruf kapital, isi 14px, garis tipis & hover baris; kolom nama/judul min. 260px (maks. 2 baris); ID,
  tanggal, status & prioritas tidak terpotong; kolom lain satu baris dengan ellipsis (lengkap saat baris
  disorot). Prioritas, status, dan "Waktu untuk menyelesaikan" menjadi pill lembut + titik warna. Header sticky,
  gulir horizontal, sorting, aksi massal, pagination, pilih kolom, tampilan peta tetap bawaan GLPI.
- **Rollback:** `config:set palette auror` (palet bawaan GLPI) → semua gaya & logo HaloSIS lepas; halaman plugin
  ikut font GLPI. Kembalikan dengan `config:set palette halosis`. Kolom daftar & warna prioritas/SLA (langkah 5c)
  adalah data konfigurasi, bukan palet: kembalikan bila perlu dengan mengatur ulang kolom lewat ikon "pilih kolom", dan nilai awal
  GLPI `priority_1..6` = `#fff2f2 #ffe0e0 #ffcece #ffbfbf #ffadad #ff5555`, `duedateok_color #06ff00`,
  `duedatewarning_color #ffb800`, `duedatecritical_color #ff0000`.

## Peta HaloSIS → menu GLPI

| Halaman HaloSIS | Di GLPI |
| --- | --- |
| Laporan Saya, Detail Laporan (pegawai) | Login pegawai → **Tiket** (antarmuka sederhana/Helpdesk) |
| Buat Laporan | **Service catalog** / Create a ticket |
| Pusat Bantuan | **FAQ** (artikel KB yang ditandai FAQ) |
| Migrasi data (FR-10) | `ai/scripts/prepare_data.py` (pembersihan & penyamaran) + `ai/scripts/reconcile.py` → `reports/rekonsiliasi.md`: jumlah sumber/berhasil/gagal, tidak lengkap, duplikat, nilai disamarkan per jenis, per bulan & per tim (lihat [`ai/README.md`](ai/README.md#fr-10--rekonsiliasi-migrasi)) |
| Konfirmasi "sudah beres / belum beres" (UC-07) | Tombol **Approve / Refuse** pada solusi tiket. *Refuse* wajib disertai alasan (ditegakkan GLPI) dan membuka kembali tiket ke tim |
| Kembalikan ke operator, salah tim (UC-06 alur alternatif) | Panel **Saran AI** di tiket → *Kembalikan ke operator (salah tim)*, alasan wajib (plugin) |
| Peringatan risiko SLA (BR-02) | Level eskalasi SLA + notifikasi **Ticket Recall** (langkah 5b) |
| Antrean validasi & Semua tiket (operator) | **Bantuan › Tiket** (filter status Baru) |
| Tiket saya & tim (Tim Teknis) | Beranda **Tampilan Personal / Tampilan Group** |
| Komentar publik / catatan internal | **Answer › Followup** (centang *Private* untuk internal), **Task** |
| Monitoring SLA | Kolom "Waktu untuk menyelesaikan" + **Setup › Service levels** |
| Pola insiden | **Bantuan › Masalah** (tiket ditautkan ke masalah) |
| Knowledge base (KM) | **Tools › Basisdata pengetahuan** |
| Kandidat Knowledge (KM, UC-09) | Menu **Kandidat knowledge** (plugin): solusi tiket selesai & solusi berulang dari indeks AI → *Jadikan artikel* (draf KB) / *Abaikan* (dengan alasan) |
| Dashboard manajemen, laporan | **Bantuan › Dashboard**, **Bantuan › Statistik** |
| Service catalog, tim, pengguna & role | **Setup › Dropdowns › ITIL categories**, **Administrasi › Groups / Users / Profil** (nama profil = role HaloSIS) |
| Workflow & aturan otomatis | **Administrasi › Rules › Business rules for tickets** |
| Audit trail | Tab **Riwayat** di setiap tiket/objek |

**Tidak ada di GLPI** (tetap dibangun sendiri di HaloSIS): chatbot AI, saran triase + keyakinan,
alur Terima/Ubah/Tolak saran AI, deteksi pola otomatis, kandidat knowledge, dan dashboard kinerja AI.

## Mematikan / mengulang dari nol
```bash
docker compose down          # matikan (data tetap)
docker compose down -v       # hapus semua data, lalu ulangi dari langkah 1
```

Folder `screenshot/` berisi contoh tampilan hasil akhirnya (GLPI 12 dengan data ini).
