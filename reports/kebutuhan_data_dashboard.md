# Kebutuhan data dashboard per peran (audit, 2026-11-10)

Metode: audit dari kode (Stats.php, DashboardMenu, dashboard GLPI) + hitung baris DB (baca saja). Tidak membuka UI per akun
(tanpa screenshot); status "kosong" = sumber datanya tidak cukup untuk widget itu. Tidak ada data DB diubah.

## Kondisi data saat ini
- Tiket 70, seluruhnya dibuat 27 Okt–7 Nov 2026 (minggu 44–45): tren 12 minggu hanya 2 titik terisi. Status: Baru 35, Diproses (ditugaskan) 25, Diproses (terjadwal) 1, Tertunda 1, Selesai 1, Ditutup 7.
- Penugasan: 37 grup (Statistik 13, Identitas 13, Jaringan 6, Perangkat 5); akun: andi 4, yoga 1, fajar 2, dedi 1 (hanya 8 penugasan akun).
- Saran AI 57 (35 demo-model, 22 asli; 17 masih pending); keputusan 40 (terima 28, ubah 6, tolak 6), semua 27 Okt–6 Nov; penugasan ulang 8.
- Survei kepuasan 1, terjawab 0. Problem 4, pola 3. Chat 51 (hanya 6 ber-rating; 32 kedaluwarsa, 13 jadi tiket). Kandidat 45 (37 AI pending). Artikel KB 23 (17 FAQ). Umpan balik pencarian 0, tinjauan KB 0.

## Widget kosong / lemah per akun
| Akun (peran) | Beranda / dasbor | Kosong atau lemah | Data yang dibutuhkan |
|---|---|---|---|
| budi (Pegawai) | Beranda Pegawai, Laporan saya, Riwayat chat | Laporan saya hanya tiket milik budi; riwayat chat campur kedaluwarsa | Beberapa tiket budi berstatus beragam (Baru/Diproses/Selesai menunggu persetujuan) + survei belum diisi; chat resolved ber-rating & ditolak |
| rina (Operator) | Dasbor, Antrean validasi, Siap ditutup, Pola | Siap ditutup (hanya 1 Selesai); banner pola (pola lama/tertutup); antrean validasi hanya 17 saran pending lama | Tiket Selesai tanpa respons (belasan), tiket Baru berbagai urgensi/SLA, pola insiden aktif 1–2 dalam 24 jam |
| andi (Tim Teknis) | Tiket saya & tim, SLA, Pola | "Ditugaskan ke saya" hanya 4 tiket; tren/jumlah per status timpang; tiket salah tim (return) 3 | 15–25 tiket per akun/grup dengan status & batas SLA bervariasi, beberapa terlambat |
| lina (KM) | Dasbor, Kandidat, Artikel | Artikel "tidak membantu" (butuh chat ber-rating ≤2/jadi tiket + article_uses), pemakaian artikel, tab Perlu ditinjau (tinjauan KB 0), kandidat bukan-AI hanya 8 | Chat ber-rating rendah terkait artikel, kandidat dari tiket Selesai, artikel jatuh tempo tinjau |
| sri (Manajemen) | Kinerja AI (Stats) | Tren mingguan 12 minggu (2 titik), drift bulanan (1 bulan terisi), KPI SLA/median waktu penugasan (sampel kecil), % L1, kepuasan (1 survei), tren pola (3), saran per pita keyakinan, filter tim/kategori nyaris kosong | Tiket 12 minggu, keputusan AI tersebar 3 bulan, penugasan ulang, tiket Selesai/Ditutup + survei, ≥2 pola, chat + rating |
| dimas (Admin) | Panel admin + Kinerja AI + Kandidat | Sama dengan sri; Pengaturan AI "Pratinjau dampak" butuh riwayat keputusan; Jejak audit memadai | Data seperti sri; perubahan konfigurasi (log) opsional |

Dasbor GLPI inti (Central/Assistance): kartu status, grup, "terlambat", evolusi tiket, top kategori terisi sebagian karena rentang tanggal sempit; pengelompokan per grup/pemohon timpang.

## Data yang perlu disuntik (ringkas)
Status campuran (Baru/Diproses/Tertunda/Selesai/Ditutup) · grup 4 tim + akun peran · rentang 12 minggu · saran + keputusan AI (terima/ubah/tolak, pita keyakinan, salah tim) · tiket Selesai/Ditutup + survei · 1–2 pola insiden (+Problem) · chat dengan rating & artikel terkait. Skrip: `scripts/seed_demo.py` (belum dijalankan).
