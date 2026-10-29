# Checklist keamanan & prosedur backup HaloSIS (NFR-05, Backup/DR)

Kolom **Prototipe** = kondisi repo saat ini. Kolom **Produksi** = yang wajib sebelum dipakai di jaringan BPS.

## 1. Checklist keamanan (NFR-05)

| # | Kontrol | Prototipe | Produksi | Cara |
| --- | --- | --- | --- | --- |
| 1 | Password Super-Admin `glpi` bukan bawaan | ⬜ (bawaan `glpi`) | Wajib | Avatar › Preferensi › Password; `setup-roles` memperingatkan selama masih bawaan |
| 2 | Password akun contoh (`halosis`) | Demo saja | Hapus akun contoh | Nonaktifkan/hapus budi…dimas; pakai akun dinas |
| 3 | Login terpusat (SSO/LDAP BPS) | ⬜ login lokal | Wajib | Setup › Autentikasi › LDAP/SAML (fitur bawaan GLPI, tanpa ubah kode) |
| 4 | HTTPS/TLS | ⬜ HTTP :8080 | Wajib | Reverse proxy (Nginx/Traefik) dengan sertifikat BPS; GLPI hanya di jaringan internal |
| 5 | Port layanan AI tidak terbuka | ✅ `127.0.0.1:8001` | Tutup sama sekali | Hapus pemetaan port; GLPI tetap memanggil `halosis-ai:8000` di jaringan compose |
| 6 | Port Mailpit tidak terbuka | ✅ `127.0.0.1:8025` | Hapus Mailpit | Ganti SMTP ke server email BPS |
| 7 | RBAC per role | ✅ `setup-roles`, hak plugin | Tinjau tiap rilis | Uji: tiap akun hanya melihat menu perannya; akses langsung URL lain → 403 |
| 8 | CSRF & permintaan AJAX | ✅ token GLPI + `X-Requested-With` | Tetap | — |
| 9 | Klien API dibatasi IP | ✅ rentang gateway Docker | Batasi ke IP server | Setup › Umum › API › API client |
| 10 | Rahasia di luar repo | ✅ `.env`, data, model, indeks di `.gitignore` | Tetap + secret manager | Cek `git log --all -- .env data/` kosong |
| 11 | API key LLM terenkripsi | ✅ `src/Config.php` | Tetap | — |
| 12 | Data ke AI disamarkan | ✅ `privacy.py`, `Privacy.php`, tes | Tetap + tinjau pola baru | `ai/tests/test_privacy.py` |
| 13 | "Remember me" | ✅ dimatikan (bug GLPI 12.0.0) | Tetap sampai GLPI diperbaiki | `login_remember_time 0` |
| 14 | Pembaruan keamanan | ⬜ | Bulanan | Ikuti rilis GLPI & image Docker; `docker compose pull` di lingkungan uji dulu |
| 15 | Uji kerentanan | ⬜ | Sebelum go-live | Pindai OWASP ZAP (baseline) ke lingkungan uji, bukan produksi; perbaiki temuan tinggi |
| 16 | Log akses & audit | ✅ Audit trail GLPI, `halosis.log` | Kirim ke log terpusat | Lihat NFR-09 |

## 2. Backup

| Yang dibackup | Isi | Frekuensi (usulan) | Cara |
| --- | --- | --- | --- |
| Database GLPI | Tiket, pengguna, KB, keputusan AI (`glpi_plugin_halosis_*`) | Harian + sebelum upgrade | `mysqldump` (perintah di bawah) |
| File GLPI | Lampiran tiket, dokumen (`glpi_data`, folder `files/`) | Harian | Arsip volume |
| Konfigurasi | `.env`, `themes/`, plugin | Setiap perubahan | Git (tanpa `.env`) + salinan `.env` terenkripsi |
| Model & indeks AI | `ai/models/`, `ai/index/` | Setiap rilis model / tiap minggu | Salin ke penyimpanan internal (data internal, jangan ke drive publik) |

Perintah (dari folder proyek):

```bash
# Database
docker compose exec -T db sh -c 'mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" --single-transaction "$MYSQL_DATABASE"' \
  | gzip > backup/glpi-$(date +%F).sql.gz

# File GLPI (volume glpi_data)
docker run --rm -v glpi-halosis_glpi_data:/data -v "$PWD/backup":/out alpine \
  tar czf /out/glpi-files-$(date +%F).tgz -C /data .

# Model & indeks AI
tar czf backup/ai-$(date +%F).tgz ai/models ai/index
```

Nama volume bisa berbeda; cek dengan `docker volume ls`. Folder `backup/` harus ada di `.gitignore`.

## 3. Uji restore (lakukan minimal sekali sebelum demo/pengumpulan)

```bash
docker compose down -v                    # HANYA di laptop uji: menghapus semua data
docker compose up -d db && sleep 20
gunzip -c backup/glpi-YYYY-MM-DD.sql.gz | \
  docker compose exec -T db sh -c 'mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"'
docker compose up -d
```

Lulus bila: login `rina` berhasil, jumlah tiket sama dengan sebelum backup, satu tiket lama menampilkan panel
Saran AI & riwayat keputusannya, dan `/health` layanan AI `"status":"ok"`.

| Tanggal uji | Backup yang dipakai | Waktu pulih (RTO) | Data hilang (RPO) | Hasil | Penguji |
| --- | --- | --- | --- | --- | --- |
| | | | | | |

## 4. Target pemulihan (usulan, disepakati dengan BPS)

| Ukuran | Usulan | Dasar |
| --- | --- | --- |
| RPO (maks. data hilang) | 24 jam | Backup harian |
| RTO (maks. waktu pulih) | 4 jam | Restore DB + volume + restart layanan |
| Bila layanan AI mati | Tidak menghentikan layanan | Tiket tetap bisa dibuat & ditangani manual (mode demo / triase manual) |
