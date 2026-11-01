# Tata kelola AI HaloSIS (NFR-14)

NFR-14: *"Kepemilikan yang jelas terhadap AI release, threshold, knowledge source, override, dan audit."*
Dokumen ini menetapkan **siapa** memiliki tiap keputusan AI, **bagaimana** perubahan dirilis, dan **di mana**
jejaknya tersimpan. Nama peran mengikuti Tabel 6.1; nama orang diisi oleh BPS.

## 1. Pemilik (RACI)

R = mengerjakan · A = memutuskan/bertanggung jawab akhir · C = dimintai pendapat · I = diberi tahu

| Keputusan | Administrator Sistem | Pengelola AI (tim pengembang) | Knowledge Manager | Operator | Manajemen |
| --- | :-: | :-: | :-: | :-: | :-: |
| Rilis/rollback model triase | C | R | I | C | **A** |
| Ambang keyakinan triase (`triage_threshold` 70% & `ai_threshold_low` 40%) | R | C | I | C | **A** |
| Ambang chat (`CHAT_MIN_SCORE` 0,83) | R | C | **A** | I | I |
| Parameter deteksi pola (ambang 0,50, jendela 60 mnt, min. 3 tiket) | R | C | I | **A** | I |
| Sumber knowledge (artikel KB, tiket historis yang diindeks) | I | R | **A** | C | I |
| Menyalakan/mematikan fitur AI & penyedia LLM opsional | **A/R** | C | I | I | I |
| Override rekomendasi per tiket (Terima/Ubah/Tolak) | I | I | I | **A/R** | I |
| Tinjauan audit berkala | C | R | C | C | **A** |

Pengelola AI = 1–2 orang yang melatih ulang model (`ai/README.md`); di prototipe ini anggota tim pengembang.

## 2. Siklus rilis model triase

| Langkah | Isi | Bukti |
| --- | --- | --- |
| 1. Latih | `ai/scripts/train_triage.py` dari data history yang sudah disamarkan (`prepare_data.py`) | Versi model `triase-tfidf-lr-<tanggal>` |
| 2. Evaluasi | Set uji terpisah; laporkan Top-1, Top-3, F1 makro, akurasi pada keyakinan ≥ ambang | `reports/triase.md` |
| 3. Syarat lulus | Top-1 & Top-3 **tidak turun** > 2 poin dari versi aktif; akurasi pada keyakinan ≥ 70% tetap ≥ 85%; tidak ada tim besar (≥ 5% tiket uji; kelas gabungan "Lainnya" dicatat terpisah) yang recall-nya < 50%; Top-1 ≥ 0,68 (baseline PoC). Model jenis: F1 makro harus mengungguli pembanding kelas mayoritas dan tidak turun > 2 poin dari versi aktif pada set uji yang sama (latih ulang mengganti artefak hanya bila lolos). Model urgensi: **per kelas pada ambangnya** (validasi silang 5 lipatan) — Low: presisi ≥ 75%, batas bawah Wilson 95% > proporsi Low, ≥ 30 tiket; Medium: akurasi > proporsi Medium + 3 poin, ≥ 30 tiket; kelas yang tidak lolos tidak pernah disarankan (`HALOSIS_GATE_MIN_PRECISION_LOW`, `_MIN_GAIN_MEDIUM`, `_MIN_SUPPORT`) | Metrik di artefak / `ai/models/triage.metrics.json` (`ai/scripts/model_metrics.py`); `halosis-ai` memeriksa otomatis (`/health` → `kualitas_model` per model); model tidak lolos tidak dipakai / panel "belum lolos uji kualitas" |
| 4. Persetujuan | Manajemen (A) setelah konsultasi Operator (C) | Catatan persetujuan di tabel §5 |
| 5. Pasang | Ganti `ai/models/triage.joblib`, `docker compose restart halosis-ai`, cek `/health` menampilkan versi baru | `/health` → `versi_model` |
| 1b. Data koreksi (T10) | Keputusan **Ubah/Tolak** Operator (`glpi_plugin_halosis_decisions`: nilai saran, nilai final, alasan) diekspor lewat tombol **Ekspor koreksi (CSV, tersamar)** di dashboard Kinerja AI (hak Pengaturan AI; `/plugins/halosis/Dashboard/Koreksi`: judul & deskripsi tersamar, jenis, tim saran vs final, alasan) dan ditinjau Pengelola AI; tim final yang dikoreksi Operator ditambahkan ke data latih berikutnya (tiket GLPI, teks disamarkan). Penggabungan ke data latih masih **manual** sebelum langkah 1 | Jumlah koreksi yang dipakai dicatat di §5 |
| 6. Pantau 2 minggu | Rasio Ubah/Tolak di dashboard Kinerja AI dibanding versi lama | Dashboard Kinerja AI |
| 7. Rollback | Bila rasio Ubah+Tolak naik > 10 poin atau ada keluhan routing berulang: pasang kembali file versi sebelumnya (simpan minimal 2 versi terakhir di luar repo) | Catatan di tabel §5 |

