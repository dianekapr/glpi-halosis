# Model saran triase HaloSIS (routing ke tim)

Versi `triase-tfidf-lr-20261028` · dibuat oleh `ai/scripts/train_triage.py`. Hanya angka; model disimpan di `ai/models/triage.joblib` (di-ignore git).

## Ringkasan

| Indikator | Nilai |
| --- | --- |
| Data latih / uji | 5.109 tiket Jan–Jun / 1.559 tiket Jul–Ags 2026 |
| Kelas (tim) | 21 (tim < 30 tiket di data latih → "Lainnya") |
| **Akurasi top-1** | **74,41%** |
| **Akurasi top-3** | **93,07%** |
| F1 makro / tertimbang | 67,69% / 73,68% |
| Pembanding: selalu tim terbanyak | 10,97% ("Technical Layanan SiPecut") |
| Keyakinan ≥ 70% (saran bisa langsung diterima) | akurasi 87,03% · cakupan 51,44% tiket |
| Keyakinan < 70% ("Perlu penilaian manual") | akurasi 61,03% · cakupan 48,56% tiket |
| Galat kalibrasi (ECE) | 7,76% |

## Input & metode

- Input hanya informasi saat tiket dibuat: **judul + deskripsi + jenis (INC/REQ)**, sudah disamarkan.
  Kolom `routing_*`, `reassignment_*`, `team_change_*`, `*sla*`, dan resolusi **tidak dipakai**.
- Target: `assignment_group_name` akhir.
- Fitur: TF-IDF kata (1–2 gram) + karakter (3–5 gram, tahan salah ketik). Model: Logistic Regression,
  probabilitas dikalibrasi (sigmoid, 5-fold) → "keyakinan" = probabilitas tim teratas.
- Split berdasarkan waktu: latih Jan–Jun, uji Jul–Ags (meniru pemakaian nyata: model dilatih dari masa lalu).
- Pemilihan pengaturan tanpa menyentuh data uji: latih Jan–Mei, validasi Juni.

| C | Bobot kelas | Validasi Juni: top-1 | F1 makro |
| --- | --- | --- | --- |
| 3 | tidak | 79,60% | 73,28% |
| 3 | balanced | 79,44% | 76,44% |
| 10 | tidak | 78,82% | 72,91% |
| 10 | balanced | 79,28% | 76,03% |
| 30 | tidak | 78,04% | 72,98% |
| 30 | balanced | 78,50% | 75,64% |

Terpilih: C = 3, bobot kelas = tidak.

## Keyakinan vs akurasi (data uji)

Bila terkalibrasi baik, "rata-rata keyakinan" ≈ "akurasi" di setiap pita.

| Pita keyakinan | Tiket | Rata-rata keyakinan | Akurasi |
| --- | --- | --- | --- |
| 0–30% | 76 | 24,9% | 25,0% |
| 30–50% | 215 | 42,4% | 47,4% |
| 50–70% | 466 | 60,2% | 73,2% |
| 70–90% | 802 | 80,9% | 87,0% |

## Per tim (data uji)

| Tim | Tiket uji | Presisi | Recall | F1 |
| --- | --- | --- | --- | --- |
| Technical Layanan Aplikasi Jaringan - Email | 288 | 82,3% | 83,7% | 83,0% |
| Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | 229 | 77,3% | 78,6% | 77,9% |
| Lainnya | 209 | 58,8% | 33,5% | 42,7% |
| Technical Layanan SiPecut | 171 | 92,3% | 97,7% | 94,9% |
| Technical Layanan Perangkat TI End User | 97 | 89,7% | 99,0% | 94,1% |
| Technical Layanan Presensi | 96 | 85,3% | 90,6% | 87,9% |
| Technical Layanan Back Office Selindo (BOS) | 74 | 80,0% | 64,9% | 71,6% |
| Operator Pusat | 68 | 6,7% | 2,9% | 4,1% |
| Technical Layanan Meeting Online | 56 | 93,2% | 98,2% | 95,7% |
| Technical Layanan Pengelolaan E-Sign | 47 | 95,9% | 100,0% | 97,9% |
| Technical Layanan Perangkat Lunak COTS | 38 | 97,0% | 84,2% | 90,1% |
| Technical Layanan SOBAT | 37 | 69,0% | 78,4% | 73,4% |
| Technical Layanan FASIH Moda CAWI CAPI | 33 | 18,8% | 78,8% | 30,4% |
| Technical Layanan Infrastruktur & Platform Jaringan - Website Hosting | 25 | 71,9% | 92,0% | 80,7% |
| Technical Layanan Koneksi Jaringan -  SSLVPN | 25 | 60,0% | 60,0% | 60,0% |
| Technical Layanan Aplikasi KipApp | 22 | 78,6% | 100,0% | 88,0% |
| Technical Layanan Infrastruktur & Platform Jaringan - Server Hosting | 10 | 50,0% | 30,0% | 37,5% |
| Technical Layanan Pengujian Aplikasi | 10 | 100,0% | 80,0% | 88,9% |
| Technical Layanan Aplikasi Monitoring/Dashboard Sensus/Survei | 10 | 33,3% | 10,0% | 15,4% |
| Technical Layanan Koneksi Jaringan - LAN BPS Pusat | 9 | 87,5% | 77,8% | 82,4% |
| Technical Layanan Aplikasi Jaringan - Community | 5 | 33,3% | 20,0% | 25,0% |

## Tim yang paling sering tertukar (data uji)

| Tim sebenarnya | Disarankan model | Tiket |
| --- | --- | --- |
| Lainnya | Technical Layanan FASIH Moda CAWI CAPI | 101 |
| Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | Technical Layanan Aplikasi Jaringan - Email | 37 |
| Technical Layanan Aplikasi Jaringan - Email | Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | 37 |
| Operator Pusat | Lainnya | 11 |
| Lainnya | Operator Pusat | 11 |
| Operator Pusat | Technical Layanan SiPecut | 11 |
| Technical Layanan Back Office Selindo (BOS) | Technical Layanan SOBAT | 9 |
| Technical Layanan Koneksi Jaringan -  SSLVPN | Lainnya | 8 |
| Operator Pusat | Technical Layanan Perangkat TI End User | 8 |
| Lainnya | Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | 8 |

## Pergeseran data: tim di balik "Lainnya" (data uji)

Tim yang kecil/baru di Jan–Jun tetapi muncul di Jul–Ags tidak bisa dipelajari model; tiketnya jatuh ke "Lainnya"
atau ke tim lama yang mirip. Latih ulang berkala (mis. bulanan) mengatasi ini.

| Tim asli | Tiket latih (Jan–Jun) | Tiket uji (Jul–Ags) |
| --- | --- | --- |
| Technical Layanan Insiden Keamanan Informasi | 16 | 129 |
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
