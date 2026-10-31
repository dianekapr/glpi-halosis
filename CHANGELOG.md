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
- **Koreksi sebelum rilis (masih 1.0.0):** SLA resmi BPS dari history ESTIM (respons 15 menit; insiden Crit 2 /
  Medium 8 / Low 15 hari; permintaan 7/14 hari; kalender jam kerja; peringatan ±20%) menggantikan angka asumsi; KPI
  kepatuhan SLA sebanding baseline 27,59%; gerbang kualitas memeriksa semua syarat tata kelola per model
  (`quality.py`, `triage.metrics.json`); model prioritas insiden (`train_prioritas.py`) hanya dipakai bila lolos.
- **Data history versi baru (masih 1.0.0):** ekspor 220 kolom (tanggal serial Excel → `halosis_ai/dates.py`),
  rekonsiliasi lama vs baru; solusi knowledge = pesan terakhir ≤ resolved + 5 menit bukan dari pemohon
  (`reports/banding_solusi.md`; dedup ditolak gerbang), potongan > 220 kata dipecah; triase & jenis dilatih ulang
  dengan gerbang "tidak turun"; **model urgensi insiden** (`train_urgensi.py`) menggantikan model prioritas; **sinyal
  dampak** (≥ 3 tiket serupa / 60 menit, layanan kritis `critical_services`) + alasan di panel (kolom
  `urgency_confidence`, `impact_reason`: jalankan `plugin:install --force`); kata kunci urgensi per kata utuh +
  negasi; KPI kepuasan pemohon & baseline dari `baseline.json` (SLA 28,87%, 1.819 berimputasi; kepuasan 95,76%);
  NIP lama 9 digit disamarkan.
- **Finalisasi konsistensi (1 Nov 2026, masih 1.0.0):** urgensi insiden dengan **ambang per kelas** dari validasi
  silang (Rendah P(Low) ≥ 0,90 presisi 78,79%; Sedang P(Low) ≤ 0,45 akurasi 84,30%), gerbang per kelas
  (`quality.check('urgensi')` → `kelas_lolos`), model terkalibrasi kedua dihapus; baseline dashboard dua baris
  (dokumen 27,59% / 42,62%, history versi baru 28,87% + respons 43,08%) + cakupan rating 17,3% (`baseline.json`
  `dokumen`, `sla_respons`, `metode`); angka triase/jenis/retrieval/DBSCAN disinkronkan di README & laporan.
- Konsistensi: eskalasi SLA = Ticket Recall tanpa mengubah prioritas; tim teratas "Lainnya" selalu penilaian manual;
  kategori contoh "Server Hosting" untuk SLA pemenuhan 14 hari.
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
