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

**4. Isi data contoh HaloSIS** (jalankan sekali saja)
```bash
python3 -m venv .venv && .venv/bin/pip install requests
.venv/bin/python seed_halosis.py http://localhost:8080
```

**5. Login sebagai role berbeda** (password semua: `halosis`)

| Login | Nama | Profil GLPI | Peran di HaloSIS |
| --- | --- | --- | --- |
| budi, siti, maya | Budi Santoso, dkk. | Self-Service | Pegawai |
| rina | Rina Wulandari | Hotliner | Operator |
| andi, yoga | Andi Pratama, Yoga Saputra | Technician | Tim Teknis (Aplikasi Statistik) |
| fajar | Fajar Nugroho | Technician | Tim Teknis (Identitas & Akses) |
| dedi | Dedi Kurniawan | Technician | Tim Teknis (Jaringan) |
| sri | Sri Handayani | Observer | Manajemen (lihat saja) |
| lina | Lina Marlina | Supervisor | Knowledge Manager |
| glpi | — | Super-Admin | Administrator |

**6. Tampilan HaloSIS** (palet, logo, bahasa, teks login)

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
| Service catalog, tim, pengguna & role | **Setup › Dropdowns › ITIL categories**, **Administrasi › Groups / Users / Profiles** |
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
