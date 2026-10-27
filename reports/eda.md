# Analisis awal history tiket HaloSIS (AS-IS)

Sumber: 6.682 tiket dibuka 1 Jan 2026 – 31 Agu 2026 (`data/processed/tickets_clean.parquet`, sudah disamarkan). Dibuat oleh `ai/scripts/eda.py`; hanya angka agregat dan label topik, tanpa isi tiket.

## Ringkasan

| Indikator | Nilai | Keterangan |
| --- | --- | --- |
| Total tiket | 6.682 | REQ 3.905 · INC 2.777 |
| **Kepatuhan SLA keseluruhan** | **27,59%** | PASS 1.621 ÷ (PASS + BREACH 4.255); IN PROGRESS & tanpa bukti SLA dikecualikan |
| Response SLA lolos | 42,62% | PASS 2.549 ÷ 5.981 |
| Resolution SLA lolos (INC) | 61,00% | PASS 1.289 ÷ 2.113 |
| Fulfillment SLA lolos (REQ) | 48,00% | PASS 780 ÷ 1.625 |
| Indikasi salah routing | 5,79% | 387 tiket dengan `potential_wrong_routing` ≠ NO |
| Waktu selesai (median) | 6,0 hari | 4.973 tiket ber-tanggal resolved; rata-rata 17,2 hari |

Bila tiket IN PROGRESS dan tanpa bukti SLA ikut dihitung sebagai penyebut, kepatuhan SLA keseluruhan menjadi 24,26% (1.621 ÷ 6.682).

## Jumlah tiket per bulan

| Bulan | INC | REQ | Total |
| --- | --- | --- | --- |
| Jan 2026 | 617 | 757 | 1374 |
| Feb 2026 | 433 | 556 | 989 |
| Mar 2026 | 230 | 354 | 584 |
| Apr 2026 | 351 | 583 | 934 |
| Mei 2026 | 226 | 374 | 600 |
| Jun 2026 | 254 | 388 | 642 |
| Jul 2026 | 393 | 502 | 895 |
| Agu 2026 | 273 | 391 | 664 |

## Status tiket

| Status | Jumlah | % |
| --- | --- | --- |
| Closed | 4413 | 66,04% |
| Assigned | 609 | 9,11% |
| In Progress | 569 | 8,52% |
| Completed | 359 | 5,37% |
| Canceled | 224 | 3,35% |
| Cancel | 198 | 2,96% |
| Resolved | 165 | 2,47% |
| Close Cancelled | 129 | 1,93% |
| UNKNOWN / STATE NOT FOUND | 11 | 0,16% |
| New | 2 | 0,03% |
| Close Incomplete | 2 | 0,03% |
| On-Hold | 1 | 0,01% |

## SLA per jenis

| SLA | PASS | BREACH | IN PROGRESS | Lolos (PASS ÷ PASS+BREACH) |
| --- | --- | --- | --- | --- |
| Keseluruhan | 1621 | 4255 | 785 | 27,59% |
| Response | 2549 | 3432 | 674 | 42,62% |
| Resolution | 1289 | 824 | 597 | 61,00% |
| Fulfillment | 780 | 845 | 179 | 48,00% |

## Routing

| `potential_wrong_routing` | Jumlah | % |
| --- | --- | --- |
| NO | 6295 | 94,21% |
| REVIEW | 385 | 5,76% |
| YES | 2 | 0,03% |

| `routing_result` | Jumlah | % |
| --- | --- | --- |
| NORMAL INITIAL HANDOFF | 5937 | 88,85% |
| NO ROUTING CHANGE | 358 | 5,36% |
| ROUTING CORRECTION + ESCALATION REVIEW | 270 | 4,04% |
| ROUTING BOUNCE + ESCALATION REVIEW | 115 | 1,72% |
| ROUTING CORRECTION | 2 | 0,03% |

## Per tim (56 tim)

Waktu selesai = `resolved − opened` (waktu kalender, bukan jam kerja), hanya tiket yang punya tanggal resolved.

