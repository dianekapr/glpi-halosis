# Kalibrasi ambang (C.9)

Dihasilkan `ai/scripts/kalibrasi_ambang.py`, 07-11-2026. Tidak mengubah ambang aktif; pemilik ambang: `reports/tata_kelola_ai.md` §1.

## Chat: 0,78 / 0,83

`/chat` menjawab bila skor ≥ 0,83, menawarkan artikel KB bila skor KB ≥ 0,78, selain itu menolak. Skor e5 atas 26 sumber KB terbit + katalog layanan pada indeks aktif.

| Set proksi | Kueri | Dijawab | Pilihan | Ditolak | Median skor |
| --- | --- | --- | --- | --- | --- |
| Judul sumber (harus terjawab) | 26 | 100,00% | 0,00% | 0,00% | 0,9144 |
| Rekaan tak terjawab (harus ditolak) | 24 | 0,00% | 33,33% | 66,67% | 0,7744 |
| Masalah tiket Jul–Ags (sebaran nyata) | 905 | 60,22% | 39,34% | 0,44% | 0,8353 |

Porsi kueri yang dijawab bila ambang atas diubah:

| Ambang atas | Judul sumber (harus terjawab) | Rekaan tak terjawab (harus ditolak) | Masalah tiket Jul–Ags (sebaran nyata) |
| --- | --- | --- | --- |
| 0,74 | 100,00% | 87,50% | 100,00% |
| 0,76 | 100,00% | 66,67% | 100,00% |
| 0,78 | 100,00% | 45,83% | 100,00% |
| 0,80 | 100,00% | 20,83% | 97,79% |
| 0,82 | 100,00% | 8,33% | 77,24% |
| 0,83 | 100,00% | 0,00% | 60,22% |
| 0,84 | 100,00% | 0,00% | 39,45% |
| 0,86 | 88,46% | 0,00% | 10,61% |
| 0,88 | 73,08% | 0,00% | 0,77% |

Pada 0,83: 0,00% kueri rekaan tak terjawab lolos ke jawaban, dan 0,00% judul sumber gagal terjawab.

Keterbatasan: judul sumber memihak skor tinggi karena teksnya ada di sumber; set rekaan ditulis tangan dan kecil; set tiket tidak punya label relevansi. Ambang belum boleh dinyatakan terkalibrasi sebelum penilaian tim (`reports/penilaian_relevansi.xlsx`) tersedia dan hasil UAT menentukan biaya salah jawab.

## Triase: 40 / 70

Model aktif `triase-tfidf-lr-20261031`, 1.559 tiket uji Jul–Ags 2026 (`kurva_ambang`). Status memakai gerbang `quality.triage_point` (akurasi ≥ 85%, cakupan ≥ 10%, ≥ 100 tiket).

| Ambang | Akurasi di atas ambang | Cakupan | Tiket | Gerbang |
| --- | --- | --- | --- | --- |
| 30% | 77,95% | 95,13% | 1.483 | tidak lolos |
| 40% | 78,67% | 91,40% | 1.425 | tidak lolos |
| 50% | 82,92% | 80,76% | 1.259 | tidak lolos |
| 60% | 86,14% | 66,20% | 1.032 | lolos |
| 70% | 88,35% | 50,67% | 790 | lolos |
| 80% | 92,90% | 28,93% | 451 | lolos |
| 90% | – | 0,00% | 0 | data tidak cukup |

Per pita keyakinan aktif:

| Pita | Tiket | Porsi | Akurasi |
| --- | --- | --- | --- |
| ≥ 70% | 790 | 50,67% | 88,35% |
| 40% sampai < 70% | 635 | 40,73% | 66,63% |
| < 40% | 134 | 8,60% | – |

Akurasi pita tengah diturunkan dari kurva yang dibulatkan 4 digit. Akurasi pita < 40% tidak tersedia karena kurva hanya memuat tiket di atas ambang. Dokumen hal. 100 meminta ambang ditentukan dari validation dataset, cost of error, dan hasil UAT; laporan ini baru mencakup yang pertama. Kurva berasal dari split waktu, jadi tidak boleh dicampur dengan split acak `replikasi_poc.md`.
