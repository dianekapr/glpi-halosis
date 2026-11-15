# Peta navigasi jendela (W-xx)

Figma: halaman "Peta Navigasi" (frame "Peta Navigasi"); PNG: `reports/peta_navigasi.png` (skala 2). Layar diambil dari frame yang sudah ada di halaman "Prototype HaloSIS"; semua kotak kini punya frame (lima frame baru dari screenshot aplikasi di `reports/shots/`). W-38–W-41 diberi label "layar bawaan GLPI". Menu tiap peran mengikuti sidebar/navbar di Figma dan `reports/panduan_peran.md`. Menu tampil sesuai peran (hak profil GLPI).

Catatan: menu Operator dan Tim Teknis tidak memuat Kinerja AI maupun Laporan (statistik); keduanya hanya untuk Manajemen (Kinerja AI juga Administrator). Operator dan Tim Teknis berbagi Pemantauan SLA dan Pola insiden. Menu Administrator lain (Kandidat pengetahuan, Kinerja AI) memakai W-23 dan W-27.

| W-xx | nama layar | peran | UC | frame Figma |
|---|---|---|---|---|
| W-01 | Masuk (SSO) | semua peran | – | LG-00 Login (1440px) 99:1500 |
| W-02 | Beranda / Dasbor | semua peran (Pegawai: Tanya HaloSIS) | – | OP-01 Dasbor 128:2 · TT-R6 309:5810 · KM-R4 310:5810 · MJ-01 55:2 · AD-R3 312:5810 |
| W-03 | Tanya HaloSIS | Pegawai | UC-01 | PG-00 Tanya HaloSIS (kosong) 153:3533 |
| W-04 | Buat laporan (Katalog layanan) | Pegawai | UC-03 | PG-03 133:2 |
| W-05 | Form Laporkan masalah | Pegawai | UC-03 | PG-04 139:2 |
| W-06 | Form Ajukan Permintaan | Pegawai | UC-03 | PG-R04 253:4650 |
| W-07 | Laporan saya | Pegawai | UC-07 | PG-06 159:3533 |
| W-08 | Detail laporan + Setujui (konfirmasi & rating) | Pegawai | UC-07 | 11 Detail laporan + Setujui (budi) 38:2; rating: 11-R1 190:3708 |
| W-09 | Tanya Jawab (FAQ) | Pegawai | UC-01 | PG-01 Pusat bantuan (FAQ) 132:2 |
| W-10 | Widget chat | Pegawai | UC-01 | PG-R09 Widget chat (FAQ) 554:6242 · screenshot `reports/shots/widget_chat.png` |
| W-11 | Riwayat percakapan | Pegawai | UC-01 | PG-02 138:2 |
| W-12 | Antrean validasi (Menunggu keputusan) | Operator | UC-05 | 06 Antrean validasi (rina) 31:2 |
| W-13 | Detail tiket + panel Saran AI | Operator | UC-05 | 07 32:2 |
| W-14 | Modal Ubah | Operator | UC-05 | 08 33:2 |
| W-15 | Semua tiket | Operator | UC-03, UC-05 | OP-02 135:2 |
| W-16 | Siap ditutup | Operator | UC-07 | OP-09 136:2 |
| W-17 | Cari pengetahuan | Operator | UC-02 | OP-08 137:2 |
| W-18 | Tiket saya & tim | Tim Teknis | UC-06 | 09 Tiket saya & tim (andi) 35:2 |
| W-19 | Panel hanya-baca + Kembalikan ke Operator | Tim Teknis | UC-06 | TT-01 134:2 |
| W-20 | Modal Kembalikan | Tim Teknis | UC-06 | TT-02 46:922 |
| W-21 | Detail tiket + tambah solusi | Tim Teknis | UC-06 | 10 36:2 |
| W-22 | Cari pengetahuan | Tim Teknis | UC-02 | TT-05 147:4372 |
| W-23 | Kandidat pengetahuan | Knowledge Manager | UC-09 | KM-01 50:2 |
| W-24 | Editor artikel / draf (Jadikan artikel) | Knowledge Manager | UC-09 | KM-R3 297:5257 |
| W-25 | Daftar artikel (basis pengetahuan) | Knowledge Manager | UC-09 | KM-03 140:2 |
| W-26 | Tulis artikel | Knowledge Manager | UC-09 | KM-04 80:2 |
| W-27 | Kinerja AI | Manajemen, Administrator | UC-08 | MJ-02 56:2 |
| W-28 | Laporan (statistik) | Manajemen | UC-08 | MJ-03 79:2 |
| W-29 | Pemantauan SLA | Manajemen, Operator, Tim Teknis | UC-08 | OP-06 130:2 (TT-03 147:3157, MJ-04 147:4586) |
| W-30 | Pola insiden | Manajemen, Operator, Tim Teknis | UC-08 | OP-07 131:2 (TT-04 147:3988, MJ-05 147:5425) |
| W-31 | Verifikasi ulang sebelum Pengaturan AI | Administrator | UC-10 | AD-R1 304:5677 |
| W-32 | Pengaturan AI (+ pratinjau dampak) | Administrator | UC-10 | AD-02 69:2 |
| W-33 | Pratinjau SLA | Administrator | UC-10 | AD-03 74:2 |
| W-34 | Katalog layanan | Administrator | UC-10 | AD-04 61:2 |
| W-35 | Kebijakan SLA | Administrator | UC-10 | AD-05 62:2 |
| W-36 | Pengguna & peran | Administrator | UC-10 | AD-06 71:2 |
| W-37 | Jejak audit | Administrator | UC-10 | AD-07 72:2 |
| W-38 | Kategori layanan | Administrator | UC-10 | AD-08 Kategori layanan 554:6243 (layar bawaan GLPI; screenshot `reports/shots/kategori_layanan.png`) |
| W-39 | Tim teknis | Administrator | UC-10 | AD-09 Tim teknis 554:6244 (layar bawaan GLPI; screenshot `reports/shots/tim_teknis.png`) |
| W-40 | Alur kerja & aturan | Administrator | UC-10 | AD-10 Alur kerja & aturan 554:6245 (layar bawaan GLPI; screenshot `reports/shots/alur_kerja.png`) |
| W-41 | Notifikasi | Administrator | UC-10 | AD-11 Notifikasi 554:6246 (layar bawaan GLPI; screenshot `reports/shots/notifikasi.png`) |
