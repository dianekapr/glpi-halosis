# Rekonsiliasi migrasi data history tiket (FR-10)

Dibuat `ai/scripts/reconcile.py` · 2026-10-31 21:26 · sumber `data/raw/data ticketing (202601_202608).xlsx`

Laporan ini hanya berisi angka, bulan, dan nama tim. Isi tiket, nama orang, dan nilai yang disamarkan tidak pernah ditampilkan.

## Ringkasan

| Ukuran | Jumlah |
| --- | ---: |
| Baris sumber | 6.681 |
| Berhasil diproses | 6.671 |
| Gagal | 10 |
| Ditandai tidak lengkap (dari yang berhasil) | 790 |
| Duplikat (dari yang berhasil) | 64 |
| Cek: sumber = berhasil + gagal | ✓ |

## Gagal per alasan

Satu baris bisa punya lebih dari satu alasan. Baris gagal tetap ada di `tickets_clean.parquet` untuk analisis AS-IS, tetapi tidak layak dimigrasikan ke GLPI.

| Alasan | Baris |
| --- | ---: |
| Tanpa nomor tiket | 0 |
| Tanggal dibuka tidak valid | 0 |
| Status tidak dikenal (tidak bisa dipetakan ke status GLPI) | 10 |
| Masih memuat pola data pribadi setelah penyamaran | 0 |

## Ditandai tidak lengkap

Tetap diproses, tetapi perlu dilengkapi atau diperlakukan khusus (mis. tidak dipakai melatih model routing bila tanpa tim, tidak masuk pasangan masalah → solusi bila tanpa solusi).

| Penanda | Baris |
| --- | ---: |
| Tanpa deskripsi | 34 |
| Tanpa tim (assignment group) | 3 |
| Selesai tanpa solusi yang bisa diambil | 758 |
| Urutan tanggal tidak valid (selesai/ditutup sebelum dibuka) | 0 |

## Duplikat

Baris pertama dianggap asli; yang dihitung adalah salinan berikutnya.

| Jenis | Baris |
| --- | ---: |
| Nomor tiket ganda | 0 |
| Isi identik dari pemohon yang sama (judul + deskripsi) | 64 |

## Nilai yang disamarkan per jenis

Jumlah kemunculan yang diganti penanda (mis. `[EMAIL]`) di kolom teks bebas, selisih keluaran terhadap sumber.

| Jenis | Nilai disamarkan |
| --- | ---: |
| Email | 3.001 |
| NIP | 1.104 |
| NIK | 131 |
| Telepon | 134 |
| Rahasia (password/PIN/OTP) | 1.161 |
| Nama | 11.484 |
| **Total** | **17.015** |

Kolom nama pengguna (requester_name, assigned_to_name, resolved_by_name, closed_by_name) dihapus dan diganti ID samaran `*_pid`.

## Banding ekspor lama vs baru

Lama `data/raw/ticketing_history_202601_202608.xlsx` (137 kolom) vs baru `data/raw/data ticketing (202601_202608).xlsx` (220 kolom). Pipeline memakai ekspor baru; dicocokkan per nomor tiket.

| Ukuran | Jumlah |
| --- | ---: |
| Baris lama / baru | 6.682 / 6.681 |
| Hanya di ekspor lama | 1 REQ tanpa nomor tiket |
| Hanya di ekspor baru | 0 |
| Nomor tiket di keduanya | 6.681 |
| Status berubah | 137 (2,05%) |
| Kolom `short_description` berubah | 9 |
| Kolom `description` berubah | 8 |
| Kolom `assignment_group_name` berubah | 6 |
| Kolom `all_conversations` berubah | 29 |
| Kolom `close_notes` berubah | 109 |
| Kolom `resolution` berubah | 49 |
| Hasil SLA keseluruhan berimputasi (DQR-04, kolom `sla_imputasi`) | 1.819 |

Perubahan status terbanyak (lama → baru); umumnya tiket yang masih berjalan saat ekspor lama lalu ditutup:

