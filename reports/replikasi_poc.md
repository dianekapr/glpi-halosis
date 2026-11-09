# Replikasi PoC (C.7)

Dihasilkan `ai/scripts/replikasi_poc.py`. Model & indeks aktif tidak berubah; laporan hanya berisi angka, nama grup, dan pertanyaan rekaan.

<!-- pola:mulai -->
## Pola insiden (BR-07)

2.777 INC, MiniLM tanpa pemusatan, teks judul + deskripsi tersamar. DBSCAN eps 0,25, min_samples 5, jarak kosinus (metrik dan teks masukan tidak tertulis di dokumen).

| DBSCAN | PoC | Replikasi |
| --- | --- | --- |
| Klaster | 14 | 8 |
| Noise | 1.073 | 1.011 |
| Tiket terkluster | 1.704 | 1.766 |
| 5 klaster terbesar | 851 / 390 / 289 / 88 / 30 | 1.330 / 295 / 88 / 29 / 7 |

Sliding window: 1 jam, kemiripan 0,70, minimal 3 insiden, tanpa union-find, himpunan tiket ganda dibuang.

| Tafsiran "strict" | PoC kandidat → episode | Replikasi kandidat → unik | Tanpa himpunan bagian |
| --- | --- | --- | --- |
| Mirip ke jangkar | 23 → 17 | 19 → 19 | 18 |
| Saling mirip semua anggota | 23 → 17 | 15 → 15 | 14 |

Definisi jangkar jendela tidak tertulis di dokumen, jadi dua tafsiran dilaporkan. 0 INC tanpa tanggal dibuka dilewati pada sliding window. Ini metode PoC, bukan metode `/pola` produksi (`reports/banding_pola.md`).

Dibuat 07-11-2026.
<!-- pola:selesai -->

<!-- triase:mulai -->
## Triase (BR-05)

Data: `tickets_clean.parquet`, 6.668 tiket bergrup, 56 grup. Split acak `random_state=42`, 20% uji, tanpa stratifikasi: referensi 5.334, uji 1.334.

| Acuan dokumen | Top-1 | Top-3 | MRR |
| --- | --- | --- | --- |
| TF-IDF | 68,33% | 90,89% | 0,7989 |
| Embedding | 70,43% | 90,29% | 0,8092 |

| Cakupan | Metode | Tiket uji | Top-1 | Top-3 | MRR | F1 makro | Presisi makro | Recall makro |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 56 grup | TF-IDF k-NN | 1.334 | 67,09% | 90,78% | 0,7925 | 37,77% | 38,60% | 38,29% |
| 56 grup | TF-IDF LR | 1.334 | 75,41% | 89,36% | 0,8297 | 30,56% | 35,18% | 30,14% |
| 56 grup | MiniLM k-NN | 1.334 | 68,37% | 89,28% | 0,7954 | 39,91% | 43,12% | 39,40% |
| 56 grup | MiniLM LR | 1.334 | 72,26% | 89,06% | 0,8126 | 31,45% | 34,00% | 31,28% |
| 56 grup | e5 k-NN | 1.334 | 68,52% | 90,85% | 0,8011 | 40,53% | 45,09% | 39,39% |
| 56 grup | e5 LR | 1.334 | 70,91% | 86,51% | 0,7948 | 23,88% | 25,39% | 24,53% |
| 39 grup terbesar | TF-IDF k-NN | 1.324 | 67,67% | 91,77% | 0,7991 | 45,45% | 47,18% | 44,95% |
| 39 grup terbesar | TF-IDF LR | 1.324 | 75,98% | 90,03% | 0,8359 | 38,09% | 43,91% | 37,47% |
| 39 grup terbesar | MiniLM k-NN | 1.324 | 68,88% | 90,03% | 0,8011 | 50,16% | 54,79% | 48,55% |
| 39 grup terbesar | MiniLM LR | 1.324 | 72,81% | 89,73% | 0,8187 | 39,29% | 42,80% | 38,89% |
| 39 grup terbesar | e5 k-NN | 1.324 | 68,96% | 91,47% | 0,8066 | 48,54% | 54,83% | 46,09% |
| 39 grup terbesar | e5 LR | 1.324 | 71,45% | 87,16% | 0,8005 | 29,76% | 31,73% | 30,50% |
| 56 grup | HaloSIS (label gabungan) | 1.334 | 82,31% | 96,10% | 0,8933 | 72,83% | 73,74% | 74,49% |
| 56 grup | HaloSIS (label asli) | 1.334 | 77,89% | 90,63% | 0,8441 | 32,71% | 33,34% | 33,19% |
| 39 grup terbesar | HaloSIS (label gabungan) | 1.324 | 82,55% | 96,22% | 0,8950 | 73,09% | 74,28% | 74,69% |
| 39 grup terbesar | HaloSIS (label asli) | 1.324 | 78,47% | 91,31% | 0,8505 | 40,62% | 41,61% | 41,06% |

