# Audit hasil aksi Figma vs aplikasi (HaloSIS)

Dibuat: 2026-11-07. Hanya baca: Figma, DB (data uji dikembalikan), kode tidak diubah. Data mentah: `logs/figma_dump.json`, `logs/app_dump.json`.

Cakupan: 158 frame (Login 4, Alur Demo 29, 01 Pegawai 25, 02 Operator 33, 03 Tim Teknis 13, 04 KM 19, 05 Manajemen 16, 06 Admin 19); 48 halaman aplikasi dibuka, 33 aksi dicoba (30 berhasil dibaca).

## Ringkasan (jumlah temuan Section × jenis)

| Section | KONTEN | HASIL | TUJUAN | TIDAK-TERSAMBUNG | STATE-HILANG | TATA-LETAK | LAIN | Total |
|---|---|---|---|---|---|---|---|---|
| 00 Login | 0 | 1 | 1 | 0 | 0 | 0 | 1 | 3 |
| Alur Demo | 0 | 6 | 1 | 2 | 2 | 5 | 1 | 17 |
| 01 Pegawai | 0 | 2 | 1 | 2 | 1 | 0 | 3 | 9 |
| 02 Operator | 3 | 3 | 1 | 0 | 1 | 1 | 1 | 10 |
| 03 Tim Teknis | 1 | 1 | 0 | 2 | 0 | 1 | 0 | 5 |
| 04 Knowledge Manager | 1 | 1 | 0 | 0 | 1 | 1 | 1 | 5 |
| 05 Manajemen | 0 | 1 | 0 | 2 | 0 | 1 | 1 | 5 |
| 06 Administrator | 2 | 0 | 0 | 0 | 1 | 1 | 1 | 5 |
| **Total** | 7 | 15 | 4 | 8 | 6 | 10 | 9 | 59 |

Jenis: KONTEN=teks/isi beda; HASIL=hasil aksi beda; TUJUAN=klik ke layar salah; TIDAK-TERSAMBUNG=aksi ada di app, tak ada reaction di Figma; STATE-HILANG=hasil app belum punya frame; TATA-LETAK=tumpang tindih/terpotong; LAIN.

## 00 Login

| frame | elemen | masalah | jenis | bukti singkat |
|---|---|---|---|---|
| LG-00 / LG-01 Login | Masuk | Figma: Masuk membuka pemilih akun demo (LG-S01); aplikasi: login sungguhan lalu masuk ke halaman peran | HASIL | LG-00 rx Masuk→LG-S01; app login budi→/plugins/halosis/Chat |
| LG-S01 Pilih akun demo | andi / lina | Tujuan setelah pilih akun beda dengan aplikasi: andi→TT-01 (detail tiket), lina→KM-01; aplikasi mendarat di Beranda GLPI (/front/central.php) | TUJUAN | app_dump: andi:beranda, sri/dimas/rina → /front/central.php |
| LG-S01 vs DM-S00 | rina / andi | Dua frame pemilih akun tak konsisten: rina→OP-01 (LG-S01) tetapi →06 Antrean validasi (DM-S00); andi→TT-01 vs →09 | LAIN | LG-S01 rx rina>128:2, DM-S00 rina>06; andi>134:2 vs 09 |

## Alur Demo

