# Banding ekstraksi solusi untuk indeks pencarian (/chat, /cari, /kandidat)

Tanggal: 31 Oct 2026. `ai/scripts/banding_solusi.py`. Hanya angka; teks tiket tidak ditampilkan.

## Set uji (sama dengan `reports/banding_embedding.md`)

- Korpus: potongan tiket selesai yang dibuka **Jan–Jun 2026**; kueri: teks masalah **1.069** tiket selesai **Jul–Ags 2026** (sama untuk semua varian, tidak bergantung pada ada/tidaknya solusi).
- Relevan = potongan dari tiket yang ditangani **tim yang sama** (potongan dedup: salah satu tiketnya).
- Metrik: Top-1, Top-3, MRR@10, per sumber (potongan lanjutan tiket yang sama tidak dihitung ulang). Model `intfloat/multilingual-e5-base`.

## Hasil

| Varian | Potongan | Tiket terwakili | Kata/potongan | Top-1 | Top-3 | MRR@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| sebelum (aturan lama) | 3.353 | 3.353 | 117 | 73,15% | 89,43% | 0,8163 |
| sesudah (aturan baru) | 3.831 | 3.324 | 106 | 72,50% | 89,06% | 0,8115 |
| sesudah + dedup | 2.138 | 3.324 | 86 | 71,19% | 88,96% | 0,8037 |
| acuan: ekspor lama + aturan lama (906 kueri, set banding_embedding) | 3.332 | 3.332 | 117 | 72,85% | 89,74% | 0,8161 |

## Aturan

- **Sebelum**: pesan substantif terakhir di seluruh percakapan (termasuk sesudah tiket diselesaikan), pesan bercirikan petugas diutamakan; cadangan `resolution` → `close_notes`; satu potongan utuh per tiket.
- **Sesudah**: pesan terakhir yang dikirim ≤ `resolved` + 5 menit, bukan dari pemohon (pesan terakhir dicek dengan `last_conversation_user_id`), lolos `substantive_text`, ≥ 5 kata; cadangan `close_notes` → `resolution` bila bukan template. Toleransi 5 menit (bukan 1): petugas sering menulis solusi 1–3 menit sesudah menekan "selesai" (median 1,6 menit, 91% ≤ 5 menit); dengan 1 menit 209 solusi asli hilang. Solusi > 220 kata dipecah, teks masalah diulang di setiap potongan (varian "potongan lanjutan berawalan judul" saja: Top-3 turun ±1,6 poin pada uji pendahuluan).
- **Dedup**: solusi identik (abaikan huruf besar & tanda baca) → satu potongan, masalah dari tiket terbaru, `jumlah_tiket` & semua nomor tiket disimpan (dipakai `/kandidat`).

## Keputusan

Syarat "tidak lebih buruk" dari *sebelum*: Top-1 & Top-3 turun ≤ 1 poin dan MRR turun ≤ 0,01. Dengan 1.069 kueri, galat baku Top-1 ±1,4 poin, jadi selisih di bawah 1 poin dianggap derau.

- sesudah (aturan baru): **lolos** (Top-1 -0,65 poin, Top-3 -0,37 poin, MRR -0,0048)
- sesudah + dedup: **tidak lolos** (Top-1 -1,96 poin, Top-3 -0,47 poin, MRR -0,0125)

- Indeks memakai **sesudah** (`ai/scripts/build_index.py`, konstanta `DEDUP`).
- Keterbatasan: relevansi berdasarkan kesamaan tim, bukan penilaian manusia atas solusi. Dedup memperkecil korpus sehingga satu potongan mewakili banyak tiket; proksi tim menghukum hal ini (tiga hasil teratas tidak lagi berisi salinan solusi yang sama). Mutu solusi aturan baru dinilai terpisah pada sampel manual.
