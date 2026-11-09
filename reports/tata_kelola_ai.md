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
| 3. Syarat lulus | Top-1 & Top-3 **tidak turun** > 2 poin dari versi aktif; akurasi pada keyakinan ≥ 70% tetap ≥ 85%; tidak ada tim besar (≥ 5% tiket uji; kelas gabungan "Lainnya" dicatat terpisah) yang recall-nya < 50%; Top-1 ≥ 0,68 (baseline PoC). Model jenis: F1 makro harus mengungguli pembanding kelas mayoritas dan tidak turun > 2 poin dari versi aktif pada set uji yang sama (latih ulang mengganti artefak hanya bila lolos). Syarat akurasi triase dihitung pada `triage_threshold` aktif Pengaturan AI; titik ambang dengan cakupan < 10% atau < 100 tiket berstatus **data tidak cukup**, bukan lolos (`_MIN_POINT_COVERAGE`, `_MIN_POINT_TICKETS`); `ai_threshold_low` tidak digerbang. Model urgensi: **skema B, per kelas pada ambangnya** (validasi silang bertingkat 5 lipatan luar, seed 42): fitur tim = tim prediksi out-of-fold dari 5 lipatan dalam, data uji luar = prediksi model tim dari seluruh data latih luar; ambang dipilih hanya di lipatan dalam; metrik dari gabungan prediksi lipatan luar. Low: presisi ≥ 75%, batas bawah Wilson 95% > proporsi Low, ≥ 30 tiket; Medium: akurasi > proporsi Medium + 3 poin, ≥ 30 tiket; lolos bila ≥ 1 kelas lolos dan kelas yang tidak lolos tidak pernah disarankan. Ambang artefak = median lima lipatan luar; rentang antarlipatan > 0,10 ditandai **tidak stabil** di laporan & metrik walau lolos. Skema A (tim aktual) hanya pembanding. Model tim skema B tanpa kalibrasi. Kedua kelas gagal → saran urgensi **tidak dipakai**: artefak disimpan hanya untuk rollback, `urgensi.metrics.json` memuat hasil skema B sehingga `/triage` tidak menyarankan, dan urgensi kembali ke aturan + validasi Operator. `train_urgensi.py` menulis artefak hanya bila lolos, selalu setelah cadangan `backup/model-<waktu>/` + `MANIFEST.txt` sha256 (`HALOSIS_GATE_MIN_PRECISION_LOW`, `_MIN_GAIN_MEDIUM`, `_MIN_SUPPORT`, `_MAX_THRESHOLD_SPREAD`). Pola insiden: pada parameter aktif Pengaturan AI, diuji pada set `reports/banding_pola.md` (666 INC Jul–Ags): kemurnian tim ≥ 0,85 dan ≥ 5 kelompok, jumlah tiket terkelompok dilaporkan; gerbang ini **peringatan saja, tidak memblokir** (`_MIN_PATTERN_PURITY`, `_MIN_PATTERN_GROUPS`) | Metrik di artefak / `ai/models/triage.metrics.json` (`ai/scripts/model_metrics.py`); `halosis-ai` memeriksa otomatis (`/health` → `kualitas_model` per model); model tidak lolos tidak dipakai / panel "belum lolos uji kualitas" |
| 4. Persetujuan | Manajemen (A) setelah konsultasi Operator (C) | Catatan persetujuan di tabel §5 |
| 5. Pasang | Ganti `ai/models/triage.joblib`, `docker compose restart halosis-ai`, cek `/health` menampilkan versi baru | `/health` → `versi_model` |
| 1b. Data koreksi (T10) | Keputusan **Ubah/Tolak** Operator (`glpi_plugin_halosis_decisions`: nilai saran, nilai final, alasan) diekspor lewat tombol **Ekspor koreksi (CSV, tersamar)** di dashboard Kinerja AI (hak Pengaturan AI; `/plugins/halosis/Dashboard/Koreksi`: judul & deskripsi tersamar, jenis, tim saran vs final, alasan) dan ditinjau Pengelola AI; tim final yang dikoreksi Operator ditambahkan ke data latih berikutnya (tiket GLPI, teks disamarkan). Penggabungan ke data latih masih **manual** sebelum langkah 1 | Jumlah koreksi yang dipakai dicatat di §5 |
| 6. Pantau 2 minggu | Rasio Ubah/Tolak di dashboard Kinerja AI dibanding versi lama | Dashboard Kinerja AI |
| 7. Rollback | Bila rasio Ubah+Tolak naik > 10 poin atau ada keluhan routing berulang: pasang kembali file versi sebelumnya (simpan minimal 2 versi terakhir di luar repo) | Catatan di tabel §5 |

**Status urgensi insiden (7 Nov 2026): tidak dipakai.** Model gagal gerbang skema B, tanpa kelas yang lolos: Low presisi 50,00%
dari 14 tiket, Medium 84,11% tidak melampaui 84,24% dan ambangnya tidak stabil (rentang 0,45). Panel memakai aturan kata kunci
dan validasi Operator. Artefak disimpan untuk rollback (`ai/models/urgensi.metrics.json`, §5).

