# TUGAS: Revisi masukan tim 11–13 Nov (branch `dev`) — batch TERAKHIR (setelah ini hanya perbaikan bug)

Dikerjakan per sesi, urut prioritas (A paling penting). Setiap sesi HANYA mengerjakan sesi yang diminta.
Limit token terbatas: kerjakan efisien, jangan menjelajah kode di luar yang perlu.

## ATURAN (WAJIB)
- Branch dev. JANGAN git add/commit/push. JANGAN ubah inti GLPI. JANGAN docker compose down -v.
- JANGAN ubah/hapus data DB lewat SQL tanpa bertanya. Catat jumlah baris tabel yang disentuh, kembalikan data uji.
  Data `[DEMO]` harus utuh setelah tes.
- Hemat token: baca kode dengan grep/sed (jangan baca file >300 baris utuh), jangan ulangi perintah gagal >2×, uji e2e
  cukup SEKALI di akhir sesi.
- Output panjang ke `logs/<nama>.log`, tampilkan `tail -20`. Tanpa screenshot kecuali perlu (maks. 2). Laporan maks. 8 baris.
- Teks UI Bahasa Indonesia baku; perbarui `id_ID.po/.mo`; `bin/console cache:clear` setelah ubah teks/template.
- Butir yang butuh ubah inti GLPI: lewati, catat alasan + file:baris.
- Akhir sesi: `tests/e2e/fitur_penutup.js` & `tests/e2e/alur_alternatif.js` lulus (assert hanya diubah untuk perilaku
  yang memang diubah, sebutkan).
- Sebutkan teks PERSIS (msgstr) setiap teks UI baru/diubah (dipakai untuk T4).

---

## SESI A — Dasbor, Jenis, Statistik, cek hak (prioritas tertinggi)
- **A1 Dasbor.** Matikan mode "data demonstrasi" dasbor GLPI (angka "114.7K"). Semua profil staf (Operator, Tim Teknis,
  Knowledge Manager, Manajemen, Administrator) hanya melihat dasbor **Assistance**; Central & Assets disembunyikan.
  Cari kenapa sri masih melihat Central/Assets meski `setup_dasbor_manajemen.py` sudah jalan; perbaiki di skrip setup
  (idempoten, untuk semua profil staf). Verifikasi per akun (rina, andi, lina, sri, dimas) setelah login ulang.
- **A2 Jenis.** Pastikan form Laporkan Masalah → Insiden, Ajukan Permintaan → Permintaan (cek tiket 2741/2742).
  Tambah kolom **Jenis** di daftar tiket Operator, Tim Teknis, dan "Laporan saya" (`setup_list_columns.py`).
  Status tetap bawaan GLPI.
- **A3 Statistik.** Terjemahkan sisa teks Inggris Statistik ("Global", "By ticket", "By hardware characteristics", dll.)
  di `plugins/halosis/locales/core/id_ID.po`.
- **A4 Cek hak (perbaiki bila salah):**
  - UC-06 2b: tombol **Kembalikan ke Operator** tidak tampil untuk akun tim yang tidak ditugaskan (mis. dedi pada
    tiket tim andi); server juga menolak.
  - UC-05 3a: tombol **Terima/Ubah/Tolak** tidak tampil untuk akun tanpa hak memutuskan; server menolak.
- **A5 Flash message UC-05.** Setelah Terima/Ubah/Tolak (dan setelah solusi 5c), tiket hilang dari daftar tersaring
  "Menunggu keputusan" tanpa penjelasan. Tampilkan pesan yang jelas, mis. "Keputusan disimpan. Tiket #<id>
  dipindahkan dari antrean validasi." dengan tautan ke tiket.
- **A6 Panel SLA (TTR/TTO)** di form tiket: rapikan kotak yang berantakan (teks terpotong, ikon bertabrakan) lewat CSS
  plugin saja (text-wrap, kotak menyesuaikan isi).

## SESI B — Chat 5b & keterlacakan pelapor
- **B1 Mode "pilihan" (UC-01 5b).** Kartu laporan langsung diganti "Apakah jawaban ini membantu?" + **Masalah
  terselesaikan** / **Belum terselesaikan** (terselesaikan → rating; belum → kartu 7a). Kartu laporan langsung tetap
  hanya untuk tidak-ditemukan (5a). Kalimat pengantar mode pilihan disesuaikan (jangan menyuruh klik "Buat laporan").
- **B2 Ditangani oleh (UC-07).** Di "Laporan saya" dan detail tiket pegawai, kolom/info **Ditangani oleh**:
  "Menunggu validasi Operator" (Baru, belum ditugaskan) / nama **grup** tim (Diproses) / "Menunggu tanggapan Anda"
  (Tertunda) / "Selesai, menunggu konfirmasi Anda" (Dipecahkan) / "Ditutup". Nama grup saja, bukan nama orang.

## SESI C — Akun demo khusus & panduan aktif-nonaktif
- **C1 Akun demo** (lewat API/skrip setup idempoten, profil turunan; kata sandi `halosis`; nama fiktif; masuk
  snapshot): `pegawai_tanpa_asisten` (Pegawai tanpa hak asisten → UC-01 1b), `pegawai_tanpa_tiket` (Pegawai tanpa hak
  membuat tiket → UC-03 5b), `operator_lihat` (Operator tanpa hak memutuskan saran → UC-05 3a). Pastikan akun demo
  lain tidak berubah. Bila butuh Keycloak, tambah ke realm demo juga.
- **C2 Panduan.** Tambahkan ke `reports/cara_memicu_alur_alternatif.md` bagian "Aktif/nonaktif fitur": mematikan fitur
  chat (UC-01 1a), mematikan layanan AI (UC-01 4a/4b, UC-06 4a), mematikan triase (UC-03 6a, UC-05 3b — sebutkan
  sakelar di Pengaturan AI bila ada, atau cara lain), beserta cara mengembalikan; dan perbarui baris UC-01 1b,
  UC-03 5b, UC-05 3a agar memakai akun C1.

## SESI D — Opsional (hanya bila limit masih ada)
- **D1 Widget chat di halaman FAQ** melanjutkan sesi yang sama (riwayat, tombol terselesaikan, rating); sesi baru
  hanya lewat "Percakapan baru" atau refresh. Cek perilaku sekarang dulu (file:baris).
- (Dibatalkan: "UI/UX lain yang belum pas" dan "alur kurang ramah pengguna baru di tiap peran" — terlalu umum;
  pengguna baru dibantu lewat `reports/panduan_peran.md` + Panduan, tanpa ubah kode. Laporkan sebagai bug spesifik bila ada.)

## Penutup (akhir sesi terakhir yang dijalankan)
`scripts/demo_snapshot.sh simpan`, hapus snapshot lama `demo-20261110-165854`, sebutkan nama snapshot baru.

## Prompt per sesi (`/clear` dulu, model Sonnet)
`Baca docs/tugas_revisi_11nov.md (ATURAN + SESI <X> saja). Kerjakan HANYA SESI <X>, jangan commit, lalu berhenti.`
