# Banding metode deteksi pola: rata-rata kemiripan (bawaan) vs DBSCAN (PoC)

Tanggal: 31 Okt 2026. Hanya angka; teks tiket tidak ditampilkan.

## Data uji

- 666 tiket **Insiden** history Jul–Ags 2026 (`data/processed/tickets_clean.parquet`, teks disamarkan).
- Dipotong per **blok 1 jam** (meniru jendela 60 menit tugas `IncidentPattern`); dipakai 84 blok berisi ≥ 3 insiden
  (319 tiket). Embedding e5-base dipusatkan dengan rata-rata vektor indeks, sama seperti `/pola`.
- Tidak ada label "pola" manual, jadi kualitas didekati dengan **kemurnian tim**: porsi anggota kelompok yang
  ditangani tim yang sama (kelompok yang benar satu masalah biasanya satu tim).

## Hasil (minimal 3 tiket per kelompok)

| Metode | Kelompok | Tiket terkelompok | Kemurnian tim | Waktu (84 blok) |
| --- | ---: | ---: | ---: | ---: |
| Rata-rata kemiripan ≥ 0,50 (bawaan) | 7 | 22 | 0,905 | 11 ms |
| DBSCAN eps 0,50, min_samples 3 | 8 | 25 | 0,917 | 203 ms |
| DBSCAN eps 0,40, min_samples 3 | 3 | 10 | 0,889 | 37 ms |

## Kesimpulan

- Pada data ini DBSCAN eps 0,50 dan metode bawaan memberi hasil **setara** (selisih 1 kelompok, kemurnian ±0,01);
  eps 0,40 terlalu ketat untuk vektor e5 yang dipusatkan. Bawaan tetap rata-rata kemiripan (lebih cepat, tanpa
  parameter tambahan); DBSCAN tersedia di **Pengaturan AI › Metode semantik** untuk mengikuti PoC.
- Uji sintetis `/pola` (3 tiket "lemot/lambat" + 1 "printer tidak bisa mencetak"): metode bawaan memisahkan tiket
  printer (`ai/tests/test_patterns.py`), sedangkan DBSCAN eps 0,50 ikut menariknya ke kelompok yang sama (efek rantai
  DBSCAN pada kelompok kecil). Ini alasan tambahan metode bawaan tidak diganti.
- eps PoC 0,25 berlaku untuk MiniLM tanpa pemusatan; untuk e5 dipusatkan setara ±0,50 (jarak tiket bertopik sama ±0,4).
- min_samples 3 (PoC 5): mengikuti aturan PoC "minimal 3 insiden" dalam jendela 1 jam (hal. 56) dan `pattern_min_tickets`;
  dengan rata-rata 3,8 insiden per blok berisi, min 5 hampir tidak pernah membentuk kelompok di jendela 60 menit.
- Keterbatasan: kemurnian tim adalah proksi, bukan penilaian manusia; data history jarang memiliki lonjakan nyata
  (rata-rata 3,8 insiden per blok berisi), sehingga jumlah kelompok kecil di kedua metode.
