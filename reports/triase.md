# Model saran triase HaloSIS (routing ke tim)

Versi `triase-tfidf-lr-20261031` · dibuat oleh `ai/scripts/train_triage.py`. Hanya angka; model disimpan di `ai/models/triage.joblib` (di-ignore git).

## Ringkasan

| Indikator | Nilai |
| --- | --- |
| Data latih / uji | 5.109 tiket Jan–Jun / 1.559 tiket Jul–Ags 2026 |
| Kelas (tim) | 21 (tim < 30 tiket di data latih → "Lainnya") |
| **Akurasi top-1** | **75,88%** |
| **Akurasi top-3** | **94,87%** |
| MRR | 0,8563 |
| F1 makro / tertimbang | 69,00% / 75,25% |
| Pembanding: selalu tim terbanyak | 10,97% ("Technical Layanan SiPecut") |
| Keyakinan ≥ 70% (saran bisa langsung diterima) | akurasi 88,35% · cakupan 50,67% tiket |
| Keyakinan < 70% ("Perlu penilaian manual") | akurasi 63,07% · cakupan 49,33% tiket |
| Galat kalibrasi (ECE) | 9,37% |

## Input & metode

- Input hanya informasi saat tiket dibuat: **judul + deskripsi + jenis (INC/REQ)**, sudah disamarkan.
  Kolom `routing_*`, `reassignment_*`, `team_change_*`, `*sla*`, dan resolusi **tidak dipakai**.
- Target: `assignment_group_name` akhir.
- Fitur: TF-IDF kata (1–2 gram) + karakter (3–5 gram, tahan salah ketik). Model: Logistic Regression,
  probabilitas dikalibrasi (sigmoid, 5-fold) → "keyakinan" = probabilitas tim teratas.
- Split berdasarkan waktu: latih Jan–Jun, uji Jul–Ags (meniru pemakaian nyata: model dilatih dari masa lalu).
- Populasi (DQR-05): `data/processed/tickets_clean.parquet` (ekspor history tiket 2026 hasil `prepare_data.py`,
  teks disamarkan); **semua status** (terbuka maupun selesai) dan **kedua jenis** INC & REQ (jenis menjadi fitur);
  hanya tiket dengan `assignment_group_name` terisi (tanpa tim tidak punya label). Latih: `opened` < 1 Jul 2026;
  uji: `opened` ≥ 1 Jul 2026. Tim dengan < 30 tiket di data latih → "Lainnya" (juga di data uji).
- Pemilihan pengaturan tanpa menyentuh data uji: latih Jan–Mei, validasi Juni.

| C | Bobot kelas | Validasi Juni: top-1 | F1 makro |
| --- | --- | --- | --- |
| 3 | tidak | 79,44% | 73,07% |
| 3 | balanced | 79,28% | 76,23% |
| 10 | tidak | 78,97% | 72,73% |
| 10 | balanced | 78,82% | 75,90% |
| 30 | tidak | 78,66% | 73,09% |
| 30 | balanced | 78,97% | 75,63% |

Terpilih: C = 3, bobot kelas = tidak.

## Keyakinan vs akurasi (data uji)

Bila terkalibrasi baik, "rata-rata keyakinan" ≈ "akurasi" di setiap pita.

| Pita keyakinan | Tiket | Rata-rata keyakinan | Akurasi |
| --- | --- | --- | --- |
| 0–30% | 76 | 25,3% | 35,5% |
| 30–50% | 224 | 42,9% | 50,0% |
| 50–70% | 469 | 60,3% | 73,8% |
| 70–90% | 790 | 80,9% | 88,4% |

## Per tim (data uji)

