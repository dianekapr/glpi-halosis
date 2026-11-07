# Peta wiring prototype Figma HaloSIS

File: HaloSIS – UI/UX (`VKBzfkB7mwadHYHz7qIwOU`), halaman **Prototype HaloSIS**. Sambungan dibuat lewat Plugin API. Kecuali 12 frame yang ditangkap ulang dari aplikasi asli (lihat Pembaruan tahap 3), layar adalah hasil tangkapan awal.

## Komponen bersama (Section "Komponen bersama")
Sidebar/navbar tiap peran dijadikan komponen; menu hanya disambung sekali di komponen utamanya.

| Komponen | Instance | Frame yang memakai |
| --- | --- | --- |
| Navbar · Pegawai | 4 | PG-01..PG-04 |
| Sidebar · Operator | 11 | OP-01..OP-04, OP-06..OP-09, Alur Demo 06/07/08 |
| Sidebar · Tim Teknis | 3 | TT-01, Alur Demo 09/10 |
| Sidebar · Knowledge Manager | 4 | KM-01..KM-04 |
| Sidebar · Manajemen | 4 | MJ-01..MJ-03, Alur Demo 12 |
| Sidebar · Administrator | 7 | AD-01..AD-07 |

Header (breadcrumb, pencarian, chip peran, avatar) tetap per frame karena isinya berbeda; elemen kliknya disambung per frame.

## Jumlah sambungan (reaksi) per Section
Total ± 1.750 (termasuk sambungan di dalam komponen).

| Section | Sambungan | State baru |
| --- | ---: | ---: |
| 00 Login | 10 | 1 |
| Alur Demo | ± 530 | 16 |
| 01 Pegawai | 95 | 12 |
| 02 Operator | 207 | 24 |
| 03 Tim Teknis | 31 | 7 |
| 04 Knowledge Manager | ± 268 | 15 |
| 05 Manajemen | 94 | 11 |
| 06 Administrator | ± 447 | 12 |
| Komponen bersama | 73 | 0 |

Angka besar di Alur Demo, KM dan Administrator karena setiap sel baris tabel disambung ke detail atau notifikasi.

## State yang dibuat (98, semuanya diberi akhiran "(state)")
- **LG-S01** Pilih akun demo: budi, rina, andi, lina, sri, dimas menuju beranda masing-masing; tautan "contoh login gagal" menuju LG-02.
- **Menu profil** per peran (Pegawai, Operator, Tim Teknis, KM, Manajemen, Administrator): "Keluar" menuju LG-00 Login; "Ganti peran / akun" tidak punya sambungan (reaction dihapus, lintas peran).
- **Notifikasi** (hilang otomatis 2,5 dtk): saran AI diterima, penilaian disimpan, saran ditolak, tiket induk dibuat, laporan terkirim, tiket dikembalikan, artikel disimpan sebagai draf, pengaturan AI disimpan, filter diterapkan, urutan kolom diubah, dan sejenisnya.
- **Daftar pilihan** (dropdown): status, urutan, kategori, tim, subkategori, satuan waktu, tanggal.
- **Kolom terisi**: pencarian FAQ, pencarian pengetahuan, kolom chat HP, judul dan isi artikel, pencarian umum.
- **Frame "sesudah"**: OP "Siap ditutup sesudah (3 tiket berstatus Ditutup)".
- Aksi "Tambah solusi" (36) dan "Setujui" (38) sudah punya sambungan sebelumnya, jadi tidak dibuat frame "sesudah".

## Alur utama
- Flow starting point: **Demo lengkap** (01 Login) dan satu per peran (Pegawai 24, Operator OP-01, Tim Teknis 35, KM-01, MJ-01, AD-01).
- 01 Login → "Masuk" → overlay pilih akun (DM-S00 di Alur Demo; LG-S01 untuk 00 Login) → beranda peran. LG-02 dicapai dari tautan kecil di overlay LG-S01; "Masuk lagi" kembali ke 01 Login.
- Alur Demo ↔ layar peran: sidebar Operator/Tim Teknis/Manajemen di Alur Demo kini instance komponen yang menuju layar peran. Arah Alur Demo → layar peran saja; Section peran tidak mengarah ke Alur Demo (lihat Pembaruan tahap 4): Antrean validasi (OP) → OP-03; Navbar Pegawai: Tanya HaloSIS → PG-01, Laporan saya → PG-02; Sidebar Tim Teknis → TT-01. Instance di Alur Demo 06/07/08/10 tetap menuju Alur Demo (override).

