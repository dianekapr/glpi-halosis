# Audit tata letak Figma — Prototype HaloSIS

| Kasus | Temuan | Tindakan |
|---|---|---|
| 5 Tabel melebar | Alur Demo 06 & 09 (Container 194/409px), AD-02 (Status 387px), AD-03 (Status:margin 180px) | Kontainer yang sudah selebar konten: clip aktif + overflow HORIZONTAL (4 frame, layer tidak dipindah) |
| 6 Halaman panjang | KM-01, KM-03, MJ-01/02/03, AD-01..07, Alur Demo 06,07,08,09,10,12 | Overflow VERTICAL + clip, Sidebar fixed (numberOfFixedChildren=1) |
| 7 Header menumpuk | Tidak ditemukan (header di dalam auto layout) | — |
| 8 Keluar batas | Hanya kasus 5 | Lihat kasus 5 |
| 9 Sidebar pendek | 17 frame (900 vs 901–3005) | Tinggi sidebar = tinggi frame |
| 10 Elemen tumpuk | Tidak ada tumpukan teknis terdeteksi (struktur auto layout) | — |
| 11 Font | Hanya Inter & Plus Jakarta Sans (tersedia); ikon tabler-icons / Font Awesome 7 Free tidak tersedia | Lihat kasus 15 |
| 12 Lebar | Semua 1440 / 390 | — |
| 13 Modal satu halaman | OP-05, TT-02, Alur Demo 08 (scrim 1440x900) | OP-05 & TT-02 dipotong ke batas modal (520x461 / 520x334), scrim dihapus, navigasi sudah OVERLAY, Batal → close overlay. Alur Demo 08 BUKAN modal (halaman detail tiket mode "Ubah", tanpa scrim) → tidak dipotong |
| 14 Sisa tangkapan | 9 grup/frame kosong di Alur Demo; sisanya dalam instance/spacer auto layout | 9 dihapus (tanpa reaction) |
| 15 Ikon gagal tampil | ±660 glyph font ikon hilang (komponen 34, Alur Demo 309, KM 184, AD 120, MJ 34, Login 12) | Dipulihkan: 659+ "•" diganti ikon SVG (lihat bagian Pemulihan ikon) |
| 16 Grid antar-frame | Sudah rapi (pitch 1540 px, state di baris bawah); LG-00 & PG-S13 ditambahkan | — |

## Pemulihan ikon & logo (langkah 0a-b)
- Sumber: salinan lama (read-only). Glyph tabler-icons (763+) & Font Awesome 7 Free (49) dipetakan lewat CSS @tabler/icons-webfont 3.50 dan @fortawesome/fontawesome-free 7.3.1 (codepoint → nama → SVG), dicocokkan per frame lewat posisi relatif + ukuran font.
- Hasil: 689 "•" → ikon SVG (node `ti/<nama>` / `fa/<nama>`), warna & ukuran = teks asli, posisi sama, reaction induk utuh. Komponen sidebar TT/KM/MJ/AD diperbarui; sidebar Operator (tanpa ikon sebelumnya) diberi 7 ikon menu + "Cari menu" + "Ciutkan menu" menurut label (ikon Siap ditutup = lock-check dari salinan).
- Ikon generik (tidak ada di Tabler 3.50): `box-seam` → folder, `message-circle-2` → bell (3 + 2 titik, dicatat). Teks gabungan ikon+label (Baru, Pertengahan, Sedang proses, Pratinjau dampak perubahan SLA; 8 node) dipulihkan labelnya + ikon.
- 13 "•" sengaja dibiarkan: karakter bullet asli Inter U+2022 di salinan (daftar riwayat/ketentuan, 3 sel judul tabel kecil).
- Logo: persegi putih/gelap di komponen "Sidebar · Operator" & "Navbar · Pegawai" diganti logo asli (light/putih untuk sidebar gelap — dibuat dari berkas logo lewat mask alfa; dark untuk navbar putih). Logo di Login/sidebar lain sudah berupa gambar.
- Atribusi Font Awesome (CC BY 4.0) & Tabler (MIT) di halaman "Indeks".