| Tim | Tiket | INC | REQ | SLA lolos | Indikasi salah routing | Rata-rata selesai | Median selesai |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Technical Layanan Aplikasi Jaringan - Email | 1094 | 369 | 725 | 23,82% | 2,74% | 14,7 hari | 10,3 hari |
| Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) | 1074 | 418 | 656 | 25,61% | 3,45% | 11,2 hari | 6,2 hari |
| Technical Layanan SiPecut | 1051 | 532 | 519 | 29,80% | 3,71% | 11,0 hari | 3,0 hari |
| Technical Layanan Perangkat TI End User | 482 | 393 | 89 | 20,42% | 2,28% | 57,4 hari | 49,9 hari |
| Operator Pusat | 392 | 136 | 256 | 22,38% | 9,95% | 11,6 hari | 30,6 jam |
| Technical Layanan Pengelolaan E-Sign | 302 | 105 | 197 | 44,64% | 2,65% | 16,0 hari | 4,9 hari |
| Technical Layanan Presensi | 273 | 188 | 85 | 23,39% | 4,03% | 10,3 hari | 5,9 hari |
| Technical Layanan Meeting Online | 232 | 6 | 226 | 48,47% | 1,29% | 3,5 hari | 8,9 jam |
| Technical Layanan SOBAT | 182 | 69 | 113 | 18,49% | 10,44% | 26,9 hari | 25,0 hari |
| Technical Layanan Back Office Selindo (BOS) | 181 | 63 | 118 | 37,21% | 2,76% | 7,6 hari | 3,7 hari |
| Technical Layanan Aplikasi KipApp | 170 | 77 | 93 | 37,65% | 1,76% | 14,7 hari | 5,0 hari |
| Technical Layanan FASIH Moda CAWI CAPI | 154 | 59 | 95 | 33,61% | 12,99% | 99,1 hari | 112,6 hari |
| Technical Layanan Insiden Keamanan Informasi | 145 | 88 | 57 | 9,35% | 48,28% | 22,4 hari | 14,0 hari |
| Technical Layanan Perangkat Lunak COTS | 131 | 47 | 84 | 42,52% | 7,63% | 11,9 hari | 4,9 hari |
| Technical Layanan Infrastruktur & Platform Jaringan - Website Hosting | 125 | 49 | 76 | 7,76% | 0,80% | 94,4 hari | 70,5 hari |
| Technical Layanan Koneksi Jaringan -  SSLVPN | 86 | 31 | 55 | 32,43% | 3,49% | 18,1 hari | 8,3 hari |
| Technical Layanan Infrastruktur & Platform Jaringan - Server Hosting | 65 | 6 | 59 | 14,29% | 7,69% | 13,2 hari | 3,8 hari |
| Technical Layanan Aplikasi Monitoring/Dashboard Sensus/Survei | 63 | 14 | 49 | 22,95% | 14,29% | 86,9 hari | 96,9 hari |
| Technical Layanan Pengujian Aplikasi | 53 | 3 | 50 | 34,69% | 16,98% | 50,0 hari | 43,9 hari |
| Technical Layanan Koneksi Jaringan - LAN BPS Pusat | 47 | 18 | 29 | 6,67% | 4,26% | 15,3 hari | 5,1 hari |
| Technical Layanan Aplikasi Jaringan - Community | 36 | 13 | 23 | 16,67% | 2,78% | 24,2 hari | 20,5 hari |
| Technical Layanan Aplikasi Simpeg Online | 31 | 14 | 17 | 25,00% | 9,68% | 54,2 hari | 54,5 hari |
| Technical Layanan Infrastruktur & Platform Jaringan - Database Hosting | 31 | 3 | 28 | 8,70% | 9,68% | 17,1 hari | 5,0 hari |
| Technical Layanan Aplikasi Jaringan - Devops & Code Repository | 29 | 0 | 29 | 16,67% | 0,00% | 19,6 hari | 10,1 hari |
| Technical Layanan Siimut | 29 | 13 | 16 | 36,00% | 3,45% | 8,9 hari | 4,9 hari |
| Technical Layanan Aplikasi Jaringan - Drive | 25 | 12 | 13 | 21,74% | 8,00% | 9,0 hari | 4,0 hari |
| Technical Layanan Infrastruktur & Platform Jaringan - Container Hosting | 24 | 2 | 22 | 41,67% | 16,67% | 8,3 hari | 2,3 hari |
| Technical Layanan Infrastruktur & Platform Jaringan - Storage Hosting | 23 | 3 | 20 | 28,57% | 13,04% | 10,2 hari | 3,5 hari |
| Layanan Aplikasi Pendataan Digital Sensus/Survei (Moda CAPI dan atau CAWI) | 21 | 11 | 10 | 14,29% | 57,14% | – | – |
| Technical Layanan MANIA | 12 | 0 | 12 | 58,33% | 0,00% | 31,5 jam | 0,7 jam |
| Technical Layanan INDAH Data Platform | 11 | 5 | 6 | 22,22% | 9,09% | 48,0 hari | 48,0 hari |
| Technical Layanan TK Online | 10 | 6 | 4 | 0,00% | 40,00% | 23,6 hari | 19,7 jam |
| Technical Layanan Permintaan Data Sensus/Survei Tahun Berjalan | 8 | 2 | 6 | 28,57% | 25,00% | 79,3 hari | 27,0 hari |
| Technical Layanan Aplikasi Sensus/Survei Moda PAPI | 7 | 1 | 6 | 16,67% | 14,29% | 105,4 hari | 105,4 hari |
| Technical Layanan Koneksi Jaringan - WAN BPS Pusat | 7 | 4 | 3 | 50,00% | 42,86% | 3,1 hari | 3,1 hari |
| Technical Layanan SEKAR | 7 | 2 | 5 | 57,14% | 28,57% | 10,3 hari | 10,3 hari |
| Technical Layanan Arsitektur SPBE | 6 | 0 | 6 | 33,33% | 16,67% | 6,2 hari | 3,7 hari |
| Technical Layanan Data | 5 | 0 | 5 | 40,00% | 60,00% | – | – |
| Technical Layanan Aplikasi Uji Kompetensi | 4 | 3 | 1 | 25,00% | 0,00% | 2,8 hari | 2,8 hari |
| Technical Layanan Counseling Center | 4 | 0 | 4 | 25,00% | 0,00% | 37,0 jam | 27,4 jam |
| Technical Layanan Kompilasi, Pemrosesan, dan Tabulasi Data Pengolahan | 4 | 1 | 3 | 0,00% | 0,00% | 47,0 hari | 20,1 hari |
| Technical Layanan Koneksi Jaringan - Ekstranet BPS | 4 | 3 | 1 | 50,00% | 25,00% | 7,5 jam | 1,8 jam |
| Technical Layanan Permintaan Data Sensus/Survei | 4 | 1 | 3 | 0,00% | 25,00% | – | – |
| Technical Layanan Aplikasi SINERGI | 3 | 2 | 1 | 0,00% | 0,00% | 27,0 hari | 27,1 hari |
| Technical Layanan Pengolahan Data Besar dan/atau Data Administratif | 3 | 0 | 3 | 0,00% | 0,00% | 10,1 hari | 10,1 hari |
| Technical Layanan SPIDER | 3 | 1 | 2 | 33,33% | 0,00% | – | – |
| Technical Layanan Scrapping Data | 3 | 0 | 3 | 33,33% | 0,00% | 15,0 hari | 15,0 hari |
| Technical Layanan HALOBPS | 2 | 1 | 1 | 0,00% | 0,00% | – | – |
| Technical Layanan IPAS (Integrated Processing & Analysis System) | 2 | 0 | 2 | 0,00% | 0,00% | 12,1 hari | 12,1 hari |
| Technical Layanan Pengelolaan Data Sensus/Survei | 2 | 0 | 2 | 50,00% | 100,00% | – | – |
| Technical Layanan Aplikasi Jaringan - Shorten URL | 1 | 0 | 1 | 100,00% | 100,00% | – | – |
| Technical Layanan Aplikasi RB | 1 | 0 | 1 | 0,00% | 0,00% | – | – |
| Technical Layanan Aplikasi iPLAN dan MasterPlan | 1 | 1 | 0 | 0,00% | 100,00% | 151,3 hari | 151,3 hari |
| Technical Layanan Insan Statistik Teladan | 1 | 0 | 1 | 0,00% | 0,00% | – | – |
| Technical Layanan Koneksi Jaringan - VSAT | 1 | 0 | 1 | 0,00% | 0,00% | – | – |
| Technical Layanan Pembangunan dan Pengembangan SIstem Informasi | 1 | 0 | 1 | 0,00% | 100,00% | – | – |

