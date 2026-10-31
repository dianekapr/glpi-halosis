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
| 3. Syarat lulus | Top-1 & Top-3 **tidak turun** > 2 poin dari versi aktif; akurasi pada keyakinan ≥ 70% tetap ≥ 85%; tidak ada tim besar yang recall-nya < 50% | Tabel banding di `reports/triase.md` |
| 4. Persetujuan | Manajemen (A) setelah konsultasi Operator (C) | Catatan persetujuan di tabel §5 |
| 5. Pasang | Ganti `ai/models/triage.joblib`, `docker compose restart halosis-ai`, cek `/health` menampilkan versi baru | `/health` → `versi_model` |
| 1b. Data koreksi (T10) | Keputusan **Ubah/Tolak** Operator (`glpi_plugin_halosis_decisions`: nilai saran, nilai final, alasan) diekspor dan ditinjau Pengelola AI; tim final yang dikoreksi Operator ditambahkan ke data latih berikutnya (tiket GLPI, teks disamarkan). Proses **manual** sebelum langkah 1; belum otomatis | Jumlah koreksi yang dipakai dicatat di §5 |
| 6. Pantau 2 minggu | Rasio Ubah/Tolak di dashboard Kinerja AI dibanding versi lama | Dashboard Kinerja AI |
| 7. Rollback | Bila rasio Ubah+Tolak naik > 10 poin atau ada keluhan routing berulang: pasang kembali file versi sebelumnya (simpan minimal 2 versi terakhir di luar repo) | Catatan di tabel §5 |

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

Domain mengikuti kategori layanan (service catalog) dan grup penanganannya di `seed_halosis.py`.

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