| frame | elemen | masalah | jenis | bukti singkat | status |
|---|---|---|---|---|---|
| 03 Jawaban + sumber | Masalah terselesaikan | Figma: notifikasi "Terima kasih, percakapan ditandai selesai" (DM-S02); aplikasi: muncul kartu rating "Seberapa membantu asisten ini?" | HASIL | act budi:chat "Masalah terselesaikan" → baru: "Seberapa membantu asisten ini?" | ✅ 03-R1 (hasil): kartu rating asli; reaction → 03-R1; DM-S02 dihapus |
| 03 Jawaban + sumber | judul artikel sumber | Figma: notifikasi "Membuka artikel sumber (demo)"; aplikasi: tautan sumber tidak diuji | LAIN | tidak diuji (lihat bagian tak bisa dicek) | ⏭ baris LAIN (tak diuji) |
| 07 Detail tiket + panel Saran AI | Terima | Teks hasil beda: Figma "Saran AI diterima (demo)"; aplikasi "Saran AI diterima dan diterapkan ke tiket." | HASIL | act rina:Terima saran | ✅ 07-R1 (hasil): saran diterapkan (notifikasi asli); DM lama tak dipakai |
| 07 Detail tiket + panel Saran AI | Tolak | Figma: notifikasi "Saran AI ditolak (demo)"; aplikasi: muncul form "Tolak & triase manual" (alasan wajib) lalu "Saran AI ditolak. Silakan triase tiket secara manual." | HASIL | act rina:Tolak (buka) / Tolak saran (kirim) | ✅ 07-R2 (form alasan asli) → 07-R3 (hasil tolak); reaction Tolak/«Tolak & triase manual» tersambung |
| 07 Detail tiket + panel Saran AI | Tolak (form alasan) | Layar form alasan penolakan tak ada di Alur Demo (hanya notifikasi) | STATE-HILANG | OP-05 ada di Section 02 tetapi isinya beda (lihat 02) | ✅ 07-R2 (hasil) = form alasan asli |
| 08 Modal Ubah | Simpan / Terapkan perubahan | Figma: "Perubahan klasifikasi disimpan" (DM-S10); aplikasi: "Nilai yang diubah diterapkan ke tiket." | HASIL | act rina:Terapkan perubahan | ✅ 08-R1 (hasil) «Nilai yang diubah diterapkan ke tiket.»; DM-S10 dihapus; Simpan/Ubah lama → DM-S07 |
| 10 Detail tiket + tambah solusi | Kembalikan ke Operator (salah tim) | Tombol ada di Figma tetapi tidak punya reaction; aplikasi membuka form alasan lalu "Tiket dikembalikan ke antrean validasi Operator." | TIDAK-TERSAMBUNG | rx frame 10 tak memuat Kembalikan; act andi:Kembalikan | ✅ 10-R1 (form alasan) → 10-R2 (hasil, «Tiket dikembalikan…»); tombol Kembalikan tersambung |
| 11 Detail laporan + Setujui (budi) | Setujui | Figma lompat ke 12 Kinerja AI (sri) — layar peran lain; aplikasi: tiket Ditutup + teks "Solution approved" (Inggris) + survei kepuasan 0–5 | TUJUAN | 11 rx Setujui→12; act budi:Setujui solusi | ✅ Setujui → 11-R1 (hasil) → «Simpan» survei lompat ke 12 (lompatan peran dipertahankan) |
| 11 Detail laporan + Setujui (budi) | Setujui (hasil) | Status Ditutup, pesan "Solution approved", "After 12 hours, you can no longer modify your response", survei kepuasan belum punya frame | STATE-HILANG | act budi:Setujui solusi baru=[Ditutup, Solution approved, Satisfaction…] | ✅ 11-R1 (hasil): Ditutup, «Solution approved», survei 0–5 (Inggris GLPI apa adanya) |
| 11 Detail laporan + Setujui (budi) | Tolak | Figma: notifikasi "Solusi ditolak, tiket dibuka kembali"; aplikasi: tiket kembali Baru, riwayat berisi "Ditolak on 2026-11-07 … by Santoso Budi" (campur Inggris), tanpa notifikasi | HASIL | act budi:Tolak solusi | ✅ 11-R2 (hasil): tiket Baru + riwayat «Ditolak on …»; DM-S11 dihapus |
| 12 Kinerja AI (sri) | 4/8/12 minggu | Figma: notifikasi "Rentang grafik diganti"; aplikasi: halaman dimuat ulang (?weeks=N), tanpa notifikasi | HASIL | act sri:rentang N minggu | ✅ 12-R1 (4 minggu), 12-R2 (12 minggu); 8 minggu = tampilan bawaan 12 (tanpa reaction); DM-S12 dihapus |
| 12 Kinerja AI (sri) | Tampilkan sebagai tabel | Tombol tidak punya reaction di Figma; aplikasi menampilkan tabel Minggu/Diterima/Diubah/Ditolak | TIDAK-TERSAMBUNG | act sri:Tampilkan sebagai tabel | ✅ 12-R3 (hasil): tabel Minggu/Diterima/Diubah/Ditolak; Tampilkan sebagai tabel → 12-R3 |
| 04 Kartu buat laporan | Ringkasan yang dilampirkan / Kirim laporan | Teks "Ringkasan…", ikon ▸ dan baris ringkasan/tombol saling tumpang tindih | TATA-LETAK | overlap: "Ringkasan yang dil\|▸", "Pegawai: FASIH gag\|Kirim laporan" | ✅ penanda ▸ digeser (padding Summary 18px), tumpang tindih 0 |
| 08 Modal Ubah | Operator / BPS vs "Jenis: perlu ditinjau" | Teks header bertumpuk dengan teks panel Saran AI; 54 teks keluar dari batas frame | TATA-LETAK | overlap "Operator\|Jenis: perlu ditin"; out=54 | ⏭ cek visual+clip: teks tumpuk hanya di balik area ter-clip/scroll (tak terlihat); tumpang tindih terlihat 0 |
| 10 / 11 | Tambah, Kerangka, HaloSIS | Teks "Tambah"/"Kerangka" menimpa judul tiket (10); "HaloSIS" menimpa "•" (11) | TATA-LETAK | overlap 10: Tambah\|FASIH gagal sinkro; 11: HaloSIS\|• | ⏭ cek visual (screenshot 11): rapi; sisa teks tumpuk di balik clip |
| 12 Kinerja AI (sri) | Tampilkan sebagai tabel ▸ / tanggal vs judul bagan | Label bertumpuk ("Tampilkan sebagai tabel"+▸; "2026-09-14"+"Perbandingan Keyakinan…") — 14 pasangan | TATA-LETAK | overlap 12 & MJ-02 = 14 pasangan | ✅ ▸ digeser; sisa pasangan label bagan ada di area ter-clip (tak terlihat) |
| 06, 07, 09, 10, 11 | kolom/teks tabel | Teks keluar batas frame (terpotong): 06=32, 07=40, 09=32, 10=52, 11=12 teks (mis. "Terakhir diperbarui", "Tanggal buka") | TATA-LETAK | cek batas absoluteBoundingBox | ⏭ teks keluar batas memang ter-clip/scroll (dibiarkan) |

