# Verifikasi akhir HaloSIS terhadap dokumen *Kelompok 4 AKPSI-6* (end-to-end)

Tanggal: 1 Nov 2026 · Branch `dev`. Verifikasi awal (hanya baca & uji), lalu **perbaikan** atas temuan dan uji ulang;
status di bawah adalah **setelah perbaikan** (status awal di kolom "Awal" tabel temuan).
Sumber kebenaran: dokumen 212 halaman (teks + gambar halaman: use case diagram hal. 125, activity hal. 144–153,
sequence hal. 176–185, communication hal. 186–190, state machine hal. 191–192, CRUDE hal. 193–198).
Audit lama dan README **tidak dipakai sebagai bukti**; setiap status didukung `file:baris`, hasil tes, query DB
(hitungan saja), atau uji aplikasi (Playwright, http://localhost:8080). Klaim tanpa bukti = 🔍.

Status: ✅ sesuai · 🟡 sebagian · ❌ belum · ⚪ di luar prototipe · ⚠ bertentangan dengan dokumen · 🔍 belum terbukti.

Data uji: tiket uji verifikasi (#1074–#1078, Problem #9) dipulihkan dari snapshot; tiket uji perbaikan & regresi
(#1074–#1075, #1080–#1084, Problem #9) dan tiket `tests/e2e` dihapus beserta saran, keputusan, pola, percakapan chat,
survei, dan notifikasi antrenya → kembali 68 tiket. Perubahan yang **sengaja dipertahankan**: grup *Pejabat* + 4 aturan
tiket, hak peran (`setup-roles`), satu suntingan artikel KB (uji revisi), akun Keycloak (email/NIP demo baru).
**Penutupan (1 Nov 2026):** tiket uji #19 (pola SSO, Problem #10) dan regresi akhir dihapus dengan cara yang sama;
alamat email demo lama dihapus dari `glpi_useremails` (akun demo saja); plugin `plugin:list` = *Enabled*.

## 1. Ringkasan per bab (setelah perbaikan)

| Bab / cakupan | Butir | ✅ | 🟡 | ❌ | ⚪ | ⚠ | 🔍 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 System request: BR-01..08, KPI Tabel 1.3, risiko Tabel 1.4, batas scope hal. 8 | 26 | 22 | 1 | 0 | 3 | 0 | 0 |
| 2 Kelayakan 2.1.2–2.1.6, Tabel 2.21, Skenario 2, PoC 2.4.7 (hal. 48–60) | 39 | 25 | 9 | 0 | 5 | 0 | 0 |
| 4 FR-01..10, NFR-01..14, DQR/AIR/KR (hal. 77–80) | 41 | 32 | 7 | 0 | 2 | 0 | 0 |
| 5 AS-IS, analisis 5.1, TO-BE hal. 96–102, BP-01..25, TOM 5.2.3 | 51 | 50 | 0 | 0 | 1 | 0 | 0 |
| 6 Aktor, UC-01..10 + alur alternatif, activity diagram | 40 | 40 | 0 | 0 | 0 | 0 | 0 |
| 7 CRC card (20 kelas), class diagram | 21 | 21 | 0 | 0 | 0 | 0 | 0 |
| 8 Sequence, communication, state machine, CRUDE | 26 | 25 | 1 | 0 | 0 | 0 | 0 |
| Wawancara E1–E21 + kebutuhan tambahan narasumber | 23 | 23 | 0 | 0 | 0 | 0 | 0 |
| WBS: pilot, parallel run, cutover, pelatihan, tata kelola, migrasi | 6 | 1 | 1 | 0 | 4 | 0 | 0 |
| **Total** | **273** | **239** | **19** | **0** | **15** | **0** | **0** |

**Status akhir: 239 ✅ · 19 🟡 · 15 ⚪ · 0 ⚠ · 0 🔍** (semua klaim terbukti; 🟡 tersisa = deviasi PoC terdokumentasi
atau butir staging/produksi: SSO BPS, migrasi penuh, uji NFR di lingkungan BPS, log kueri). Penutupan kelompok fitur
(UC-10 pratinjau SLA, FR-04 pola permintaan, UC-04 pemecah seri, E19 pengingat progres, E15 ringkasan): +5 ✅.
Setelah penutupan verifikasi: 234 ✅ · 24 🟡. Setelah putaran perbaikan pertama: 230 ✅ · 24 🟡 · 15 ⚪ · 4 🔍.
Sebelum perbaikan: 215 ✅ · 37 🟡 · 12 ⚪ · 1 ⚠ · 8 🔍. KPI Tabel 1.3 yang memerlukan pengukuran waktu kerja manusia
(waktu perubahan, waktu monitoring, waktu pencarian solusi) kini ⚪ = *time study* saat pilot (keputusan desain README).

## 2. Temuan (urut prioritas) dan status setelah perbaikan

| # | Kode | Dokumen (hal.) | Awal | Kini | Kondisi sistem / bukti | Saran sisa | Usaha |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | NFR-06, batas scope | hal. 8, 78 | ⚠ | ✅ | Semua jalur ke `Ai/Client.php` menyamarkan teks: `Triage::aiPrompt` (judul & isi), `Chatbot::aiPrompt` (pertanyaan, 6 pesan riwayat, artikel), jaring pengaman `Client::outgoingPrompt` sebelum `callAnthropic`/`callOpenAiCompatible`. Hanya dua pemanggil `completeJson` (`Triage.php`, `Chatbot.php`); kandidat knowledge & ringkasan sudah `Privacy::mask`. Tes container `php plugins/halosis/tools/test_ai_masking.php` → 3/3 LULUS (email, HP, NIP, password tidak bocor) | — | – |
| 2 | UC-10 langkah 5 | hal. 142, 153 | 🟡 | ✅ | Pengaturan AI › *Pratinjau dampak perubahan SLA* (`ConfigAudit::previewSla`, `previewSlaRule`): pilih SLA + target baru, atau aturan SLA + SLA pengganti (jenis SLA pengganti menentukan aksi respons/penyelesaian; tiket dicocokkan dengan kriteria aturan) → jumlah tiket aktif terdampak dan status aman / berisiko (sisa ≤ 20%) / terlewati sekarang vs target baru, tanpa menyimpan. Uji `dimas`: SLA terbanyak → 1 menit = semua tiket terdampak *terlewati*, nilai SLA di DB tetap; aturan SLA dengan pengganti respons & penyelesaian | — | – |
| 3 | UC-09, CRC/state ArtikelKnowledge | hal. 140, 167, 192 | 🟡 | ✅ | Sunting artikel lewat UI (`lina`) → `glpi_knowbaseitems_revisions` 1 baris berisi isi lama; padanan Draf (tanpa target) / Terbit / Diarsipkan (target dicabut) + versi = revisi GLPI di README Keputusan desain | — | – |
| 4 | UC-04 langkah 5 | hal. 133 | 🟡 | ✅ | Pemecah seri `Triage::workloadTiebreak`: selisih keyakinan kandidat 1–2 < 5 poin, grup berbeda, kandidat 2 lebih sedikit tiket aktif → kandidat 2 disarankan (keyakinan = miliknya) dan alasan tampil di panel (`data-halosis-tiebreak`) + penjelasan. Uji unit 4 kasus; uji aplikasi: "Tidak bisa login aplikasi" (SSO vs FASIH, selisih 1,2 poin) → grup tim dengan beban lebih ringan + alasan | — | – |
| 5 | FR-01, 2.1.5 SSO | hal. 77, 16 | 🟡 | 🟡 | SSO Keycloak lokal; entry point pegawai = chat | Uji ke SSO BPS di staging | besar |
| 6 | Wawancara: prioritas pejabat | hal. 204, 211 | 🟡 | ✅ | Config `official_titles` (bawaan Kepala, Direktur, Deputi, Sekretaris Utama) → login SSO memasukkan pemohon ke grup *Pejabat*; `setup_pejabat_rules.py` (idempoten, dijalankan 2×) membuat 4 aturan "Pejabat: urgensi N → N+1" paling awal & menurun. Uji: tiket `sri` (Direktur) urgensi 3 → 4, saran urgensi 4 + panel "Urgensi Tinggi: pemohon pejabat (Direktur)"; tiket `budi` tetap 3. **Penutupan:** README & `panduan_peran.md` menyatakan prioritas tiket pejabat mengikuti matriks urgensi × dampak saat saran diterima/Operator mengubah (GLPI menghitung prioritas sebelum aturan) | — | – |
| 7 | KPI Tabel 1.3 | hal. 6–7 | 🟡 | ✅ / ⚪ | Dashboard pola: *Waktu sampai diketahui (median)* dan *Pemohon terdampak* (uji: 4 menit, 3 pemohon); waktu perubahan/monitoring/pencarian = time study pilot (README, `audit_dokumen_e2e.md` §8.3) | — | – |
| 8 | FR-04 (request & incident) | hal. 78 | 🟡 | ✅ | Pengaturan AI *Sertakan permintaan dalam deteksi pola* (`pattern_include_requests`, bawaan mati sesuai PoC): bila aktif REQ dikelompokkan terpisah dari INC (tanda `req:`, Problem "Pola permintaan: …"). Uji: 3 permintaan mirip, mati → 0 Problem; aktif → 1 "Pola permintaan"; pengaturan dikembalikan | — | – |
| 9 | FR-10, NFR-13, WBS 6.1 | hal. 78–79, 72 | 🟡 | 🟡 | Migrasi sampel 200 tiket | Migrasi penuh saat implementasi | besar |
| 10 | NFR-01/05/08/09 | hal. 78–79 | 🟡 | 🟡 | Uji beban laptop, tanpa uji kerentanan/usability, monitoring opsional | Ulang di staging BPS | besar |
| 11 | TO-BE tabel confidence (REQ/INC) | hal. 100 | 🟡 | ✅ | Keyakinan jenis antara ambang rendah dan ambang → "Jenis: perlu ditinjau (…%) · model condong ke …" (`TriagePanel::typeHint`); uji UI pada tiket keyakinan 51% | — | – |
| 12 | KR-01, KR-03, KR-08 | hal. 79–80 | 🟡 | ✅ | Kategori KB = domain + pemilik (`tata_kelola_ai.md` §4b); jejak perubahan = revisi GLPI (terbukti, #3) | — | – |
| 13 | PoC 2.4.7 (deviasi) | hal. 53–56 | 🟡 | 🟡 | e5, tanpa LLM lokal, ambang pola 0,50, DBSCAN 0,50/3, routing 21 kelas — terdokumentasi | — | – |
| 14 | UC-02 langkah 6 / sequence UC-02 | hal. 130, 177 | 🟡 | 🟡 | Keputusan terdokumentasi (README): log retrieval angka saja (NFR-06) | Kueri tersamar bila tata kelola setuju | kecil |
| 15 | E15 / E19 | hal. 10 | 🟡 | ✅ | E15: ringkasan ekstraktif 3 kalimat (`Summary`, tanpa LLM, teks disamarkan dulu, kalimat ganda dihitung sekali) di panel Saran AI untuk deskripsi > 150 kata. E19: tugas terjadwal `ProgressReminder` (harian, 07–17) → notifikasi "HaloSIS: Pengingat progres" (email + browser) ke teknisi & grup untuk tiket Diproses/Menunggu tanpa tindak lanjut/tugas > N hari kerja (Pengaturan AI, bawaan 5; kalender entitas), sekali per periode. Uji: tiket 14 hari → 1 pengingat, jalan kedua tidak menambah; tiket 2 hari → 0; ringkasan 3 butir tanpa email/HP, tiket pendek tanpa ringkasan | — | – |
| 16 | Kebersihan rilis (realm demo) | NFR-06 | 🟡 | ✅ | `keycloak/halosis-realm.json`: 16 akun `@contoh.go.id`, NIP `199001012020121001…016`; seed & tes disamakan; realm diimpor ulang lewat *partial import* admin (16 ditimpa, volume tidak dihapus); login 7 peran OK. **Penutupan:** alamat demo lama dihapus dari `glpi_useremails` untuk 16 akun demo saja (sebelum: 16 alamat lama utama + 8 alamat baru non-utama; sesudah: 0 lama, 16 alamat baru utama; akun lain tidak tersentuh); sinkron SSO kini **mengganti** email utama (`KeycloakAuth::syncPrimaryEmail`): uji `budi` dengan alamat utama lama → setelah login 1 alamat (klaim, utama), login ulang tetap 1; `seed_halosis.py` membersihkan secara idempoten | — | – |
| 17 | Matriks §7 vs menu | hal. 125 | 🟡 | ✅ | `setup-roles`: Reservasi Pegawai dicabut, hak `rule_*` Operator/Tim Teknis/KM dipastikan 0; `front/rule.php` hanya cek antarmuka, jadi hook `post_init` (`RoleMenu::guardRuleIndex`) → 403. Uji: menu Pegawai tepat 5 item; rule.php 403 untuk rina, andi, hendra, lina, sri; dimas 200; akses lain tidak berubah | — | – |
| 18 | Alur alternatif tidak diuji | hal. 129–141 | 🔍 (8) | ✅ | `tests/e2e/alur_alternatif.js` 9 alur: UC-01 4a / UC-02 5a, **UC-03 4a** (judul "abc" ditolak peramban & server, tanpa tiket), **UC-04 1a** (`halosis-ai` dihentikan → tiket tersimpan tanpa saran + tombol *Buat saran AI*; dinyalakan lagi → tombol menghasilkan saran), UC-05 S-2 & S-1, UC-06 2a, **UC-06 S-1** (teknisi → Menunggu, status 4), UC-07 5a, **UC-09 5a** (Jadikan artikel → draf, 0 target visibilitas). Hasil: 9/9 LULUS dua kali berturut-turut (navigasi tiket diulang sekali bila macet; satu putaran sebelumnya gagal karena navigasi pertama sesudah container dihentikan macet > 60 dtk); data uji (tiket, chat, artikel draf, kandidat) dihapus/dipulihkan otomatis | — | – |
| 19 | Kartu pola "Dikonfirmasi" (baru) | BP-17, UC-08 | 🟡 | ✅ | `Stats::patterns` menghitung *dikonfirmasi* dari tindakan manusia (`Stats::humanTouchedProblems`): log Problem dari pengguna non-sistem (bukan `cron_*`: ubah status, tautkan tiket manual) atau tindak lanjut/tugas Problem; status awal *Ditugaskan* hasil pembuatan otomatis tidak dihitung. Uji: pola baru → Terdeteksi 4 / Dikonfirmasi 0; `rina` ubah status Problem lewat UI → Dikonfirmasi 1. README plugin (tabel dashboard) diperbarui | — | – |

Catatan proses: penjaga `rule.php` versi pertama memakai `Html::displayRightError()` (tidak ada di GLPI 12) di
`plugin_init`; GLPI menonaktifkan plugin untuk request itu dan status plugin menjadi *not activated*. Dipindah ke hook
`post_init` dengan `AccessDeniedHttpException` dan plugin diaktifkan kembali (`plugin:activate`); tidak ada data hilang.

## 3. Angka yang tidak konsisten (status)

| Angka | Lokasi | Status |
| --- | --- | --- |
| Baseline SLA hanya 28,87% | `audit_kelengkapan.md` BR-02 | ✅ diperbaiki: dua baseline (dokumen 27,59 / 42,62; history baru 28,87 + respons 43,08) + cakupan rating 17,3% |
| Teks dashboard lama | `uji_regresi_demo.md:53` | ✅ ditandai historis dengan teks UI sekarang |
| Retrieval 72,74% vs 72,85% | `banding_embedding.md` vs `banding_solusi.md` | ✅ dijelaskan: data, aturan, dan 906 kueri sama, potongan dari dua skrip; selisih 0,11 poin = **1 kueri** (1/906) |
| Median umur 24,0 vs 6,0 hari | dokumen hal. 82 vs `eda.md` | ✅ dijelaskan di `eda.md`: dokumen = `closed − opened` (dihitung ulang: 24,0 hari, 4.600 tiket); `eda.md` = `resolved − opened` (6,0; ekspor baru 6,1) |
| Cakupan rating 15–16% vs 17,3% | dokumen vs dashboard | Dijelaskan (ekspor baru) |
| Populasi 6.682 vs 6.681 | dokumen vs README | Dijelaskan (1 REQ tanpa nomor) |
| Routing PoC 68,33/70,43% vs 75,88% | dokumen vs `triase.md` | Tidak sebanding (kelas & split berbeda), dinyatakan di README |
| Triase, jenis, urgensi, SLA, kepuasan | README ×3, laporan, audit, `/health` | Konsisten |

## 4. Hasil uji B (fungsional) & C (kebersihan rilis) — setelah perbaikan

| Uji | Hasil | Rincian |
| --- | --- | --- |
| Regresi demo langkah 1–5 | ✅ | Penutupan: diulang setelah semua perbaikan (laporan #1137 → Ditutup; 2b/2c & Bonus pola Problem #12 lulus; lalu dihapus → 68 tiket). Putaran sebelumnya: chat → laporan #1080, panel + Terima, `andi` tanpa tombol keputusan + solusi, `budi` Approve → Ditutup, dashboard `sri` (dua baseline, cakupan rating, pola, drift; tanpa tombol ekspor) |
| 2b, 2c | ✅ | Tiket telepon atas nama `siti` + saran AI, terlihat oleh `siti`; Siap ditutup tersedia |
| Bonus pola | ✅ | 3 insiden SSO → Problem pola, banner `rina`, panel "Bagian dari pola insiden" + alasan dampak; kartu pola menampilkan waktu sampai diketahui & pemohon terdampak |
| Perbaikan baru | ✅ | Pejabat (urgensi 3 → 4 + alasan), "Jenis: perlu ditinjau (51%)", revisi KB, menu Pegawai 5 item, `rule.php` 403 |
| Alur alternatif `tests/e2e` | ✅ | 9/9 LULUS dua kali berturut-turut (navigasi tiket diulang sekali bila macet; satu putaran sebelumnya gagal karena navigasi pertama sesudah container dihentikan macet > 60 dtk), data uji terhapus |
| Email demo & SSO | ✅ | `glpi_useremails` akun demo: 0 alamat lama, 16 utama baru, 0 akun tanpa email utama; login SSO mengganti, tidak menambah |
| Status plugin | ✅ | `plugin:list`: halosis 1.0.0 *Enabled*; `plugin:install --force` dua kali → 1 notifikasi, 1 templat, 1 tugas `ProgressReminder` (idempoten) |
| Fitur penutup `tests/e2e/fitur_penutup.js` | ✅ | 6/6 LULUS dua kali (UC-10 SLA & aturan SLA, FR-04, UC-04, E19, E15); `alur_alternatif.js` tetap 9/9; data uji (tiket, Problem pola, pengingat, notifikasi antre, Catatan perubahan pengaturan) dihapus otomatis, pengaturan dikembalikan |
| Tes unit fitur `tools/test_fitur.php` | ✅ | 12/12 LULUS (ringkasan, pemecah seri, status SLA) |
| Login SSO 7 peran | ✅ | Setelah impor ulang realm; email/NIP baru tersinkron |
| Tes AI / tes masking / `php -l` / `/health` | ✅ | 51 lulus / 3 LULUS / 43 berkas, 0 galat / `ok`, triase-jenis-urgensi lolos (diulang saat penutupan, hasil sama) |
| `.gitignore`, `git ls-files`, inti GLPI, versi | ✅ | Seperti verifikasi awal; ditambah `node_modules/`. Inti GLPI tidak diubah (perbaikan hanya di plugin & skrip API). Versi plugin 1.0.0 = CHANGELOG |

## 5. Klaim audit/README lama yang terbukti SALAH (dan koreksinya)

| Klaim | Lokasi | Bukti | Koreksi |
| --- | --- | --- | --- |
| Claude: "teks disamarkan sebelum dikirim" | `README.md:711` | Saran triase mengirim teks mentah (`Triage.php:300-305`, sebelum perbaikan) | Kode diperbaiki + README menyebut tiga lapisan & tesnya |
| BR-02 "KPI kepatuhan sebanding baseline 28,87%" | `audit_kelengkapan.md:90` | Dashboard membandingkan ke dua baseline | Baris diperbarui |
| Menu Pegawai = 5 item | `audit_kelengkapan.md` §7 | Ada *Reservation* | Hak dicabut; kini benar (5 item) |

| UC-04 1a "AI tidak tersedia → tanpa saran, tombol Buat saran AI" | `audit_kelengkapan.md` UC-04 | Uji penutupan: layanan dihentikan → tiket tetap mendapat saran **aturan demo** (`Triage::generate` jatuh ke `suggestDemo`) | Layanan AI terkonfigurasi tapi gagal → tanpa saran (kecuali penyedia eksternal dikonfigurasi); `TriageRetry`/tombol mencoba lagi; README plugin diperbarui |

Klaim yang **tidak terbukti / dilebihkan** saat verifikasi awal: UC-09 "revisi artikel bawaan" (kini terbukti, ✅) dan
UC-10 ✅ "pratinjau dampak" (diturunkan ke 🟡 di kedua audit; kembali ✅ setelah pratinjau SLA/aturan SLA, 1 Nov).
