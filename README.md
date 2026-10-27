# Coba GLPI untuk HaloSIS

Paket ini menyalakan GLPI di laptop kamu lalu mengisinya dengan data contoh HaloSIS:
4 tim teknis, kategori layanan (SSO, FASIH, SiPecut, VPN, dll.), 10 pengguna per role,
SLA per prioritas, 12 tiket (lengkap dengan balasan, catatan internal, solusi),
5 artikel knowledge base, dan 1 "masalah" sebagai contoh pola insiden.

## Yang dibutuhkan
- Docker Desktop (Mac/Windows) atau Docker Engine (Linux)
- Python 3 (untuk skrip pengisi data)

## Langkah

**1. Nyalakan GLPI**
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