Perbaikan 2026-11-07: frame hasil asli ditangkap dari aplikasi (Section Alur Demo, baris bawah y=3800): 03-R1, 07-R1..R3, 08-R1, 10-R1..R2, 11-R1..R2, 12-R1..R3. Verifikasi Alur Demo: lintas peran = 4 lompatan sengaja (07→09, 08→09, 10→11, 11-R1→12), self-link 0, menggantung 0, 01→12 utuh (01→02 dan 05→06 via DM-S00). Data uji (13 tiket + percakapan chat) dihapus; DB kembali 70 tiket/30 chat. Layar: logs/ad_ss1_frame11.png, logs/ad_ss2_07R3.png.

## 01 Pegawai

| frame | elemen | masalah | jenis | bukti singkat | status |
|---|---|---|---|---|---|
| PG-S21 / PG-S22 | Tidak, terima kasih | Figma: kembali ke PG-00 (chat kosong); aplikasi: kartu tutup, percakapan tetap terbuka (tetap di chat) | TUJUAN | act budi:chat "Tidak, terima kasih": url tetap /Chat, tidak ada teks baru | ✅ 2026-11-08: "Tidak, terima kasih" → PG-R06 / PG-R07 (chat yang sama, kartu tutup, hasil asli) |
| PG-04 Form Laporkan masalah | Kirim | Figma: notifikasi "Laporan terkirim. Tiket #1295 dibuat"; aplikasi: pindah ke halaman tiket dengan pesan "Item successfully updated: Laporkan Masalah" (Inggris) | HASIL | act budi:form kirim dengan judul | ✅ 2026-11-08: Kirim → PG-R03 (halaman tiket, pesan Inggris GLPI apa adanya) |
| PG-04 Form Laporkan masalah | Kirim tanpa Judul | Tak ada frame galat wajib isi; aplikasi menampilkan "This field is mandatory" (Inggris) | STATE-HILANG | act budi:form kirim tanpa judul | ✅ 2026-11-08: PG-R02 galat wajib isi (dipicu dari kolom Judul PG-04, karena Kirim sudah menuju PG-R03) |
| PG-03 Buat laporan | Ajukan Permintaan | Figma: notifikasi "luar cakupan prototype"; aplikasi membuka /Form/Render/2 (formulir berfungsi) | TIDAK-TERSAMBUNG | PG-03 rx →PG-S13; visit budi:form permintaan | ✅ 2026-11-08: Ajukan Permintaan → PG-R04 (form permintaan hasil asli) |
| PG-06 Laporan saya | baris tiket, Cari, Muat ulang | Semua reaction → PG-S13 "luar cakupan"; aplikasi: baris membuka detail tiket, Cari menyaring | TIDAK-TERSAMBUNG | PG-06 rx semua →PG-S13 | ✅ 2026-11-08: baris tiket (ID+judul, pola baris) → PG-R05; Cari/Muat ulang/paginasi tetap → PG-S13 (⏭ di luar cakupan prototype) |
| PG-01 Pusat bantuan (FAQ) | artikel FAQ | Figma: notifikasi "Membuka artikel sumber (demo)"; aplikasi membuka isi artikel (helpdesk.faq.php?id=…) | HASIL | PG-01 rx artikel→PG-S03 | ✅ 2026-11-08: 17 tautan artikel (pola daftar) → PG-R01 isi artikel |
| PG-S11, PG-S12 | — | Frame "tidak dipakai" masih ada (S11 duplikat DM-S02) | LAIN | nama frame berisi "(tidak dipakai)" | ⏭ dipertahankan: masih ada reaction masuk dari PG-05 (HP, tidak disentuh) |
| PG-05 Chat di HP | — | Tampilan HP tak diuji di aplikasi | LAIN | tidak diuji | ⏭ tampilan HP (PG-05) tidak disentuh (keputusan) |
| PG-00 / PG-S20 dll | kolom input | Placeholder "Tulis kendala Anda…" tidak muncul sebagai teks halaman (kemungkinan atribut placeholder, bukan beda) | LAIN | teks tidak terbaca innerText; tidak dinilai | ⏭ baris LAIN "tidak dinilai" dilewati (keputusan) |