## Elemen yang belum tersambung
| Elemen | Alasan |
| --- | --- |
| Item menu/tab yang menuju frame sendiri (Beranda di 35, 50, 55, 58; Menunggu (40) di KM-01; Perlu ditinjau (0) di KM-02; Tanya HaloSIS di 24; Laporan saya di 30) | Figma menolak NAVIGATE ke frame yang sama; sudah di layar tujuan |
| Ikon tanpa label teks (bintang rating, panah kembali, ikon aksi) | Tidak ada teks layer untuk dicocokkan; hasil tangkapan tidak menamai ikon, jadi tidak bisa dipetakan otomatis |
| Menu "Dasbor" KM/Tim Teknis | Tidak ada frame dasbor khusus; diarahkan ke beranda peran |
| Menu Administrator tanpa layar (Kategori layanan, Tim teknis, Alur kerja & aturan, Notifikasi), breadcrumb dan tombol Tambah | Diarahkan ke notifikasi generik "di luar cakupan prototype" (± 60 sambungan generik) |
| Judul kolom AD-02/AD-03 (Disarankan, Ambang saat ini, Target baru, dll.), label sumbu grafik MJ-02/12, gelembung chat, teks "Berulang di N tiket" (KM-01) | Bukan elemen yang bisa diklik di aplikasi |
| Kolom isian di 01 Login (Nama Pengguna, Kata Sandi) | Isian tidak ditangkap sebagai layer terpisah |

## Catatan teknis
- Properti overlay (posisi, latar redup, tutup saat klik di luar) hanya-baca di Plugin API, jadi overlay memakai bawaan Figma (posisi tengah, tanpa latar); notifikasi hilang lewat timer, modal lewat tombol Batal.
- Sambungan lama dipertahankan: elemen yang sudah punya reaksi tidak ditimpa, kecuali sambungan "Masuk" di 01 Login yang sengaja diganti ke overlay pilih akun.
- Sidebar TT-01 yang sebelumnya hanya 2 item kini memakai sidebar 5 item dari Alur Demo 09.

## Pembaruan tahap 2
- Frame baru: DM-S00 (Alur Demo, pilih akun demo, lintas peran sesuai urutan demo), TT-S08 (Tim Teknis, notifikasi solusi ditambahkan).
- Alur demo 01→12 utuh; ikon aksi tanpa label kini bersambung ke notifikasi "di luar cakupan" per Section; sidebar Operator kini berikon dan berlogo asli.
- Elemen yang belum tersambung: tinggal tabel/sel/link bawaan GLPI, ikon dekoratif, dan tab GLPI (tidak diklik di aplikasi prototype).

## Pembaruan tahap 3 (12 frame ditangkap ulang)
- Frame baru memakai id: OP-01 128:2, OP-06 130:2, OP-07 131:2, OP-02 135:2, OP-09 136:2, OP-08 137:2, TT-01 134:2, KM-03 140:2, PG-01 132:2, PG-03 133:2, PG-02 138:2, PG-04 139:2. Frame lama ("(Usulan)") ada di Section "Usulan desain (bukan aplikasi)", tanpa sambungan.
- Menu sidebar/navbar: mengikuti komponen (sudah diarahkan ke frame baru); menu ke frame sendiri dilepas.
- Tombol/tautan frame baru: Cari/Urutkan/Disaring/Tutup/Kirim/Tambah/Home dan profil → state di Section yang sama (mis. OP-S07/S14/S17/S19, PG-S07, TT-S08, KM-S03/S04/S10); tombol & tautan sisa → notifikasi "di luar cakupan" Section itu (OP-S06, TT-S01, KM-S03, PG-S13). PG-03 "Laporkan Masalah" → PG-04; "Tanya asisten" → PG-01 (diubah di tahap 4; sebelumnya ke Alur Demo).
- Alur Demo 01→12 tidak diubah (29/29 frame terjangkau dari 01 Login); isolasi peran terjaga (tidak ada sambungan dari/ke Section Usulan).


## Pembaruan tahap 4
- Baris tabel OP-02/06/07 (sel ID dan Judul): status "Baru" → OP-03, lainnya → OP-04; OP-09 → OP-04; KM-03 → KM-S12 (state "Membuka artikel di editor"); PG-02 baris percakapan & "Tanya asisten" → PG-01. TT-01 dilewati.
- PG-02 (2136 px) dan PG-04 (1385 px): frame diperpanjang (konten penuh sudah ada, hanya terpotong), overflow VERTICAL, navbar + tombol "Tanya asisten" fixed.
- Komponen "Sidebar · Operator" kini component set dengan 7 varian "Aktif=…"; tiap frame OP/Alur Demo 06-08 memakai varian sesuai menu.
- Tujuan komponen diubah ke Section sendiri; lihat audit_wiring_figma.md.


## Pembaruan tahap 5
- Frame baru: TT-03 147:3157, TT-04 147:3988, TT-05 147:4372 (Section 03); MJ-04 147:4586, MJ-05 147:5425 (Section 05). Sidebar memakai instance komponen peran masing-masing.
- Sidebar · Tim Teknis: Pemantauan SLA → TT-03, Pola insiden → TT-04, Cari pengetahuan → TT-05. Sidebar · Manajemen: Pemantauan SLA → MJ-04, Pola insiden → MJ-05.
- Dalam frame duplikat: avatar → menu profil peran (TT-S02/MJ-S04); sambungan lain ke Operator → TT-S01 / MJ-S02 (notifikasi di luar cakupan).
- Reaction per Section lintas peran: 0 (kecuali Keluar → 00 Login). Total 2012, menggantung 0.