| Tim | Tiket uji | Presisi | Recall | F1 |
| --- | --- | --- | --- | --- |
| Technical Layanan Aplikasi Jaringan - Email | 288 | 82,3% | 83,7% | 83,0% |
| Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | 230 | 78,0% | 78,7% | 78,4% |
| Lainnya | 213 | 64,8% | 43,2% | 51,8% |
| Technical Layanan SiPecut | 171 | 92,3% | 97,7% | 94,9% |
| Technical Layanan Perangkat TI End User | 97 | 89,7% | 99,0% | 94,1% |
| Technical Layanan Presensi | 96 | 85,3% | 90,6% | 87,9% |
| Technical Layanan Back Office Selindo (BOS) | 74 | 80,0% | 64,9% | 71,6% |
| Operator Pusat | 67 | 8,3% | 3,0% | 4,4% |
| Technical Layanan Meeting Online | 56 | 93,2% | 98,2% | 95,7% |
| Technical Layanan Pengelolaan E-Sign | 47 | 95,9% | 100,0% | 97,9% |
| Technical Layanan Perangkat Lunak COTS | 38 | 97,0% | 84,2% | 90,1% |
| Technical Layanan SOBAT | 37 | 69,0% | 78,4% | 73,4% |
| Technical Layanan FASIH Moda CAWI CAPI | 33 | 21,0% | 78,8% | 33,1% |
| Technical Layanan Infrastruktur & Platform Jaringan - Website Hosting | 25 | 71,9% | 92,0% | 80,7% |
| Technical Layanan Koneksi Jaringan -  SSLVPN | 25 | 60,0% | 60,0% | 60,0% |
| Technical Layanan Aplikasi KipApp | 22 | 78,6% | 100,0% | 88,0% |
| Technical Layanan Infrastruktur & Platform Jaringan - Server Hosting | 10 | 50,0% | 30,0% | 37,5% |
| Technical Layanan Pengujian Aplikasi | 10 | 100,0% | 80,0% | 88,9% |
| Technical Layanan Koneksi Jaringan - LAN BPS Pusat | 9 | 100,0% | 77,8% | 87,5% |
| Technical Layanan Aplikasi Monitoring/Dashboard Sensus/Survei | 6 | 50,0% | 16,7% | 25,0% |
| Technical Layanan Aplikasi Jaringan - Community | 5 | 33,3% | 20,0% | 25,0% |

## Tim yang paling sering tertukar (data uji)

| Tim sebenarnya | Disarankan model | Tiket |
| --- | --- | --- |
| Lainnya | Technical Layanan FASIH Moda CAWI CAPI | 90 |
| Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | Technical Layanan Aplikasi Jaringan - Email | 37 |
| Technical Layanan Aplikasi Jaringan - Email | Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | 37 |
| Operator Pusat | Lainnya | 11 |
| Operator Pusat | Technical Layanan SiPecut | 11 |
| Technical Layanan Back Office Selindo (BOS) | Technical Layanan SOBAT | 9 |
| Technical Layanan Koneksi Jaringan -  SSLVPN | Lainnya | 8 |
| Operator Pusat | Technical Layanan Perangkat TI End User | 8 |
| Operator Pusat | Technical Layanan Presensi | 7 |
| Operator Pusat | Technical Layanan Aplikasi Jaringan - Email | 7 |

## Pergeseran data: tim di balik "Lainnya" (data uji)

Tim yang kecil/baru di Jan–Jun tetapi muncul di Jul–Ags tidak bisa dipelajari model; tiketnya jatuh ke "Lainnya"
atau ke tim lama yang mirip. Latih ulang berkala (mis. bulanan) mengatasi ini.

| Tim asli | Tiket latih (Jan–Jun) | Tiket uji (Jul–Ags) |
| --- | --- | --- |
| Technical Layanan Insiden Keamanan Informasi | 17 | 133 |
| Layanan Aplikasi Pendataan Digital Sensus/Survei (Moda CAPI dan atau CAWI) | 0 | 21 |
| Technical Layanan Aplikasi Simpeg Online | 22 | 9 |
| Technical Layanan Infrastruktur & Platform Jaringan - Container Hosting | 16 | 8 |
| Technical Layanan Infrastruktur & Platform Jaringan - Database Hosting | 24 | 7 |

## Catatan

- Akurasi diukur terhadap tim akhir di data history; tim akhir itu sendiri kadang hasil koreksi routing
  (≈5,8% tiket berindikasi salah routing), jadi sebagian "salah" model bisa berarti kasus ambigu.
- Tiket "Operator Pusat" (ditangani langsung operator) ikut menjadi kelas sendiri.
- Pembanding retrieval + LLM (opsional) tidak dijalankan: proyek berjalan tanpa API key LLM, sehingga tidak
  ada data yang dikirim ke API eksternal. Triase sepenuhnya memakai model lokal ini.

<!-- latih-ulang:mulai -->
## Latih ulang 31-10-2026 (data history versi baru)

Set uji sama untuk keduanya: 1.559 tiket Jul–Ags 2026 dari `tickets_clean.parquet` terbaru.

| Indikator | Model aktif `triase-tfidf-lr-20261028` | Kandidat `triase-tfidf-lr-20261031` |
| --- | --- | --- |
| Top-1 | 74,47% | 75,88% |
| Top-3 | 93,01% | 94,87% |
| MRR | 0,8422 | 0,8563 |
| F1 makro | 68,01% | 69,00% |
| Akurasi keyakinan ≥ 70% | 87,16% | 88,35% |
| Cakupan keyakinan ≥ 70% | 51,44% | 50,67% |
| Recall tim besar terendah | 78,70% | 78,70% |