Status Section 01 (2026-11-08): baris ⏳ selesai (✅/⏭). figma_verify Section 01 & 02: lintas peran 0, menggantung 0, self-link 0; Alur Demo 01→12 utuh. Frame hasil baru PG-R01..R07 di Section 01; PG-06 ditangkap ulang + navbar Pegawai.

## 02 Operator

| frame | elemen | masalah | jenis | bukti singkat | status |
|---|---|---|---|---|---|
| OP-03 Panel Saran AI | "Pilih dari 3 kandidat" + "Terapkan kandidat terpilih" | Aplikasi tidak punya pemilih 3 kandidat kategori; menampilkan satu saran (Keyakinan 75%, "Disarankan · keyakinan mencapai ambang 70%") dengan tombol Terima/Ubah/Tolak | KONTEN | app: rina:detail tiket + saran AI; Figma OP-03 | ✅ ditangkap ulang dari app (rina, 1440 px): satu saran 82%, «Disarankan · keyakinan mencapai ambang 70%», Terima/Ubah/Tolak; tanpa pemilih 3 kandidat. Terima→OP-S09, Tolak→OP-05. «Ubah» → OP-R4 (lihat tambahan 2026-11-08) |
| OP-04 Panel "Perlu penilaian manual" | Simpan penilaian / Kembali ke saran AI | Figma: ambang 60% ("38%, di bawah ambang 60%") dan formulir Kategori/Prioritas/Grup/Catatan; aplikasi: "ambang 40%", tanpa formulir/tombol Simpan penilaian (triase lewat Tolak & form tiket) | KONTEN | app tiket 1340: "Perlu penilaian manual · keyakinan di bawah ambang 40%" | ✅ ditangkap ulang: «Perlu penilaian manual · keyakinan di bawah ambang 40%», tanpa formulir; Tolak→OP-05 |
| OP-S12 | Simpan penilaian | Notifikasi "Penilaian manual disimpan, tiket diteruskan" tak punya padanan di aplikasi | HASIL | tak ada tombol Simpan penilaian di app | ✅ OP-S12 dihapus (tak ada aksinya); reaction ke sana ikut hilang |
| OP-05 Modal Tolak | alasan | Figma: pilihan alasan (Kategori tidak sesuai / Solusi tidak relevan / Sumber artikel usang / Lainnya) + Catatan opsional; aplikasi: satu kolom "Alasan (wajib)" teks bebas | KONTEN | act rina:Tolak (buka): "Alasan (wajib)", "Tolak & triase manual" | ✅ modal = satu kolom «Alasan (wajib)» + «Tolak & triase manual» (salinan form asli); tombol kirim → OP-R1 |
| OP-S13 | Tolak saran | Figma: "Saran AI ditolak, alasan tersimpan"; aplikasi: "Saran AI ditolak. Silakan triase tiket secara manual." | HASIL | act rina:Tolak saran (kirim) | ✅ OP-R1 (hasil) «Saran AI ditolak. Silakan triase tiket secara manual.»; OP-S13 dihapus |
| OP-02 Semua tiket | Cari | Figma: notifikasi "Halaman daftar tiket diganti"; aplikasi: pencarian GLPI sungguhan | HASIL | OP-02 rx Cari→OP-S07 | ✅ OP-R2 (hasil) daftar tiket hasil pencarian GLPI; Cari→OP-R2; OP-S07 dihapus |
| OP-07 Pola insiden | baris pola | Figma: baris → OP-04 (panel penilaian manual tiket); aplikasi: baris membuka Masalah (pola), bukan panel AI | TUJUAN | OP-07 rx Pola insiden…→OP-04 | ✅ OP-R3 (hasil) layar Masalah «Pola insiden: …»; 8 reaction baris/tautan → OP-R3 (bukan OP-04) |
| OP-09 Siap ditutup | Tutup / Tutup yang dipilih | Hasil klik tidak diuji; Figma → OP-S19 "Tidak ada tiket siap ditutup" | LAIN | tidak diuji (mengubah tiket nyata) | ⏭ baris LAIN: Tutup tidak dijalankan pada tiket nyata |
| OP-S14, S16, S18 | — | Notifikasi "Filter status SLA", "Tiket induk dibuat…", "Filter kategori pengetahuan" tak punya padanan aksi di aplikasi | STATE-HILANG | tak ditemukan aksi sepadan | ✅ OP-S14, S16, S18 dihapus (tanpa aksi padanan, tanpa reaction masuk); OP-S08/S10/S11 (dropdown desain lama) ikut dihapus karena yatim |
| OP-02, OP-06 | kolom tabel | Teks keluar batas frame: OP-02=31, OP-06=49 | TATA-LETAK | out of bounds | ⏭ dicek: OP-02 31 & OP-06 49 teks keluar batas semuanya ter-clip/scroll; teks terlihat bertumpuk 0 |