| Lama | Baru | Tiket |
| --- | --- | ---: |
| Completed | Closed | 39 |
| Resolved | Closed | 35 |
| In Progress | Closed | 20 |
| Assigned | Closed | 19 |
| Assigned | In Progress | 8 |
| In Progress | Resolved | 5 |
| Assigned | Cancel | 3 |
| In Progress | Completed | 3 |
| Assigned | Resolved | 2 |
| Assigned | Completed | 1 |

Hasil SLA keseluruhan versi diperluas (`overall_sla_result_extended`): OVERDUE 4.580, MET 1.859, UNKNOWN 222, NO SLA EVIDENCE 20.

Kolom tambahan ekspor baru: 92 (antara lain impact, urgency, priority, rating_*, SLA *_native/_final/_imputation_*).

## Per bulan (tanggal dibuka)

| Bulan | Sumber | Berhasil | Gagal | Tidak lengkap | Duplikat |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-01 | 1.374 | 1.365 | 9 | 160 | 12 |
| 2026-02 | 989 | 989 | 0 | 158 | 5 |
| 2026-03 | 584 | 584 | 0 | 61 | 5 |
| 2026-04 | 933 | 933 | 0 | 91 | 10 |
| 2026-05 | 600 | 599 | 1 | 58 | 10 |
| 2026-06 | 642 | 642 | 0 | 82 | 6 |
| 2026-07 | 895 | 895 | 0 | 116 | 8 |
| 2026-08 | 664 | 664 | 0 | 64 | 8 |
| **Total** | **6.681** | **6.671** | **10** | **790** | **64** |

## Per tim