Gerbang (tata_kelola_ai.md §2): **lolos — kandidat dipakai**.
<!-- latih-ulang:selesai -->

<!-- jenis:mulai -->
## Saran jenis tiket REQ/INC (T4)

Versi aktif `jenis-tfidf-lr-20261031` · `ai/scripts/train_jenis.py` · artefak `ai/models/jenis.joblib` (di-ignore git). Input judul + deskripsi (tersamar), tanpa token jenis; pembagian waktu sama dengan model tim.

| Indikator | Nilai |
| --- | --- |
| Data latih / uji | 5.122 / 1.559 tiket |
| **Akurasi** | **68,25%** |
| F1 makro | 67,52% |
| Pembanding: selalu jenis terbanyak | 57,28% |
| Keyakinan ≥ 70% (saran ditampilkan) | akurasi 83,96% · cakupan 40,80% tiket |
| Tiket uji yang yakin tetapi berbeda dari jenis asli | 102 |

Latih ulang 31-10-2026 pada set uji yang sama: model aktif `jenis-tfidf-lr-20261031` akurasi 68,25% · F1 makro 67,50%; kandidat `jenis-tfidf-lr-20261031` akurasi 68,25% · F1 makro 67,52% → gerbang **lolos, kandidat dipakai**.

Panel Saran AI menampilkan "Jenis disarankan" hanya bila saran berbeda dari jenis tiket dan keyakinan ≥ ambang; Operator tetap memutuskan (ubah jenis di form tiket).
<!-- jenis:selesai -->

<!-- urgensi:mulai -->
## Saran urgensi insiden (BR-05, 2.1.4 Urgency/Impact/Priority)

Versi `urgensi-tfidf-tim-lr-20261101` · `ai/scripts/train_urgensi.py` · artefak `ai/models/urgensi.joblib` + `urgensi.metrics.json` (di-ignore git). Label = kolom `urgency` history versi baru (insiden Medium vs Low). Dampak = urgensi pada 99,74% insiden dan prioritas = matriks keduanya, jadi satu model; model prioritas lama (proksi tier SLA) dihapus.

Insiden berlabel Medium / Low: 2.200 / 508; validasi silang 5 lipatan bertingkat (seed 42); LR berbobot kelas seimbang → P(Low). **Ambang per kelas** dipilih otomatis dari P(Low) validasi silang (bukan satu ambang keyakinan):

| Kelas | Aturan | Hasil validasi silang | Pembanding | Gerbang |
| --- | --- | --- | --- | --- |
| Low (Rendah) | P(Low) ≥ 0,90 | presisi **78,79%** (Wilson 95% 62,25%–89,32%), recall 5,12%, 33 tiket | proporsi Low 18,76% | **lolos** |
| Medium (Sedang) | P(Low) ≤ 0,45 | akurasi **84,30%**, cakupan 76,70% insiden (2.077) | proporsi Medium 81,24% | **lolos** |
| Di antaranya | – | 22,08% insiden | – | aturan kata kunci |

Syarat (quality.urgency_class_check): Low presisi ≥ 75,00%, batas bawah Wilson > pembanding, ≥ 30 tiket (ambang terendah yang lolos = recall terbesar); Medium akurasi > pembanding + 3 poin, ≥ 30 tiket (ambang tertinggi yang lolos = cakupan terbesar). Kisi ambang 0,05.

**Keterbatasan cakupan Low:** hanya 5,12% insiden Low dikenali model; sisanya tetap dari aturan kata kunci. Tanpa ambang per kelas (argmax 0,5): akurasi 74,30%, F1 makro 57,97% vs pembanding selalu Medium 81,24%.

Tidak dimodelkan (tetap aturan + sinyal): (kosong) 57, High 12 insiden; permintaan (REQ).
Catatan label: 81,24% insiden berlabel Medium; sebagian besar kemungkinan nilai bawaan formulir, bukan penilaian petugas, sehingga batas atas akurasi model terbatas.

Panel Saran AI menampilkan "Urgensi disarankan: Rendah/Sedang (keyakinan)" hanya bila kelas itu lolos gerbang dan P(Low) melewati ambangnya (keyakinan = P(Low) untuk Rendah, 1 − P(Low) untuk Sedang); selain itu urgensi dari aturan kata kunci. Dampak = urgensi, naik satu tingkat bila ≥ 3 tiket serupa dalam 60 menit atau layanan kritis (konfigurasi). Operator tetap memutuskan.
<!-- urgensi:selesai -->