Perbaikan 2026-11-07 (Section 02): OP-03/04/05 diisi ulang dari tangkapan app (ID frame, nama, posisi tetap; sidebar = komponen «Sidebar · Operator» varian Antrean validasi; ikon SVG; OP-03/04 kini 1440×1109 agar tombol Terima/Ubah/Tolak tidak ter-clip). Frame hasil baru di baris bawah (y=2300): OP-R1, OP-R2, OP-R3. Baris state digeser +200 px. Verifikasi Section 02: menggantung 0, self-link 0, lintas peran 0 (satu-satunya tujuan di luar section = «Keluar» OP-S02 → Login, memang logout). Alur Demo: 01→12 utuh; tambahan: label/tombol «Terima» 07 → 07-R1 → 09, «Terapkan perubahan» 08 → 08-R1 → 09 (klik di mana saja pada frame hasil); label «Terima» sebelumnya menimpa tombol dan langsung ke 09. Tidak bisa dimunculkan: «Ubah» di OP-03 (modal Ubah hanya ada di Alur Demo 08). Teks Inggris GLPI ditangkap apa adanya. Data uji: 4 tiket (1354–1357) + saran/keputusan/antrean notifikasinya dibuat lalu dihapus; DB kembali 70 tiket / 30 chat. Layar: logs/op_ss1_OP03.png (sebelum perbaikan tinggi), logs/op_ss2_OP05.png, logs/op_ss3_OP03_final.png.

Tambahan 2026-11-08 (Section 02, diuji dengan alat tools/figma/): akun rina, tiket uji 1358, 1440 px, ikon SVG Tabler, sidebar = instance «Sidebar · Operator» varian Antrean validasi. **OP-R4 (hasil)** (frame `232:4526`, 4670,2300) = form «Ubah» terbuka di panel Saran AI (Urgensi + «Alasan (wajib)» terisi, tombol «Terapkan perubahan»); **OP-R5 (hasil)** (`234:4526`, 6210,2300) = hasil «Terapkan perubahan»: lencana «Diubah», «Diubah oleh Wulandari Rina…», «Alasan: …», pesan «Nilai yang diubah diterapkan ke tiket.» (teks apa adanya). Alur: OP-03 «Ubah» → OP-R4 → «Terapkan perubahan» → OP-R5. Verifikasi Section 02: lintas peran 0, menggantung 0, self-link 0 (296 reaction); Alur Demo 01→12 semua terjangkau. Data uji: tiket 1358 + saran/keputusan dibuat lalu dihapus; DB kembali 70 tiket / 30 chat. Layar: logs/op_ss4_ubah_0.png, logs/op_ss4_ubah_1.png (+ logs/pg_ss1_pg00.png dari uji awal).

