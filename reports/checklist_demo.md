# Checklist hari demo HaloSIS

Untuk penyaji & operator laptop demo. Waktu siap ±15 menit. Skenario lengkap: `plugins/halosis/README.md`
(Skenario demo); hasil regresi terakhir: `reports/uji_regresi_demo.md`.

## 1. H-1 (sekali)

- [ ] `git pull` lalu jalankan blok **Update untuk anggota tim** di README induk.
- [ ] Data demo bersih → `scripts/demo_snapshot.sh simpan` (snapshot DB GLPI + Keycloak + indeks AI di `backup/`).
- [ ] Uji cepat langkah 1–5 skenario demo; bila ada tiket/percakapan uji tersisa: `scripts/demo_snapshot.sh pulihkan`.

## 2. Menyalakan layanan (urut)

```bash
docker compose up -d db keycloak mailpit      # data & SSO dulu
docker compose up -d glpi halosis-ai           # aplikasi & layanan AI (AI siap ±1 menit: model dimuat)
docker compose ps                              # semua "running"
```

| Cek | Perintah / tempat | Harus |
| --- | --- | --- |
| Layanan AI | `curl -s localhost:8001/health` | `"status":"ok"`, `"triase":true`, `"pencarian":true`, `"kualitas_model": {"lolos": true}` |
| Model lengkap | `ls ai/models ai/index` | `triage.joblib`, `jenis.joblib`, `chunks.parquet`, `vectors.npy` (dari Drive, README C2; tidak dilatih ulang) |
| Katalog layanan & FAQ terindeks | `curl -s localhost:8001/metrics \| grep index_chunks` | ±4.263 potongan (tiket + 9 KB + 16 layanan). Kurang → `seed_halosis.py` (FAQ Email/SSO/SiPecut), lalu `plugin:install --force` saat `halosis-ai` hidup |
| Role Keycloak = JSON | konsol http://localhost:8180 (realm halosis) › Users › Role mapping | `budi`/`siti`/`maya`/`ani` = pegawai, `rina` = operator, dst. sesuai `keycloak/halosis-realm.json` |
| Mailpit | http://localhost:8025 | Terbuka; hapus email lama (ikon tempat sampah) agar notifikasi demo mudah ditemukan |
| Tugas terjadwal | GLPI › Setup › Tindakan otomatis | `IncidentPattern` & `TriageRetry` aktif (mode CLI) |
| Cache | `docker compose exec glpi php bin/console cache:clear` | Setelah update plugin/template |

## 3. Browser

- [ ] Kosongkan cache/situs `localhost:8080` atau pakai profil browser baru (aset CSS/JS plugin terbaru).
- [ ] **Satu akun per jendela** (sesi GLPI berbasis cookie): jendela biasa `budi` (Pegawai), jendela privat `rina`
  (Operator), profil browser kedua `andi` (Tim Teknis) dan `sri` (Manajemen). Password semua `halosis`.
- [ ] Zoom 110–125% untuk proyektor; tab Mailpit terbuka.

## 4. Rencana cadangan

| Masalah | Tindakan saat demo |
| --- | --- |
| `halosis-ai` mati/lambat | Lanjut: tiket tetap tersimpan (UC-03 alur alternatif); chatbot memakai pencarian kata kunci KB dan triase **mode demo** (aturan kata kunci); sebut sebagai bukti NFR-03. `TriageRetry` membuat saran yang terlewat dalam 15 menit; untuk langsung: tombol **Buat saran AI** di panel. Pulihkan: `docker compose restart halosis-ai` |
| Keycloak mati | Login `glpi` (akun lokal darurat) untuk menunjukkan sisi petugas; `docker compose restart keycloak` |
| Data demo berantakan | `scripts/demo_snapshot.sh pulihkan` (±15 detik, kembali ke snapshot) |
| Pola insiden tidak muncul | Setup › Tindakan otomatis › IncidentPattern › **Jalankan**; butuh ≥ 3 insiden mirip dalam 60 menit |
| Email tidak masuk | Notifikasi browser (lonceng) tetap jalan; cek `use_notifications` di README langkah 5b |

## 5. Skrip bicara singkat

| Langkah | Akun | Yang ditunjukkan | Kalimat kunci (acuan dokumen) |
| --- | --- | --- | --- |
| 0 Di luar TI | budi | "Bagaimana mengajukan cuti?" → diarahkan ke Kepegawaian, tanpa tiket | "HaloSIS fokus layanan TI; pertanyaan lain diarahkan ke unit yang tepat." (wawancara Operator) |
| 1 Chatbot | budi | Login SSO → Tanya HaloSIS, chip FASIH, privasi, "Maksud Anda…?" ("lampiran besar"), Belum terselesaikan → laporan | "Pegawai mencari solusi sendiri dulu; jawaban hanya dari Pusat Bantuan, data pribadi disamarkan, laporan otomatis berisi ringkasan." (UC-01, UC-02, BR-01, BR-04, NFR-06) |
| 2 Validasi | rina | Panel Saran AI: tingkat keyakinan, 3 kandidat & beban tim, Terima/Ubah/Tolak, Riwayat | "AI menyarankan, Operator memutuskan; setiap keputusan dan alasannya tercatat." (UC-04, UC-05, BR-05, BR-06, HITL) |
| 2b Telepon | rina | Tiket atas nama pegawai lain | "Laporan telepon/walk-in tetap masuk jalur yang sama." (EI input tiket operator) |
| 3 Penanganan | andi | Panel tanpa tombol keputusan, Kembalikan ke operator, solusi | "Tim Teknis fokus menyelesaikan; salah tim bisa dikembalikan dengan alasan." (UC-06, BR-02 SLA respons & penyelesaian) |
| 4 Konfirmasi | budi | Approve / Refuse dengan alasan, survei | "Tiket ditutup oleh pegawai, bukan sepihak." (UC-07) |
| 2d SLA resmi | rina | Buat permintaan kategori **Jaringan & Perangkat > Server Hosting** → kolom SLA: respons 15 menit + pemenuhan 14 hari; insiden biasa → 15 menit + Medium 8 hari | "SLA mengikuti kebijakan BPS yang tercatat di history ESTIM, dihitung jam kerja." (BR-02, T22) |
| 5b Siap ditutup | rina | Menu **Siap ditutup**: tiket Selesai tanpa respons > 48 jam → Tutup per tiket/massal | "Penutupan tetap keputusan manusia; menghapus antrean tiket menggantung." (5.1, T21) |
| 5 Kinerja AI | sri, dimas | Dashboard: KPI tabel 1.3 (SLA breach, median penugasan, L1), volume per minggu, % diterima, drift, tren pola, filter, ekspor koreksi | "Manajemen memantau apakah AI bisa dipercaya dari keputusan petugas." (UC-08, BR-08, BP-17, BP-19) |
| Bonus | glpi + rina | 3 laporan SSO mirip → Problem pola + banner + notifikasi | "Lonjakan insiden terdeteksi lebih awal; tindak lanjut tetap oleh Operator." (BR-07, UC-08, BP-21) |
| Knowledge | lina | Kandidat → draf artikel, tab Perlu ditinjau | "Solusi tiket menjadi pengetahuan yang dikurasi dan ditinjau berkala." (UC-09, BR-03, KR-02) |

## 6. Setelah demo

- [ ] `scripts/demo_snapshot.sh pulihkan` bila laptop dipakai demo berikutnya.
- [ ] Profile opsional dimatikan: `docker compose --profile tls --profile monitoring stop`.
