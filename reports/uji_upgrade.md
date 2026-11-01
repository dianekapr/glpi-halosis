# Uji upgrade GLPI 12.0.0 → 12.0.1 (T27, Skenario 2 §2.4.2)

Tanggal: 31 Okt 2026 · Penguji: tim proyek (dibantu Claude Code). Lingkungan utama **tidak disentuh**.

## Cara uji (terisolasi)

1. Jaringan Docker sementara `halosis-upgrade-uji`; MySQL 8.4 sementara (alias `db`) diisi dump snapshot terakhir
   (`backup/terakhir/glpi.sql.gz`, restore 5 dtk).
2. Volume `/var/glpi` sementara = salinan volume GLPI utama (dibaca saja: konfigurasi, `glpicrypt.key`).
3. Container `glpi/glpi:12.0.1` (patch terbaru yang tersedia; 12.0.2+ belum ada) dengan plugin HaloSIS 1.0.0
   dipasang read-only, port `127.0.0.1:8090`.
4. Setelah uji: container, jaringan, dan volume sementara dihapus.

## Hasil

| Pemeriksaan | Hasil |
| --- | --- |
| Migrasi skema | ✅ Dijalankan otomatis oleh entrypoint image saat start (±25 dtk); `database:update` setelahnya: *No migration needed*, versi DB 12.0.1 |
| Integritas skema (`database:check_schema_integrity`) | ✅ *Database schema is OK* |
| Plugin HaloSIS 1.0.0 | ✅ *Enabled*, tanpa galat baru di `php-errors.log` |
| Halaman login | ✅ HTTP 200 |
| Data | ✅ 67 tiket, 108 saran AI, 39 keputusan AI terbaca sama seperti sebelum upgrade |
| Fitur plugin (server) | ✅ Statistik dashboard, daftar Siap ditutup, 6 template utama terkompilasi |
| REST API | ⚠️ Ditolak `ERROR_NOT_ALLOWED_IP` dari jaringan uji: pembatasan IP klien API ikut terbawa (perilaku yang benar) |
| SSO Keycloak | Tidak diuji (Keycloak tidak ada di jaringan uji); kode SSO plugin tidak bergantung versi patch |

## Prosedur upgrade untuk produksi

1. `scripts/demo_snapshot.sh simpan` (atau backup harian) → 2. ganti tag image di `docker-compose.yml`
(`glpi/glpi:12.0.x`) → 3. `docker compose up -d glpi` (migrasi otomatis) → 4. `php bin/console database:check_schema_integrity`
→ 5. `plugin:list` (HaloSIS *Enabled*) → 6. jalankan regresi `reports/uji_regresi_demo.md`. Rollback: tag lama +
`demo_snapshot.sh pulihkan` / restore backup.

Catatan: repo tetap mengunci `glpi/glpi:12.0.0` sampai upgrade disetujui (tata kelola rilis); hasil ini menunjukkan
patch 12.0.1 aman untuk plugin HaloSIS 1.0.0.