## 03 Tim Teknis

| frame | elemen | masalah | jenis | bukti singkat | status |
|---|---|---|---|---|---|
| TT-01 Panel hanya-baca | Kembalikan ke Operator | Tombol tak punya reaction → TT-02 tak terjangkau; aplikasi: form alasan lalu "Tiket dikembalikan ke antrean validasi Operator." | TIDAK-TERSAMBUNG | TT-01 rx hanya Semua/BS/waktu→TT-S01 | ✅ 2026-11-08: TT-01 ditangkap ulang (andi, 1440 px, sidebar «Sidebar · Tim Teknis»); «Kembalikan ke Operator (salah tim)» → TT-02 |
| TT-02 Modal Kembalikan | alasan | Figma: pilihan alasan + catatan; aplikasi: kolom "Alasan (wajib)" teks bebas | KONTEN | act andi:Kembalikan (buka) | ✅ TT-02 = tangkapan asli (satu kolom «Alasan (wajib)»); tombol «Kembalikan ke Operator» → TT-R1 |
| TT-S05 | Kembalikan | Figma "Tiket dikembalikan ke Operator"; aplikasi "Tiket dikembalikan ke antrean validasi Operator." | HASIL | act andi:Kembalikan (kirim) | ✅ TT-R1 (hasil) = tangkapan asli setelah kirim (halaman tiket dimuat ulang, panel isi kosong karena tiket sudah lepas dari andi; sama dengan Alur Demo 10-R2); TT-S05 dan TT-S04 (dropdown yatim) dihapus |
| TT-03 / TT-04 / TT-05 | baris tabel, Cari, Masalah | Semua reaction → TT-S01 "Fitur menu (demo)"; aplikasi: baris membuka tiket/masalah, Cari bekerja | TIDAK-TERSAMBUNG | rx →TT-S01 | ✅ TT-03: 38 elemen baris (ID+judul+ikon, pola baris) → TT-R2 detail tiket; TT-04: 8 elemen baris → TT-R3 detail Masalah; Cari TT-04 → TT-R4 (hasil cari Masalah «SSO»); Cari TT-05 → TT-R5 (hasil cari pengetahuan). ⏭ paginasi «1»/«2» TT-03 tetap → TT-S01 (di luar cakupan) |
| TT-01, TT-03 | tabel/detail | Teks keluar batas frame: TT-01=30, TT-03=49 | TATA-LETAK | out of bounds | ⏭ ter-clip/scroll dibiarkan; cek visual TT-02 & TT-R3: tumpang tindih terlihat 0 |

Perbaikan 2026-11-08 (Section 03, alat tools/figma/, akun andi, tiket uji 1360 ditugaskan ke andi; testdata.js kini mendukung env ASSIGN): frame hasil baru TT-R1..R5 di baris bawah (y=1700), sidebar = instance «Sidebar · Tim Teknis»; baris state digeser +300 px; Section 03 diperbesar dan Section 04–06 + Usulan digeser +3026 px agar tak tumpang tindih. TT-R2 = tiket 42, TT-R3 = Masalah 1 (hanya-baca). figma_verify: Section 03 lintas peran 0, menggantung 0, self-link 0 (197 reaction; self-link sidebar TT-01 dibersihkan); Section 01 & 02 tetap 0/0/0; Alur Demo 01→12 utuh. Catatan: Section «01 Pegawai» (49:5) sempat tertelan ke Alur Demo; dikembalikan ke level halaman (0, 3400). Data uji: tiket 1360 + reassignment/saran/followup/notifikasi dibuat lalu dihapus; 15 tabel DB sama persis sebelum/sesudah (tiket 70, chat 30). Log: logs/tt_counts_sebelum.txt, logs/tt_counts_sesudah.txt.

## 04 Knowledge Manager

