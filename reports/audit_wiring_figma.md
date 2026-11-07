# Audit wiring Figma — Prototype HaloSIS

## Reaction per Section (sebelum → sesudah)
| Section | Sebelum | Sesudah |
|---|---|---|
| 00 Login | 10 | 12 (+LG-00) |
| Alur Demo | 526 | 526 (tidak diubah, lintas peran sesuai urutan demo) |
| 01 Pegawai | 95 | 91 |
| 02 Operator | 207 | 198 |
| 03 Tim Teknis | 31 | 25 |
| 04 Knowledge Manager | 271 | 270 |
| 05 Manajemen | 94 | 93 |
| 06 Administrator | 447 | 446 |
| Komponen bersama | 73 | 73 (komponen sumber tidak diubah; override di tingkat instance) |

## Pelanggaran & perbaikan (154 reaction lintas peran)
- Semua "Tombol Ganti peran / akun" (6 peran): reaction dihapus.
- Semua "Tombol Keluar" (6 peran): Alur Demo/01 Login → 00 Login/LG-00 Login (1440px) (frame baru, klon 01 Login).
- 00 Login: Akun budi Alur Demo/02 → PG-01; Akun andi Alur Demo/09 → TT-01; "Masuk lagi" (LG-02) Alur Demo/01 → LG-00.
- 01 Pegawai: Nav Tanya HaloSIS (Alur Demo/02) → PG-01; Nav Laporan saya (Alur Demo/05) → PG-S13 (overlay baru "Halaman ini di luar cakupan prototype"); "Lanjutkan percakapan" → PG-01.
- 02 Operator: Nav Antrean validasi (Alur Demo/06, 9 frame) → OP-02 Semua tiket (padanan terdekat).
- 03 Tim Teknis: Dasbor/Tiket saya & tim/HaloSIS (Alur Demo/09) → TT-01; Pemantauan SLA/Pola insiden/Cari pengetahuan (OP-06/07/08) → overlay TT-S01; Btn Tambah solusi (Alur Demo/10) → reaction dihapus.
- 05 Manajemen: Pemantauan SLA/Pola insiden (OP-06/07) → overlay MJ-S02.
- 06 Administrator: Kinerja AI (MJ-02) & Kandidat pengetahuan (KM-01) → overlay AD-S02.
- Reaction navigasi ke frame yang sedang dibuka (self-link, mis. Nav aktif) dihapus karena Figma menolak NAVIGATE ke frame sendiri.

## Belum tersambung (nama Nav/Btn/Tab tanpa reaction)
- 01 Pegawai: Btn Kirim laporan, Btn Batal, Btn Ya selesai, Btn Buat laporan, Btn Lanjutkan percakapan.
- 02 Operator: Btn Simpan penilaian, Btn Kembali ke saran AI, Btn Tutup 3 tiket terpilih; Tabel (tiket/SLA/siap ditutup).
- 03 Tim Teknis: 6 Link; 06 Administrator: Tab (Tampilan Pribadi/Global/Umpan RSS), 122 Link.
- Tabel/Table Cell/Link bawaan GLPI tidak diberi reaction (di luar cakupan prototype).

## Pembaruan (tahap 2)
- Alur Demo 01→12: utuh (12/12 terjangkau). 01 Login "Masuk" → overlay baru DM-S00 "Pilih akun demo" (budi→02, rina→06, andi→09, lina→KM-01, sri→12, dimas→AD-01); 05 chip peran "Pegawai" → DM-S00 (05→06); 10 "Tambah" (solusi) → 11 sudah tersambung; 08 "Terima" → 09 (baru). Rantai: 01>02, 02>03, 03>04, 04>05 langsung; 05>06 via DM-S00; 06>07>08 langsung; 07>09 langsung; 09>10>11>12 langsung.
- Modal: OP-05 & TT-02 dipotong ke batas modal, navigasi sudah OVERLAY (OP-03 Tolak, TT-01 Kembalikan), Batal → close overlay. Alur Demo 08 bukan modal (halaman penuh) → tetap NAVIGATE.
- Belum tersambung: elemen yang disebut semua sudah bersambung (PG-04 Kirim laporan/Batal → PG-S07; PG-02 Lanjutkan percakapan → PG-01; OP-04 Simpan penilaian/Kembali → OP-S12; OP-09 Tutup 3 tiket → OP-S19; AD-01 tab → AD-S06). Baru: TT-01 "Tambah solusi" → TT-S08 (frame state baru "Solusi ditambahkan"). "Btn Ya selesai" tidak ditemukan sebagai layer (tidak ada di frame PG saat ini).
- Ikon aksi tanpa label (chevron/halaman, refresh, hapus, unduh, titik tiga, filter, caret, simpan, toggle, kirim) → 53 sambungan: Alur Demo → DM-S07, KM → KM-S03, MJ → MJ-S02, AD → AD-S09; ikon kirim chat 02→03, 03→04, 04→DM-S02. Total sambungan baru ≈ 64 (+2 frame: DM-S00, TT-S08).
- Sisa tanpa reaction (alasan): Tabel/Table Cell/Link bawaan GLPI; ikon dekoratif di judul/label (sparkles, user, clock, dst.); Tab List GLPI.

