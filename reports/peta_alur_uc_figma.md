# Peta alur UC → frame Figma (halaman "Alur Real Use Case")

Sumber: `reports/T4_final.md` bagian B; frame sumber dari halaman "Prototype HaloSIS" (hanya disalin). Langkah ber-`-` → kotak abu: "Proses sistem — tanpa layar: …" (abu lebih terang; proses sistem/AI/cron, notifikasi latar, aktivitas di luar aplikasi; 26 langkah) atau "Belum ada layar: <alur>" (layar aplikasi yang menunggu capture tim; 50 langkah). Satu baris alur dengan satu salinan tidak memiliki tombol "Lanjut ▶" (Figma menolak tautan ke diri sendiri).

| UC | alur | langkah | frame sumber | catatan |
|---|---|---|---|---|
| UC-01 | Normal flow | 1 Masuk SSO, buka Tanya HaloSIS | LG-00 Login (1440px) 99:1500 | |
| UC-01 | Normal flow | 2 Sapaan, kartu, contoh | PG-00 Tanya HaloSIS (kosong) 153:3533 | |
| UC-01 | Normal flow | 3 Ketik kendala, Kirim | PG-00 Tanya HaloSIS (kosong) 153:3533 | |
| UC-01 | Normal flow | 4 Catat & cari (UC-02) | – | Proses sistem |
| UC-01 | Normal flow | 5 Jawaban + sumber | PG-S20 Chat: jawaban ditemukan 154:3533 | |
| UC-01 | Normal flow | 6 Mencoba solusi | – | Proses sistem |
| UC-01 | Normal flow | 7 Klik Masalah terselesaikan | PG-S20 Chat: jawaban ditemukan 154:3533 | |
| UC-01 | Normal flow | 8 Rating bintang | PG-S23 Chat: rating bintang 157:3533 | |
| UC-01 | Normal flow | 9 Terima kasih, berakhir | – | Belum ada layar |
| UC-01 | 1a Chat dimatikan | 1a Asisten Sedang Tidak Tersedia | – | Belum ada layar |
| UC-01 | 1b Tanpa hak asisten | 1b Asisten tidak tersedia untuk akun | – | Belum ada layar |
| UC-01 | 2a Kartu Laporkan masalah | 2a Fokus kotak + sapaan asisten | PG-R08 Chat: klik Laporkan masalah 317:6217 | |
| UC-01 | 2b Kartu Ajukan permintaan | 2b Form Ajukan Permintaan | PG-R04 Form Ajukan Permintaan 253:4650 | |
| UC-01 | 3a Pesan kosong | 3a Silakan ketik pertanyaan | – | Belum ada layar |
| UC-01 | 3b Percakapan terlalu panjang | 3b Buat laporan atau percakapan baru | – | Belum ada layar |
| UC-01 | 3c Percakapan sudah berakhir | 3c Klik Percakapan baru | – | Belum ada layar |
| UC-01 | 4a AI gagal menjawab | 4a Pencarian kata kunci | – | Proses sistem |
| UC-01 | 4b Permintaan server gagal | 4b Asisten tidak tersedia + kartu laporan | – | Belum ada layar |
| UC-01 | 5a Solusi tidak ditemukan | 5a Tawaran laporan | PG-S22 Chat: tidak ditemukan + tawaran laporan 156:3533 | |
| UC-01 | 5a Solusi tidak ditemukan | S-1 Form laporan dari chat | PG-S24 Chat: form laporan dari chat 158:3533 | |
| UC-01 | 5a Solusi tidak ditemukan | S-1 Laporan sudah dibuat | – | Belum ada layar |
| UC-01 | 5a Tidak, terima kasih | 5a Tawaran laporan | PG-S22 Chat: tidak ditemukan + tawaran laporan 156:3533 | |
| UC-01 | 5a Tidak, terima kasih | 5a Kartu ditutup | PG-R06 Chat: setelah Tidak, terima kasih (tidak ditemukan) 249:4650 | |
| UC-01 | 5b Keyakinan sedang | 5b Pilihan artikel | PG-S21 Chat: mode pilihan artikel 155:3533 | |
| UC-01 | 5c Di luar layanan TI | 5c Diarahkan ke unit terkait | – | Belum ada layar |
| UC-01 | 7a Belum terselesaikan | 7a Kartu Masalah belum selesai? | PG-R07 Chat: pilihan artikel + kartu belum selesai 250:4650 | |
| UC-01 | 7a Belum terselesaikan | S-1 Form laporan | PG-S24 Chat: form laporan dari chat 158:3533 | |
| UC-01 | 7a Belum terselesaikan | S-1 Laporan sudah dibuat | – | Belum ada layar |
| UC-01 | 7b Tidak, terima kasih (7a) | 7b Klik Tidak, terima kasih | PG-R07 Chat: pilihan artikel + kartu belum selesai 250:4650 | |
| UC-01 | 7b Tidak, terima kasih (7a) | 7b Percakapan diakhiri | – | Belum ada layar |
| UC-02 | Normal flow | 1 Pegawai kirim pertanyaan | PG-00 Tanya HaloSIS (kosong) 153:3533 | |
| UC-02 | Normal flow | 2 Samarkan data | – | Proses sistem |
| UC-02 | Normal flow | 3 Embedding + banding indeks | – | Proses sistem |
| UC-02 | Normal flow | 4 Skor & urut | – | Proses sistem |
| UC-02 | Normal flow | 5 Susun jawaban | – | Proses sistem |
| UC-02 | Normal flow | 6 Hasil ke Tanya HaloSIS | PG-S20 Chat: jawaban ditemukan 154:3533 | |
| UC-02 | S-1 Pencarian petugas | S-1 Cari, klik Cari | TT-05 Cari pengetahuan 147:4372 | |
| UC-02 | S-1 Pencarian petugas | S-1 Hasil + Relevansi | TT-R5 Cari pengetahuan (hasil) 266:4825 | |
| UC-02 | 3a Indeks/layanan mati | 3a Hasil kata kunci + pemberitahuan | – | Belum ada layar |
| UC-02 | 5a Tidak ada hasil | 5a Tidak ditemukan / maks. 3 artikel | – | Belum ada layar |
| UC-02 | S-1a Hasil kosong | S-1a Pengetahuan tidak ditemukan | – | Belum ada layar |
| UC-02 | S-1b Umpan balik petugas | S-1b Terima kasih, umpan balik tersimpan | – | Belum ada layar |
| UC-03 | Normal flow | 1 Menu Buat laporan | PG-03 Buat laporan (Katalog layanan) 133:2 | |
| UC-03 | Normal flow | 2 Pilih Laporkan Masalah/Ajukan Permintaan | PG-03 Buat laporan (Katalog layanan) 133:2 | |
| UC-03 | Normal flow | 3 Isi Judul, Deskripsi, dst. | PG-04 Form Laporkan masalah 139:2 | |
| UC-03 | Normal flow | 4 Klik Kirim | PG-04 Form Laporkan masalah 139:2 | |
| UC-03 | Normal flow | 5 Tiket Baru terbuka | PG-R03 Tiket terkirim: halaman tiket 248:4650 | |
| UC-03 | Normal flow | 6 SLA, notifikasi, saran triase | – | Proses sistem |
| UC-03 | Normal flow | 7 Antrean validasi | 06 Antrean validasi (rina) 31:2 | |
| UC-03 | 1a Tiket dari konsultasi (S-1) | S-1 Tawaran laporan | PG-S22 Chat: tidak ditemukan + tawaran laporan 156:3533 | |
| UC-03 | 1a Tiket dari konsultasi (S-1) | S-1 Judul laporan + ringkasan | PG-S24 Chat: form laporan dari chat 158:3533 | |
| UC-03 | 1a Tiket dari konsultasi (S-1) | S-1 Laporan #… dibuat | – | Belum ada layar |
| UC-03 | 1b Operator catat laporan | 1b Semua tiket, Tambah | OP-02 Semua tiket 135:2 | |
| UC-03 | 1b Operator catat laporan | 1b Form Tambah (Pemohon, Sumber) | – | Belum ada layar |
| UC-03 | 5a Kolom wajib kosong | 5a Judul wajib diisi | PG-R02 Galat Judul wajib diisi 247:4650 | |
| UC-03 | 5b Tanpa hak membuat tiket | 5b Anda tidak berhak membuat tiket | – | Belum ada layar |
| UC-03 | 6a Saran triase gagal | 6a Belum ada saran AI + Buat saran AI | – | Belum ada layar |
| UC-04 | Normal flow | 1 Kirim ke AI Engine | – | Proses sistem |
| UC-04 | Normal flow | 2 Prediksi 3 tim | – | Proses sistem |
| UC-04 | Normal flow | 3 Petakan Grup/Kategori | – | Proses sistem |
| UC-04 | Normal flow | 4 Urgensi, Dampak, Prioritas | – | Proses sistem |
| UC-04 | Normal flow | 5 Keyakinan mencapai ambang | 07 Detail tiket + panel Saran AI 32:2 | |
| UC-04 | Normal flow | 6 Panel Saran AI Menunggu keputusan | 07 Detail tiket + panel Saran AI 32:2 | |
| UC-04 | 1a AI tidak tersedia | 1a Dicoba ulang tiap 15 menit | – | Proses sistem |
| UC-04 | 1b Mode demo | 1b Saran dari aturan kata kunci | – | Proses sistem |
| UC-04 | 5a Keyakinan di antara ambang | 5a Pilih dari 3 kandidat | OP-03 Panel Saran AI "Pilih dari 3 kandidat" 46:289 | |
| UC-04 | 5b Keyakinan di bawah ambang rendah | 5b Perlu penilaian manual | OP-04 Panel "Perlu penilaian manual" 46:390 | |
| UC-04 | 5c Model belum lolos / Lainnya | 5c Perlu penilaian manual + peringatan model | OP-04 Panel "Perlu penilaian manual" 46:390 | |
| UC-05 | Normal flow | 1 Menu Antrean validasi | 06 Antrean validasi (rina) 31:2 | |
| UC-05 | Normal flow | 2 Daftar tiket Baru | 06 Antrean validasi (rina) 31:2 | |
| UC-05 | Normal flow | 3 Klik satu tiket | 06 Antrean validasi (rina) 31:2 | |
| UC-05 | Normal flow | 4 Detail + panel Saran AI | 07 Detail tiket + panel Saran AI 32:2 | |
| UC-05 | Normal flow | 5 Klik Terima | 07 Detail tiket + panel Saran AI 32:2 | |
| UC-05 | Normal flow | 6 Saran diterapkan | 07-R1 Terima saran → diterapkan 195:3708 | |
| UC-05 | Normal flow | 7 Status Sedang proses | 07-R1 Terima saran → diterapkan 195:3708 | |
| UC-05 | S-1 Ubah (5a) | S-1 Ubah + Alasan | 08 Modal Ubah 33:2 | |
| UC-05 | S-1 Ubah (5a) | S-1 Nilai diterapkan | 08-R1 Terapkan perubahan 197:3708 | |
| UC-05 | S-1 Ubah (5a) | 7 Status Sedang proses | 07-R1 Terima saran → diterapkan 195:3708 | |
| UC-05 | S-2 Tolak (5b) | S-2 Tolak & triase manual | 07-R2 Tolak → form alasan 185:3708 | |
| UC-05 | S-2 Tolak (5b) | S-2 Triase manual | 07-R3 Tolak saran → triase manual 196:3708 | |
| UC-05 | 3a Tanpa hak memutuskan | 3a Menunggu keputusan Operator | – | Belum ada layar |
| UC-05 | 3b Tiket tanpa saran | 3b Buat saran AI | – | Belum ada layar |
| UC-05 | 5c Selesai di level 1 | 5c Balas, Tambah solusi, Dipecahkan | – | Belum ada layar |
| UC-05 | 5d Saran sudah diputuskan | 5d Saran ini sudah diputuskan | – | Belum ada layar |
| UC-05 | S-1a Nilai sama | S-1a Gunakan tombol Terima | – | Belum ada layar |
| UC-05 | S-1b Alasan < 5 karakter | S-1b Alasan wajib minimal 5 karakter | – | Belum ada layar |
| UC-06 | Normal flow | 1 Menu Tiket saya & tim | 09 Tiket saya & tim (andi) 35:2 | |
| UC-06 | Normal flow | 2 Buka tiket, panel hanya-baca | TT-01 Panel hanya-baca + Kembalikan ke Operator 134:2 | |
| UC-06 | Normal flow | 3 Tambahkan saya + Simpan | – | Belum ada layar |
| UC-06 | Normal flow | 4 Cari pengetahuan | TT-05 Cari pengetahuan 147:4372 | |
| UC-06 | Normal flow | 5 Tangani, Balas | 10 Detail tiket + tambah solusi 36:2 | |
| UC-06 | Normal flow | 6 Balas ▾, Tambah solusi | 10 Detail tiket + tambah solusi 36:2 | |
| UC-06 | Normal flow | 7 Dipecahkan, SLA, kandidat | – | Belum ada layar |
| UC-06 | S-1 / 5a Minta informasi | S-1 Balas + status Tertunda | – | Belum ada layar |
| UC-06 | 2a Penugasan tidak sesuai | 2a Klik Kembalikan ke Operator | TT-01 Panel hanya-baca + Kembalikan ke Operator 134:2 | |
| UC-06 | 2a Penugasan tidak sesuai | 2a Isi alasan, Kembalikan | 10-R1 Kembalikan → form alasan 188:3708 | |
| UC-06 | 2a Penugasan tidak sesuai | 2a Dikembalikan ke antrean | TT-R1 Kembalikan → antrean Operator 262:4825 | |
| UC-06 | 2b Bukan tim ditugaskan | 2b Hanya tim ditugaskan | – | Belum ada layar |
| UC-06 | 4a Layanan AI mati | 4a Hanya hasil kata kunci | – | Belum ada layar |
| UC-06 | 7a Pegawai menolak solusi | 7a Dibuka kembali | 11-R2 Tolak solusi → dibuka kembali 191:3708 | |
| UC-07 | Normal flow | 1 Menu Laporan saya | PG-06 Laporan saya 159:3533 | |
| UC-07 | Normal flow | 2 Daftar + Ditangani oleh | PG-06 Laporan saya 159:3533 | |
| UC-07 | Normal flow | 3 Klik tiket Dipecahkan | PG-06 Laporan saya 159:3533 | |
| UC-07 | Normal flow | 4 Baca solusi | 11 Detail laporan + Setujui (budi) 38:2 | |
| UC-07 | Normal flow | 5 Klik Setujui | 11 Detail laporan + Setujui (budi) 38:2 | |
| UC-07 | Normal flow | 6 Status Ditutup | 11-R1 Setujui → Ditutup + survei 190:3708 | |
| UC-07 | Normal flow | 7 Riwayat, notifikasi | – | Proses sistem |
| UC-07 | Normal flow | 8 Tab Kepuasan, survei | 11-R1 Setujui → Ditutup + survei 190:3708 | |
| UC-07 | 3a Belum Dipecahkan | 3a Detail tiket, Balas | PG-R05 Detail tiket pegawai 254:4650 | |
| UC-07 | 3a Belum Dipecahkan | 3a Keterangan terkirim | – | Belum ada layar |
| UC-07 | 5a Masalah belum selesai | 5a Komentar + Tolak | 11 Detail laporan + Setujui (budi) 38:2 | |
| UC-07 | 5a Masalah belum selesai | 5a Kembali ke proses | 11-R2 Tolak solusi → dibuka kembali 191:3708 | |
| UC-07 | 5b Tolak tanpa alasan | 5b Alasan wajib diisi | – | Belum ada layar |
| UC-07 | 5c Pegawai tidak merespons | 5c Siap ditutup, Tutup | OP-09 Siap ditutup 136:2 | |
| UC-07 | 5c Pegawai tidak merespons | 5c Tiket Ditutup | OP-S19 Siap ditutup sesudah (3 tiket Ditutup) 90:554 | |
| UC-08 | Normal flow | 1 Tugas terjadwal | – | Proses sistem |
| UC-08 | Normal flow | 2 Kelompokkan Insiden | – | Proses sistem |
| UC-08 | Normal flow | 3 Notifikasi SLA | – | Proses sistem |
| UC-08 | Normal flow | 4 Masalah Pola insiden dibuat | – | Proses sistem |
| UC-08 | Normal flow | 5 Dasbor banner Pola insiden | – | Belum ada layar |
| UC-08 | Normal flow | 6 Kinerja AI, Terapkan | MJ-02 Kinerja AI (filter tim/kategori) 56:2 | |
| UC-08 | Normal flow | 7 Buka Masalah terkait | OP-R3 Pola insiden → Masalah 209:4340 | |
| UC-08 | Normal flow | 8 Riwayat dicatat | – | Proses sistem |
| UC-08 | 2a AI gagal | 2a Pengelompokan cadangan | – | Proses sistem |
| UC-08 | 3a Tidak ada tiket berisiko | 3a Tidak ada peringatan | – | Proses sistem |
| UC-08 | 4a Tidak ada kelompok | 4a Tidak ada Masalah baru | – | Proses sistem |
| UC-08 | 4b Pola sudah ber-Masalah | 4b Hanya menautkan tiket | – | Proses sistem |
| UC-08 | 6a Tanpa hak Kinerja AI | 6a Akses ditolak | – | Belum ada layar |
| UC-08 | 7a Tidak perlu tindak lanjut | 7a Use case berakhir | – | Proses sistem |
| UC-09 | Normal flow | 1 Menu Kandidat pengetahuan | KM-01 Kandidat pengetahuan 50:2 | |
| UC-09 | Normal flow | 2 Halaman + tab | KM-01 Kandidat pengetahuan 50:2 | |
| UC-09 | Normal flow | 3 Baca kartu | KM-01 Kandidat pengetahuan 50:2 | |
| UC-09 | Normal flow | 4 Klik Jadikan artikel | KM-01 Kandidat pengetahuan 50:2 | |
| UC-09 | Normal flow | 5 Draf dibuat | KM-R3 Jadikan artikel → editor draf 297:5257 | |
| UC-09 | Normal flow | 6 Sunting, Simpan | KM-R3 Jadikan artikel → editor draf 297:5257 | |
| UC-09 | Normal flow | 7 Tambahkan ke FAQ | – | Belum ada layar |
| UC-09 | Normal flow | 8 Indeks diperbarui | KM-R3 Jadikan artikel → editor draf 297:5257 | |
| UC-09 | Normal flow | 9 Revisi dicatat | – | Proses sistem |
| UC-09 | S-1 Perbarui/arsipkan | S-1 Perlu ditinjau, Simpan tanggal | KM-02 Kandidat · tab Perlu ditinjau 52:2 | |
| UC-09 | S-1 Perbarui/arsipkan | S-1 Tanggal tersimpan | – | Belum ada layar |
| UC-09 | S-2 Tulis artikel baru | S-2 Tulis artikel | KM-01 Kandidat pengetahuan 50:2 | |
| UC-09 | S-2 Tulis artikel baru | S-2 Tambah artikel | KM-04 Tulis artikel 80:2 | |
| UC-09 | S-2 Tulis artikel baru | S-2 Draf tersimpan | – | Belum ada layar |
| UC-09 | 1a AI mati | 1a Pemberitahuan layanan AI | – | Belum ada layar |
| UC-09 | 1b Hanya melihat | 1b Tombol tersembunyi | – | Belum ada layar |
| UC-09 | 3a Tidak ada kandidat | 3a Belum ada kandidat di sini | – | Belum ada layar |
| UC-09 | 4a Kandidat tidak layak | 4a Abaikan + alasan | KM-01 Kandidat pengetahuan 50:2 | |
| UC-09 | 4a Kandidat tidak layak | 4a Diabaikan | KM-R2 Tab Diabaikan 296:5257 | |
| UC-09 | 4b Sudah diputuskan | 4b Kandidat sudah diputuskan | – | Belum ada layar |
| UC-09 | 5a Draf LLM | 5a Disusun AI, wajib ditinjau | – | Belum ada layar |
| UC-09 | 7a Belum layak terbit | 7a Item belum diterbitkan | – | Belum ada layar |
| UC-09 | 8a Indeks gagal | 8a Gagal memperbarui indeks | – | Belum ada layar |
| UC-09 | S-1a Tanggal tidak valid | S-1a Pilih tanggal setelah hari ini | – | Belum ada layar |
| UC-10 | Normal flow | 1 Menu Pengaturan AI | AD-01 Panel administrasi 58:2 | |
| UC-10 | Normal flow | 2 Konfirmasi diperlukan | AD-R1 Verifikasi ulang sebelum Pengaturan AI 304:5677 | |
| UC-10 | Normal flow | 3 Klik Verifikasi | AD-R1 Verifikasi ulang sebelum Pengaturan AI 304:5677 | |
| UC-10 | Normal flow | 4 Formulir | AD-02 Pengaturan AI (+ pratinjau dampak) 69:2 | |
| UC-10 | Normal flow | 5 Ubah nilai | AD-02 Pengaturan AI (+ pratinjau dampak) 69:2 | |
| UC-10 | Normal flow | 6 Pratinjau dampak | AD-02 Pengaturan AI (+ pratinjau dampak) 69:2 | |
| UC-10 | Normal flow | 7 Simpan | AD-02 Pengaturan AI (+ pratinjau dampak) 69:2 | |
| UC-10 | Normal flow | 8 Berhasil disimpan | – | Belum ada layar |
| UC-10 | Normal flow | 9 Dicatat + Catatan Beranda | AD-R3 Beranda (dimas) 312:5810 | |
| UC-10 | S-1 Mengubah SLA | S-1 Pratinjau SLA | AD-03 Pratinjau SLA 74:2 | |
| UC-10 | S-1 Mengubah SLA | S-1 Kebijakan SLA | AD-05 Kebijakan SLA 62:2 | |
| UC-10 | S-2 Objek lain | S-2 Katalog layanan | AD-04 Katalog layanan 61:2 | |
| UC-10 | 1a Tidak berhak | 1a Akses ditolak | – | Belum ada layar |
| UC-10 | 6a Pratinjau tanpa pilihan | 6a Pilih SLA & target | – | Belum ada layar |
| UC-10 | 8a URL tidak valid | 8a URL harus http(s) | – | Belum ada layar |
| UC-10 | 8b API key kosong | 8b Nilai lama dipakai | – | Belum ada layar |

Catatan umum: UC-08 langkah 5 (banner "Pola insiden terdeteksi") hanya tampak di AD-01 (Administrator), bukan dasbor rina (OP-01) → tetap "Belum ada layar" (diverifikasi ulang 13 Nov). UC-08 langkah 6 memakai MJ-02 (satu-satunya yang memuat Terapkan). UC-05 5c memakai abu karena layar "10" milik Tim Teknis. Elemen tebal yang cocok teks persis disambung ke salinan berikutnya; "Balas"/"Tambah solusi" (UC-06) dan "Kirim" (UC-01 langkah 3, ikon) tidak ditemukan sebagai teks, "Kembalikan ke Operator" langkah 2 hanya cocok varian "(salah tim)". Di UC-09 label seperti Jadikan artikel/Abaikan cocok di semua kartu kandidat (sengaja, per pola baris).
