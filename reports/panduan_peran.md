# Panduan peran HaloSIS (bahan pelatihan)

Untuk pelatihan operator, tim teknis, dan pegawai (WBS 6.3) serta dokumen serah terima (7.3). Satu bagian per peran:
tugas harian, menu, dan langkah use case. Login di http://localhost:8080 (produksi: alamat HaloSIS BPS) memakai akun
SSO. Skenario demo lengkap: `plugins/halosis/README.md`.

## Pegawai (Requester) — contoh akun `budi`

- **Menu:** Tanya HaloSIS · Buat laporan · Laporan saya · Tanya Jawab (FAQ) · Riwayat percakapan.
- **Tugas:** tanyakan kendala ke asisten dulu (UC-01); bila belum selesai, **Belum terselesaikan → Ya, buat laporan**
  (UC-03, ringkasan percakapan terlampir); ajukan layanan lewat **Ajukan permintaan**; setujui atau tolak solusi dengan
  alasan (UC-07); isi survei kepuasan.
- **Perlu tahu:** data pribadi disamarkan otomatis; jangan kirim kata sandi. Pertanyaan non-TI (cuti, tunjangan)
  diarahkan ke unit terkait. Percakapan berakhir sendiri setelah 30 menit tanpa aktivitas.

## Operator Service Desk — contoh akun `rina`

- **Menu:** Dasbor · Antrean validasi · Semua tiket · **Siap ditutup** · Pemantauan SLA · Pola insiden · Cari pengetahuan.
- **Harian:** buka Antrean validasi (tiket Baru, urut batas waktu) → panel **Saran AI**: lihat tingkat keyakinan
  (*Disarankan* / *Pilih dari 3 kandidat* / *Perlu penilaian manual*), 3 kandidat tim & beban tiket aktif, jenis
  disarankan → **Terima / Ubah / Tolak** (alasan wajib) (UC-04, UC-05). Catat laporan telepon/walk-in atas nama
  pegawai (Bantuan › Buat tiket). Tutup tiket Selesai tanpa respons di **Siap ditutup**. Tindak lanjuti banner
  **Pola insiden** (UC-08). Bila panel menyatakan model belum lolos uji kualitas: triase manual.
- **Tiket pejabat:** pemohon grup *Pejabat* (jabatan Kepala/Direktur/Deputi/Sekretaris Utama dari SSO) otomatis
  mendapat urgensi +1 dan panel menulis "Urgensi …: pemohon pejabat". Prioritas belum ikut naik saat tiket dibuat;
  **prioritas mengikuti matriks urgensi × dampak saat Anda menerima saran (Terima/Ubah) atau mengubah urgensi/dampak
  di tiket**, lalu SLA menyesuaikan. Jangan menurunkan urgensi tanpa alasan.
- **Notifikasi:** peringatan risiko SLA, eskalasi, pola insiden baru (email + lonceng).

## Tim Teknis — contoh akun `andi`; ketua tim `hendra`

- **Menu:** Dasbor · Tiket saya & tim · Pemantauan SLA · Pola insiden · Cari pengetahuan.
- **Harian:** kerjakan tiket tim urut batas waktu; cari solusi di **Cari pengetahuan** (nilai Membantu/Tidak membantu);
  tulis solusi (UC-06). Salah tim → **Kembalikan ke operator (salah tim)** + alasan. Balasan pemohon masuk sebagai
  notifikasi "New followup". Ketua tim menerima peringatan risiko SLA & eskalasi timnya.

## Knowledge Manager — contoh akun `lina`

- **Menu:** Dasbor · Kandidat pengetahuan · Daftar artikel · Tulis artikel.
- **Harian/mingguan:** kurasi **Kandidat pengetahuan** → *Jadikan artikel* (draf) atau *Abaikan* + alasan; sunting &
  terbitkan (otomatis masuk indeks chatbot) (UC-09). Tab **Perlu ditinjau**: tinjau artikel jatuh tempo lalu atur
  tanggal tinjau berikut. SOP ditulis sebagai artikel kategori **SOP**. Pantau "artikel paling sering dinilai tidak
  membantu" di dashboard bersama pemilik domain.

## Manajemen — contoh akun `sri`

- **Menu:** Dasbor kinerja · **Kinerja AI** · Pemantauan SLA · Pola insiden · Laporan.
- **Mingguan/bulanan:** Kinerja AI: KPI tabel 1.3 (SLA terlampaui, median waktu penugasan, % L1, volume per minggu),
  % saran diterima, salah tim, drift bulanan, tren pola; filter tim/kategori (UC-08, BR-08). Menyetujui rilis model
  & ambang (`tata_kelola_ai.md` §1).

## Administrator Sistem — contoh akun `dimas`

- **Menu:** Panel administrasi · Katalog layanan · Kategori layanan · Kebijakan SLA · Tim teknis · Pengguna & peran · Alur kerja & aturan · **Pengaturan AI** · Kinerja AI · Kandidat pengetahuan · Notifikasi · Jejak audit.
- **Tugas:** kelola katalog layanan, aturan SLA (`config/sla_layanan.json` + `setup_sla_alerts.py`), notifikasi,
  role (UC-10). Di Pengaturan AI pakai **Pratinjau dampak** sebelum mengubah ambang; setiap perubahan konfigurasi
  tercatat (Administrasi › Log) dan diumumkan lewat Catatan di beranda Administrator. Ekspor koreksi (CSV) untuk
  Pengelola AI. Snapshot/pemulihan demo: `scripts/demo_snapshot.sh`.