**Kelas gabungan "Lainnya" dikecualikan dari syarat recall tim besar.** "Lainnya" menggabungkan tim dengan < 30
tiket latih (21 kelas → 1 kelas gabungan); kelas ini bukan tim tujuan sehingga recall-nya (0,4319 pada uji Jul–Ags)
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
| Artikel KB yang terbit | Otomatis saat terbit/berubah target/FAQ, dihapus saat ditarik (`/reindex/artikel`, hook `KnowledgeIndex`) | Knowledge Manager | Hanya artikel terbit; draf tidak diindeks. **`/chat` (pegawai) = artikel yang terlihat pegawai di Tanya Jawab (FAQ): is_faq=1 DAN bertarget.** Artikel internal (non-FAQ) atau FAQ tanpa target hanya masuk Cari pengetahuan petugas (`/cari`, `jenis_sumber kb_internal`) |
| Solusi tiket historis | Dibangun ulang manual (`build_index.py`) | Pengelola AI | Wajib lewat penyamaran PII; data mentah tidak pernah masuk repo. Hanya untuk petugas (`/cari`), tidak dipakai `/chat` |
| Kandidat knowledge | Tidak diindeks sampai diterbitkan sebagai artikel | Knowledge Manager | Kurasi manusia (Jadikan artikel / Abaikan + alasan) |
| SOP & service catalog | Ya. Katalog layanan lewat `/reindex/layanan`; SOP sebagai artikel KB terbit | Knowledge Manager | Sumber tersetujui `/chat` bersama artikel FAQ bertarget |

Akses artikel internal (non-FAQ): hanya **Tim Teknis** (dan Knowledge Manager) lewat `/cari`; **Operator** memakai FAQ + solusi tiket
(hak profil Operator sengaja tidak diubah; keputusan 9 Nov 2026).

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
| 6 Nov 2026 | Gerbang | urgensi tim aktual → skema B; triase ambang tetap 70% → ambang aktif + syarat data cukup; pola: belum ada → peringatan | `reports/usulan_gerbang_a.md` + tambahan persetujuan: stabilitas ambang ≤ 0,10, min. 5 kelompok, cakupan ≥ 10% & ≥ 100 tiket | Tim proyek | Tim proyek |
| 6 Nov 2026 | Rilis model / gerbang | urgensi `urgensi-tfidf-tim-lr-20261101` aktif → **tidak dipakai**, aturan kata kunci + validasi Operator | Skema B gagal, tidak lolos dalam kondisi nyata (tim prediksi): Low presisi 50,00% dari 14 tiket; Medium 84,11% tidak > 84,24%; Medium tidak stabil (rentang ambang 0,45). Skema A: 70,83% / 84,87%. Bukti `reports/triase.md`, `logs/train_urgensi.log`; artefak disimpan untuk rollback | Tim proyek | Tim proyek |
| 6 Nov 2026 | Ambang / gerbang | ambang rata-rata pola tetap 0,50 → `pattern_threshold` di Pengaturan AI; `triage.metrics.json` + kurva ambang (nilai lain tetap); gerbang dinilai pada nilai aktif (`POST /gerbang`, peringatan saat menyimpan) | Set pola `ai/scripts/gerbang_pola.py`: bawaan 8 kelompok, 25 tiket, kemurnian 0,917 → lolos. Triase 70% → 88,35%, 790 tiket → lolos | Tim proyek | Tim proyek |
| 7 Nov 2026 | Sumber | 26 → 35 sumber `/chat` (impor 9 artikel KB); ambang chat 0,83 / 0,78 tetap | Kalibrasi ulang 35 sumber: rekaan 0,00% dijawab, 37,50% pilihan; judul sumber 100,00% dijawab. Bukti `reports/kalibrasi_ambang.md`, `logs/c9_kalibrasi_ulang.log` | Tim proyek | Tim proyek |
| 7 Nov 2026 | Fitur | LLM opsional lewat env, bawaan `none`; draf artikel disusun LLM dengan fallback templat | Peninjauan KM wajib karena model kecil bisa menambah frasa di luar sumber. Bukti `logs/uji_llm.log`, `logs/draf_llm.log`, `reports/dokumentasi_ai.md` §5.4–5.5 | Tim proyek | Tim proyek |
| 9 Nov 2026 | Sumber | Sumber `/chat` = artikel FAQ **dan** bertarget (sebelumnya: FAQ **atau** bertarget): 18 → 17 sumber KB (+17 layanan = 34); KB-5 (internal) keluar dari `/chat`, tetap di `/cari`; KB-31–39 (FAQ hasil impor) diberi target Entity seperti KB-2..15; plugin tidak lagi jatuh ke pencarian KB lokal saat sumber tidak terlihat (dikecualikan + ditanya ulang dengan ambang sama); ambang 0,83 / 0,78 tetap | Kalibrasi ulang 34 sumber: rekaan 0,00% dijawab (62,50% ditolak, 37,50% pilihan); judul sumber 100,00% dijawab. Bukti `reports/kalibrasi_ambang.md`, `logs/kb_inventaris_sebelum.md`, `logs/kb_inventaris_sesudah.md` | Tim proyek | Tim proyek |
| 9 Nov 2026 | Fitur (urutan `/chat`) | urutan murni skor e5 → artikel KB didahulukan bila lolos ambang 0,83, katalog jadi tautan layanan (`search.utamakan_kb`); ambang 0,83 / 0,78 tetap | Dipicu kasus "Lupa kata sandi SSO" (katalog layanan mengalahkan artikel KB). Retrieval 8 kasus: e5 mentah Top-1 62,50% / MRR 0,7614 → e5 + urutan /chat 75,00% / Top-3 87,50% / MRR 0,8239; n=8, kenaikan = 1 kasus (K6), kasus pemicu bukan bagian dari 8 kasus. Bukti `reports/replikasi_poc.md` (Retrieval) | Tim proyek | Tim proyek |
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