## 20 masalah paling sering (topik)

Judul tiket hampir selalu ditulis bebas (5.881 judul berbeda dari 6.682 tiket), jadi tiket dikelompokkan berdasarkan kemiripan teks (TF-IDF judul+deskripsi, K-Means 40 kelompok). Label = kata kunci paling dominan di kelompok; kelompok dengan ≥ 3 kata kunci sama digabung. Kelompok "campuran" (tim terbanyak < 25%, isinya beragam) tidak diperingkat: 2 kelompok, 1.537 tiket.

| # | Topik (kata kunci) | Tiket | % | INC | REQ | Tim terbanyak |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | reset, password, akun, pegawai | 758 | 11,34% | 188 | 570 | Technical Layanan Aplikasi Jaringan - Email (91%) |
| 2 | cuti, sipecut, mengajukan, tahunan | 650 | 9,73% | 322 | 328 | Technical Layanan SiPecut (91%) |
| 3 | sso, akun, login, username | 457 | 6,84% | 240 | 217 | Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) (77%) |
| 4 | presensi, aplikasi, manual, pegawai | 309 | 4,62% | 191 | 118 | Technical Layanan Presensi (62%) |
| 5 | cuti, ketua, tim, approval | 212 | 3,17% | 125 | 87 | Technical Layanan SiPecut (87%) |
| 6 | zimbra, login, password, masuk | 207 | 3,10% | 123 | 84 | Technical Layanan Aplikasi Jaringan - Email (70%) |
| 7 | zoom, peserta, meeting, unlimited | 204 | 3,05% | 0 | 204 | Technical Layanan Meeting Online (96%) |
| 8 | mitra, sobat, manajemen, akun | 199 | 2,98% | 80 | 119 | Technical Layanan SOBAT (78%) |
| 9 | laptop, dell, latitude, mati | 185 | 2,77% | 141 | 44 | Technical Layanan Perangkat TI End User (95%) |
| 10 | kipapp, skp, jabatan, periode | 168 | 2,51% | 72 | 96 | Technical Layanan Aplikasi KipApp (89%) |
| 11 | otp, reset, sso, akun | 159 | 2,38% | 56 | 103 | Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) (87%) |
| 12 | fasih, petugas, assign, survei | 154 | 2,30% | 62 | 92 | Technical Layanan FASIH Moda CAWI CAPI (58%) |
| 13 | authenticator, google, sso, otp | 150 | 2,24% | 58 | 92 | Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) (93%) |
| 14 | ettd, signer, klaim, sertifikat | 132 | 1,98% | 45 | 87 | Technical Layanan Pengelolaan E-Sign (95%) |
| 15 | bsre, sertifikat, elektronik, aktivasi | 130 | 1,95% | 50 | 80 | Technical Layanan Pengelolaan E-Sign (95%) |
| 16 | rusak, laptop, keyboard, dell | 128 | 1,92% | 112 | 16 | Technical Layanan Perangkat TI End User (94%) |
| 17 | gagal, login, sso, password | 123 | 1,84% | 72 | 51 | Technical Layanan Aplikasi Jaringan - Single Sign On (SSO) (87%) |
| 18 | pembatalan, cuti, tahunan, januari | 114 | 1,71% | 46 | 68 | Technical Layanan SiPecut (93%) |
| 19 | sakit, cuti, sipecut, pengajuan | 111 | 1,66% | 45 | 66 | Technical Layanan SiPecut (86%) |
| 20 | bot, fasih, terdeteksi, kode | 108 | 1,62% | 72 | 36 | Technical Layanan Insiden Keamanan Informasi (80%) |

## Judul identik paling sering (pembanding)

Setelah huruf kecil, angka → `#`, dan penanda samaran dihapus.

| Judul | Tiket |
| --- | --- |
| permintaan reset password | 67 |
| tidak bisa login sso | 60 |
| reset password | 50 |
| reset password sso | 33 |
| reset password email | 27 |
| pembatalan cuti | 20 |
| permintaan reset password email | 19 |
| bot # | 19 |
| permohonan reset password | 18 |
| tidak bisa login email | 17 |
| pengajuan cuti | 17 |
| sipecut | 17 |
| reset otp | 16 |
| lupa password | 15 |
| permohonan reset password sso | 13 |
| t # # laptop rusak | 12 |
| tidak bisa login email bps | 12 |
| gagal login sso | 12 |
| tidak bisa mengajukan cuti di sipecut | 11 |
| t # # perbaikan laptop | 11 |