**Selisih dari PoC yang tidak bisa dihilangkan.** Dokumen menulis 6.659 tiket, 39 grup, referensi 5.319, uji 1.339; jumlah itu tidak saling cocok, dan data ini punya 56 grup. Tidak ada ambang jumlah tiket minimum yang menghasilkan tepat 39 grup, jadi cakupan 39 grup diambil dari grup terbanyak tiketnya, dengan tiket split yang sama. Hasil ini pembanding, bukan replikasi identik.

**Tafsiran (tidak tertulis di dokumen).** Teks masukan = judul + deskripsi tersamar. k-NN: grup diurutkan menurut tiket referensi termirip (kosinus). LR: `LogisticRegression` bawaan sklearn. TF-IDF: unigram + bigram, `min_df=2`, `sublinear_tf`. e5 memakai awalan `query:` untuk kueri k-NN dan `passage:` selain itu.

**Model HaloSIS.** Pipeline `build_pipeline` (C = 3, bobot kelas = tidak, terkalibrasi) dilatih ulang di memori pada referensi split ini; artefak aktif tidak dipakai karena tiket uji acak bisa ada di data latihnya, dan tidak ditulis ulang. Tim < 30 tiket digabung "Lainnya". *Label gabungan* = cara produksi menilai; *label asli* = tiket tim kecil otomatis salah, sehingga sebanding dengan baris lain.

Waktu proses: embedding MiniLM 15,8 dtk, e5 65,8 dtk, latih HaloSIS 25,6 dtk.

Pasangan grup paling sering tertukar pada TF-IDF LR, 39 grup terbesar (aktual → prediksi):

| Aktual | Prediksi | Tiket |
| --- | --- | --- |
| Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | Technical Layanan Aplikasi Jaringan - Email | 30 |
| Technical Layanan Aplikasi Jaringan - Email | Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | 24 |
| Operator Pusat | Technical Layanan SiPecut | 21 |
| Operator Pusat | Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | 19 |
| Operator Pusat | Technical Layanan Aplikasi Jaringan - Email | 14 |
| Technical Layanan Back Office Selindo (BOS) | Technical Layanan Presensi | 8 |
| Technical Layanan Perangkat Lunak COTS | Technical Layanan Aplikasi Jaringan - Email | 7 |
| Technical Layanan Back Office Selindo (BOS) | Technical Layanan SiPecut | 6 |
| Technical Layanan Aplikasi Monitoring/Dashboard Sensus/Survei | Technical Layanan FASIH Moda CAWI CAPI | 6 |
| Technical Layanan Koneksi Jaringan -  SSLVPN | Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | 5 |

Matriks kebingungan lengkap: `reports/replikasi_poc_confusion.csv`. Presisi/recall per grup: `reports/replikasi_poc_per_grup.csv`.

Dibuat 07-11-2026.
<!-- triase:selesai -->

<!-- chat:mulai -->
## Ekstraktif vs Qwen grounded (BR-06)

Lewat `/chat` nyata, sumber hanya KB terbit + katalog layanan. Pertanyaan rekaan; P1 dari dokumen hal. 55.

- P1: Saya lupa password akun BPS, bagaimana cara mengatasinya?
- P2: Bagaimana cara mengajukan permintaan VPN?
- P3: Bagaimana cara memasang printer jaringan Epson L9999?
- P4: Apa resep nasi goreng yang enak?
- P5: Berapa harga tiket pesawat Jakarta ke Medan besok?