## Pembaruan tahap 6 (layar chatbot Pegawai)
- Penyebab: Section 01 tidak punya layar chatbot, sehingga Navbar "Tanya HaloSIS" → PG-01 (FAQ) dan "Laporan saya" → PG-02 (riwayat percakapan) salah. PG-05 ("Chat di HP", 390 px) hanyalah mockup lama versi HP tanpa sambungan; bukan layar desktop, jadi tidak dipakai.
- Frame baru (ditangkap dari localhost:8080, akun budi, 1440 px, tanpa "Tiket serupa"; navbar hasil tangkapan diganti instance "Navbar · Pegawai"): PG-00 Tanya HaloSIS kosong 153:3533, PG-S20 jawaban ditemukan 154:3533, PG-S21 mode pilihan 155:3533, PG-S22 tidak ditemukan + tawaran laporan 156:3533, PG-S23 rating bintang 157:3533, PG-S24 form laporan dari chat 158:3533, PG-06 Laporan saya 159:3533 (sisi kanan Section 01, Section diperlebar).
- Navbar · Pegawai: Tanya HaloSIS → PG-00, Buat laporan → PG-03, Laporan saya → PG-06, Tanya Jawab (FAQ) → PG-01, Riwayat percakapan → PG-02. Item menu ke frame sendiri dikosongkan (override per instance). Garis bawah menu aktif diatur per instance di frame baru.
- Chat: chip/Kirim di PG-00 → PG-S20; Masalah terselesaikan → S23; Belum terselesaikan → S22; Ya, buat laporan (S21/S22) → S24; Kirim laporan → PG-S07; Batal → S22; Tidak, terima kasih → PG-00; bintang → PG-S04; tautan sumber → PG-S03; Kirim di S20..S24 → PG-S10 (kecuali Kirim di S22 → S21, jalur masuk S21 sebagai "kata lain"); Percakapan baru → PG-00; kartu Ajukan permintaan → PG-03, Laporkan masalah → PG-04.
- PG-06: baris tiket (ID dan judul) dan kontrol tabel → PG-S13 (tidak ada layar detail tiket di Section 01); Tanya asisten → PG-00.
- Dialihkan ke PG-00: "Tanya asisten" PG-01/03/04 (sebelumnya PG-01) dan 24 baris percakapan/tautan PG-02 (lanjutkan percakapan). LG-S01 akun budi → PG-00. Titik awal alur "Pegawai" dipindah dari 24:2 ke PG-00.
- Label jawaban: "Dari Pusat Bantuan" (bukan "Dijawab oleh AI") adalah perilaku normal mode ekstraktif/LLM none, bukan hasil jalur 4a: /health halosis-ai `ok` (generasi `ekstraktif`, model_llm null) dan /chat "lupa password SSO" → mode ekstraktif, sumber KB-15. Kode: label dipilih `chat.js:109` dari `ai` yang dihitung `Chatbot.php:201` lewat `isAiModel()` (`Chatbot.php:212-214`: false bila model = `demo-extractive-v1` atau berakhiran `-ekstraktif`, set di `Chatbot.php:264`/`:370`); teks label di `chat_conversation.html.twig:61-62`. Jadi PG-S20 tidak ditangkap ulang; T4 UC-01 langkah 5 perlu menyebut "Dijawab oleh AI" hanya bila LLM aktif.
- Ikon (tahap 2 diulang): ±330 glyph tabler-icons/FA kosong di 7 frame baru + 12 frame tangkapan ulang tahap 3 + duplikat tahap 5 (TT-03..05, MJ-04/05; 88 glyph) → ikon SVG `ti/<nama>` (Tabler 3.50, FA 7.3.1 untuk `info`), ukuran/warna = teks asli, reaction ikut. 4 teks gabungan glyph+label (TT-01 Baru/Sangat Tinggi, dst.) diganti titik ●+label. Sisa glyph kosong: 0. Bintang S23 tetap ★ (Inter).
- Garis bawah menu aktif: PG-01 FAQ, PG-02 Riwayat, PG-03 dan PG-04 Buat laporan; PG-00/S20..S24 Tanya HaloSIS; PG-06 Laporan saya.
- Self-link: 33 reaction turunan sidebar (TT-03..05, KM-01/04, MJ-01..05, AD-01/02/04..07) dihapus; 0 tersisa di seluruh file.
- State tak terjangkau: PG-S01 ← kolom "Cari artikel" PG-01 (overlay); PG-S06 ← dropdown "Lokasi" PG-04 (overlay; opsi Subdit, tapi S06 juga memuat opsi dampak, jadi pemetaan kasar). PG-S11 dan PG-S12 hanya dipicu PG-05 (mockup HP yatim): dinamai "(tidak dipakai)" dan dipindah ke baris bawah Section 01 (y=1340). PG-05 sendiri tetap tak terjangkau.
