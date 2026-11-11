# TUGAS: Revisi masukan tim 11 Nov (branch `dev`) — batch TERAKHIR (setelah ini hanya perbaikan bug)

Dikerjakan per sesi. Setiap sesi HANYA mengerjakan bagian yang diminta di prompt sesi.

## ATURAN (WAJIB)
- Branch `dev`. Sebelum mulai: `git pull --rebase origin dev`. JANGAN ubah inti GLPI. JANGAN `docker compose down -v`.
- Commit & push HANYA di akhir sesi, setelah uji lulus: `git add` file yang diubah saja (JANGAN `logs/`, `data/`,
  `backup/`, `.env`, `*.xlsx`, `ai/models/`, `ai/index/`), pesan `Revisi 11 Nov sesi <N>: <ringkas>`, lalu
  `git push origin dev`. Bila push ditolak: `git pull --rebase origin dev`, uji ulang singkat, push lagi.
- JANGAN ubah/hapus data DB lewat SQL tanpa bertanya. Catat jumlah baris tabel yang disentuh sebelum mulai,
  kembalikan data uji yang dibuat. Data `[DEMO]` harus utuh setelah tes.
- Output panjang ke `logs/<nama>.log`, tampilkan `tail -20`. Screenshot maks. 3 per sesi. Laporan chat maks. 8 baris.
- Teks UI Bahasa Indonesia baku; perbarui `id_ID.po/.mo`; `bin/console cache:clear` setelah ubah teks/template.
- Bila sebuah butir tidak bisa tanpa ubah inti GLPI: BERHENTI untuk butir itu, catat alasan + file:baris, lanjut butir lain.
- Akhir setiap sesi: `tests/e2e/fitur_penutup.js` & `tests/e2e/alur_alternatif.js` lulus (assert hanya boleh
  diubah untuk perilaku yang memang diubah di sesi itu, sebutkan).
- Sebutkan teks PERSIS (msgstr) setiap teks UI baru/diubah di laporan (dipakai untuk T4).

---

## SESI 1 — Dasbor, Statistik, Jenis tiket

**1.1 Dasbor.** Matikan mode "data demonstrasi" dasbor GLPI (angka seperti "114.7K Perangkat lunak" bukan data kita).
Semua profil staf (Operator, Tim Teknis, Knowledge Manager, Manajemen, Administrator) hanya melihat dasbor
**Assistance** (bawaan); Central & Assets tidak ditampilkan. Cari tahu kenapa sri masih melihat Central/Assets
padahal `setup_dasbor_manajemen.py` sudah jalan; perbaiki di skrip setup (idempoten). Verifikasi per akun
(rina, andi, lina, sri, dimas) setelah logout/login.

**1.2 Statistik.** Terjemahkan teks Inggris di Statistik ("Global", "By ticket", "By hardware characteristics", dsb.)
lewat mekanisme terjemahan lokal yang sama dengan 47 teks sebelumnya (`plugins/halosis/locales/core/id_ID.po`).
Opsi perangkat keras tetap ada (keputusan: menyembunyikannya mematikan Statistik tiket).

**1.3 Jenis tiket.** Pastikan form **Laporkan Masalah → Insiden** dan **Ajukan Permintaan → Permintaan** (cek tiket
2741/2742). Tambahkan kolom **Jenis** di daftar tiket Operator, Tim Teknis, dan "Laporan saya" pegawai
(`setup_list_columns.py`). Status tetap bawaan GLPI (Dipecahkan → Ditutup untuk keduanya; tidak ada status "Dipenuhi").

---

## SESI 2 — Chat & keterlacakan (UC-01, UC-07)

**2.1 Mode "pilihan" (UC-01 5b).** Kartu laporan langsung diganti dengan "Apakah jawaban ini membantu?" +
**Masalah terselesaikan** / **Belum terselesaikan**, sama seperti jawaban biasa (terselesaikan → rating;
belum → kartu 7a dengan tawaran laporan + petunjuk ketik ulang). Kartu laporan langsung TETAP untuk mode
tidak-ditemukan (5a). Kalimat pengantar mode pilihan boleh disesuaikan agar tidak menyuruh klik "Buat laporan".

**2.2 Widget chat di halaman FAQ.** Saat pegawai membuka artikel dari chat (tautan sumber / pilihan 5b) dan
berpindah ke Tanya Jawab (FAQ), widget chat kanan bawah aktif dan **melanjutkan sesi yang sama** (riwayat pesan,
tombol Masalah terselesaikan / Belum terselesaikan, rating) — bukan sesi baru. Sesi baru hanya dibuat lewat tombol
"Percakapan baru". Alur tetap UC-01 langkah 6–8, hanya lokasi tombolnya. Cek dulu perilaku sekarang (file:baris)
sebelum mengubah.

**2.3 Keterlacakan untuk pelapor (UC-07).** Di "Laporan saya" dan detail tiket pegawai, tampilkan **posisi tiket**
dengan bahasa awam, mis. kolom "Ditangani oleh": "Menunggu validasi Operator" (status Baru, belum ditugaskan) /
nama **grup** tim yang ditugaskan / "Menunggu tanggapan Anda" (Tertunda) / "Selesai, menunggu konfirmasi Anda"
(Dipecahkan). Tampilkan nama grup saja, BUKAN nama petugas perorangan. Lewat konfigurasi kolom / plugin.

**2.4 (HANYA BACA)** Di `Stats.php`, percakapan UC-01 7b ("Belum terselesaikan" → "Tidak, terima kasih", tanpa
rating, "Berakhir tanpa laporan") dihitung sebagai apa ("Terbantu tanpa tiket"? rating?). Bila salah dihitung
terbantu, usulkan perbaikan minimal — JANGAN ubah dulu.

---

## SESI 3 — Penutup
- Uji kedua file e2e, `cache:clear`, lalu `scripts/demo_snapshot.sh simpan` dan hapus snapshot lama
  `demo-20261110-165854`. Laporkan nama snapshot baru.
- Ringkasan maks. 8 baris: per butir (selesai / tidak bisa + alasan), teks UI persis yang berubah, hasil uji, snapshot.

---

## Prompt per sesi (jalankan `/clear` dulu, model Sonnet)
- Sesi 1: `Baca docs/tugas_revisi_11nov.md (ATURAN + SESI 1 saja). Kerjakan HANYA SESI 1, lalu berhenti.`
- Sesi 2: `Baca docs/tugas_revisi_11nov.md (ATURAN + SESI 2 saja). Kerjakan HANYA SESI 2, lalu berhenti.`
- Sesi 3: `Baca docs/tugas_revisi_11nov.md (ATURAN + SESI 3 saja). Kerjakan HANYA SESI 3, lalu berhenti.`

Catatan untuk dokumen (dikerjakan terpisah setelah semua sesi): T4 UC-01 5b (kartu baru), UC-01 Implementasi
("widget chat juga dapat dibuka dari halaman FAQ dan melanjutkan sesi yang sama"), UC-07 (kolom Ditangani oleh,
kolom Jenis); Figma (dasbor tiap peran, PG-S21, Laporan saya, daftar tiket) — Sabtu.