| frame | elemen | masalah | jenis | bukti singkat |
|---|---|---|---|---|
| KM-01 Kandidat pengetahuan | tab Dijadikan artikel / Diabaikan | Figma: notifikasi "Filter kandidat diterapkan" di layar yang sama; aplikasi: pindah ke ?status=article / ?status=ignored dengan daftar lain | HASIL | act lina:tab … |
| KM-01 → KM-04 | Jadikan artikel | Figma: editor kosong "Artikel tanpa judul"; aplikasi: editor artikel draf terisi + pesan "Draf artikel dibuat. Tinjau, lalu terbitkan agar dapat dilihat." | STATE-HILANG | act lina:Jadikan artikel → knowbaseitem.form.php?id=43 |
| KM-01 | Abaikan | Hasil klik tidak terbaca (skrip gagal); Figma → "Kandidat diabaikan" | LAIN | act lina:Abaikan error |
| KM-01 | daftar kandidat | 373 teks keluar batas frame (tinggi 1100) | TATA-LETAK | out=373 |
| KM-03 Daftar artikel | Cari | Figma: dropdown "Kolom terisi: laporan FASIH"; aplikasi: filter daftar | KONTEN | KM-03 rx Cari→KM-S04 |

## 05 Manajemen

| frame | elemen | masalah | jenis | bukti singkat |
|---|---|---|---|---|
| MJ-01 Dasbor kinerja | widget/tab | Tidak ada reaction selain menu; aplikasi interaktif (/front/dashboard_helpdesk.php) | TIDAK-TERSAMBUNG | rx kosong (non-navigasi) |
| MJ-03 Laporan, MJ-04, MJ-05 | — | Tidak ada reaction selain menu: baris SLA/pola, filter, tanggal tak terhubung | TIDAK-TERSAMBUNG | rx kosong (non-navigasi) |
| MJ-02 Kinerja AI | Rentang / Terapkan / legenda | Figma: notifikasi MJ-S06/S09/S10; aplikasi: muat ulang ?weeks=…, tanpa notifikasi | HASIL | act sri:rentang … |
| MJ-S11 | Daftar pilihan 2025-11-06 | Frame daftar pilihan kosong tanpa isi | LAIN | teks kosong |
| MJ-02, MJ-04 | tabel | Teks keluar batas / bertumpuk: MJ-04=49 teks keluar; MJ-02 14 pasangan tumpuk | TATA-LETAK | out/overlap |

## 06 Administrator

| frame | elemen | masalah | jenis | bukti singkat |
|---|---|---|---|---|
| AD-02 / AD-06 / AD-07 (+ Tim teknis) | buka halaman | Aplikasi meminta verifikasi ulang (/ReAuth/Prompt) sebelum halaman; tak ada frame di Figma | STATE-HILANG | app_crawl_dimas.txt: config, user, group, event => /ReAuth/Prompt |
| AD-03 Pratinjau SLA | seluruh frame | Nama "Pratinjau SLA" tetapi isinya sama dengan AD-02 Pengaturan AI (tombol Pratinjau dampak, Simpan) | KONTEN | AD-03 texts = AD-02 |
| AD-02 | Simpan | Figma: "Pengaturan AI disimpan"; hasil di aplikasi tidak terbaca (ReAuth) | LAIN | act dimas:Simpan → halaman reauth |
| AD-04..07 | Cari | Figma: dropdown "Kolom terisi: laporan FASIH"; aplikasi: filter tabel | KONTEN | rx Cari→AD-S03 |
| AD-01 / AD-02 / AD-03 | konten melebihi frame | AD-01=248, AD-02=11, AD-03=11 teks di luar batas ("Disarankan", "Pilih dari 3 kandidat", "Aman", "Berisiko") | TATA-LETAK | out of bounds |

## Tidak bisa dicek

- Gagal otomatis (selector/timeout): rating bintang di chat, "Kirim laporan" di kartu chat, klik percakapan di Riwayat, Cari pengetahuan, Abaikan kandidat, filter Tim/Kategori Kinerja AI, Simpan pengaturan AI (butuh ReAuth).
- Tidak diuji: Tutup di Siap ditutup (mengubah tiket nyata), login SSO Keycloak, tampilan HP (PG-05, LG-01), tautan artikel sumber, halaman Pegawai "Laporan saya" klik baris.
- Teks halaman dipotong 140 baris per halaman: item di bawah (mis. "Indikator Pergeseran", "Tren Pola Insiden" di Kinerja AI) tidak dibandingkan; baris data/tanggal diabaikan karena bergantung data.
- TATA-LETAK dihitung dari batas koordinat teks (di luar frame / tumpang >35%), tanpa screenshot; teks di luar batas bisa saja disembunyikan clip frame atau memang tabel yang melebar — perlu dilihat langsung.
- Perbandingan reaction memakai versi ringkas (menu navigasi berulang disaring); keputusan "tidak ada reaction" hanya untuk elemen non-navigasi.