**Kelas gabungan "Lainnya" dikecualikan dari syarat recall tim besar.** "Lainnya" menggabungkan tim dengan < 30
tiket latih (21 kelas → 1 kelas gabungan); kelas ini bukan tim tujuan sehingga recall-nya (0,335 pada uji Jul–Ags)
tidak mengukur ketepatan routing ke tim nyata, dan menggabungkannya ke syarat akan menolak model hanya karena tim kecil
memang tidak dipelajari. Gantinya: setiap saran dengan tim teratas "Lainnya" **selalu** berstatus *Perlu penilaian
manual* (`triage_model.py`, plugin `Triage.php`; tes `test_lainnya_selalu_penilaian_manual`), dan recall "Lainnya"
tetap dicatat terpisah di `triage.metrics.json` (`recall_lainnya`) untuk dipantau di audit bulanan.

Versi model tercatat di setiap saran (`glpi_plugin_halosis_suggestions.model`), sehingga keputusan lama
tetap bisa ditelusuri ke model yang menghasilkannya.

## 3. Perubahan ambang & parameter

- Diubah lewat **Pengaturan AI** (hak `plugin_halosis_config`, profil Administrator); nilai di luar rentang
  ditolak oleh validasi `src/Config.php`.
- Setiap perubahan dicatat di tabel §5 beserta alasan dan pemilik yang menyetujui (§1).
- Dasar perubahan harus data, mis. kalibrasi di `reports/triase.md` (keyakinan vs akurasi) atau jumlah
  Problem palsu dari deteksi pola yang ditutup Operator.

## 4. Sumber knowledge

| Sumber | Masuk indeks | Pemilik | Aturan |
| --- | --- | --- | --- |
| Artikel KB yang terbit / FAQ | Otomatis saat terbit, dihapus saat ditarik (`/reindex/artikel`) | Knowledge Manager | Hanya artikel terbit; draf tidak diindeks |
| Solusi tiket historis | Dibangun ulang manual (`build_index.py`) | Pengelola AI | Wajib lewat penyamaran PII; data mentah tidak pernah masuk repo |
| Kandidat knowledge | Tidak diindeks sampai diterbitkan sebagai artikel | Knowledge Manager | Kurasi manusia (Jadikan artikel / Abaikan + alasan) |
| SOP & service catalog | Belum (rencana lanjut) | Knowledge Manager | — |

Artikel yang terbukti salah: Knowledge Manager menarik artikel → indeks terhapus otomatis → catat di §5.
Artikel terbit yang tidak diubah > `kb_review_months` (bawaan 6 bulan) muncul di tab **Perlu ditinjau** halaman
Kandidat knowledge; menyuntingnya menandai sudah ditinjau.

### 4b. Pemilik per domain knowledge (KR-01)

Knowledge Manager tetap **A** (menerbitkan/menarik). Pemilik domain **R**: menjamin isi teknis benar dan
meninjau artikel domainnya saat muncul di "Perlu ditinjau".

Domain mengikuti kategori layanan (service catalog) dan grup penanganannya di `seed_halosis.py`. **Kategori artikel KB = domain**:
artikel ditempatkan di kategori KB domainnya, sehingga pemilik domain (tabel di bawah) berlaku tanpa field tambahan per artikel
(KR-01, KR-03).

