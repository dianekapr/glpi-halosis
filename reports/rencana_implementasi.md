# Rencana implementasi HaloSIS (pilot → produksi)

Untuk tim proyek, sponsor, dan tim operasional TI BPS. Mengacu WBS Fase 5–7 (dokumen §WBS: Integrasi & Pengujian,
Deployment/Migrasi/Pelatihan, Closing & Hypercare), kelayakan integrasi 2.1.5 (Tabel 2.5), dan risiko organisasi
2.3.5. Status prototipe per butir ada di `reports/audit_kelengkapan.md`.

## 1. Lingkungan (2.1.5: pemisahan pengembangan, staging, produksi)

| Lingkungan | Isi | Data | Akses | Catatan |
| --- | --- | --- | --- | --- |
| Pengembangan | docker-compose repo ini (laptop/VM dev) | Data contoh `seed_halosis.py` + model dari Drive (tersamar) | Tim proyek | Profile opsional `tls`, `monitoring` |
| Staging | VM/OpenShift BPS, konfigurasi = produksi | Salinan tersamar history ≥ 3 tahun (migrasi uji) | Tim proyek, perwakilan Operator & Tim Teknis (UAT) | SSO BPS uji (realm terpisah), SMTP uji |
| Produksi | VM/OpenShift BPS, replika `halosis-ai` ≥ 2, DB terkelola, backup harian | Data operasional + arsip history (entitas terpisah) | Pengguna BPS | TLS sertifikat BPS, port 8080 tertutup, Prometheus/Grafana + alert |

Promosi rilis: dev → staging (SIT + UAT, WBS 5.1–5.5) → produksi; model AI dirilis lewat siklus `tata_kelola_ai.md`
§2 (syarat lulus + gerbang kualitas `/health`), artefak model & indeks di-versikan di luar git.

## 2. Tahapan

| Tahap (WBS) | Lama | Kegiatan | Keluaran / gerbang |
| --- | --- | --- | --- |
| Uji integrasi (5.1–5.4) | 6 minggu | SIT SSO BPS (pemetaan role & tim dari grup AD/Keycloak), notifikasi SMTP BPS, uji akurasi model (`reports/triase.md`, `banding_embedding.md`), uji keamanan (checklist + pemindaian), uji beban di staging (`tests/load/`) | Semua skenario `reports/uji_regresi_demo.md` lolos di staging; uji beban Normal/Peak lolos; gerbang kualitas model lolos |
| UAT (5.5) | 2–3 minggu | Operator, Tim Teknis, Knowledge Manager, Manajemen menjalankan skenario per peran (`reports/panduan_peran.md`) | Berita acara sign-off |
| **Pilot** | 4 minggu | 1–2 satker + layanan Email, SSO, SiPecut (48,2% tiket, 5.1 Outcome); chatbot & triase aktif, Operator memvalidasi semua saran | Ambang tingkat keyakinan dikalibrasi ulang dari keputusan Operator; % diterima, % salah tim, % terbantu tanpa tiket di dashboard |
| **Migrasi data** (6.1) | 7 HK | Ekspor ESTIM ≥ 3 tahun → `prepare_data.py` (penyamaran) → `reconcile.py` → muat ke entitas arsip lewat API (`migrate_sample.py` diperluas: batch, idempoten, `externalid`) | Rekonsiliasi sumber = berhasil + dilewati + gagal; sampel diverifikasi Operator |
| **Parallel run** (6.2) | 2–4 minggu | ESTIM tetap sistem resmi; tiket baru juga dicatat di HaloSIS (atau HaloSIS resmi untuk satker pilot, ESTIM hanya baca). Bandingkan harian: jumlah tiket, SLA breach, waktu penugasan | Selisih jumlah tiket < 2%; KPI HaloSIS ≥ ESTIM; tidak ada insiden kritis terbuka |
| **Cutover** (6.5 Go Live) | 1 hari (akhir pekan) | Bekukan ESTIM (baca saja) → migrasi delta → indeks ulang AI → buka HaloSIS untuk semua pengguna | Checklist go-live (`reports/checklist_demo.md` §2 versi produksi) |
| **Hypercare** (7.1) | 13 HK | Tim proyek siaga; triase insiden pasca go-live harian; pantau Grafana & log; evaluasi KPI awal (7.2) | Log insiden hypercare; laporan KPI awal; serah terima (7.3) |

## 3. Rollback

| Pemicu | Tindakan |
| --- | --- |
| Insiden kritis HaloSIS > 4 jam atau galat login SSO meluas saat cutover/hypercare | Buka kembali ESTIM untuk pencatatan tiket baru; HaloSIS hanya baca; tiket yang sudah masuk HaloSIS diekspor (API) untuk dicatat ulang |
| Model AI menurun (gerbang kualitas tidak lolos, rasio Ubah+Tolak naik > 10 poin) | Rollback model ke versi sebelumnya (`tata_kelola_ai.md` §2 langkah 7); triase manual tetap berjalan |
| Data rusak setelah perubahan konfigurasi | Pulihkan DB dari backup harian (uji restore `keamanan_backup.md` §3: ±6 detik untuk DB uji) |

## 4. Risiko organisasi (2.3.5) → tindakan implementasi

| Risiko | Tindakan |
| --- | --- |
| Pengguna tidak terbiasa proses baru | Pilot bertahap, sosialisasi (6.4), chatbot sebagai pintu masuk dengan tombol "Buat laporan" selalu tersedia |
| Operator tidak percaya hasil AI | HITL penuh (Terima/Ubah/Tolak + alasan), penjelasan & 3 kandidat tim, dashboard kalibrasi keyakinan |
| Ownership sistem/knowledge tidak jelas | RACI & pemilik domain knowledge (`tata_kelola_ai.md` §1, §4b); tab "Perlu ditinjau" |
| Kebutuhan kompetensi baru | Pelatihan per peran (`panduan_peran.md`), dokumentasi README & plugin README, serah terima 7.3 |
| Perubahan terlalu besar sekaligus | Layanan pilot dulu; fitur AI bisa dimatikan per fitur di Pengaturan AI |
| Tim teknis menilai routing belum sesuai | "Kembalikan ke operator (salah tim)" + ekspor koreksi untuk latih ulang |
