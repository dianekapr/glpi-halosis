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

Catatan: baris *acuan* (72,85%) dan `banding_embedding.md` (72,74%) memakai ekspor, aturan solusi, dan 906 kueri yang sama,
tetapi potongan dibangun oleh dua skrip berbeda. Selisih 0,11 poin = **1 kueri dari 906** (1/906 = 0,11%), jauh di
bawah galat baku (± 1,5 poin); bukan perbedaan model.

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

<!-- sumber-chat:mulai -->
## Dampak pembatasan sumber /chat (A.1)

Tanggal: 06 Nov 2026. `ai/scripts/banding_sumber_chat.py` (jalankan ulang setelah `banding_solusi.py`, yang menulis ulang berkas ini). `/chat` hanya menjawab dari artikel KB terbit + katalog layanan; solusi tiket tetap untuk Cari pengetahuan dan Kandidat Knowledge.

Simulasi keputusan `/chat` pada indeks aktif (9 artikel KB, 17 layanan, 3324 tiket Jan–Jun), ambang 0.83/0.78, 1069 kueri (masalah tiket selesai Jul–Ags 2026). Tiket sejak Juli dibuang dari korpus agar kueri tidak menemukan dirinya sendiri.

| Kebijakan | Dijawab | Pilihan "Maksud Anda" | Tidak ditemukan | Jawaban dari tiket | dari KB | dari layanan | Median skor teratas |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| sebelum (semua sumber) | 99,81% | 0,00% | 0,19% | 99,91% | 0,00% | 0,09% | 0,895 |
| sesudah (KB + layanan) | 60,24% | 38,17% | 1,59% | 0,00% | 73,76% | 26,24% | 0,835 |

### Contoh (pertanyaan rekaan, bukan teks tiket)

| Pertanyaan | Sebelum (mode · sumber · skor) | Sesudah (mode · sumber · skor) |
| --- | --- | --- |
| Lupa kata sandi akun SSO | jawab · KB-15 "Akun SSO terkunci setelah salah kata sandi" · 0,867 | jawab · KB-15 "Akun SSO terkunci setelah salah kata sandi" · 0,867 |
| Printer di ruangan tidak bisa mencetak | jawab · tiket (disembunyikan) · 0,849 | jawab · LAYANAN-C14 "Jaringan & Perangkat > Printer" · 0,845 |
| Bagaimana cara mengajukan akun Zoom | jawab · tiket (disembunyikan) · 0,875 | pilihan · KB-15 "Akun SSO terkunci setelah salah kata sandi" · 0,825 |
| Kuota email saya penuh | jawab · tiket (disembunyikan) · 0,858 | jawab · KB-14 "Kotak masuk email dinas penuh" · 0,848 |
| Aplikasi presensi error saat dibuka | jawab · tiket (disembunyikan) · 0,872 | jawab · LAYANAN-C5 "Aplikasi Statistik" · 0,839 |
| Bagaimana resep nasi goreng | tidak-ditemukan · tiket (disembunyikan) · 0,798 | tidak-ditemukan · LAYANAN-C5 "Aplikasi Statistik" · 0,786 |

Keterbatasan: **"dijawab" bukan berarti benar**, hanya skor teratas ≥ ambang. Korpus sesudah sangat kecil, dan skor e5 teratas tetap tinggi walau topiknya meleset (lihat contoh presensi → layanan umum), jadi tingkat jawab sesudah kemungkinan melebihi jawaban yang benar-benar relevan; ketepatan belum diukur dan ambang belum dikalibrasi ulang untuk korpus ini (bagian C.9). Kueri berupa teks tiket, bukan pertanyaan chat.
<!-- sumber-chat:selesai -->