| Tim | Sumber | Berhasil | Gagal | Tidak lengkap | Duplikat |
| --- | ---: | ---: | ---: | ---: | ---: |
| Technical Layanan Aplikasi Jaringan - Email | 1.094 | 1.094 | 0 | 93 | 7 |
| Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | 1.075 | 1.075 | 0 | 174 | 9 |
| Technical Layanan SiPecut | 1.051 | 1.051 | 0 | 74 | 6 |
| Technical Layanan Perangkat TI End User | 482 | 482 | 0 | 83 | 0 |
| Operator Pusat | 391 | 391 | 0 | 36 | 21 |
| Technical Layanan Pengelolaan E-Sign | 302 | 302 | 0 | 15 | 5 |
| Technical Layanan Presensi | 273 | 273 | 0 | 8 | 1 |
| Technical Layanan Meeting Online | 232 | 232 | 0 | 107 | 5 |
| Technical Layanan SOBAT | 182 | 182 | 0 | 2 | 0 |
| Technical Layanan Back Office Selindo (BOS) | 181 | 181 | 0 | 9 | 0 |
| Technical Layanan Aplikasi KipApp | 170 | 170 | 0 | 2 | 1 |
| Technical Layanan FASIH Moda CAWI CAPI | 153 | 153 | 0 | 31 | 0 |
| Technical Layanan Insiden Keamanan Informasi | 150 | 150 | 0 | 7 | 0 |
| Technical Layanan Perangkat Lunak COTS | 131 | 131 | 0 | 6 | 1 |
| Technical Layanan Infrastruktur & Platform Jaringan - Website Hosting | 125 | 125 | 0 | 26 | 1 |
| Technical Layanan Koneksi Jaringan -  SSLVPN | 86 | 86 | 0 | 15 | 1 |
| Technical Layanan Infrastruktur & Platform Jaringan - Server Hosting | 65 | 65 | 0 | 17 | 0 |
| Technical Layanan Aplikasi Monitoring/Dashboard Sensus/Survei | 59 | 59 | 0 | 20 | 1 |
| Technical Layanan Pengujian Aplikasi | 53 | 53 | 0 | 4 | 1 |
| Technical Layanan Koneksi Jaringan - LAN BPS Pusat | 47 | 47 | 0 | 1 | 0 |
| Technical Layanan Aplikasi Jaringan - Community | 36 | 36 | 0 | 4 | 0 |
| Technical Layanan Aplikasi Simpeg Online | 31 | 31 | 0 | 0 | 0 |
| Technical Layanan Infrastruktur & Platform Jaringan - Database Hosting | 31 | 31 | 0 | 9 | 0 |
| Technical Layanan Siimut | 29 | 29 | 0 | 0 | 1 |
| Technical Layanan Aplikasi Jaringan - Devops & Code Repository | 29 | 29 | 0 | 11 | 0 |
| Technical Layanan Aplikasi Jaringan - Drive | 25 | 25 | 0 | 1 | 0 |
| Technical Layanan Infrastruktur & Platform Jaringan - Container Hosting | 24 | 24 | 0 | 11 | 0 |
| Technical Layanan Infrastruktur & Platform Jaringan - Storage Hosting | 23 | 23 | 0 | 4 | 0 |
| Layanan Aplikasi Pendataan Digital Sensus/Survei (Moda CAPI dan atau CAWI) | 21 | 21 | 0 | 1 | 0 |
| (tanpa tim) | 13 | 3 | 10 | 3 | 0 |
| Technical Layanan MANIA | 12 | 12 | 0 | 7 | 0 |
| Technical Layanan INDAH Data Platform | 11 | 11 | 0 | 0 | 0 |
| Technical Layanan TK Online | 10 | 10 | 0 | 1 | 0 |
| Technical Layanan Permintaan Data Sensus/Survei Tahun Berjalan | 8 | 8 | 0 | 2 | 0 |
| Technical Layanan Koneksi Jaringan - WAN BPS Pusat | 7 | 7 | 0 | 0 | 0 |
| Technical Layanan SEKAR | 7 | 7 | 0 | 1 | 0 |
| Technical Layanan Aplikasi Sensus/Survei Moda PAPI | 7 | 7 | 0 | 0 | 0 |
| Technical Layanan Arsitektur SPBE | 6 | 6 | 0 | 3 | 3 |
| Technical Layanan Data | 5 | 5 | 0 | 0 | 0 |
| Technical Layanan Kompilasi, Pemrosesan, dan Tabulasi Data Pengolahan | 4 | 4 | 0 | 1 | 0 |
| Technical Layanan Koneksi Jaringan - Ekstranet BPS | 4 | 4 | 0 | 0 | 0 |
| Technical Layanan Permintaan Data Sensus/Survei | 4 | 4 | 0 | 0 | 0 |
| Technical Layanan Counseling Center | 4 | 4 | 0 | 0 | 0 |
| Technical Layanan Aplikasi Uji Kompetensi | 4 | 4 | 0 | 0 | 0 |
| Technical Layanan Scrapping Data | 3 | 3 | 0 | 0 | 0 |
| Technical Layanan SPIDER | 3 | 3 | 0 | 0 | 0 |
| Technical Layanan Aplikasi SINERGI | 3 | 3 | 0 | 1 | 0 |
| Technical Layanan Pengolahan Data Besar dan/atau Data Administratif | 3 | 3 | 0 | 0 | 0 |
| Technical Layanan IPAS (Integrated Processing & Analysis System) | 2 | 2 | 0 | 0 | 0 |
| Technical Layanan Pengelolaan Data Sensus/Survei | 2 | 2 | 0 | 0 | 0 |
| Technical Layanan HALOBPS | 2 | 2 | 0 | 0 | 0 |
| Technical Layanan Aplikasi iPLAN dan MasterPlan | 1 | 1 | 0 | 0 | 0 |
| Technical Layanan Pembangunan dan Pengembangan SIstem Informasi | 1 | 1 | 0 | 0 | 0 |
| Technical Layanan Koneksi Jaringan - VSAT | 1 | 1 | 0 | 0 | 0 |
| Technical Layanan Aplikasi RB | 1 | 1 | 0 | 0 | 0 |
| Technical Layanan Aplikasi Jaringan - Shorten URL | 1 | 1 | 0 | 0 | 0 |
| Technical Layanan Insan Statistik Teladan | 1 | 1 | 0 | 0 | 0 |
| **Total** | **6.681** | **6.671** | **10** | **790** | **64** |