## Audit kesesuaian konten dengan aplikasi (langkah 0c) — 12 frame SUDAH diganti (lihat "Tindak lanjut" di bawah)
Dibandingkan dengan localhost:8080 (akun budi, rina, andi, lina, sri; teks saja).
| Frame | Isi Figma | Isi aplikasi | Status |
|---|---|---|---|
| OP-01 Dasbor | kartu Tiket baru/Perlu validasi/Mendekati batas SLA + grafik + Antrean prioritas | beranda GLPI: tab Tampilan Pribadi/Grup/Global/Umpan RSS/Semua, Rencana Anda | Tidak sesuai |
| OP-06 Pemantauan SLA | kartu Patuh SLA + tabel Sisa waktu/Status SLA/Grup teknis | daftar tiket GLPI terfilter (kolom standar Tiket) | Tidak sesuai |
| OP-07 Pola insiden | kartu Insiden aktif + "Buat tiket induk" | daftar Masalah GLPI (/front/problem.php) | Tidak sesuai |
| PG-01 Pusat bantuan | kotak cari + chip kategori + akordeon | Tanya Jawab (FAQ) = pohon artikel GLPI (Artikel/Favorites/Home) | Tidak sesuai |
| PG-03 Buat laporan | 6 kartu kategori (Akun, Jaringan, …) | Katalog layanan: 2 kartu (Laporkan Masalah, Ajukan Permintaan) | Tidak sesuai |
| TT-01 Panel hanya-baca | panel Klasifikasi + Kembalikan ke Operator + Tambah solusi | form tiket GLPI bertab (Tiket, Statistik, Persetujuan, …) | Tidak sesuai |
| OP-02 Semua tiket | tabel ringkas 7 kolom | daftar tiket GLPI (banyak kolom, pencarian) | Sebagian |
| OP-09 Siap ditutup | "Tutup 3 tiket terpilih", kolom Dikonfirmasi | "Siap Ditutup": tiket Selesai tanpa respons >48 jam, kolom Terselesaikan/Jam tanpa respons, "Tutup yang dipilih" | Sebagian |
| OP-08 Cari pengetahuan | kotak cari + hasil + pratinjau artikel | kotak "Cari pengetahuan" + Cari (hasil dinamis) | Sebagian |
| PG-02 Riwayat percakapan | daftar + detail percakapan | daftar percakapan saja (judul, tanggal, status) | Sebagian |
| PG-04 Form Laporkan masalah | form + panel Saran solusi cepat, Unit kerja, Dampak | form: Urgensi, Kategori, Perangkat, Pengamat, Lokasi, Judul, Deskripsi, Lampiran | Sebagian |
| KM-03 Daftar artikel | daftar tabel | /front/knowbaseitem.php?list=1 (formulir pencarian) | Sebagian |
Jumlah: 12 frame (6 tidak sesuai, 6 sebagian). Frame hasil tangkapan GLPI (Alur Demo 06–12, KM-01/02/04, MJ, AD, Login) sesuai. OP-03/OP-04 (panel Saran AI) tidak punya halaman sendiri di aplikasi (panel dalam detail tiket).

## Cek visual tahap 2
Dicek (29): PG-01..04, OP-01..04, OP-05, OP-06..09, TT-01, TT-02, KM-02..04, MJ-01..03, AD-01..07, LG-00.
- Diperbaiki: 14 frame (PG-01..04, OP-01..04, OP-06..09, OP-S19, TT-01) — instance sidebar/navbar absolut menutupi konten (judul & kartu bertumpuk di sidebar/navbar). Padding kiri 240 / atas 56 pada frame induk, Main/Body diubah Fill; reaction tidak berubah.
- Logo komponen Operator tidak tampil (putih di latar gelap) → diperbaiki dengan mask.
- Dibiarkan (hasil tangkapan GLPI): header KM/AD-04 breadcrumb & tombol bertumpuk dua baris, judul kartu terpotong di MJ-01 (Sumber permintaan), tombol abu tanpa label di MJ-03.
- Belum dicek: KM-01, PG-05, LG-01/02, Alur Demo 02–05/07/09–12, DM-S00 dan semua frame state (±100).

## Tindak lanjut audit kesesuaian: 12 frame ditangkap ulang dari aplikasi asli (7 Nov 2026)
- Diganti: OP-01, OP-06, OP-07, PG-01, PG-03, TT-01, OP-02, OP-09, OP-08, PG-02, PG-04, KM-03 — ditangkap dari localhost:8080 dengan akun peran masing-masing (rina/budi/andi/lina), viewport 1440x900; nama & posisi sama dengan frame lama, tinggi dipotong 900 (PG-02 & PG-04 aslinya lebih panjang). TT-01 = tiket #42. Teks "Tiket serupa …" tidak muncul (0 simpul ditemukan).
- Frame lama TIDAK dihapus: dipindah ke Section "Usulan desain (bukan aplikasi)" (di bawah Section 06, di luar alur), nama berakhiran "(Usulan)", tanpa reaction masuk/keluar.
- Sidebar/navbar hasil tangkapan diganti instance komponen peran (Sidebar · Operator/Tim Teknis/Knowledge Manager, Navbar · Pegawai): ikon & logo tampil.
- Cek visual 12/12 frame baru: tidak ada konten tertimpa sidebar/navbar. Catatan: item aktif sidebar Operator selalu "Dasbor" (komponen tunggal).

