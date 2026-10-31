# Changelog plugin HaloSIS

Versi = `PLUGIN_HALOSIS_VERSION` (`plugins/halosis/setup.php`). Setiap kenaikan versi menambah tabel/kolom/config:
jalankan `plugin:install --force` + `plugin:activate` (README › C3). Rincian audit: `reports/audit_dokumen_e2e.md`.

## 1.0.0 — 31 Okt 2026
- **Siap ditutup (T21):** daftar Operator untuk tiket Selesai tanpa respons pemohon > `close_after_hours` (48), tutup
  per tiket/massal, tanpa tutup otomatis.
- **SLA per layanan (T22):** `config/sla_layanan.json` → aturan per kategori & jenis (respons + penyelesaian/pemenuhan),
  cadangan SLA per prioritas (`setup_sla_alerts.py`); notifikasi "New followup" ke teknisi & grup (T23).
- **Dashboard KPI tabel 1.3 (T24/T25):** % SLA terlampaui, median waktu sampai diambil, % L1, volume per minggu.
- **Layanan AI:** rate limit per klien (T26, `HALOSIS_RATE_LIMIT_PER_MIN`), gerbang kualitas model (T32, kolom
  `quality_ok`), FAQ Email/SSO/SiPecut (T30), chatbot mengarahkan pertanyaan non-TI (T31).
- Snapshot demo ikut menyimpan & memulihkan indeks AI.
- Diuji pada GLPI 12.0.1 (`reports/uji_upgrade.md`); dokumen `rencana_implementasi.md`, `panduan_peran.md`.

## 0.10.0 — 31 Okt 2026
- **Jenis disarankan (T4):** `/triage` mengembalikan saran REQ/INC bila `ai/models/jenis.joblib` ada; panel
  menampilkannya hanya bila berbeda dari jenis tiket & keyakinan ≥ ambang (kolom `type_suggested`, `type_confidence`).
- **Pratinjau dampak & jejak konfigurasi (T20, UC-10):** tombol *Pratinjau dampak* di Pengaturan AI; perubahan
  Pengaturan AI, aturan tiket/SLA, SLA, kategori → log sistem GLPI + Catatan untuk Administrator (`ConfigAudit`).
- **Perbaikan login SSO bersamaan:** dropdown Jabatan/Lokasi toleran duplikat; galat jalur login ditangkap agar GLPI
  tidak menonaktifkan plugin.
- Tugas `TriageRetry` & `IncidentPattern` mengecualikan entitas arsip migrasi ("Arsip ESTIM").

## 0.9.0
- Tugas terjadwal **`TriageRetry`** (NFR-03): saran untuk tiket Baru tanpa saran, idempoten, maks. 5 percobaan.
- Deteksi pola: opsi **DBSCAN** (eps, min_samples) di Pengaturan AI; tiket yang dibuat sudah selesai tidak ditriase.

## 0.8.0
- **Katalog layanan & SOP** di indeks chatbot (`POST /reindex/layanan`, BR-03); sumber `LAYANAN-*` diarahkan ke form.
- **Tanggal tinjau berikut per artikel** (KR-03, tabel `kb_reviews`); **tren pola 12 minggu** di dashboard (BP-21).

## 0.7.0
- Beban tim per kandidat (T5), filter dashboard tim/kategori (T18), umpan balik agent di Cari knowledge (KR-07),
  dashboard artikel tidak membantu / pola / drift (BP-13/17/19), ekspor koreksi CSV (T10), chatbot keyakinan sedang
  "Maksud Anda…?" (T3), atribut NIP/unit kerja/jabatan dari Keycloak (T11).

## 0.6.0
- SLA respons (time to own), keyakinan 3 tingkat, pola hanya Insiden + tautkan ke Problem terbuka + notifikasi,
  tab "Perlu ditinjau", sesi chat berakhir 30 menit, sumber tiket "HaloSIS Chat", hitungan pemakaian artikel,
  hak hapus tiket hanya Super-Admin.

## 0.5.0
- Dasar: chatbot, saran triase + HITL, deteksi pola, Kandidat knowledge, dashboard kinerja AI, SSO Keycloak.