| Mode uji | No | Harapan | Mode /chat | Sesuai | Skor | Ada sumber | Kata dari sumber | Detik |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Ekstraktif | P1 | jawab | ekstraktif | ya | 0,8963 | ya | 90% | 0,1 |
| Ekstraktif | P2 | jawab | ekstraktif | ya | 0,8500 | ya | 67% | 0,0 |
| Ekstraktif | P3 | tolak | pilihan | ya | – | – | – | 0,0 |
| Ekstraktif | P4 | tolak | tidak-ditemukan | ya | – | – | – | 0,0 |
| Ekstraktif | P5 | tolak | tidak-ditemukan | ya | – | – | – | 0,0 |
| Qwen grounded (qwen2.5:3b) | P1 | jawab | openai | ya | 0,8963 | ya | 76% | 4,3 |
| Qwen grounded (qwen2.5:3b) | P2 | jawab | tidak-ditemukan | **tidak** | – | – | – | 0,6 |
| Qwen grounded (qwen2.5:3b) | P3 | tolak | pilihan | ya | – | – | – | 0,0 |
| Qwen grounded (qwen2.5:3b) | P4 | tolak | tidak-ditemukan | ya | – | – | – | 0,0 |
| Qwen grounded (qwen2.5:3b) | P5 | tolak | tidak-ditemukan | ya | – | – | – | 0,0 |

Tidak sesuai harapan: 1 dari 10. Kolom *Kata dari sumber* indikator kasar; menilai halusinasi tetap perlu pembacaan manusia atas cuplikan berikut. Similarity PoC 0,8592 (MiniLM) tidak sebanding dengan skor e5.

Cuplikan jawaban (dari sumber tersetujui, tersamar, maks. 200 karakter):

- Ekstraktif, P1: Berdasarkan artikel "Mengatur ulang kata sandi SSO BPS": Mengatur ulang kata sandi SSO BPS. Buka portal akun BPS, pilih Lupa password , masukkan NIP, lalu ikuti tautan yang dikirim ke email dinas.
- Ekstraktif, P2: Permintaan ini bisa diajukan lewat layanan "Ajukan Permintaan" di katalog layanan. Layanan Ajukan Permintaan. Minta tim layanan TI menyediakan layanan yang Anda perlukan.
- Qwen grounded (qwen2.5:3b), P1: Jika Anda lupa password akun BPS, Anda bisa menggunakan fitur Lupa password di portal akun BPS. Masukkan NIP Anda, lalu ikuti tautan yang dikirim ke email dinas Anda.

Dibuat 07-11-2026.
<!-- chat:selesai -->

<!-- retrieval:mulai -->
## Retrieval terkendali (BR-04)

8 kasus real dari KB HaloSIS existing, pertanyaan disusun tim (bukan kasus PoC asli), dari `ai/scripts/kasus_retrieval_poc.json`. Korpus: 34 sumber (artikel KB yang terlihat pegawai: FAQ + bertarget) + katalog layanan pada indeks aktif, bukan korpus Zammad PoC. Acuan dokumen: Top-1 100%, Top-3 100%, MRR 1,0000, dan dokumen menegaskan angka itu hanya berlaku pada PoC terkendali.

| Model | Top-1 | Top-3 | MRR |
| --- | --- | --- | --- |
| MiniLM | 75,00% | 87,50% | 0,8208 |
| e5 | 62,50% | 87,50% | 0,7614 |
| e5 + urutan /chat | 75,00% | 87,50% | 0,8239 |

`e5 + urutan /chat`: peringkat e5 setelah aturan /chat (artikel KB yang lolos ambang 0,83 di depan katalog layanan, `search.utamakan_kb`).

Peringkat sumber benar per kasus:

| Model | K1 | K2 | K3 | K4 | K5 | K6 | K7 | K8 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MiniLM | 1 | 1 | 1 | 1 | 1 | 1 | 2 | 15 |
| e5 | 1 | 1 | 2 | 1 | 1 | 2 | 1 | 11 |
| e5 + urutan /chat | 1 | 1 | 2 | 1 | 1 | 1 | 1 | 11 |

Dibuat 09-11-2026.
<!-- retrieval:selesai -->
