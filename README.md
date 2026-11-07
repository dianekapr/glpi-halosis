# HaloSIS — layanan bantuan TI BPS dengan asisten AI

## Apa ini?

HaloSIS adalah aplikasi **layanan bantuan TI (helpdesk)** untuk pegawai BPS. Pegawai yang punya kendala TI
(misalnya aplikasi FASIH gagal sinkron, VPN putus, lupa password) cukup bertanya ke **asisten chat**. Bila asisten
tidak bisa menyelesaikan, laporan dibuat otomatis dan diteruskan ke tim TI yang tepat.

AI di sini **membantu, bukan memutuskan**: AI menyarankan kategori, tim, dan tingkat kepentingan laporan, lalu
petugas (Operator) yang menerima, mengubah, atau menolak sarannya. HaloSIS dibangun di atas
[GLPI](https://glpi-project.org) (aplikasi helpdesk sumber terbuka) dengan tambahan *plugin* HaloSIS.

Paket ini menyalakan semuanya **di laptop sendiri** dan mengisinya dengan **data contoh** (pengguna, tim, laporan,
artikel bantuan), jadi bisa langsung dicoba tanpa internet kantor dan tanpa data asli.

**Siapa melakukan apa**

| Peran | Akun contoh | Yang dilakukan di HaloSIS |
| --- | --- | --- |
| Pegawai | `budi`, `siti`, `maya` | Bertanya ke asisten chat, membuat laporan, memantau dan menyetujui penyelesaian |
| Operator layanan | `rina` | Memeriksa laporan baru beserta saran AI, lalu meneruskannya ke tim teknis |
| Tim teknis | `andi`, `fajar`, `dedi`, … | Mengerjakan laporan dan menulis solusinya |
| Pengelola pengetahuan | `lina` | Menjadikan solusi yang sering dipakai sebagai artikel bantuan |
| Manajemen | `sri` | Melihat dashboard kinerja layanan dan AI |
| Administrator | `dimas` | Mengatur layanan, SLA (batas waktu), dan pengaturan AI |

Password semua akun contoh: **`halosis`**. Daftar lengkap ada di [Pemasangan manual › langkah 6](#pemasangan-manual-yang-dijalankan-scriptspasangsh).

## Cara memasang di laptop (untuk pemula)

Tidak perlu bisa memrogram. Ikuti 5 langkah ini berurutan; cukup dilakukan **sekali**.

### Langkah 1 — Pasang tiga aplikasi

| Aplikasi | Gunanya | Unduh |
| --- | --- | --- |
| **Docker Desktop** | "Wadah" yang menjalankan HaloSIS di laptop | https://www.docker.com/products/docker-desktop |
| **Git** | Mengambil kode HaloSIS dari GitHub | Mac: sudah ada (lihat langkah 2). Windows: https://git-scm.com/download/win (klik *Next* terus) |
| **Python 3** | Mengisi data contoh | Mac: biasanya sudah ada. Windows: https://www.python.org/downloads (**centang "Add python.exe to PATH"**) |

Setelah memasang Docker Desktop, **buka aplikasinya** dan tunggu sampai ikon paus 🐳 di pojok layar berhenti
bergerak. Laptop sebaiknya punya RAM minimal 8 GB dan ruang kosong ±15 GB.

### Langkah 2 — Buka Terminal

Terminal adalah jendela untuk mengetik perintah. Cukup salin-tempel perintah dari panduan ini, lalu tekan **Enter**.

- **Mac:** tekan `⌘ Command` + `Spasi`, ketik **Terminal**, tekan Enter.
- **Windows:** klik Start, ketik **Git Bash**, buka aplikasinya (jangan pakai Command Prompt).

Cek ketiga aplikasi sudah terpasang (masing-masing harus menampilkan nomor versi, bukan pesan galat):
```bash
docker --version
git --version
python3 --version      # Windows: python --version
```
Di Mac, bila muncul tawaran memasang *command line developer tools* saat mengetik `git`, klik **Install**.

### Langkah 3 — Ambil kode HaloSIS

Salin-tempel tiga baris ini ke Terminal (satu per satu, tekan Enter tiap baris):
```bash
cd ~/Downloads
git clone https://github.com/dianekapr/glpi-halosis.git
cd glpi-halosis
```
Kode tersimpan di folder **Downloads › glpi-halosis**. (Bila diminta login GitHub, minta akses ke pemilik repo.)

### Langkah 4 — Jalankan pemasangan otomatis

Masih di Terminal yang sama, ketik:
```bash
scripts/pasang.sh
```
Perintah ini menyalakan HaloSIS, memasang plugin, dan mengisi data contoh. **Pertama kali bisa 10–20 menit**
(mengunduh beberapa GB) — biarkan sampai muncul tulisan **"Selesai!"**. Kalau muncul tulisan merah **GAGAL**, baca
pesannya (biasanya Docker belum dibuka) lalu ulangi perintah yang sama; aman dijalankan berkali-kali.

### Langkah 5 — Buka HaloSIS di browser

Buka **http://localhost:8080** di Chrome/Edge/Safari, lalu login **`budi`** / **`halosis`**. Anda langsung masuk ke
**Tanya HaloSIS** (asisten chat). Selamat, HaloSIS sudah berjalan! Lanjutkan dengan tur di bawah.

> Tanpa file model AI, HaloSIS memakai **mode demo** (jawaban contoh yang tetap). Untuk AI sungguhan dari history
> tiket, anggota tim memasang file model sesuai bagian [C2](#c2-pasang-model-ai-dari-google-drive-untuk-penguji).

## Tur 10 menit: coba satu laporan dari awal sampai selesai

Pakai **jendela penyamaran/privat** baru untuk setiap akun, supaya bisa login sebagai beberapa orang sekaligus.

1. **Pegawai bertanya** — login `budi`. Klik **Laporkan masalah**, lalu klik contoh **FASIH gagal sinkron**.
   Asisten menjawab dengan langkah-langkah dari artikel bantuan.
2. **Pegawai membuat laporan** — di bawah jawaban klik **Belum terselesaikan** → **Ya, buat laporan** →
   **Kirim laporan**. Ringkasan percakapan ikut terlampir, jadi pegawai tidak perlu menjelaskan ulang.
3. **Operator memeriksa saran AI** — login `rina`, buka menu **Antrean validasi**, buka laporan tadi. Panel
   **Saran AI** menunjukkan kategori, tim, dan tingkat keyakinan AI. Klik **Terima** (atau **Ubah**/**Tolak**
   dengan alasan).
4. **Tim teknis menyelesaikan** — login `andi`, buka menu **Tiket saya & tim**, buka laporan tadi, lalu klik
   **Answer ▾ › Add a solution** (beberapa tombol bawaan GLPI masih berbahasa Inggris), tulis solusinya, simpan.
5. **Pegawai menyetujui** — login `budi`, buka **Laporan saya**, buka laporannya, klik **Approve** (setujui solusi).
   Laporan pun **Ditutup**.
6. **Manajemen melihat hasil** — login `sri`, buka **Kinerja AI**: berapa saran AI yang diterima, diubah, ditolak,
   dan kepatuhan SLA.

Skenario lengkap (termasuk pola insiden, artikel bantuan, dan pengaturan) ada di
[`plugins/halosis/README.md`](plugins/halosis/README.md#skenario-demo-langkah-demi-langkah).

## Menyalakan, mematikan, dan mengulang

Jalankan dari Terminal di folder `glpi-halosis` (`cd ~/Downloads/glpi-halosis`):

| Mau apa | Perintah |
| --- | --- |
| Mematikan HaloSIS (data tetap tersimpan) | `docker compose down` |
| Menyalakan lagi besok | Buka Docker Desktop, lalu `docker compose up -d`, tunggu ±1 menit |
| Menyimpan kondisi sebelum demo | `scripts/demo_snapshot.sh simpan` |
| Kembali ke kondisi yang disimpan | `scripts/demo_snapshot.sh pulihkan` |
| Menghapus **semua** data lalu mulai dari nol | `docker compose down -v` lalu `scripts/pasang.sh` |

## Kalau ada masalah

| Yang terlihat | Coba ini |
| --- | --- |
| `GAGAL: Docker belum menyala` / `Cannot connect to the Docker daemon` | Buka aplikasi Docker Desktop, tunggu ikon paus diam, ulangi perintah |
| `command not found: python3` (Windows) | Pasang ulang Python dan centang **Add python.exe to PATH**, lalu tutup & buka lagi Git Bash |
| `permission denied: scripts/pasang.sh` | Ketik `bash scripts/pasang.sh` |
| Halaman http://localhost:8080 tidak terbuka | Tunggu 1–2 menit setelah menyalakan, lalu muat ulang. Cek Docker Desktop menyala |
| Login `budi` ditolak padahal password benar | Salah password 5× membuat akun terkunci ±15 menit. Tunggu, lalu coba lagi |
| Tidak bisa login sama sekali | Login darurat `glpi` / `glpi` tetap bisa; laporkan ke pemilik repo |
| Laptop jadi lambat | Matikan HaloSIS saat tidak dipakai (`docker compose down`) |
| Masalah lain | Simpan tulisan galatnya (screenshot), kirim ke pemilik repo |

**Alamat yang perlu diketahui**

| Alamat | Isinya |
| --- | --- |
| http://localhost:8080 | Aplikasi HaloSIS |
| http://localhost:8025 | Kotak masuk email uji (semua email HaloSIS ditahan di sini, tidak terkirim ke luar) |
| http://localhost:8180 | Pengelola akun/SSO (Keycloak; login `admin` / `admin`) — untuk administrator |

---

# Bagian untuk anggota tim & rincian teknis

Bagian di bawah ini untuk anggota tim yang ikut mengembangkan atau perlu tahu cara kerjanya. Pengguna yang hanya
mencoba HaloSIS cukup membaca bagian di atas.

**Ringkas teknis:** GLPI 12 + **plugin HaloSIS** (chatbot Tanya HaloSIS, saran triase, deteksi pola insiden,
kandidat knowledge, pengingat progres, dashboard kinerja AI) + palet tema HaloSIS + layanan AI lokal `halosis-ai` +
**login SSO Keycloak** (pengganti SSO BPS; password dicek ke Keycloak di belakang layar, akun/role/tim diatur di
Keycloak). Data contoh: 4 tim teknis, kategori layanan (SSO, FASIH, SiPecut, VPN, dll.), 15 pengguna contoh, SLA
resmi BPS, 12 tiket, artikel knowledge base, dan 1 "masalah" contoh pola insiden. Cara pakai fitur & skenario demo:
[`plugins/halosis/README.md`](plugins/halosis/README.md).

## Untuk anggota tim: mulai dari link GitHub

Untuk anggota tim yang ikut mengubah kode. Belum pernah pakai Git/GitHub? Ikuti dari atas sampai bawah. Cukup
sekali di langkah A–C; langkah D dipakai setiap kali kamu bekerja.

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

Jalankan `scripts/pasang.sh` (sama dengan [Langkah 4 pemula](#langkah-4--jalankan-pemasangan-otomatis)); rincian tiap
langkahnya ada di [Pemasangan manual](#pemasangan-manual-yang-dijalankan-scriptspasangsh). Catatan untuk anggota tim:

- `docker compose up -d` pertama kali juga membangun layanan AI (`halosis-ai`), mengunduh Keycloak, dan
  mengunduh beberapa GB; bisa 10–20 menit. Selanjutnya cepat.
- **Sudah punya `.env` dari sebelumnya?** Salin blok `HALOSIS_KEYCLOAK_*` dari `.env.example` ke `.env`, lalu
  `docker compose up -d`. Tanpa blok itu SSO mati dan login memakai password lokal GLPI.
- **Data history tiket, model AI, dan indeks pencarian TIDAK ada di GitHub** (berisi data pribadi, lihat
  [`ai/README.md`](ai/README.md)). Siapa perlu apa:

  | Kebutuhan | Yang diperlukan |
  | --- | --- |
  | Menjalankan & menguji GLPI + plugin | Tidak perlu data apa pun. `seed_halosis.py` mengisi data contoh; tanpa model AI, plugin otomatis memakai **mode demo** |
  | **Menguji end-to-end dengan AI sungguhan** (saran triase dari model, chatbot dari artikel KB terbit & katalog layanan) | Folder `ai/models/` dan `ai/index/` dari pemilik repo. **Tidak perlu file Excel** |
  | Melatih ulang model dari Excel | Hanya 1–2 orang yang mengurus AI; ikuti [`ai/README.md`](ai/README.md) |

  Cara memasangnya ada di bagian **C2** di bawah.
- Windows: ganti `.venv/bin/python` dengan `.venv\Scripts\python` dan `.venv/bin/pip` dengan `.venv\Scripts\pip`.

### C2. Pasang model AI dari Google Drive (untuk penguji)

> ⚠️ Isi folder ini diturunkan dari history tiket BPS (sudah disamarkan, tetapi tetap **data internal**).
> Jangan unggah ulang, jangan kirim ke orang lain/grup chat, dan jangan di-commit ke GitHub.

**Syarat:** `scripts/pasang.sh` sudah selesai (GLPI menyala, plugin terpasang, data contoh sudah diisi).
Indeks chatbot merujuk artikel Knowledge Base hasil `seed_halosis.py`, jadi langkah 5 wajib dijalankan dulu.

**1. Unduh dari Google Drive** (login dengan akun Google yang diberi akses oleh pemilik repo):

| Yang diunduh | Untuk siapa | Link |
| --- | --- | --- |
| Folder **`models`** (model AI) | Semua penguji | [Google Drive](https://drive.google.com/drive/folders/1XFP020tMVDOuHLvurjcnKSUjHqCVmYlS?usp=share_link) |
| Folder **`index`** (indeks pencarian chatbot) | Semua penguji | [Google Drive](https://drive.google.com/drive/folders/1XFP020tMVDOuHLvurjcnKSUjHqCVmYlS?usp=share_link) |
| **Data ticketing** (Excel history tiket mentah) | **Hanya Pengelola AI** yang melatih ulang model ([`ai/README.md`](ai/README.md)); penguji **tidak perlu** | [Google Drive](https://drive.google.com/drive/folders/1XFP020tMVDOuHLvurjcnKSUjHqCVmYlS?usp=share_link) |

Ketiganya ada di folder Drive yang sama; unduh hanya yang Anda perlukan. File data ticketing disimpan di
`data/raw/` (di-ignore git) dan **tidak boleh** disalin ke tempat lain.

Isi `models` + `index` **7 file**: `models/triage.joblib` (±40 MB,
saran tim) + `models/triage.metrics.json` (metrik gerbang kualitas), `models/jenis.joblib` (saran jenis REQ/INC),
`models/urgensi.joblib` + `models/urgensi.metrics.json` (saran urgensi insiden), dan `index/chunks.parquet` +
`index/vectors.npy`. Versi 31 Okt 2026 dilatih dari **ekspor history versi baru** (220 kolom); `prioritas.joblib`
lama tidak dipakai lagi — hapus bila masih ada di folder Anda (pemilik repo: hapus juga dari Drive dan unggah
ulang ketujuh file ini).
**Anggota tim tidak melatih ulang model**: cukup pakai file ini (melatih ulang butuh data history mentah yang hanya
dipegang Pengelola AI; lihat `reports/tata_kelola_ai.md`). Tanpa berkas opsional (`jenis`/`urgensi`), panel hanya
tidak menampilkan saran itu; tanpa `triage.metrics.json` model triase dinyatakan belum lolos uji kualitas.

Di Drive: pilih kedua folder (atau folder induknya) → klik kanan → **Download**. Drive mengemasnya jadi file
`.zip` (namanya bisa seperti `drive-download-20261028T…-001.zip`). Ekstrak: Mac → klik dua kali file zip;
Windows → klik kanan → **Extract All**.

> 🔒 **Untuk pemilik repo:** repo ini **publik**, jadi link di atas terbaca siapa pun. Bagikan folder Drive
> **hanya ke akun Google anggota tim** (Bagikan › tambahkan email satu per satu, peran *Pelihat*); jangan pakai akses
> umum "Siapa saja yang memiliki link". **Data ticketing berisi data pribadi mentah**: sebaiknya ditaruh di folder
> Drive terpisah yang hanya dibagikan ke Pengelola AI.

**2. Taruh di folder proyek** sehingga susunannya **persis** seperti ini (nama huruf kecil semua):
```text
glpi-halosis/
└── ai/
    ├── models/
    │   ├── triage.joblib
    │   ├── triage.metrics.json
    │   ├── jenis.joblib
    │   ├── urgensi.joblib
    │   └── urgensi.metrics.json
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
Harus terlihat tepat enam file di atas.

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
Metrik: http://localhost:8001/metrics

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
- Login `budi` / `halosis` → langsung di **Tanya HaloSIS** dengan kartu *Ajukan permintaan* & *Laporkan masalah*.
- Klik **Laporkan masalah** → tanya *"kuota email saya penuh"* → jawaban punya sumber artikel KB atau layanan
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

### C3. Update untuk anggota tim (setiap kali `git pull` membawa perubahan plugin/AI)

**Cara singkat** (aman diulang): `git pull && docker compose up -d --build halosis-ai && scripts/pasang.sh`.

> **Anggota tim yang sudah clone sebelum 2 Nov 2026: jalankan ulang `scripts/pasang.sh` sekali.** Gejala bila belum:
> halaman login/menu tampil berbahasa Inggris di browser berbahasa Inggris ("Login to your account", "Welcome to
> HaloSIS"). Penyebabnya bukan berkas `.mo` (ikut git), melainkan instalasi lama: bahasa bawaan GLPI belum id_ID,
> label inti belum disalin ke `files/_locales/core_halosis`, dan cache terjemahan GLPI masih versi lama. Sejak
> versi ini plugin memaksa halaman login berbahasa Indonesia dan memasang ulang terjemahan + mengosongkan cache
> terjemahan otomatis bila berkas `.mo` berubah setelah `git pull` (`LoginPage::syncLocales`); `pasang.sh` juga
> menyetel bahasa bawaan & bahasa akun demo ke id_ID.

Rinciannya, bila ingin menjalankan satu per satu dari folder repo (aman diulang). Urutan penting: `halosis-ai` harus
hidup **sebelum** install plugin, karena install juga mengisi katalog layanan ke indeks chatbot.

```bash
git pull
docker compose up -d --build halosis-ai                          # kode layanan AI terbaru (tunggu /health "ok")
curl -s localhost:8001/health
docker compose exec glpi php bin/console plugin:install halosis -u glpi --force --allow-superuser   # tabel/config baru + katalog layanan → indeks
docker compose exec glpi php bin/console plugin:activate halosis --allow-superuser
docker compose exec glpi php bin/console plugins:halosis:setup-roles --allow-superuser             # role & hak (mis. hapus tiket hanya Super-Admin)
.venv/bin/python setup_sla_alerts.py http://localhost:8080        # SLA respons & penyelesaian, notifikasi
.venv/bin/python setup_pejabat_rules.py http://localhost:8080     # grup Pejabat + aturan urgensi +1 pemohon pejabat
.venv/bin/python setup_list_columns.py http://localhost:8080      # kolom daftar (mis. Waktu untuk mengambil alih)
docker compose exec glpi php bin/console cache:clear --allow-superuser                             # template/CSS plugin terbaru
```

- **Impor ulang realm Keycloak** hanya bila `keycloak/halosis-realm.json` berubah (mis. atribut NIP/unit/jabatan).
  Ini menghapus **data Keycloak saja** (akun & role dibuat ulang dari JSON; data GLPI tidak tersentuh):
  `docker compose stop keycloak && docker compose rm -f keycloak && docker volume rm glpi-halosis_keycloak_data && docker compose up -d keycloak`
- **Katalog layanan belum masuk indeks** (cek: `curl -s localhost:8001/metrics | grep index_chunks`): ulangi
  `plugin:install` saat `halosis-ai` hidup, atau simpan ulang salah satu kategori di Pengaturan › Daftar pilihan › Kategori ITIL.
- Sebelum demo: `scripts/demo_snapshot.sh simpan`; kembali ke kondisi itu: `scripts/demo_snapshot.sh pulihkan`
  (lihat `reports/checklist_demo.md`).

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

## Pemasangan manual (yang dijalankan `scripts/pasang.sh`)

Langkah 1–7 di bawah adalah isi `scripts/pasang.sh`, dengan penjelasan tiap pengaturan. Pakai bagian ini bila
skrip gagal di langkah tertentu, atau untuk memasang di server. Butuh Docker Desktop (Mac/Windows) atau Docker
Engine (Linux), Python 3, dan Git.

**1. Nyalakan GLPI** (pastikan file `.env` sudah ada: `cp .env.example .env`)
```bash
docker compose up -d
```
Tunggu 1–3 menit (pertama kali GLPI menginstal dirinya sendiri). Cek dengan `docker compose logs -f glpi`.

| Layanan | Alamat | Keterangan |
| --- | --- | --- |
| GLPI + plugin HaloSIS | http://localhost:8080 | Aplikasi utama |
| Keycloak (SSO) | http://localhost:8180 | Konsol admin `admin`/`admin`; realm `halosis` diimpor otomatis (langkah 6b) |
| Mailpit | http://localhost:8025 | Kotak masuk email uji (langkah 5b) |
| Layanan AI | http://localhost:8001/health | Triase & chatbot (lihat [`ai/README.md`](ai/README.md)) |

**2. Buka** http://localhost:8080 dan login `glpi` / `glpi` (akun super-admin bawaan; akun lokal GLPI, tidak
ada di Keycloak, jadi tetap login dengan password GLPI).

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
.venv/bin/python setup_pejabat_rules.py http://localhost:8080   # urgensi +1 untuk pemohon pejabat (grup Pejabat dari jabatan SSO)
docker compose exec glpi php bin/console config:set use_notifications 1 --allow-superuser
docker compose exec glpi php bin/console config:set notifications_ajax 1 --allow-superuser
# Email lewat Mailpit (layanan `mailpit` di docker-compose; kotak masuk http://localhost:8025)
docker compose exec glpi php bin/console config:set smtp_mode 1 --allow-superuser            # SMTP tanpa SSL/TLS
docker compose exec glpi php bin/console config:set smtp_host mailpit --allow-superuser
docker compose exec glpi php bin/console config:set smtp_port 1025 --allow-superuser
docker compose exec glpi php bin/console config:set smtp_username '' --allow-superuser       # tanpa autentikasi
docker compose exec glpi php bin/console config:set smtp_check_certificate 0 --allow-superuser
docker compose exec glpi php bin/console config:set from_email halosis@bps.local --allow-superuser
docker compose exec glpi php bin/console config:set admin_email halosis@bps.local --allow-superuser
docker compose exec glpi php bin/console config:set notifications_mailing 1 --allow-superuser
```
> ⚠️ **Mailpit hanya untuk uji lokal**: semua email ditahan di http://localhost:8025 dan tidak pernah terkirim
> ke alamat sungguhan. Untuk produksi, ganti SMTP ke server email BPS.

Skrip ini hanya memakai fitur bawaan GLPI (lewat API, tanpa mengubah kode inti):
- **SLA resmi BPS dari history ESTIM** (`config/sla_layanan.json`, sumber history Jan–Ags 2026): respons (*time to
  own*) **15 menit** untuk semua tiket; penyelesaian insiden menurut tier prioritas: **Crit 2 hari** (prioritas
  Sangat tinggi/Mayor), **Medium 8 hari** (Sedang/Tinggi), **Low 15 hari** (Rendah/Sangat rendah); pemenuhan
  permintaan **7 hari**, **14 hari** untuk layanan tim yang di history dominan 14 hari (Server Hosting, SOBAT, LAN/WAN
  BPS Pusat, Container Hosting; kategori dipasang saat sudah ada di katalog). Dihitung dengan kalender jam kerja GLPI
  (Senin–Jumat 08.00–20.00).
- **Aturan bisnis "SLA BPS …"** (jenis × prioritas, dan kategori 14 hari) memasang SLA respons & penyelesaian saat
  tiket dibuat maupun saat prioritas/kategori diubah (mis. operator menerima saran triase). Aturan versi lama ("SLA
  Kritis/Tinggi/Sedang/Rendah", "SLA layanan: …") dinonaktifkan. Bisa diubah Administrator di **Alur kerja & aturan**.
- **Level eskalasi "Peringatan risiko SLA"** di tiap SLA penyelesaian/pemenuhan, **±20% sebelum batas** dalam jam
  kerja (2 hari → 5 jam, 7 hari → 17 jam, 8 hari → 19 jam, 14 hari → 34 jam, 15 hari → 36 jam). Dokumen memodelkan
  `ambangPeringatan` sebagai persentase (hal. 162); GLPI memakai waktu tetap sebelum batas, jadi persentase
  dihitung per SLA.
- **Level eskalasi "Eskalasi SLA terlewati"** tepat saat batas waktu (FR-09): Ticket Recall dikirim lagi ke tim,
  ketua tim, dan Operator (prioritas tidak diubah, agar SLA resmi tiket tidak berganti).
- **Notifikasi "Ticket Recall"** dikirim ke teknisi & tim yang ditugaskan, **supervisor tim (atasan)**, dan grup
  **Operator Service Desk**, lewat
  notifikasi browser (tanpa server email) dan email (bila SMTP diatur).
- Penerima "atasan" adalah **ketua tim** masing-masing (`hendra`, `agus`, `rudi`, `wati`), yaitu supervisor grup
  yang dibuat `seed_halosis.py`. Skrip memperingatkan bila ada tim tanpa supervisor. Ketua tim diatur dengan
  **role `ketua-tim` di Keycloak** (langkah 6b); tanda *Supervisor* yang diubah langsung di GLPI tertimpa lagi
  saat orangnya login.

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
Skrip ini juga mengaktifkan **survei kepuasan** GLPI untuk setiap tiket yang ditutup (UC-07: pegawai memberi
penilaian), berlaku untuk tiket yang ditutup setelah skrip dijalankan.

`setup_list_columns.py` menulis *Display preferences* global (Administrasi › … › ikon "pilih kolom"). GLPI selalu
menambahkan kolom **ID** dan **nama/judul**; berikut kolom tambahannya (kiri → kanan):

| Daftar (menu) | Kolom tambahan | Dibuang (alasan) |
| --- | --- | --- |
| Tiket — Antrean validasi & Semua tiket (Operator) | Status, Prioritas, Kategori, Pemohon, Grup teknisi, Waktu untuk menyelesaikan, Terakhir diperbarui | Tanggal buka (dobel tanggal), Teknisi (Operator menugaskan ke tim) |
| Tiket — Tiket saya & tim (kolom pribadi tiap pengguna Tim Teknis) | Status, Prioritas, Kategori, Pemohon, Teknisi, Waktu untuk menyelesaikan, Terakhir diperbarui | Grup teknisi (sudah tersaring ke tim sendiri), Tanggal buka |
| Tiket — Laporan saya (Pegawai, Helpdesk) | Status, Kategori, Waktu untuk menyelesaikan, Terakhir diperbarui | Tanggal buka (dobel tanggal) |
| Masalah / pola insiden | Status, Prioritas, Kategori, Jumlah tiket, Tanggal buka | Deskripsi (panjang), Waktu untuk menyelesaikan (kosong untuk pola) |
| Knowledge Base (Daftar artikel) | Kategori, FAQ, Pengguna (penulis), Tampilan, Terakhir diperbarui | Parent article, Unsur terkait (kosong) |
| Pengguna | Nama depan, Nama belakang, Email, Profil (Entitas), Grup, Aktif, Terakhir login | Telepon, Lokasi (kosong) |
| Tim (Grup) | Manager (ketua tim), Jumlah pengguna, Bisa ditugaskan | Komentar (kosong) |
| Kategori layanan (ITIL) | Grup, Jumlah tiket, Terlihat untuk insiden / permintaan / antarmuka sederhana | — |
| SLA / SLM | SLM, Tipe, Waktu / Kalender | — |
| Alur kerja & aturan (aturan tiket) | Kolom tetap bawaan GLPI (Nama, Deskripsi, Dipakai untuk, Kriteria, Tindakan, Aktif, Posisi) | Daftar aturan bukan mesin pencarian, kolomnya tidak bisa diatur preferensi |

Urutan default **Antrean validasi, Tiket saya & tim, Pemantauan SLA**: "Waktu untuk menyelesaikan" terdekat dulu
(URL menu ringkas di `plugins/halosis/src/RoleMenu.php`).

Batasan GLPI: preferensi kolom berlaku per *itemtype* (dan per pengguna), **bukan per URL pencarian**. Antrean
validasi dan Semua tiket sama-sama daftar Tiket milik Operator, jadi kolom Status tetap tampil di antrean
(isinya selalu "Baru") karena dibutuhkan di Semua tiket. Pengguna yang berhak (hak *Search config*) tetap bisa
mengubah kolomnya sendiri; menjalankan ulang skrip menimpa kolom global & kolom pribadi Tim Teknis.

**6. Login sebagai role berbeda** (password semua: `halosis`; diperiksa SSO Keycloak, role & tim diatur di Keycloak — lihat 6b)

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
| — | — | — | Petugas Layanan TI (abstrak) | UC-08 | — | Aktor induk Operator + Tim Teknis, tanpa akun sendiri: kemampuan bersama Pemantauan SLA & Masalah (pola insiden) |
| — | — | — | AI Engine (aktor sistem) | UC-02, UC-04 | — | Layanan `halosis-ai` (lihat [`ai/README.md`](ai/README.md)) |
| glpi | — | Super-Admin | **Di luar aktor dokumen** | — | Standar | Akun pengelola sistem (instalasi, plugin, profil); bukan role bisnis |

Database yang diisi dengan versi seed lama (belum ada `dimas` atau ketua tim): jalankan ulang langkah 5
lalu 5b; hanya pengguna yang belum ada yang dibuat.

Akun di tabel ini juga ada di realm Keycloak (`keycloak/halosis-realm.json`) dengan role & tim yang sama. Saat
login, **profil & tim mengikuti Keycloak**. Menambah atau mengubah akun contoh berarti mengubah keduanya
(`seed_halosis.py` dan file realm) supaya tetap sama.

Hak inti GLPI untuk UC-08 (diatur `setup-roles`):

| Hak | Operator | Tim Teknis | Manajemen |
| --- | --- | --- | --- |
| Pemantauan SLA (tiket melewati batas waktu) | lihat | lihat | lihat |
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
| Dasbor kinerja AI | | | | ✓ | | ✓ | ✓ |
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

**6b. Login SSO Keycloak** (pengganti SSO BPS untuk uji lokal)

Pegawai cukup login **sekali** di form login HaloSIS. GLPI mengirim username & password ke Keycloak di belakang
layar (*Direct Access Grant*), tanpa diarahkan ke halaman login Keycloak. Keycloak hanya dipakai untuk autentikasi:
sesi Keycloak langsung ditutup, sesi kerja tetap sesi GLPI. Setelah login, Pegawai langsung masuk ke **Tanya
HaloSIS** dan memilih:

- **Ajukan permintaan** → langsung ke form katalog *Request a service* (tiket bertipe Permintaan).
- **Laporkan masalah** → menulis kendala ke chatbot dulu; tiket dibuat dari percakapan bila solusinya belum ketemu.

Layanan `keycloak` di docker-compose mengimpor realm `halosis` dari `keycloak/halosis-realm.json` saat pertama kali
jalan: semua akun langkah 6 (kecuali `glpi`) lengkap dengan role & timnya, password `halosis`, ditambah `ani`
(Ani Lestari, Pegawai) yang **belum ada** di GLPI untuk menguji pembuatan akun otomatis.
Setiap akun juga punya atribut kepegawaian contoh (fiktif) **NIP, unit kerja, jabatan** (profil pengguna realm,
hanya admin yang bisa mengubah); saat login disalin ke GLPI: NIP → *Nomor registrasi*, jabatan → *Jabatan*,
unit kerja → *Lokasi* (dropdown dibuat otomatis). Realm diimpor hanya sekali: untuk Keycloak yang sudah berjalan
sebelum atribut ini ada, hapus volume `keycloak_data` lalu `docker compose up -d keycloak` agar realm diimpor ulang.
Konsol admin: http://localhost:8180 (`admin`/`admin`, hanya lokal; pilih realm **halosis** di kiri atas).
Pengaturan di `.env` (lihat `.env.example`): `HALOSIS_KEYCLOAK_URL`, `_REALM`, `_CLIENT_ID`, `_CLIENT_SECRET`.
Setelah mengubahnya: `docker compose up -d glpi`.

**Keycloak = sumber akun, role, dan tim.** Setiap kali login, plugin menyamakan pengguna GLPI dengan Keycloak
sebelum sesi dimulai (perubahan di Keycloak berlaku pada login berikutnya):

| Di Keycloak (realm `halosis`) | Di GLPI |
| --- | --- |
| User | Pengguna GLPI (dibuat otomatis bila belum ada; nama & email ikut Keycloak) |
| Realm role `pegawai` / `operator` / `tim-teknis` / `manajemen` / `knowledge-manager` / `administrator` | Profil Pegawai / Operator / Tim Teknis / Manajemen / Knowledge Manager / Administrator (tanpa role HaloSIS → Pegawai) |
| Group `Tim Aplikasi Statistik`, `Tim Jaringan`, `Tim Perangkat`, `Tim Identitas & Akses`, `Operator Service Desk` | Keanggotaan grup GLPI bernama sama (grup yang tidak ada di GLPI dilewati & dicatat di log) |
| Realm role `ketua-tim` | Supervisor di grup timnya (penerima "atasan" peringatan risiko SLA) |

Menambah pegawai baru: konsol admin › realm *halosis* › **Users › Create user** (isi email, nama depan & belakang)
› tab *Credentials* (set password, *Temporary* off) › *Role mapping* (role HaloSIS) › *Groups* (tim, bila petugas).
Profil di luar daftar di atas (mis. Super-Admin) tidak disentuh sinkron, jadi tetap diatur di GLPI.

Realm hanya diimpor bila belum ada. Setelah `keycloak/halosis-realm.json` berubah, buat ulang data Keycloak lokal
(perubahan lewat konsol admin ikut hilang):
```bash
docker compose rm -sf keycloak && docker volume rm glpi-halosis_keycloak_data && docker compose up -d keycloak
```

Dropdown "Sumber login" disembunyikan karena isinya hanya database GLPI:
```bash
docker compose exec glpi php bin/console config:set display_login_source 0 --allow-superuser
```

| Kondisi | Hasil |
| --- | --- |
| Password benar di Keycloak | Login; profil & tim disamakan dengan Keycloak; akun ditandai dikelola SSO (authtype *Other*), password lokalnya dihapus |
| Password salah / akun nonaktif di Keycloak | Ditolak ("Incorrect username or password"); 5× salah → dikunci sementara oleh Keycloak |
| Akun yang tidak ada di Keycloak (`glpi`) | Login dengan password lokal GLPI (jalur darurat Super-Admin) |
| Keycloak mati | Akun SSO tidak bisa login, `glpi` tetap bisa; tercatat di `docker compose exec glpi tail /var/glpi/logs/halosis.log` |

**Cara menguji SSO**
1. Login `budi` / `halosis` di http://localhost:8080 → langsung di **Tanya HaloSIS**.
2. Login `ani` / `halosis` → akun GLPI baru dibuat otomatis (profil Pegawai).
3. Konsol admin http://localhost:8180 → realm **halosis** › *Users* › `budi` › *Role mapping*: ganti `pegawai`
   menjadi `operator` → login lagi sebagai `budi` → masuk antarmuka Operator. Kembalikan ke `pegawai` setelahnya.
4. Login `budi` dengan password salah → ditolak; login `glpi` / `glpi` → tetap bisa (akun lokal).

**Kalau login gagal**

| Gejala | Penyebab & solusi |
| --- | --- |
| Akun SSO selalu "Incorrect username or password" | Cek `.env` punya blok `HALOSIS_KEYCLOAK_*` lalu `docker compose up -d glpi`; cek Keycloak hidup (`docker compose ps keycloak`) dan `/var/glpi/logs/halosis.log` |
| Tadinya bisa, sekarang ditolak | Keycloak mengunci akun sementara setelah 5× salah password. Tunggu ±15 menit, atau konsol admin › realm *halosis* › *Users* › (akun) › matikan *Temporarily locked* |
| Tidak bisa login di http://localhost:8180 dengan `budi` | Halaman itu konsol **admin** (realm *master*): login `admin`/`admin`. Akun pegawai dicek di http://localhost:8180/realms/halosis/account |
| Role/tim di GLPI belum berubah | Perubahan di Keycloak berlaku saat login berikutnya: logout lalu login lagi |
| Plugin HaloSIS tiba-tiba nonaktif | Error PHP saat plugin dimuat membuat GLPI menonaktifkannya. Cek `php-errors.log`, perbaiki, lalu `docker compose exec glpi php bin/console plugin:activate halosis` |

> Password akun SSO diganti di Keycloak, bukan di GLPI (link "Forgot password" GLPI tidak berlaku untuk akun ini).
> Kosongkan `HALOSIS_KEYCLOAK_URL` untuk mematikan SSO; akun yang sudah dikelola SSO lalu perlu password lokal lagi
> (ubah *Authentication* pengguna ke database GLPI dan set password di Administrasi › Pengguna).

**6c. HTTPS lokal (opsional, NFR-05)**

```bash
docker compose --profile tls up -d tls      # Caddy reverse proxy → https://localhost:8443
```
Caddy (`tls/Caddyfile`) memakai sertifikat **CA internal** (self-signed): browser menampilkan peringatan sekali,
lalu GLPI, login SSO, dan chatbot berjalan seperti di :8080. Ditambahkan HSTS, `nosniff`, dan penanda `Secure` pada
cookie sesi. `docker compose up -d` biasa tidak menyalakan layanan ini. Matikan: `docker compose --profile tls stop
tls`. Produksi: ganti `tls internal` dengan sertifikat BPS dan jangan buka port 8080 ke luar jaringan internal.

**6d. Monitoring (opsional, NFR-09)**

```bash
docker compose --profile monitoring up -d   # Prometheus + mysqld-exporter + Grafana
```
Grafana http://localhost:3001 (`admin`/`admin`, hanya lokal) langsung membuka dasbor **HaloSIS – operasional**
(`monitoring/grafana/dashboards/halosis.json`): status layanan AI & MySQL, permintaan & latensi p95 AI per endpoint
(dari `/metrics`), galat 5xx, jumlah potongan indeks, koneksi & query MySQL. Prometheus: http://localhost:9090.
Matikan: `docker compose --profile monitoring stop`. Unduhan pertama ±600 MB image.

**7. Tampilan HaloSIS** (palet, logo, bahasa, teks login)

Palet ada di `themes/halosis.scss` (di-mount ke `/var/glpi-themes`, folder tema kustom GLPI lewat variabel
`GLPI_THEMES_DIR` di `docker-compose.yml`).
Jadikan default untuk semua pengguna:
```bash
docker compose exec glpi php bin/console config:set palette halosis --allow-superuser
docker compose exec glpi php bin/console config:set language id_ID --allow-superuser
docker compose exec glpi php bin/console config:set text_login '' --allow-superuser
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
- **Halaman login** (`LoginPage`: hook `add_css_anonymous_page`, `add_javascript_anonymous_page`, `display_login`;
  `public/css/login.css`, `public/js/login.js`, `templates/login.html.twig`, `public/img/login-ilustrasi.svg`
  [unDraw]; warna dari token `--halosis-login-*` di palet). Latar teal gelap dengan lingkaran samar; satu kartu dua
  panel: kiri (±55%) teal dengan ilustrasi, "Selamat datang di HaloSIS" · "Layanan TI BPS", dibatasi lengkung SVG
  bergaris aksen teal terang; kanan putih: logo kecil, judul "Masuk", field berikon (tombol tampil/sembunyikan kata
  sandi: `aria-label`, `aria-pressed`), tombol "Masuk", lencana "Login terpusat (SSO)" (bila Keycloak aktif) dan
  "Lupa kata sandi? Hubungi Operator layanan TI" (menggantikan tautan reset GLPI; akun lokal seperti `glpi` tetap bisa
  memakai `/front/lostpassword.php?lostpassword=1`). Footer di luar kartu "Didukung GLPI · © Teclib' and
  contributors" (tautan atribusi tetap); tautan *Bantuan* (dokumentasi GLPI) disembunyikan. HP (≤ 768px): pita
  sambutan pendek di atas tanpa ilustrasi & lengkung, form penuh lebar. Teks konfigurasi `text_login` tidak ditampilkan
  (sambutan sudah ada di panel kiri; `pasang.sh` mengosongkannya). Field `login_name`/`login_password`, alamat form & CSRF tidak berubah;
  tanpa JS form bawaan GLPI tampil apa adanya; aset ini tidak dimuat setelah login. Halaman galat login & lupa
  password ikut berlatar teal dengan logo terang. Tangkapan: `screenshot/modernisasi/login-*.png`.
- **HaloSIS hanya berbahasa Indonesia (PUEBI/KBBI):** GLPI memilih bahasa halaman anonim dari bahasa browser; plugin
  memaksa id_ID di halaman login & lupa kata sandi apa pun bahasa browser (`LoginPage::useIndonesian`). Bahasa
  bawaan GLPI = id_ID (`plugin:install` & `pasang.sh`), akun demo (`seed_halosis.py`) & akun baru dari SSO = id_ID.
  Label inti GLPI yang belum diterjemahkan/tidak baku di id_ID bawaan (hanya ±19% lengkap): login ("Masuk ke Akun
  Anda", "Nama Pengguna", "Kata Sandi", "Masuk", pesan galat) dan label di alur demo (Balas, Tambah solusi, Setujui,
  Tolak, Tampilan Pribadi/Grup, "Menampilkan … baris", dll.) di `plugins/halosis/locales/core/id_ID.po` → folder
  terjemahan lokal GLPI `files/_locales/core_halosis` (mekanisme bawaan, bukan mengubah GLPI). Dipasang ulang dan
  cache terjemahan dikosongkan otomatis bila `.mo` berubah (`LoginPage::syncLocales`); dihapus saat uninstall.
  Glosarium: Dasbor, pengetahuan/basis pengetahuan, asisten, layanan mandiri, percakapan, riwayat, penilaian,
  kunci API, isian, formulir, petugas, acuan awal, pergeseran, Masalah, Tanya Jawab (FAQ), ponsel. Judul halaman/
  kartu huruf kapital tiap kata; menu, tombol, label huruf kapital di awal saja.
- **Warna aksen per peran** (`RoleTheme`, `public/js/role.js`, variabel di `public/css/halosis.css`, pemakaian di
  palet): peran dibaca dari **profil aktif** (ID profil seperti `RoleMenu`, bukan nama pengguna) → `<meta
  name="halosis-role">` (hook `add_header_tag`, tanpa kedip) + kelas `hs-role-<peran>` di `<body>`; ikut berubah
  saat pengguna ganti profil tanpa logout. Super-Admin = Administrator, ketua tim = Tim Teknis; halaman login tetap
  teal. Yang memakai warna peran: sidebar & item aktif, tombol utama, tautan & ring fokus, judul kartu/bagian form,
  chip filter, chat Pegawai, dan lencana nama peran di header (latar `--hs-role-soft`, teks `--hs-role-ink`). Yang
  tetap: warna status/prioritas/SLA, peringatan & galat, grafik dashboard, tingkat keyakinan Saran AI, logo.

  | Peran | `--hs-role` | `--hs-role-soft` | `--hs-role-ink` | putih / role | ink / soft | ink / putih |
  |---|---|---|---|---|---|---|
  | Pegawai | `#176568` | `#E1F0EF` | `#176568` | 6,78 | 5,78 | 6,78 |
  | Operator | `#496B85` | `#E8EFF4` | `#496B85` | 5,64 | 4,85 | 5,64 |
  | Tim Teknis | `#A66552` | `#F4EAE6` | `#905747` | 4,56 | 4,88 | 5,77 |
  | Knowledge Manager | `#79627F` | `#F0EAF2` | `#755F7B` | 5,43 | 4,83 | 5,71 |
  | Manajemen | `#667C62` | `#EAF0E7` | `#596C56` | 4,54 | 4,89 | 5,67 |
  | Administrator | `#A05D70` | `#F4E8EC` | `#905465` | 4,89 | 4,83 | 5,77 |

  `--hs-role-ink` = warna utama dengan lightness HLS diturunkan sampai ≥ 4,5:1 di atas aksen ringan (Terracotta,
  Sage, Rose gagal bila memakai warna utama: 3,9 / 3,9 / 4,1). Teks redup sidebar memakai putih penuh dan item
  aktif memakai warna peran digelapkan 22% (≥ 6,7:1). Tangkapan: `screenshot/modernisasi/peran-*.png`.
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
| Login (SSO BPS) | Form login HaloSIS, password dicek ke **Keycloak** (langkah 6b) |
| Beranda pegawai: permintaan / masalah | **Tanya HaloSIS** › *Ajukan permintaan* (form *Request a service*) / *Laporkan masalah* (chatbot → laporan) |
| Laporan Saya, Detail Laporan (pegawai) | Login pegawai → **Tiket** (antarmuka sederhana/Helpdesk) |
| Buat Laporan | **Katalog layanan** / Buat tiket |
| Pusat Bantuan | **FAQ** (artikel KB yang ditandai FAQ) |
| Migrasi data (FR-10) | `ai/scripts/prepare_data.py` (pembersihan & penyamaran) + `ai/scripts/reconcile.py` → `reports/rekonsiliasi.md`: jumlah sumber/berhasil/gagal, tidak lengkap, duplikat, nilai disamarkan per jenis, per bulan & per tim (lihat [`ai/README.md`](ai/README.md#fr-10--rekonsiliasi-migrasi)) |
| Konfirmasi "sudah beres / belum beres" (UC-07) | Tombol **Approve / Refuse** pada solusi tiket. *Refuse* wajib disertai alasan (ditegakkan GLPI) dan membuka kembali tiket ke tim |
| Kembalikan ke operator, salah tim (UC-06 alur alternatif) | Panel **Saran AI** di tiket → *Kembalikan ke operator (salah tim)*, alasan wajib (plugin) |
| Peringatan risiko SLA (BR-02) | Level eskalasi SLA + notifikasi **Ticket Recall** (langkah 5b) |
| Antrean validasi & Semua tiket (operator) | **Bantuan › Tiket** (filter status Baru) |
| Tiket saya & tim (Tim Teknis) | Beranda **Tampilan Personal / Tampilan Group** |
| Komentar publik / catatan internal | **Answer › Followup** (centang *Private* untuk internal), **Task** |
| Pemantauan SLA (respons & penyelesaian) | Kolom "Waktu untuk mengambil alih" (SLA respons) & "Waktu untuk menyelesaikan" + **Setup › Service levels** |
| Pola insiden | **Bantuan › Masalah** (tiket ditautkan ke masalah) |
| Knowledge base (KM) | **Tools › Basisdata pengetahuan** |
| Cari pengetahuan (Operator & Tim Teknis) | Menu **Cari pengetahuan** (plugin, `/plugins/halosis/CariKnowledge`): pencarian semantik artikel KB & tiket historis; layanan AI mati → kata kunci artikel KB |
| Kandidat Knowledge (KM, UC-09) | Menu **Kandidat pengetahuan** (plugin): solusi tiket selesai & solusi berulang dari indeks AI → *Jadikan artikel* (draf KB) / *Abaikan* (dengan alasan) |
| Dashboard manajemen, laporan | **Bantuan › Dasbor**, **Bantuan › Statistik** |
| Katalog layanan, tim, pengguna & peran | **Pengaturan › Daftar pilihan › Kategori ITIL**, **Administrasi › Groups / Users / Profil** (nama profil = role HaloSIS) |
| Alur kerja & aturan otomatis | **Administrasi › Rules › Business rules for tickets** |
| Jejak audit | Tab **Riwayat** di setiap tiket/objek |

**Tidak ada di GLPI** (tetap dibangun sendiri di HaloSIS): chatbot AI, saran triase + keyakinan,
alur Terima/Ubah/Tolak saran AI, deteksi pola otomatis, kandidat knowledge, dan dashboard kinerja AI.

## Konfigurasi model AI (env & profile `llm`)

Bawaannya tidak memakai LLM: chatbot mengutip sumber (ekstraktif), dan draf artikel memakai templat. Semua pengaturan ada di
`.env` (contoh: `.env.example`).

| Env | Isi |
| --- | --- |
| `EMBEDDING_PROVIDER` | `local` (bawaan, e5 lokal) atau `openai` (endpoint `/v1/embeddings`). Ada juga `EMBEDDING_BASE_URL`, `EMBEDDING_MODEL`, `EMBEDDING_API_KEY` |
| `LLM_PROVIDER` | `none`, `openai` (server kompatibel OpenAI, termasuk Ollama), atau `anthropic` |
| `LLM_BASE_URL`, `LLM_MODEL` | Alamat dan nama model. Untuk `anthropic`, `LLM_BASE_URL` tidak perlu |
| `LLM_API_KEY` | Boleh kosong untuk Ollama |

Bila `LLM_PROVIDER` kosong dan `ANTHROPIC_API_KEY` terisi, layanan memakai Anthropic. Tulis `LLM_PROVIDER=none` agar pasti nonaktif.

**Ollama di Docker (profile `llm`):**

```bash
docker compose --profile llm up -d ollama
docker compose exec ollama ollama pull qwen2.5:3b
```

Lalu isi `.env`:

```bash
LLM_PROVIDER=openai
LLM_BASE_URL=http://ollama:11434/v1
LLM_MODEL=qwen2.5:3b
```

**Ollama native di Mac:** Docker di Mac tidak memakai GPU, jadi jalankan Ollama di host.

```bash
ollama pull qwen2.5:3b
```

Isi `.env` seperti di atas, tetapi dengan `LLM_BASE_URL=http://host.docker.internal:11434/v1`.

**Menerapkan perubahan:** jalankan `docker compose up -d halosis-ai` setelah mengubah `.env`. Setelah kode `ai/` berubah, jalankan
`docker compose up -d --build halosis-ai`, karena kode layanan ada di dalam image.

Bila model, penyedia, atau dimensi embedding berubah, layanan menolak indeks lama. Bangun ulang dengan `ai/scripts/build_index.py`.

Dengan LLM aktif, draf artikel diberi label "Disusun AI, wajib ditinjau Knowledge Manager". Model kecil bisa menambah frasa di
luar sumber, jadi peninjauan KM wajib. Untuk penerapan di BPS, lihat [`reports/dokumentasi_ai.md`](reports/dokumentasi_ai.md) §5.5.

## Keputusan desain & keterbatasan

Perbedaan implementasi dengan dokumen perancangan / PoC (§2.4.7) dan alasannya
(audit lengkap: [`reports/audit_kelengkapan.md`](reports/audit_kelengkapan.md)).

| Area | Dokumen / PoC | Implementasi | Alasan | Rencana lanjut |
| --- | --- | --- | --- | --- |
| Embedding | `paraphrase-multilingual-MiniLM-L12-v2` | `intfloat/multilingual-e5-base` | Dibandingkan pada set uji yang sama ([`reports/banding_embedding.md`](reports/banding_embedding.md)): e5 Top-1 72,74% / MRR 0,8144 vs MiniLM 67,99% / 0,7650 (ekspor lama, 906 kueri); lokal & gratis. Angka indeks aktif (ekspor baru, 1.069 kueri, aturan solusi baru) di baris *Sumber knowledge*: set berbeda, tidak dibandingkan langsung | — |
| LLM jawaban | Qwen2.5 3B via Ollama (RAG) | Bawaan **ekstraktif** dari artikel KB terbit dan katalog layanan. Opsional lewat env: server kompatibel OpenAI atau Anthropic (lihat *Konfigurasi model AI*) | Tanpa API berbayar dan tanpa GPU secara bawaan; dokumen sendiri memilih RAG *grounded* karena risiko halusinasi | Server LLM internal BPS atau model terbuka di server BPS; cloud hanya dengan penyamaran + izin BPS |
| Vector DB | Layanan vector database | Indeks file (`ai/index/*.parquet`, `vectors.npy`), kosinus di memori; artikel KB diperbarui inkremental (`POST /reindex/artikel`) | Cukup untuk ribuan potongan, nol infrastruktur tambahan | pgvector/Qdrant bila korpus membesar |
| Deteksi pola | Embedding + DBSCAN (eps 0,25; min 5), similarity 0,70, jendela 1 jam | Semantik: `POST /pola` (embedding e5 dipusatkan, rata-rata kemiripan ≥ 0,50, jendela 60 menit, min. 3 tiket (sesuai PoC)); fallback kata kunci bila layanan AI mati; metode dicatat di Problem | Skala kosinus e5 berbeda dari MiniLM (tiket tak terkait pun ±0,85), jadi vektor dipusatkan dan ambang dikalibrasi ulang. **DBSCAN tersedia sebagai opsi** (Pengaturan AI, eps 0,50, min_samples 3; PoC eps 0,25 / min 5): eps 0,25 PoC untuk MiniLM tanpa pemusatan, pada e5 dipusatkan jarak tiket bertopik sama ± 0,4 → 0,50; min 3 mengikuti aturan PoC "minimal 3 insiden" dalam jendela 1 jam (min 5 jarang tercapai: rata-rata 3,8 insiden per blok berisi); pada 666 insiden hasilnya setara, bawaan tetap rata-rata kemiripan karena lebih cepat & tanpa efek rantai ([`reports/banding_pola.md`](reports/banding_pola.md)); tren 12 minggu di dashboard | — |
| Routing triase | 39 assignment group | 21 kelas (tim < 30 tiket latih → "Lainnya"); dilatih ulang dari history versi baru: Top-1 75,88% / Top-3 94,87% (model lama pada set uji sama 74,47% / 93,01%) → lolos gerbang, dipakai | Kelas kecil tidak bisa dipelajari andal | Latih ulang berkala; tim kecil/baru tetap manual |
| Login | SSO BPS | SSO Keycloak lokal (realm `halosis`), dicek dari form login HaloSIS lewat password grant | Prototipe tanpa akses SSO BPS; satu kali login tanpa halaman Keycloak | Arahkan `HALOSIS_KEYCLOAK_URL` ke Keycloak SSO BPS + client resmi (Direct Access Grants aktif) |
| Claude (perangkum opsional) | Batas scope hal. 8: tanpa GenAI publik eksternal tanpa batas untuk data internal BPS | Claude via API = **GenAI eksternal**: **nonaktif secara bawaan** (`ANTHROPIC_API_KEY` kosong). Judul & isi tiket, pertanyaan, riwayat chat, dan artikel disamarkan sebelum dikirim (`Triage::aiPrompt`, `Chatbot::aiPrompt`, jaring pengaman terakhir `Client::outgoingPrompt`; tes container `php plugins/halosis/tools/test_ai_masking.php`) | Mengaktifkannya **butuh persetujuan tata kelola AI BPS** (`reports/tata_kelola_ai.md`) | Alternatif sesuai dokumen: LLM lokal (Ollama + Qwen2.5 3B) |
| Log retrieval (T16) | Log audit berisi kueri, sumber, skor (hal. 145, 177) | `ai/logs/latency.jsonl` hanya angka (latensi, jumlah hasil); **teks kueri tidak disimpan** | NFR-06 (privasi): kueri pegawai bisa memuat data pribadi; sumber jawaban tetap tercatat di transkrip chat (sudah disamarkan) | Simpan kueri tersamar + id sumber + skor bila tata kelola menyetujui |
| Arsip & tag artikel (T7) | Status "Diarsipkan", kata kunci/tag (hal. 140, 167) | **Tidak terbit = arsip**: artikel tanpa target visibilitas & bukan FAQ dikeluarkan dari indeks AI tetapi tetap tersimpan di GLPI; **kategori KB = tag** | Fitur bawaan GLPI sudah setara; tanpa ubah kode inti (NFR-10) | — |
| Prioritas & urgensi (BR-05, FR-08, 2.1.4) | Rekomendasi prioritas (P1) & prediksi urgensi (P2) dari history | **Status 7 Nov 2026: model urgensi tidak dipakai karena gagal gerbang skema B; panel memakai aturan kata kunci + validasi Operator.** Riwayat sebelum keputusan itu: history versi baru memuat `urgency`/`impact`/`priority`: dampak = urgensi pada 99,7% insiden dan prioritas = matriks keduanya, jadi **satu model urgensi insiden** Medium vs Low (`ai/scripts/train_urgensi.py`: TF-IDF teks tersamar + nama tim, LR seimbang → P(Low), validasi silang 5 lipatan) dengan **ambang per kelas** dipilih otomatis: **Rendah** bila P(Low) ≥ 0,90 (presisi 78,79%, Wilson 95% 62,25–89,32%, vs proporsi Low 18,76%; recall 5,12%, 33 tiket), **Sedang** bila P(Low) ≤ 0,45 (akurasi 84,30% vs pembanding 81,24%, cakupan 76,70%), di antaranya aturan kata kunci; gerbang per kelas (kedua kelas lolos, `urgensi.metrics.json`). Panel "Urgensi disarankan: Rendah/Sedang (keyakinan)" hanya bila kelasnya lolos & di atas ambangnya. **Keterbatasan:** Rendah hanya mengenali ± 5% insiden Low (sisanya aturan); Sedang lolos tipis (syarat > 84,24%). Dampak = urgensi, **naik 1 tingkat** bila ≥ 3 tiket serupa dalam 60 menit / Problem pola terbuka atau kategori layanan kritis (`critical_services`, bawaan SSO, Email, Jaringan); panel menampilkan alasannya. Prioritas = matriks GLPI. High/Critical (21 tiket) & REQ (hampir semua Medium): aturan kata kunci (kata utuh, negasi "tidak mendesak") + sinyal. Model prioritas lama (proksi tier SLA, F1 = pembanding) dihapus; satu ambang keyakinan 70% versi 31 Okt (Low tidak pernah tertangkap) diganti | 81% insiden berlabel Medium, kemungkinan besar **nilai bawaan formulir**, bukan penilaian petugas → batas atas model rendah; dokumen menempatkan urgensi P2 dengan validasi manusia | Rekam urgensi/dampak final Operator (Terima/Ubah) sebagai label yang lebih bersih → latih ulang; gerbang `/health` mencegah model lemah dipakai |
| Sumber knowledge dari history (AI-4, UC-09) | Masalah → solusi dari tiket selesai | Solusi = pesan terakhir ≤ `resolved` + 5 menit yang bukan dari pemohon (pesan terakhir dicek lewat `last_conversation_user_id`), lolos penyaring template & ≥ 5 kata; cadangan `close_notes` → `resolution` bila bukan template. Solusi > 220 kata dipecah (masalah diulang di tiap potongan). Uji retrieval ekspor baru, 1.069 kueri Jul–Ags ([`reports/banding_solusi.md`](reports/banding_solusi.md); set berbeda dari banding embedding 906 kueri ekspor lama): Top-1 72,50% / Top-3 89,06% / MRR 0,8115 vs aturan lama 73,15% / 89,43% / 0,8163 → dalam toleransi 1 poin, dipakai. **Dedup solusi identik tidak dipakai** (Top-1 −1,96 poin) | Pesan setelah tiket diselesaikan (terima kasih, tiket dibuka lagi) bukan solusi; petugas sering menulis solusi 1–3 menit setelah menekan "selesai", jadi toleransi 5 menit (bukan 1) | Penilaian manual mutu solusi pada sampel; dedup dinilai ulang bila ada label relevansi manusia |
| Rekomendasi jenis REQ/INC (T4) | Triase menyarankan jenis tiket (hal. 97, 100, 104) | Klasifier ringan terpisah (`ai/scripts/train_jenis.py`, `ai/models/jenis.joblib`, dilatih ulang dari history versi baru, F1 makro 67,52% vs 67,50% model lama → lolos): akurasi 68,25%, ≥ 70% yakin → 83,96%; panel hanya menampilkan "Jenis disarankan" bila berbeda & yakin | Jenis tetap ditentukan jalur masuk & Operator; model tim tidak diubah | — |
| Chatbot keyakinan sedang (T3) | Jawaban terbatas / klarifikasi (hal. 100) | Skor 0,78–0,83: tidak menjawab, menawarkan ≤ 3 judul artikel KB "Maksud Anda…?" + Buat laporan (`HALOSIS_CHAT_SUGGEST_MIN_SCORE`) | Tanpa mengarang jawaban; hanya artikel KB karena tiket historis tidak punya tautan | Jarang muncul selama KB masih sedikit (± 6 artikel vs ± 6.700 potongan tiket); ambang 0,78 asumsi |
| HTTPS, monitoring (NFR-05, NFR-09) | HTTPS & observability terpusat | **Profile opsional** di docker-compose: `tls` (Caddy, sertifikat internal) dan `monitoring` (Prometheus + mysqld-exporter + Grafana); `docker compose up -d` biasa tidak berubah | Demo lokal tetap ringan; unduhan image hanya bila dipakai | Sertifikat BPS, alert, metrik GLPI & host |
| Konfigurasi admin (T20, UC-10) | Pratinjau dampak & notifikasi perubahan konfigurasi | Pratinjau dampak (tanpa menyimpan): ambang AI (saran 30 hari) dan **perubahan SLA / aturan SLA** (tiket aktif terdampak; status aman / berisiko = sisa ≤ 20% / terlewati sekarang vs target baru; aturan: tiket dicocokkan kriteria aturan, jenis SLA pengganti menentukan aksi respons/penyelesaian); perubahan Pengaturan AI, aturan SLA, SLA, kategori → log sistem GLPI + Catatan untuk Administrator | Tanpa ubah kode inti: memakai Event log, Reminder, perhitungan tanggal SLA & pencocokan kriteria aturan GLPI; risiko memakai waktu jam dinding (eskalasi GLPI memakai jam kerja) | Pratinjau kategori (Rules › Test) |
| Tingkat keyakinan triase (T2) | Tinggi / sedang / rendah (hal. 100) | Dua ambang di Pengaturan AI: ≥ 70% "Disarankan", 40–69% "Pilih dari 3 kandidat", < 40% "Perlu penilaian manual" | Angka tidak ditentukan dokumen; 70%: akurasi 88,35% di atasnya (`reports/triase.md`); 40%: di bawahnya akurasi ≤ 50% (pita 30–50% = 50,0%, 0–30% = 35,5%) | Kalibrasi ulang setelah data keputusan Operator cukup |
| SLA respons & penyelesaian (T1, T22) | `KebijakanSLA.targetRespons` (hal. 162), SLA per layanan (E3) | **SLA resmi BPS dari history ESTIM** (`config/sla_layanan.json`): respons 15 menit; insiden Crit 2 / Medium 8 / Low 15 hari; permintaan 7 hari (14 hari untuk layanan tim yang dominan 14 hari); kalender jam kerja GLPI | Nama SLA di kolom `*_sla_name` history (6.655 tiket respons, 2.710 insiden, 1.804 permintaan) | Pasang SLA 14 hari ke kategori Server Hosting/SOBAT/LAN-WAN/Container saat katalog memuatnya |
| Urgensi pemohon pejabat (wawancara PM & operator) | Tiket pejabat/kepala kantor diprioritaskan | Grup GLPI **Pejabat** diisi saat login SSO dari jabatan Keycloak (Pengaturan AI › *Jabatan pejabat*, bawaan Kepala, Direktur, Deputi, Sekretaris Utama); aturan bisnis `setup_pejabat_rules.py` "Pejabat: urgensi N → N+1" (paling awal, menurun, tanpa kenaikan berantai); saran triase menaikkan urgensi yang sama dan panel menulis "Urgensi …: pemohon pejabat (…)" | Konfigurasi GLPI bawaan, tanpa kode inti. GLPI menghitung prioritas sebelum aturan berjalan, jadi saat tiket dibuat prioritas masih dari urgensi awal; **prioritas tiket pejabat mengikuti matriks urgensi × dampak saat saran diterima (Terima/Ubah) atau saat Operator mengubah urgensi/dampak di tiket**, dan SLA menyusul (aturan SLA juga berjalan saat tiket diubah) | — |
| Beban kerja tim (UC-04 langkah 5) | Rekomendasi berdasarkan kategori, riwayat, beban kerja | Beban kerja (tiket aktif per kandidat) tampil di panel; urutan dari model, **kecuali seri**: selisih keyakinan 2 kandidat teratas < 5 poin dan kandidat 2 lebih sedikit tiket aktif → kandidat 2 disarankan, alasan tampil di panel | Beban kerja tidak dicampur ke skor model (metrik yang lolos gerbang tetap); hanya memutus seri yang secara statistik tidak bermakna; Operator tetap memutuskan | Bobot beban kerja di luar seri setelah ada data keputusan Operator |
| Pola permintaan (FR-04) | Analisis request **dan** incident | Bawaan hanya Insiden; Pengaturan AI *Sertakan permintaan dalam deteksi pola* (bawaan mati) → REQ dikelompokkan terpisah, Problem "Pola permintaan: …" | Bawaan mengikuti PoC BR-07 (2.777 INC, hal. 56); lonjakan permintaan musiman bisa dipantau sebagai pola bila diaktifkan | — |
| Pengingat progres (wawancara E19) | Pemohon tidak tahu progres tiket pengembangan | Tugas terjadwal **`ProgressReminder`** (harian 07–17): tiket Diproses/Menunggu tanpa tindak lanjut/tugas > N hari kerja (Pengaturan AI, bawaan 5; kalender entitas) → notifikasi GLPI "HaloSIS: Pengingat progres" (email + browser) ke teknisi & grup yang ditugaskan, sekali per periode | Memakai notifikasi GLPI (penerima & templat dapat diubah di Setup › Notifikasi); aktivitas = tindak lanjut/tugas, waktu diambil, atau waktu dibuat | — |
| Ringkasan deskripsi panjang (wawancara E15) | Deskripsi panjang sulit dibaca cepat | Panel Saran AI menampilkan **ringkasan ekstraktif 3 kalimat** untuk deskripsi > 150 kata: teks disamarkan dulu, kalimat berskor frekuensi kata kunci, urutan asli (`src/Summary.php`) | Tanpa LLM (NFR-06, tanpa API eksternal), deterministik | Ringkasan abstraktif bila LLM lokal tersedia |
| Siklus artikel KB (UC-09, state machine hal. 192) | Draf → Terbit → Diarsipkan, versi | **Draf** = artikel tanpa target visibilitas, **Terbit** = punya target, **Diarsipkan** = target dicabut (tetap tersimpan, keluar dari indeks AI); **versi** = revisi GLPI (`KnowbaseItem_Revision`, isi lama tersimpan setiap sunting; uji 1 Nov: 1 revisi tercatat) | Fitur bawaan GLPI, tanpa ubah kode inti | — |
| Pemilik & metadata knowledge (KR-01, KR-03) | Pemilik per domain, metadata | **Kategori KB = domain**; pemilik domain di `reports/tata_kelola_ai.md` §4b; metadata = kategori, target visibilitas, tanggal tinjau berikut | Tanpa field tambahan di artikel | — |
| Log retrieval (UC-02 langkah 6) | Catat kueri, sumber, skor | Angka saja (skor teratas, jumlah hasil, latensi) di `ai/logs/latency.jsonl`; teks kueri tidak disimpan | NFR-06: kueri pegawai bisa memuat data pribadi | Kueri tersamar + id sumber bila tata kelola menyetujui |
| KPI Tabel 1.3 yang butuh pengukuran manusia | Waktu perubahan, waktu monitoring, waktu pencarian solusi | **Time study saat pilot** (`reports/rencana_implementasi.md`); sistem mengukur waktu sampai diketahui (median tiket pertama → pola) & pemohon terdampak per pola di dashboard | Tidak ada jejak waktu kerja manual di sistem | — |

**Padanan status tiket** (state machine Tiket hal. 191 ↔ GLPI):

| Dokumen | GLPI (id_ID) | Keterangan |
| --- | --- | --- |
| Baru | Baru (*New*) | Menunggu validasi Operator (antrean validasi) |
| Assigned | Diproses (ditugaskan) | Setelah Operator menerima/ubah saran AI dan menugaskan tim; SLA respons berhenti |
| Dalam Penanganan | Diproses (direncanakan) | Tim Teknis mengerjakan (tugas/tindak lanjut) |
| Pending | Menunggu (*Pending*) | Menunggu pegawai/pihak lain; jam SLA berhenti |
| Resolved | Selesai (*Solved*) | Solusi diajukan, menunggu konfirmasi pegawai (Approve/Refuse) |
| Closed | Ditutup (*Closed*) | Pegawai menyetujui solusi atau tutup otomatis; survei kepuasan dikirim |
| Reopened | Diproses kembali | Pegawai menolak solusi (*Refuse* + alasan) → tiket kembali ke tim |

**Evidence Maturity** (format §2.4.7.8; PoC evidence ≠ production readiness):

| Area | Evidence | Status |
| --- | --- | --- |
| ITSM core (tiket, role, menu per peran) | Uji skenario 12 langkah lintas 6 role | Proven |
| Login SSO & sinkron role/tim | 16 akun login lewat Keycloak lokal; user baru, pindah tim, dan ketua tim dari Keycloak terbawa ke GLPI | Proven (Keycloak lokal); SSO BPS: belum diuji |
| SLA & peringatan risiko | Aturan SLA + level peringatan, notifikasi ke teknisi/tim/ketua tim (tiket uji #58) | Proven (browser); email: Proven (Mailpit lokal) |
| Knowledge & Kandidat Knowledge | Kandidat → draf KB (UC-09), re-index otomatis saat artikel terbit/dihapus, katalog layanan & SOP terindeks; `ai/tests/test_candidates.py`, `test_reindex.py` | Proven |
| AI retrieval (chatbot) | `ai/tests/test_search.py`, uji chat end-to-end; banding embedding 906 kueri (`reports/banding_embedding.md`); banding ekstraksi solusi 1.069 kueri (`reports/banding_solusi.md`); /chat Email, SSO, SiPecut menjawab setelah indeks dibangun ulang | Proven |
| AI routing (triase) | 1.559 tiket uji Jul–Ags (history versi baru): top-1 75,88%, top-3 94,87%, MRR 0,8563, F1 makro 69,00%; keyakinan ≥ 70% → akurasi 88,35% pada 50,67% tiket; recall tim besar terendah 78,70% (`reports/triase.md`, `triage.metrics.json`) | Partially proven |
| Conversation (self-service) | Chat → laporan → tiket, riwayat & rating | Partially proven (ekstraktif, tanpa uji usability) |
| Deteksi pola insiden | Semantik `/pola` (uji 10 tiket "lemot/lambat" → 1 Problem), fallback kata kunci; banding rata-rata vs DBSCAN pada 666 insiden history (`reports/banding_pola.md`); regresi demo Bonus pola (`reports/uji_regresi_demo.md`) | Partially proven (tanpa label pola manual) |
| HITL & audit | Terima/Ubah/Tolak + alasan, Kembalikan ke operator, tab Riwayat; regresi skenario demo 17 langkah lolos (`reports/uji_regresi_demo.md`) | Proven |
| Login SSO bersamaan (beban halaman) | k6 10 akun petugas, 5 menit: 0% galat, login p95 60 ms, daftar tiket p95 56 ms; bug duplikat Jabatan ditemukan & ditutup (`reports/rencana_uji.md` §7) | Proven (laptop) |
| Kesiapan demo | Snapshot simpan/pulihkan (tiket uji hilang setelah pulihkan, 11 dtk), `reports/checklist_demo.md` | Proven |
| Upgrade platform (Skenario 2) | GLPI 12.0.0 → 12.0.1 dari snapshot di lingkungan terpisah: skema OK, plugin Enabled, data utuh (`reports/uji_upgrade.md`) | Proven (patch) |
| SLA resmi BPS & KPI tabel 1.3 | Aturan SLA BPS (uji: insiden prioritas 3 → respons 15 menit + Medium 8 hari, permintaan → 7 hari, prioritas 5 → Crit 2 hari); KPI kepatuhan SLA dengan dua baris pembanding: **dokumen** 27,59% (overall) / 42,62% (respons) dan **history versi baru** 28,87% (extended, 1.819 imputasi) / respons 43,08% (`response_sla_final_result`); selisih karena metode (ekspor baru mengestimasi komponen SLA yang tidak tercatat, lihat `metode` di baseline.json & `reports/eda.md`). Kepuasan pemohon (% nilai ≥ 4, baseline 95,76%) dengan cakupan rating 1.155/6.681 = 17,3% dan catatan dokumen §5.2.1 (rating tidak wajib, klaim tinggi berisiko optimistis); `plugins/halosis/baseline.json` (`ai/scripts/baseline.py`) | Proven (data contoh) |
| Gerbang kualitas model (UC-04) | `/health` & panel "belum lolos uji kualitas" saat syarat dinaikkan (tes + uji container); latih ulang triase/jenis dari history baru: kandidat & model aktif dinilai pada set uji sama, artefak diganti hanya bila lolos | Proven |
| Saran urgensi & sinyal dampak (BR-05) | `ai/tests/test_service.py` (urgensi per kelas: Rendah/Sedang hanya bila kelasnya lolos & di atas ambangnya, di antaranya / REQ → aturan), `test_triage_model.py` (pemilihan ambang, Wilson); uji PHP di container: 3 insiden SSO → "Dampak Tinggi: 3 tiket serupa dalam 1 jam; layanan kritis (SSO)", prioritas = matriks, pertanyaan REQ "tidak mendesak" → urgensi Rendah | Proven (uji skrip); label urgensi history lemah (81% Medium), Rendah hanya ± 5% insiden Low |
| Ketahanan triase saat AI mati (NFR-03) | Tugas `TriageRetry`: gagal → percobaan tercatat; pulih → saran dibuat; tanpa duplikat; batas 5 percobaan | Proven (uji skrip) |
| Migrasi data (FR-10) | `reports/rekonsiliasi.md` (termasuk banding ekspor lama 6.682 vs baru 6.681: 1 REQ tanpa nomor hilang, 137 status berubah); sampel 200 tiket ke entitas "Arsip ESTIM" lewat API (`ai/scripts/migrate_sample.py`): 199 berhasil + 1 gagal, idempoten, bisa dihapus | Proven (sampel); skala penuh belum |
| Performa (AI & API GLPI) | AI: Normal 10 VU (galat 0%, `/chat` p95 140 ms), Peak 50 VU (0,03%, 223 ms), Stress 25→200 VU tidak jenuh (0,04%, 846 ms); API GLPI Normal 10 VU (0%, buat tiket p95 71 ms) ([`reports/rencana_uji.md`](reports/rencana_uji.md) §7) | Partially proven (laptop; halaman GLPI belum) |
| Backup & restore DB | `mysqldump` → DB terpisah: 455 tabel & jumlah baris sama, pulih 6 dtk ([`reports/keamanan_backup.md`](reports/keamanan_backup.md) §3) | Proven (DB saja; volume berkas belum) |
| Keamanan | Checklist [`reports/keamanan_backup.md`](reports/keamanan_backup.md); HTTPS lokal profile `tls` (Caddy, HSTS, cookie `Secure`; login SSO lewat https diuji) | Partially proven (sertifikat internal; belum uji kerentanan) |
| Monitoring | Profile `monitoring`: Prometheus (target AI & MySQL `up`) + Grafana dasbor terprovisi (`screenshot/15-grafana-monitoring.png`) | Partially proven (tanpa metrik GLPI & alert) |
| Ketersediaan (HA) | — | Rencana |

## Mematikan / mengulang dari nol (catatan teknis)

Perintahnya ada di [Menyalakan, mematikan, dan mengulang](#menyalakan-mematikan-dan-mengulang). `docker compose down -v`
juga menghapus data Keycloak; realm `halosis` diimpor ulang dari `keycloak/halosis-realm.json` saat
`docker compose up -d` berikutnya.

Folder `screenshot/` berisi contoh tampilan hasil akhirnya (GLPI 12 dengan data ini).
