# Indeks screenshot alur (UC-01 s.d. UC-05)

| UC | alur | langkah | file | catatan |
|---|---|---|---|---|
| UC-01 | 1a | – | UC-01_1a.png | Sakelar chat dimatikan |
| UC-01 | 3a | – | UC-01_3a.png | Kotak kosong, tombol Kirim nonaktif |
| UC-01 | 3b | – | UC-01_3b.png | Pesan ke-21: percakapan terlalu panjang |
| UC-01 | 3c | – | UC-01_3c.png | Muat ulang: percakapan sudah selesai, kotak ketik terkunci |
| UC-01 | 4b | – | UC-01_4b.png | Request chat diputus (page.route abort) |
| UC-01 | 5a | – | UC-01_5a.png | Kartu tawaran laporan |
| UC-01 | 5a | S1 | UC-01_5a_S1.png | Laporan sudah dibuat |
| UC-01 | 5a | S1_form | UC-01_5a_S1_form.png | Form laporan dengan ringkasan terlampir |
| UC-01 | 5c | – | UC-01_5c.png | Diarahkan ke unit terkait |
| UC-01 | 7a | – | UC-01_7a.png | Kartu laporan setelah Belum terselesaikan |
| UC-01 | 7a | S1 | UC-01_7a_S1.png | Laporan sudah dibuat |
| UC-01 | 7b | – | UC-01_7b.png | Percakapan diakhiri; kotak ketik terkunci |
| UC-01 | normal | 9 | UC-01_normal_9.png | Terima kasih, percakapan berakhir |
| UC-02 | 3a | – | UC-02_3a.png | Layanan AI dimatikan |
| UC-02 | 5a | – | UC-02_5a.png | Tanpa hasil di atas ambang |
| UC-02 | S1a | – | UC-02_S1a.png | Pengetahuan tidak ditemukan |
| UC-02 | S1b | – | UC-02_S1b.png | Umpan balik tersimpan + penanda Ditandai tidak membantu |
| UC-03 | 1a | S1 | UC-03_1a_S1.png | Salinan UC-01_5a_S1 (alur sama: Ya, buat laporan → Kirim) |
| UC-03 | 1a | S1_form | UC-03_1a_S1_form.png | Salinan UC-01_5a_S1_form (judul terisi + ringkasan) |
| UC-03 | 1b | – | UC-03_1b.png | Form Tambah tiket (Pemohon, Sumber permintaan, Judul, Deskripsi) — belum diisi |
| UC-03 | 6a | – | UC-03_6a.png | Sakelar triase dimatikan saat tiket dibuat |
| UC-05 | 3a | – | UC-05_3a.png | Setelah klik Buat saran AI |
| UC-05 | 5c | – | UC-05_5c.png | Setelah solusi disimpan: Dipecahkan |
| UC-05 | 5c | form | UC-05_5c_form.png | Form Tambah solusi |
| UC-05 | 5d | – | UC-05_5d.png | Dua sesi: sesi kedua mencoba memutuskan saran yang sudah diputuskan |
| UC-05 | S1a | – | UC-05_S1a.png | Nilai sama dengan saran: gunakan tombol Terima |
| UC-05 | S1b | – | UC-05_S1b.png | Alasan <5 karakter: Terapkan perubahan nonaktif |

**Dilewati / catatan**
- UC-05 5c: tangkapan awal gagal (selektor "Balas"), diulang dengan dropdown; kini berhasil.
- UC-01 normal 9, 5a, 7a, 3c/7b memakai artikel nyata SSO; 5b (zona sedang) tidak ditangkap karena tidak dapat dipastikan.
- UC-03 1b: hanya form Tambah kosong (pengisian Pemohon/Sumber via select2 tidak diotomatisasi).
- UC-03 1a: salinan UC-01 5a (alur identik).
- UC-01 1a/UC-03 6a memakai sakelar Pengaturan AI (dikembalikan; seluruh data uji juga dibersihkan lewat pulihkan snapshot).
