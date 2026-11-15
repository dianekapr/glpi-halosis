# TUGAS: Revisi 15 Nov (branch `dev`)

Aturan sama dengan `docs/tugas_revisi_11nov.md` (ATURAN): `git pull --rebase origin dev` dulu; tanpa ubah inti GLPI (NFR-10);
tanpa SQL tanpa bertanya; data uji dikembalikan, `[DEMO]` utuh; hemat token (grep/sed, e2e sekali di akhir);
laporan maks. 8 baris; sebutkan teks UI baru PERSIS (msgstr).

- **E1 Kueri tanpa makna (UC-02 S-1a, /chat 5a).** Kueri seperti "<<>><<>><<>>", satu huruf, atau hanya angka/simbol mendapat
  banyak artikel berskor tinggi. Tambah penjaga SEBELUM pencarian semantik di halosis-ai (berlaku /cari dan /chat): bila kueri
  tidak memuat minimal satu kata huruf ≥3 karakter → hasil kosong (Cari pengetahuan: "Pengetahuan tidak ditemukan. Silakan coba
  kata lain."; chat: alur 5a). Ambang jangan diubah. Ukur sebelum & sesudah dengan `replikasi_poc.py --bagian retrieval` dan
  `kalibrasi_ambang.py`; laporkan bila memburuk. Tambah tes pytest.
- **E2 "Tidak membantu" (UC-02 S-1b).** Peringkat TIDAK diubah (umpan balik untuk evaluasi/kurasi KM). Perbaiki tampilan saja:
  setelah diklik, tombol jadi penanda "Ditandai tidak membantu" / "Ditandai membantu" pada hasil itu dan tidak bisa diklik dua
  kali. Pesan "Terima kasih, umpan balik Anda tersimpan." tetap.
- **E3 Chat dimatikan (UC-01 1a).** Saat sakelar "Asisten layanan mandiri untuk pegawai" mati, menu Tanya HaloSIS TETAP tampil;
  halaman menampilkan "Asisten Sedang Tidak Tersedia", "Laporkan kendala Anda dan petugas akan membantu.", tombol "Buat laporan",
  tautan "Tanya Jawab (FAQ)". Widget chat di halaman lain menampilkan pemberitahuan yang sama (tidak hilang), bukan error.
- **E4 Masking langsung (NFR-06).** Pesan berisi "password: xxx", NIP, email, nomor HP baru tersamar setelah refresh. Setelah
  server menyimpan pesan, gelembung pesan pengguna langsung diganti teks tersamar dari server. Tambah tes e2e singkat.
- **E5 Cek saja (HANYA BACA, laporkan file:baris).** (a) tombol "Terapkan perubahan" dan "Tolak & triase manual" UC-05 tidak aktif
  sampai alasan ≥5 karakter? (b) tombol "Kirim" chat tidak aktif saat kotak kosong/hanya spasi? (c) kata kunci 5c untuk
  Kepegawaian/Keuangan/Umum? (d) anggota tim lain memang tidak bisa membuka tiket tim lain (UC-06)?
- **E6 Akhir.** `tests/e2e/fitur_penutup.js` dan `tests/e2e/alur_alternatif.js` lulus; `scripts/demo_snapshot.sh` simpan (hapus
  snapshot lama); commit "Revisi 15 Nov: guard kueri, umpan balik, chat mati, masking langsung" + push origin dev. Laporkan nama
  snapshot.
