# Banding model embedding: MiniLM-L12-v2 (PoC) vs multilingual-e5-base (implementasi)

Tanggal: 31 Okt 2026. Hanya angka; teks tiket tidak ditampilkan. Indeks dibuat sementara di luar `ai/index/` dan
dihapus setelah uji.

## Set uji (sama untuk kedua model)

- Sumber: `data/processed/qa_pairs.parquet` (tiket selesai dengan solusi, teks disamarkan `prepare_data.py`).
- **Korpus** (yang dicari): 3.332 pasangan *Masalah + Solusi* dengan tanggal dibuka **Jan–Jun 2026**.
- **Kueri**: teks masalah 906 tiket **Jul–Ags 2026** (pembagian waktu sama dengan `reports/triase.md`).
- **Relevan** = tiket korpus yang ditangani **tim yang sama** dengan tiket kueri (44 tim). Proksi ini dipakai karena
  tidak ada label relevansi manual; solusi dari tim yang sama paling mungkin berguna bagi petugas.
- Metrik: Top-1 & Top-3 (ada tiket relevan di 1 / 3 hasil teratas), MRR (1 / peringkat hasil relevan pertama,
  10 teratas; tidak ada → 0). Kosinus pada vektor ternormalisasi; e5 memakai awalan `query:` / `passage:`.

## Hasil

| Model | Dimensi | Top-1 | Top-3 | MRR | Waktu indeks (3.332 potongan, CPU) | Waktu per kueri |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `paraphrase-multilingual-MiniLM-L12-v2` (PoC) | 384 | 67,99% | 83,55% | 0,7650 | 9,9 dtk | 2,0 ms |
| `intfloat/multilingual-e5-base` (implementasi) | 768 | **72,74%** | **89,62%** | **0,8144** | 60,9 dtk | 8,0 ms |

Lingkungan: MacBook (Apple Silicon, CPU), sentence-transformers 6.2.0, torch 2.14.1.

**Catatan data (1 Nov 2026):** banding ini memakai **ekspor lama** (korpus 3.332, 906 kueri). Indeks aktif dibangun
dari ekspor versi baru dengan aturan solusi baru dan diuji di [`banding_solusi.md`](banding_solusi.md) pada 1.069
kueri: Top-1 72,50% / Top-3 89,06% / MRR 0,8115 (aturan lama pada ekspor baru 73,15%). Korpus & kueri berbeda, jadi
72,74% vs 73,15% bukan selisih model; keputusan e5 vs MiniLM tetap dari tabel di atas (set uji yang sama).

## Kesimpulan

- e5-base lebih baik di ketiga metrik (+4,8 poin Top-1, +6,1 poin Top-3, +0,049 MRR) pada set uji yang sama, jadi
  pilihan implementasi dipertahankan.
- Biayanya: vektor 2× lebih besar dan pengodean ±4–6× lebih lambat; masih jauh di bawah target latensi (8 ms per
  kueri untuk embedding; indeks penuh dibangun ulang sekitar 1 menit).
- Skala kosinus e5 lebih tinggi (tiket tak terkait pun ±0,8), sehingga ambang chat (0,83) dan pola (0,50 setelah
  vektor dipusatkan) dikalibrasi khusus e5 dan tidak bisa dipakai langsung untuk MiniLM.
- Keterbatasan: relevansi berdasarkan kesamaan tim, bukan penilaian manusia atas solusi; angka ini membandingkan
  model secara relatif, bukan mengukur kualitas jawaban chatbot.