| Domain | Kategori layanan | Pemilik domain (R) | Penyetuju terbit (A) |
| --- | --- | --- | --- |
| Identitas & akses | SSO / Login, TTE, hak akses folder | Ketua Tim Identitas & Akses | Knowledge Manager |
| Email & kolaborasi | Email Dinas, Zoom / Konferensi | Ketua Tim Aplikasi Statistik | Knowledge Manager |
| Jaringan | Jaringan & VPN | Ketua Tim Jaringan | Knowledge Manager |
| Aplikasi statistik | FASIH, SiPecut, SIMDASI | Ketua Tim Aplikasi Statistik | Knowledge Manager |
| Perangkat TI end user | Laptop / Perangkat, Printer | Ketua Tim Perangkat | Knowledge Manager |
| Layanan umum & service catalog | Form permintaan, SOP layanan | Operator Service Desk (koordinator) | Knowledge Manager |

## 5. Log perubahan tata kelola (diisi)

| Tanggal | Jenis (rilis model / ambang / sumber / fitur) | Dari → ke | Alasan & bukti | Disetujui (peran, nama) | Dikerjakan |
| --- | --- | --- | --- | --- | --- |
| 29 Okt 2026 | Parameter pola | min. 10 → 3 tiket | Disamakan dengan PoC hal. 56 (minimum 3 incident) | Tim proyek | Tim proyek |
| 31 Okt 2026 | Sumber data | ekspor history 137 → 220 kolom | Versi baru memuat urgensi/dampak/prioritas, rating, SLA diperluas; rekonsiliasi `reports/rekonsiliasi.md` (1 REQ tanpa nomor hilang, 2,05% status berubah) | Tim proyek | Tim proyek |
| 31 Okt 2026 | Sumber knowledge | solusi = pesan petugas terakhir di seluruh percakapan → pesan terakhir ≤ resolved + 5 menit, bukan pemohon | `reports/banding_solusi.md`: Top-1 −0,65 / Top-3 −0,37 poin / MRR −0,005 (dalam toleransi 1 poin); dedup solusi identik **ditolak** (Top-1 −1,96 poin) | Tim proyek | Tim proyek |
| 31 Okt 2026 | Rilis model | triase `20261028` → `20261031`; jenis `20261031` (latih ulang) | Set uji sama (data baru): Top-1 74,47 → 75,88%, Top-3 93,01 → 94,87%; jenis F1 makro 67,50 → 67,52% → gerbang lolos | Tim proyek | Tim proyek |
| 31 Okt 2026 | Rilis model / fitur | prioritas (proksi tier SLA, tidak lolos) → urgensi insiden `urgensi-tfidf-tim-lr-20261031` + sinyal dampak | F1 makro 57,97% vs pembanding 44,82% (CV 5 lipatan) → lolos; dipakai hanya bila keyakinan ≥ 70%; dampak naik 1 bila ≥ 3 tiket serupa / 60 menit atau layanan kritis (`critical_services`). *Historis — diganti 1 Nov* | Tim proyek | Tim proyek |
| 1 Nov 2026 | Ambang / gerbang | urgensi: satu ambang keyakinan 70% (model terkalibrasi, Low tertangkap 0%) → ambang per kelas dari P(Low) LR seimbang, `urgensi-tfidf-tim-lr-20261101` | CV 5 lipatan: Low P ≥ 0,90 presisi 78,79% (Wilson 62,25–89,32%) vs proporsi 18,76%, recall 5,12% (33 tiket); Medium P ≤ 0,45 akurasi 84,30% vs 81,24%, cakupan 76,70%; kedua kelas lolos. Keterbatasan: Low hanya ± 5% insiden Low, sisanya aturan; Medium lolos tipis (syarat > 84,24%) | Tim proyek | Tim proyek |
| | | | | | |

## 6. Audit berkala (bulanan)

| Yang ditinjau | Sumber data | Pemeriksa |
| --- | --- | --- |
| Rasio Terima/Ubah/Tolak per tim & per versi model | Dashboard Kinerja AI, `glpi_plugin_halosis_decisions` | Pengelola AI → Manajemen |
| Alasan Ubah/Tolak yang berulang (tim yang sering salah) | Kolom alasan keputusan | Operator |
| Chat "tidak ditemukan" & rating rendah | `glpi_plugin_halosis_chats`, `reports/latensi.md` | Knowledge Manager |
| Problem dari deteksi pola: dikonfirmasi vs ditutup sebagai palsu | Menu Pola insiden | Operator |
| Latensi AI p95 | `ai/scripts/latency_report.py` | Pengelola AI |
| Residu PII di indeks | `prepare_data.py::residual_pii` | Pengelola AI |
