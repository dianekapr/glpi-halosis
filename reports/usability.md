# Uji usability Self-Service Conversation HaloSIS (NFR-08)

Status: **rencana + lembar isian**. Isi bagian §6–§8 setelah sesi uji.

## 1. Tujuan

NFR-08: *"Self-Service Conversation harus dapat digunakan tanpa perlu pemahaman teknis tentang ITSM."*
Dokumen juga menyebut **usability testing** sebagai cara melibatkan Pegawai/Requester (analisis pemangku
kepentingan). Uji ini membuktikan bahwa pegawai biasa bisa bertanya, melapor, dan mengonfirmasi penyelesaian
tanpa dilatih dan tanpa tahu istilah seperti *incident*, *SLA*, atau *assignment group*.

## 2. Peserta

| Kriteria | Nilai |
| --- | --- |
| Jumlah | 5 orang (cukup untuk menemukan sebagian besar masalah utama pada uji formatif) |
| Profil | Pegawai non-IT; campuran usia & kebiasaan teknologi; belum pernah memakai HaloSIS/GLPI |
| Akun | `budi`, `siti`, `maya` (bergantian; reset data uji di antara sesi bila perlu) |
| Perangkat | 3 peserta di laptop, 2 peserta di HP (tampilan 390px) |
| Persetujuan | Peserta setuju direkam layarnya; **tanpa** merekam wajah/suara bila tidak perlu; nama diganti P1–P5 |

## 3. Peran tim saat sesi

| Peran | Tugas |
| --- | --- |
| Fasilitator | Membacakan skenario, tidak membantu kecuali peserta macet > 2 menit |
| Pencatat | Mengisi waktu, keberhasilan, kesalahan, dan kutipan peserta |
| Pengamat teknis | Memastikan layanan AI hidup (`/health`), mencatat galat |

Metode: *think-aloud* (peserta menyuarakan apa yang dipikirkan). Durasi ±25 menit per peserta.

## 4. Skenario tugas

Bacakan skenario dengan bahasa sehari-hari. **Jangan** menyebut nama menu atau tombol.

| # | UC | Skenario yang dibacakan | Berhasil bila | Batas waktu |
| --- | --- | --- | --- | ---: |
| T1 | UC-01, UC-02 | "Kotak masuk email kantor Anda katanya penuh. Coba cari tahu cara mengatasinya lewat HaloSIS." | Membaca jawaban yang relevan & melihat sumbernya | 3 menit |
| T2 | UC-01 | "Jawaban tadi membantu? Beri tahu sistemnya." | Memberi rating pada jawaban | 1 menit |
| T3 | UC-01 (4a, 6a), UC-03 | "Anda tidak bisa login SSO sejak pagi dan cara di layar belum berhasil. Laporkan masalah ini." | Tiket terbuat dari chat dengan ringkasan otomatis | 4 menit |
| T4 | UC-07 | "Besok Anda ingin tahu laporan tadi sudah sampai mana. Cek statusnya." | Menemukan laporan & membaca status/perkiraan waktu selesai | 2 menit |
| T5 | UC-07 (5a) | "Petugas bilang masalahnya sudah beres, tapi Anda masih belum bisa login. Sampaikan." | Menolak solusi dengan alasan | 3 menit |
| T6 | UC-01 (4a) | "Tanyakan resep nasi goreng ke HaloSIS." | Memahami bahwa sistem belum menemukan jawaban & ditawari jalan lain | 1 menit |

Persiapan data sebelum sesi: satu tiket milik akun peserta yang sudah diberi solusi oleh `andi`
(untuk T5), layanan AI dalam keadaan `"status":"ok"`.

## 5. Ukuran