## Status perbaikan 2026-11-09 (langkah 1–4; tidak di-commit)

- ✅ **TT-R1 & Alur Demo 10-R2**: ditangkap ulang setelah «Kembalikan», pesan «Tiket dikembalikan ke antrean validasi Operator.» terlihat (tunggu teks muncul; `steps/tt_kembalikan.js`). ID/posisi/reaction masuk tetap; sidebar = «Sidebar · Tim Teknis». Layar: logs/f2_ss1_10R2.png.
- ✅ **Tata letak**: Section 01 (49:5) kembali ke level halaman (sempat tertelan Alur Demo); urutan 00, Alur Demo, 01–06, Komponen, Usulan; tumpang tindih 0; Alur Demo dirapatkan. Layar: logs/f2_ss2_halaman.png.
- **04 KM (lina)**: ✅ tab Dijadikan artikel → KM-R1, Diabaikan → KM-R2 (daftar asli ?status=…); ✅ «Jadikan artikel» (40 tombol, pola baris) → KM-R3 editor draf terisi + «Draf artikel dibuat. Tinjau, lalu terbitkan agar dapat dilihat.» (layar logs/f2_ss3_KMR3.png). ⏭ «Abaikan» (mengubah kandidat; tidak dijalankan), ⏭ KM-03 Cari, ⏭ tata letak KM-01 (373 teks luar batas = clip/scroll).
- **05 Manajemen (sri)**: ✅ Rentang 4/12 minggu → MJ-R1/R2, «Tampilkan sebagai tabel» → MJ-R3 (hasil asli, dari MJ-02 dan sesamanya). ⏭ MJ-01/03/04/05 (halaman GLPI bawaan: dasbor/statistik/tiket/masalah; tak ada keadaan baru yang ditangkap), ⏭ MJ-S11 (daftar pilihan tanggal, ada reaction masuk; app tak punya padanan), ⏭ tata letak MJ-02/04 (teks di balik clip).
- **06 Administrator (dimas)**: ✅ AD-R1 = /ReAuth/Prompt; «Pengaturan AI» di sidebar 10 frame AD → AD-R1, «Verifikasi» → AD-02. ✅ AD-03 diganti tangkapan asli Pratinjau dampak SLA (ID/nama tetap). ⏭ Simpan pengaturan AI (mengubah konfigurasi), ⏭ AD-04..07 Cari, tata letak AD-01..03.
- **00 Login**: keputusan «Masuk → pilih akun demo» tetap. ✅ LG-S01 disamakan dengan beranda aplikasi (/front/central.php): rina → OP-R5, andi → TT-R6, lina → KM-R4, sri → MJ-R4, dimas → AD-R3 (budi tetap PG-00 = /Chat). ⏭ LG-S01 vs DM-S00 beda (Alur Demo memakai layar alur, sengaja).
- ✅ **figma_verify**: Section 01–06 lintas peran 0, menggantung 0, self-link 0 (reaction 286/304/213/226/225/447); 00 Login: 6 lompatan pilih-akun ke Section peran (disengaja), menggantung 0, self-link 0; Alur Demo 01→12 utuh (12/12 terjangkau).
- **Data uji**: 458 tabel dihitung (logs/f2_all_sebelum_04.txt vs f2_all_akhir.txt); 15 tabel inti (logs/f2_counts_*.txt) identik: tiket 70, chat 44 (basis sebelum mulai; sebelumnya 30 di audit lama, bertambah di luar sesi ini). Tiket uji 1367/1368 dibuat lalu dihapus. «Jadikan artikel» mengubah kandidat 51 + membuat artikel KB 45: dipulihkan (kandidat 51 → pending, date_mod = date_creation; artikel, relasi, log dihapus; logs/f2_km_pulih.sh). Selisih sisa hanya noise login/cron (events +12, sessions +12, crontasklogs).