## Pembaruan tahap 3 (12 frame ditangkap ulang)
- Reaction MASUK ke frame lama dipindah ke frame baru: 113 reaction (termasuk komponen sidebar/navbar & titik awal alur "Operator" 46:2 → 128:2); sisa yang masih menuju frame lama: 0; sambungan menggantung: 0.
- Reaction di dalam frame lama dilepas (±287 simpul, termasuk 11 reaction turunan instance). Frame baru: ±175 elemen disambung (ke state/frame di Section yang sama), menu ke frame sendiri dilepas (±12).
- Catatan jujur: reaction keluar frame lama dilepas SEBELUM dicatat, sehingga "sama seperti frame lama bila teksnya sama" tidak bisa disalin persis; penyambungan dibuat ulang berdasarkan teks tombol dan daftar state (lihat peta_wiring tahap 3). Sambungan khusus lama yang mungkin hilang: tautan baris tiket/laporan ke layar detail, Lanjutkan percakapan (PG-02 → PG-01).
- Alur Demo 01→12: utuh (29/29 frame Alur Demo terjangkau dari 01 Login; tidak ada reaction Alur Demo yang diubah selain tujuan ke frame baru).


## Pembaruan tahap 4 (audit dibaca dari reaction nyata)
- Sebelum: Section peran → Alur Demo = 23 reaction (Navbar Pegawai "Tanya HaloSIS"→24:2 & "Laporan saya"→30:2; tombol "Tanya asisten" PG-01/03/04; Sidebar Operator "Antrean validasi"→31:2 di 9 frame OP; Sidebar Tim Teknis→35:2).
- Sesudah: 0. Tanya HaloSIS→PG-01, Laporan saya→PG-02 (padanan terdekat; tidak ada layar "Laporan saya" di Section 01), Antrean validasi→OP-03, Sidebar Tim Teknis→TT-01, "Tanya asisten" PG-03/04→PG-01 (PG-01 dilepas karena sama dengan frame sendiri). Menu ke frame sendiri dilepas.
- Alur Demo: instance sidebar Operator di 06/07/08 dan Tim Teknis di 09/10 di-override agar tetap seperti semula (menuju Alur Demo / frame Operator). Catatan jujur: di tengah pekerjaan reaction 6 item sidebar TT di Alur Demo 09/10 sempat tertimpa, lalu dipulihkan sesuai komponen; link-ke-diri di Alur Demo 06/09 dilepas (no-op).
- Section Usulan: reaction turunan instance (17) dibersihkan lagi; 0 reaction keluar, 0 masuk.
- Total reaction 1832; menggantung 0. Alur Demo 29/29 terjangkau dari 01 Login; rantai 02→12 langsung utuh (01→02 dan 05→06 lewat overlay pilih akun/ganti peran, bukan tautan langsung).
- Belum diubah (bukan Alur Demo): 03 Tim Teknis→02 Operator (6), 05 Manajemen→02 Operator (12) — lintas peran, perlu keputusan.


## Pembaruan tahap 5 (reaction lintas peran 18 → 0)
- Cek aplikasi (localhost:8080, teks, `logs/tahap5_menu_andi.log` & `_sri.log`): andi (Tim Teknis) punya menu Pemantauan SLA, Pola insiden, Cari pengetahuan; sri (Manajemen) punya Pemantauan SLA, Pola insiden. Jadi ke-18 sambungan memang menu yang ada → semuanya diduplikat, tidak ada yang dialihkan ke TT-S01/MJ-S02 sebagai pengganti.
- Duplikat: TT-03 Pemantauan SLA (dari OP-06), TT-04 Pola insiden (OP-07), TT-05 Cari pengetahuan (OP-08) di Section 03; MJ-04 Pemantauan SLA (OP-06), MJ-05 Pola insiden (OP-07) di Section 05. Sidebar Operator diganti instance "Sidebar · Tim Teknis"/"Sidebar · Manajemen". Isi duplikat: avatar → menu profil peran; semua sambungan lain ke Operator → notifikasi "di luar cakupan" (TT-S01 / MJ-S02).
- Tujuan menu di komponen sidebar diubah: TT (6) → TT-03/04/05; MJ (12, lewat 1 komponen, 3 instance) → MJ-04/05.
- Verifikasi: reaction lintas Section peran = 0 selain Alur Demo → peran, Login → beranda, dan "Keluar" → 00 Login (sudah ada sejak awal); menggantung 0; Alur Demo 29/29 terjangkau dari 01 Login; total reaction 2012. Section Usulan sempat mewarisi 6 reaction dari komponen yang diubah → dilepas (0 keluar).
- Catatan: frame duplikat ditaruh di kanan state tiap Section (Section 03 dan 05 diperlebar); belum dicek visual per elemen (2 tangkapan layar saja).