| Ukuran | Cara | Target (usulan) |
| --- | --- | --- |
| Tingkat keberhasilan tugas | Berhasil tanpa bantuan / dengan bantuan / gagal | ≥ 80% tugas berhasil tanpa bantuan |
| Waktu per tugas | Stopwatch dari selesai dibacakan sampai berhasil | Di bawah batas waktu §4 |
| Kesalahan | Klik salah arah, kembali ke halaman sebelumnya, bertanya ke fasilitator | Dicatat, dibahas di §8 |
| Istilah teknis | Peserta bertanya arti kata di layar (mis. "Masalah", "Followup", "SLA") | 0 istilah yang menghalangi tugas |
| SUS (System Usability Scale) | Kuesioner §7 setelah semua tugas | Rata-rata ≥ 68 (di atas rata-rata umum) |

## 6. Lembar pencatatan (per peserta)

Peserta: P__ · Perangkat: laptop / HP · Tanggal: ____ · Fasilitator: ____ · Pencatat: ____

| Tugas | Hasil (✅ sendiri / 🟡 dibantu / ❌ gagal) | Waktu (mnt:dtk) | Kesalahan / istilah yang membingungkan | Kutipan peserta |
| --- | --- | --- | --- | --- |
| T1 | | | | |
| T2 | | | | |
| T3 | | | | |
| T4 | | | | |
| T5 | | | | |
| T6 | | | | |

## 7. Kuesioner SUS

Skala 1 (sangat tidak setuju) – 5 (sangat setuju). Terjemahan bahasa Indonesia dari 10 pernyataan SUS standar.

| # | Pernyataan | 1 | 2 | 3 | 4 | 5 |
| --- | --- | :-: | :-: | :-: | :-: | :-: |
| 1 | Saya rasa saya akan sering menggunakan HaloSIS. | | | | | |
| 2 | Saya merasa HaloSIS terlalu rumit. | | | | | |
| 3 | Saya merasa HaloSIS mudah digunakan. | | | | | |
| 4 | Saya rasa saya butuh bantuan orang teknis untuk bisa memakai HaloSIS. | | | | | |
| 5 | Saya merasa fitur-fitur HaloSIS terpadu dengan baik. | | | | | |
| 6 | Saya merasa banyak hal yang tidak konsisten di HaloSIS. | | | | | |
| 7 | Saya rasa kebanyakan orang akan cepat belajar memakai HaloSIS. | | | | | |
| 8 | Saya merasa HaloSIS canggung/merepotkan untuk digunakan. | | | | | |
| 9 | Saya merasa percaya diri saat memakai HaloSIS. | | | | | |
| 10 | Saya perlu belajar banyak hal sebelum bisa memakai HaloSIS. | | | | | |

**Cara menghitung skor SUS (0–100) per peserta:**
butir ganjil (1, 3, 5, 7, 9) → nilai − 1; butir genap (2, 4, 6, 8, 10) → 5 − nilai;
jumlahkan kesepuluh hasil, lalu kalikan **2,5**.

## 8. Rekap hasil

| Peserta | Perangkat | T1 | T2 | T3 | T4 | T5 | T6 | Berhasil sendiri | Skor SUS |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | ---: | ---: |
| P1 | | | | | | | | /6 | |
| P2 | | | | | | | | /6 | |
| P3 | | | | | | | | /6 | |
| P4 | | | | | | | | /6 | |
| P5 | | | | | | | | /6 | |
| **Rata-rata** | | | | | | | | **__%** | **__** |

Temuan (urutkan dari yang paling parah):

| # | Temuan | Tugas | Jumlah peserta terdampak | Tingkat (tinggi/sedang/rendah) | Usulan perbaikan (tema/plugin/konfigurasi, sesuai NFR-10) |
| --- | --- | --- | ---: | --- | --- |
| 1 | | | | | |
| 2 | | | | | |

Kesimpulan NFR-08: ✅ terpenuhi / 🟡 sebagian / ❌ belum. Alasan: ____

## 9. Etika & data

- Peserta boleh berhenti kapan saja; yang diuji sistemnya, bukan pesertanya.
- Pertanyaan chat memakai skenario buatan; peserta diminta **tidak** mengetik data pribadi asli
  (NIP, nomor HP, password).
- Rekaman layar disimpan di luar repo dan dihapus setelah rekap selesai; repo hanya berisi rekap tanpa nama.
