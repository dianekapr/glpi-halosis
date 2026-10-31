# Audit kelengkapan HaloSIS terhadap dokumen perancangan

Sumber: *Kelompok 4 AKPSI-6.pdf* (212 halaman; ekstrak teks `docs/dokumen.txt`, di-ignore git).
Objek audit: repo `glpi-halosis` (plugin `plugins/halosis`, `ai/`, skrip setup/seed, `docker-compose.yml`, README)
dan aplikasi lokal `http://localhost:8080`. Tanggal audit: 29 Okt 2026.

Status: ✅ Ada · 🟡 Sebagian · ❌ Belum · ⚪ Di luar cakupan prototipe.
Bukti "uji skenario" merujuk ke uji end-to-end 12 langkah yang lolos (tiket #55 dan #57), uji peringatan SLA
(tiket #58), dan tangkapan layar di `screenshot/modernisasi/`.

## Ringkasan

| Kelompok | Jumlah | ✅ | 🟡 | ❌ | ⚪ |
| --- | ---: | ---: | ---: | ---: | ---: |
| Business Requirements (BR-01..08) | 8 | 8 | 0 | 0 | 0 |
| Functional Requirements (FR-01..10) | 10 | 10 | 0 | 0 | 0 |
| Non-Functional Requirements (NFR-01..14) | 14 | 8 | 4 | 0 | 2 |
| Use Case (UC-01..10, termasuk alur alternatif) | 10 | 10 | 0 | 0 | 0 |
| Hasil & keputusan PoC (2.4.7) | 6 | 5 | 1 | 0 | 0 |
| Komponen arsitektur TO-BE (Tabel 2.10) | 10 | 6 | 2 | 0 | 2 |
| **Total** | **58** | **47** | **7** | **0** | **4** |

**Pembaruan 29 Okt 2026:** semua P1 (#1–#6) selesai; status "Diperbaiki" di tabel menunjukkan butirnya.

**Pembaruan 31 Okt 2026:** revisi dari [`audit_dokumen_e2e.md`](audit_dokumen_e2e.md): SLA respons, keyakinan
3 tingkat, pola hanya INC + tambah ke Problem terbuka + notifikasi, artikel "Perlu ditinjau", sesi chat 30 menit,
sumber tiket "HaloSIS Chat", hitungan pemakaian artikel, hak hapus tiket dicabut; NFR-14 → ✅.

**Pembaruan 31 Okt 2026:** beban kerja per kandidat tim, filter dashboard tim & kategori, umpan balik agent di Cari
knowledge, dashboard BP-13/17/19 (artikel tidak membantu, pola terdeteksi/dikonfirmasi/ditutup, drift bulanan),
ekspor koreksi CSV, flag data DQR-02/04, chatbot keyakinan sedang, atribut NIP/unit kerja/jabatan dari Keycloak.
Status tabel di bawah tidak berubah: sisa 🟡 di sini (SOP belum diindeks, dampak/urgensi berbasis aturan, migrasi
belum di-load, NFR produksi, pratinjau UC-10) bukan bagian revisi ini. Ringkasan saat itu 38 ✅ · 14 🟡 · 6 ⚪.

**Pembaruan 31 Okt 2026 (bukti uji):** BR-03 → ✅ (SOP & katalog layanan terindeks), embedding PoC → ✅ (banding
MiniLM vs e5), MRR triase 0,8420 (historis; kini 0,8563), uji beban Normal layanan AI, uji backup–restore DB (455 tabel, jumlah baris sama,
pulih 6 dtk), tanggal tinjau per artikel (KR-03), tren pola 12 minggu (BP-21). BR-05/FR-08: dampak/urgensi tetap
aturan karena history tidak punya kolomnya (*historis: ekspor lama; lihat Pembaruan 1 Nov*). Ringkasan: **40 ✅ · 12 🟡 · 6 ⚪**.

**Pembaruan 31 Okt 2026 (kesiapan demo):** regresi 17 langkah skenario demo lolos (`uji_regresi_demo.md`, 3 bug
tampilan diperbaiki); NFR-03 → ✅ (`TriageRetry`), DBSCAN opsional + banding (`banding_pola.md`) → PoC pola ✅;
NFR-01 ⚪ → 🟡 (Peak 50 VU & Stress sampai 200 VU tidak jenuh, API GLPI Normal); TLS (profile `tls`) & monitoring
(profile `monitoring`) opsional; FR-10 & NFR-13 → ✅ (migrasi sampel 200 tiket + rekonsiliasi). Belum: LLM lokal
(profile `llm`). Ringkasan: **44 ✅ · 9 🟡 · 5 ⚪**.

**Pembaruan 31 Okt 2026 (hari demo):** arsip migrasi dikecualikan dari tugas plugin & sampel dihapus; arsitektur
§6: monitoring ✅, reverse proxy 🟡; UC-10 → ✅ (pratinjau dampak + jejak & pemberitahuan konfigurasi); T4 jenis
REQ/INC ✅; uji beban halaman GLPI menemukan & menutup bug login bersamaan; snapshot demo (`scripts/demo_snapshot.sh`)
& `checklist_demo.md`. Ringkasan: **46 ✅ · 8 🟡 · 4 ⚪**.

**Pembaruan 31 Okt 2026 (selaras bab analisis, plugin 1.0.0):** Siap ditutup (T21), SLA per layanan dari
`config/sla_layanan.json` (T22, BR-02 diperkuat), notifikasi balasan ke teknisi & grup (T23), KPI tabel 1.3 & volume
per minggu (T24/T25), rate limit AI (T26), uji upgrade 12.0.0 → 12.0.1 (T27), FAQ Email/SSO/SiPecut (T30), chatbot
non-TI (T31), gerbang kualitas model (T32); `rencana_implementasi.md`, `panduan_peran.md`; regresi demo 17 langkah
lolos. Status tabel tidak berubah (butir baru berasal dari bab analisis, dicatat di `audit_dokumen_e2e.md` §8).
Ringkasan tetap **46 ✅ · 8 🟡 · 4 ⚪**.

**Pembaruan 31 Okt 2026 (data history versi baru):** ekspor 220 kolom (rekonsiliasi lama vs baru di
`reports/rekonsiliasi.md`); solusi knowledge = pesan terakhir ≤ resolved + 5 menit bukan dari pemohon
(`reports/banding_solusi.md`, dedup ditolak gerbang); triase & jenis dilatih ulang (lolos gerbang); model prioritas
diganti model urgensi + sinyal dampak (BR-05/FR-08/P2 #7); baseline dashboard SLA 28,87% (extended, 1.819 berimputasi)
& kepuasan 95,76% ≥ 4; NIP lama 9 digit disamarkan.

**Pembaruan 31 Okt 2026 (koreksi konsistensi):** BR-05 & P2 #7 satu narasi (*historis:* dampak/urgensi tanpa kolom → aturan;
prioritas dari proksi SLA ditolak gerbang, F1 makro 44,80% = pembanding); BR-02 SLA resmi BPS + peringatan ±20% jam
kerja; FR-09 disamakan dengan kode (eskalasi = recall, prioritas tidak diubah; bukti tiket uji #1044). Status tidak
berubah: **46 ✅ · 8 🟡 · 4 ⚪**.

**Pembaruan 1 Nov 2026 (data versi baru, finalisasi konsistensi):** urgensi insiden kini ambang per kelas dari validasi silang 5 lipatan: Rendah bila P(Low) ≥ 0,90 → presisi 78,79% (Wilson 95% 62,25–89,32%; pembanding proporsi Low 18,76%), recall 5,12%, 33 tiket; Sedang bila P(Low) ≤ 0,45 → akurasi 84,30% (pembanding 81,24%), cakupan 76,70%; di antaranya aturan kata kunci. **Kedua kelas lolos gerbang per kelas** →
**BR-05 🟡 → ✅** (keterbatasan: Rendah hanya mengenali ± 5% insiden Low, sisanya aturan; Sedang lolos tipis). Angka
triase disinkronkan ke model `20261031` (Top-1 75,88%, Top-3 94,87%, MRR 0,8563, akurasi pada ambang 88,35%), jenis
T4 (akurasi 68,25%, F1 makro 67,52%, ≥ 70% → 83,96% pada 40,80% tiket), retrieval (72,74% ekspor lama vs 72,50%
indeks aktif, set berbeda), alasan DBSCAN eps 0,50 / min 3; baseline dashboard dua baris (dokumen 27,59% / 42,62%;
history versi baru 28,87% extended + respons 43,08%) dan cakupan rating 17,3%. Ringkasan: **47 ✅ · 7 🟡 · 4 ⚪**.

Kesimpulan: alur inti dokumen (chat → tiket → triase AI + HITL → penanganan → konfirmasi → SLA → knowledge)
berjalan end-to-end, termasuk deteksi pola semantik, re-index knowledge otomatis, eskalasi SLA, dan log latensi
AI, katalog layanan & SOP di indeks chatbot, serta dashboard dengan filter, drift, dan tren pola. Bukti uji ada untuk
retrieval (e5 mengungguli MiniLM PoC pada set uji yang sama), triase (Top-1 75,88%, Top-3 94,87%, MRR 0,8563), urgensi insiden per kelas, beban Normal layanan AI, dan
backup–restore DB, regresi 17 langkah skenario demo, serta migrasi sampel. Sisa celah: teknologi yang berbeda dari PoC (indeks file), cakupan saran
urgensi Rendah kecil (± 5% insiden Low; High/Critical & dampak tetap aturan + sinyal), LLM lokal belum dipasang, migrasi baru sampel 200 tiket, serta NFR
produksi (uji di lingkungan BPS, ketersediaan/HA, uji kerentanan, metrik GLPI & alert). Uji beban Normal/Peak/Stress
layanan AI dan Normal API GLPI lolos di laptop; TLS dan monitoring tersedia sebagai profile opsional.

## 1. Business Requirements (Tabel 1.2, hal. 5–6)

| Kode | Kebutuhan (ringkas) | Status | Bukti | Catatan |
| --- | --- | --- | --- | --- |
| BR-01 | Konfigurasi service catalog, workflow, role, tim, SLA, notifikasi, rule tanpa ubah source core | ✅ | Menu Administrator `dimas` (`src/RoleMenu.php::admin`): Service catalog, Kategori, SLA, Tim, Pengguna & role, Workflow & aturan, Notifikasi; `setup-roles`, `setup_sla_alerts.py`, `setup_list_columns.py` hanya memakai API/konfigurasi GLPI | Template notifikasi butuh hak `config` (Super-Admin); dijelaskan di README UC-10 |
| BR-02 | SLA otomatis, status & risiko keterlambatan, peringatan ke operator/tim | ✅ | **SLA resmi BPS dari history** (`config/sla_layanan.json`: respons 15 menit; insiden Crit 2 / Medium 8 / Low 15 hari; permintaan 7/14 hari) dipasang aturan "SLA BPS …" (`setup_sla_alerts.py`), kalender jam kerja; level "Peringatan risiko SLA" **±20% sebelum batas dalam jam kerja** + notifikasi *Ticket Recall* ke teknisi, grup, supervisor, Operator; menu Monitoring SLA; KPI kepatuhan sebanding baseline 28,87% (`overall_sla_result_extended`, 1.819 hasil berimputasi; `plugins/halosis/baseline.json`) + kepuasan pemohon vs baseline 95,76% ≥ 4 | Bukti: tiket uji #58 (penerima andi, yoga, hendra), #1044 (SLA resmi, recall ke andi, yoga, hendra, rina); email lewat Mailpit lokal |
| BR-03 | Knowledge management: KB, SOP, service catalog, solusi historis, hasil tiket; dapat dikurasi | ✅ | KB GLPI + Kandidat Knowledge (`src/KnowledgeCandidates.php`) → draf artikel; artikel terbit/dihapus langsung memperbarui indeks (`src/KnowledgeIndex.php` → `POST /reindex/artikel`) | Re-index otomatis diperbaiki (P1 #5). 31 Okt: SOP = artikel KB kategori "SOP" (terindeks saat terbit); katalog layanan (kategori Helpdesk & form) diindeks lewat `POST /reindex/layanan` (hook kategori/form + saat install), chatbot mengarahkan ke layanan |
| BR-04 | Semantic retrieval knowledge/tiket historis | ✅ | `ai/halosis_ai/search.py::cari` (embedding `intfloat/multilingual-e5-base`); `/chat` mengembalikan sumber artikel & "Tiket serupa …"; `ai/tests/test_search.py` | Model berbeda dari PoC (lihat §5 dan §8) |
| BR-05 | Rekomendasi kategori, dampak, urgensi, prioritas, routing + validasi | ✅ | Panel Saran AI (`src/TriagePanel.php`, `src/Triage.php::suggestService`), model `triase-tfidf-lr` (`reports/triase.md`); kategori dari tim, jenis REQ/INC dari model terpisah; **urgensi insiden dari model** `urgensi-tfidf-tim-lr` (`ai/scripts/train_urgensi.py`) bila kelasnya lolos & di atas ambangnya; **dampak = urgensi + sinyal** (≥ 3 tiket serupa / 60 menit atau layanan kritis, alasan tampil di panel); prioritas = matriks GLPI | History versi baru **memuat** urgency/impact/priority (dampak = urgensi 99,7%; 81% Medium, kemungkinan nilai bawaan). Model urgensi (1 Nov): ambang per kelas dari validasi silang 5 lipatan: Rendah bila P(Low) ≥ 0,90 → presisi 78,79% (Wilson 95% 62,25–89,32%; pembanding proporsi Low 18,76%), recall 5,12%, 33 tiket; Sedang bila P(Low) ≤ 0,45 → akurasi 84,30% (pembanding 81,24%), cakupan 76,70%; di antaranya aturan kata kunci. **Kedua kelas lolos gerbang per kelas**. **Keterbatasan cakupan Low:** hanya 5,12% insiden Low dikenali, sisanya aturan kata kunci; Sedang lolos tipis (syarat > 84,24%). Versi 31 Okt (satu ambang 70%, Low tidak pernah yakin) historis. High/Critical (21) & REQ: aturan + sinyal. Model prioritas lama (proksi tier SLA) dihapus (2.1.4: Priority P1, Urgency P2; E9) |
| BR-06 | Percakapan self-service cek knowledge sebelum tiket, lanjut tiket bila belum selesai | ✅ | `/plugins/halosis/Chat` (`src/Chatbot.php`, `public/js/chat.js`); tawaran laporan + ringkasan percakapan (`Chatbot::summaryHtml`); uji skenario UC-01..03 | Jawaban ekstraktif (tanpa LLM) sesuai keputusan "tanpa API berbayar" |
| BR-07 | Deteksi kemiripan/pengelompokan/lonjakan tiket → peringatan dini | ✅ | `ai/halosis_ai/patterns.py` + `POST /pola` (embedding e5 dipusatkan, rata-rata kemiripan ≥ 0,50, jendela 60 menit), dipanggil `PatternDetector::groupSemantic` dengan fallback kata kunci; metode dicatat di Problem; uji: 10 tiket "lemot/lambat/lelet" → Problem #4; `ai/tests/test_patterns.py` | Diperbaiki (P1 #1); tren pola per minggu per topik 12 minggu di dashboard (BP-21, 31 Okt) |
| BR-08 | Terima/ubah/tolak rekomendasi AI, penjelasan, audit trail | ✅ | `Triage::decide` (alasan wajib ≥ 5 karakter untuk Ubah/Tolak), tabel `glpi_plugin_halosis_decisions`, `Log::history` di tab Riwayat tiket, penjelasan + 3 tim teratas di panel | — |

## 2. Functional Requirements (§4.2.1, hal. 77–78)

| Kode | Kebutuhan (ringkas) | Status | Bukti | Catatan |
| --- | --- | --- | --- | --- |
| FR-01 | Satu pintu masuk utama: Self-Service Conversation | ✅ | Pegawai (Helpdesk) diarahkan ke `/plugins/halosis/Chat` (`src/HelpdeskHome.php`); menu Tanya HaloSIS paling atas | — |
| FR-02 | Self-service melalui AI chatbot | ✅ | `src/Chatbot.php`, `ai/service/app.py` `/chat`; riwayat & lanjut otomatis (`src/Chat.php`, `/plugins/halosis/ChatHistory`) | — |
| FR-03 | Pencarian knowledge berbasis keyword **dan** semantic untuk pengguna/agent | ✅ | Pengguna: semantik (`/chat`); agent (Operator & Tim Teknis): menu Cari knowledge → `/plugins/halosis/CariKnowledge` (`CariKnowledgeController`) → `POST /cari` semantik atas KB & tiket historis; layanan AI mati → kata kunci (`KnowledgeSearch::search`); uji rina/andi 10 hasil, sri 403 | Diperbaiki (P2 #8) |
| FR-04 | Analisis pola kemiripan request/incident dalam time window, dikirim ke operator untuk validasi | ✅ | `ai/halosis_ai/patterns.py` + `POST /pola` (embedding e5 dipusatkan, rata-rata kemiripan ≥ 0,50, jendela 60 menit), dipanggil `PatternDetector::groupSemantic` dengan fallback kata kunci; metode dicatat di Problem; uji: 10 tiket "lemot/lambat/lelet" → Problem #4; `ai/tests/test_patterns.py`; Problem ditugaskan ke grup Operator | Diperbaiki (P1 #1) |
| FR-05 | Agent menerima, menolak, mengubah rekomendasi AI | ✅ | Tombol Terima/Ubah/Tolak (`templates/triase_panel.html.twig`, `ajax/triase.php`); uji skenario UC-04/05 | — |
| FR-06 | Tiket Request/Incident dari percakapan; status, assignment, update, resolution, closure, history | ✅ | `Chatbot` membuat tiket dengan ringkasan; siklus tiket GLPI; uji skenario (#57: Baru → Diproses → Selesai → Ditutup) | — |
| FR-07 | Mengarahkan, memantau, mengonfirmasi penyelesaian | ✅ | "Laporan saya", Approve/Refuse solusi (Refuse wajib alasan, ditegakkan GLPI); uji UC-07 | — |
| FR-08 | Mencatat rekomendasi kategori & impact/urgency yang terpercaya | ✅ | Tabel `glpi_plugin_halosis_suggestions` (model, keyakinan, penjelasan, **`urgency_confidence`** = keyakinan urgensi model / 0 = aturan, **`impact_reason`** = alasan dampak naik); kalibrasi di `reports/triase.md` (triase keyakinan ≥ 70% → akurasi 88,35%); urgensi per kelas di `urgensi.metrics.json` (Rendah presisi 78,79%, Wilson 62,25–89,32%; Sedang akurasi 84,30%) | Urgensi insiden dari model hanya bila kelasnya lolos & di atas ambangnya; dampak dari aturan + sinyal (lihat BR-05) |
| FR-09 | Hitung & pantau SLA sesuai policy; eskalasi saat melewati threshold | ✅ | SLA resmi BPS + peringatan ±20% sebelum batas + level "Eskalasi SLA terlewati" tepat di batas: **Ticket Recall** ke teknisi, grup, ketua tim, Operator; **prioritas tidak diubah** (agar SLA resmi tiket tidak berganti) (`setup_sla_alerts.py`). Tiket uji #1044: eskalasi dipaksa → prioritas tetap 3, recall ke andi, yoga, hendra, rina | Diperbaiki (#4); 31 Okt: perilaku "prioritas → Sangat tinggi" (tiket uji lama #59) dihapus bersama SLA asumsi |
| FR-10 | Pelaporan operasional & SLA; loading & reconciliation data migrasi | ✅ | Laporan: dashboard kinerja AI, Statistik GLPI; rekonsiliasi: `ai/scripts/reconcile.py` → `reports/rekonsiliasi.md` | 31 Okt: **sampel 200 tiket history** di-*load* lewat API ke entitas terpisah "Arsip ESTIM" (`ai/scripts/migrate_sample.py`, idempoten, bisa dihapus): sumber 200 = berhasil 199 + gagal 1; migrasi penuh 6.682 tiket belum |

## 3. Non-Functional Requirements (§4.2.2, hal. 78–79)

| Kode | Kebutuhan (ringkas) | Status | Bukti | Catatan / pengganti |
| --- | --- | --- | --- | --- |
| NFR-01 | Uji portal & API pada beban normal, peak, stress | 🟡 | k6 (`tests/load/`): AI Normal 10 VU (galat 0%, `/chat` p95 140 ms), Peak 50 VU (0,03%, 223 ms), Stress 25→200 VU tidak jenuh (0,04%, 846 ms); API GLPI Normal 10 VU (0%, buat tiket p95 71 ms) ([`rencana_uji.md`](rencana_uji.md) §7) | Laptop, bukan lingkungan produksi. 31 Okt: + halaman GLPI Normal 10 VU (login SSO → daftar tiket: 0% galat, p95 56–60 ms); uji ini menemukan & menutup bug login bersamaan (plugin sempat dinonaktifkan GLPI) |
| NFR-02 | Target ketersediaan core ITSM sesuai SLA internal | ⚪ | `restart: unless-stopped` di `docker-compose.yml` | Butuh HA/infra BPS. Pengganti: rancangan HA (replika DB, 2 node GLPI di balik load balancer) |
| NFR-03 | Timeout, retry, error handling, idempotency | ✅ | Timeout `service_timeout`/`ai_timeout` (`src/Ai/Service.php`, `src/Ai/Client.php`); AI gagal → tiket tetap tersimpan, mode demo; skrip setup & seed idempoten; `UNIQUE(source, source_ref)` kandidat | Tanpa retry saat tiket disimpan (tiket tidak menunggu); **tugas terjadwal `TriageRetry`** (tiap 15 menit, 31 Okt) membuat saran untuk tiket Baru tanpa saran, idempoten, maks. 5 percobaan per tiket, tercatat di log (`src/TriageRetry.php`) |
| NFR-04 | Scale-out API, worker, AI | ⚪ | Layanan `halosis-ai` terpisah (`docker-compose.yml`) | Pengganti: AI sudah stateless & terpisah → bisa direplikasi; worker = cron GLPI dalam container |
| NFR-05 | Autentikasi, otorisasi, enkripsi, API security, vulnerability testing | 🟡 | Login GLPI + RBAC per profil (`src/Roles.php`), re-auth area sensitif, CSRF/`X-Requested-With`, API key AI terenkripsi (`src/Config.php`), klien API dibatasi IP, port AI hanya `127.0.0.1` | TLS opsional (profile `tls`, Caddy, sertifikat internal, HSTS, cookie `Secure`, 31 Okt); belum SSO BPS, password demo bawaan, belum uji kerentanan |
| NFR-06 | Data ke AI mengikuti data minimization | ✅ | `ai/halosis_ai/privacy.py` (email, NIP, NIK, HP, rahasia, nama), pindai ulang sebelum simpan (`prepare_data.py::residual_pii`), `src/Privacy.php` sebelum kirim; `ai/tests/test_privacy.py`; `.gitignore` data | Batasan: nama tanpa sapaan & tidak ada di kolom pengguna tidak terdeteksi |
| NFR-07 | Rekomendasi & keputusan dapat ditelusuri ke aktor & waktu | ✅ | `glpi_plugin_halosis_decisions` (users_id, date_creation), `reassignments`, keputusan kandidat (`users_id`, `date_decision`), tab Riwayat, Audit trail `/front/event.php` | — |
| NFR-08 | Self-service tanpa pemahaman teknis ITSM | 🟡 | Menu Helpdesk ringkas (5 item), chat dengan saran pertanyaan, tampilan HP 390px (`screenshot/modernisasi/`) | Belum ada uji usability dengan pengguna |
| NFR-09 | Monitoring/logging aplikasi, API, AI, DB, infra | 🟡 | `files/_log/halosis.log`, log GLPI, `GET /health` layanan AI, log latensi AI (`ai/logs/latency.jsonl`), `GET /metrics` Prometheus layanan AI (jumlah permintaan, durasi per endpoint, ukuran indeks), `docker compose logs` | Metrik AI ditambahkan (P2 #13); 31 Okt: profile `monitoring` (Prometheus + mysqld-exporter + Grafana, dasbor terprovisi: status, permintaan & latensi p95 AI, galat 5xx, MySQL). Belum: metrik aplikasi GLPI & host, alert |
| NFR-10 | Kustomisasi GLPI minimal | ✅ | Tidak ada perubahan kode inti; kustomisasi = plugin + palet `themes/halosis.scss` + konfigurasi | — |
| NFR-11 | Integrasi via API; AI dapat diganti tanpa ganti core | ✅ | Plugin → HTTP `service_url` (`src/Ai/Service.php`) → FastAPI; penyedia Claude/OpenAI-kompatibel opsional (`src/Ai/Client.php`); fallback demo | — |
| NFR-12 | Latensi AI: retrieval, generation, end-to-end terpisah | ✅ | `ai/service/app.py::record_latency` → `ai/logs/latency.jsonl` (angka saja); `ai/scripts/latency_report.py` → `reports/latensi.md` (chat retrieval p50 91 ms / p95 454 ms; triase p50 13 ms); `ai/tests/test_service.py::test_log_latensi_tanpa_teks` | Diperbaiki (#2); generation hanya bila Claude aktif |
| NFR-13 | Referential integrity & audit trail pada migrasi/transaksi | ✅ | Transaksi lewat API/ORM GLPI; rekonsiliasi `reconcile.py` (sumber = berhasil + gagal ✓) | Migrasi sampel lewat API GLPI (riwayat & entitas tercatat), `externalid` = nomor tiket sumber untuk penelusuran, rekonsiliasi sumber = berhasil + dilewati + gagal ✅ (`rekonsiliasi.md`); skala penuh belum |
| NFR-14 | Kepemilikan AI release, threshold, knowledge source, override, audit | ✅ | Ambang & fitur di Pengaturan AI (hak `plugin_halosis_config`), versi model tercatat per saran, human override + audit; `reports/tata_kelola_ai.md`: RACI, siklus rilis model, pemilik sumber & **per domain** knowledge (31 Okt) | Proses umpan balik Ubah/Tolak ke data latih masih manual |

## 4. Use Case UC-01..UC-10 (Tabel 6.4–6.13, hal. 128–142)

| UC | Nama | Status | Bukti (normal flow) | Alur alternatif/pengecualian | Catatan |
| --- | --- | --- | --- | --- | --- |
| UC-01 | Berkonsultasi melalui AI Chatbot | ✅ | `/plugins/halosis/Chat`: catat percakapan, jawaban + sumber, rating (`glpi_plugin_halosis_chats.rating`) | 4a tidak ditemukan → tawaran laporan ✅; 6a belum selesai → laporan + ringkasan ✅; 6b tidak lapor → riwayat tersimpan ✅; 3a AI tidak tersedia → pemberitahuan + arah ke portal (`.hc-unavailable`) ✅ | — |
| UC-02 | Mencari Knowledge Relevan | ✅ | Masking → embedding → cari KB & tiket historis → skor `CHAT_MIN_SCORE` 0,83 → sumber (`ai/service/app.py`, `search.py`) | 7a skor di bawah ambang → "belum menemukan" ✅; **4a vector DB tidak merespons** → `AiException` → kutipan KB mode demo (`Chatbot.php`) ✅ | Langkah 8 diperbaiki (#2): log retrieval per permintaan (skor teratas, mode, durasi) di `latency.jsonl` |
| UC-03 | Membuat Tiket | ✅ | "Buat laporan" (`/ServiceCatalog`) atau dari chat; status Baru; SLA mulai (aturan SLA); triase AI; antrean validasi | 1a dari chat → S-1 ringkasan otomatis ✅; 4a data belum lengkap → validasi (judul min. 5 karakter / form GLPI) ✅; AI tidak tersedia → tiket tersimpan, triase manual ✅ | Notifikasi konfirmasi email terbukti di Mailpit lokal (tiket uji #70, P2 #9) |
| UC-04 | Rekomendasi Triase & Routing | ✅ | `Triage::generate` saat `item_add`; keyakinan, penjelasan, tiket mirip, tiket aktif per kandidat tim (31 Okt); disimpan di `suggestions` | AI tidak tersedia → tanpa saran, tombol "Buat saran AI" ✅; keyakinan 3 tingkat (31 Okt): ≥ 70% "Disarankan", 40–69% "Pilih dari 3 kandidat", < 40% "Perlu penilaian manual" ✅ | Urgensi insiden Rendah/Sedang dari model (ambang per kelas, gerbang per kelas); High/Critical, REQ & dampak dari aturan + sinyal; prioritas = matriks |
| UC-05 | Validasi Rekomendasi & Meneruskan | ✅ | Menu Antrean validasi (urut waktu penyelesaian), Terima → tiket ditugaskan, keputusan tercatat | S-1 Ubah + alasan ✅; S-2 Tolak + alasan ✅; operator menyelesaikan langsung (solusi GLPI) ✅ | — |
| UC-06 | Menangani & Menyelesaikan Tiket | ✅ | Menu Tiket saya & tim; panel Saran AI (tiket mirip); solusi → Selesai; solusi masuk Kandidat knowledge | Penugasan tidak sesuai → **Kembalikan ke operator** + alasan, `reassignments.kind=return` ✅; S-1 Pending (status Menunggu GLPI) ✅ | — |
| UC-07 | Memantau Status & Konfirmasi | ✅ | "Laporan saya" dengan kolom Waktu untuk menyelesaikan, Approve → Ditutup, survei kepuasan GLPI 100% tiket ditutup (`setup_list_columns.py`) | 3a follow-up ✅; 5a Refuse wajib alasan → diproses lagi ✅ | Diperbaiki (#3) |
| UC-08 | Memantau SLA & Pola Insiden | ✅ | Cron `slaticket` + peringatan & eskalasi ke petugas, ketua tim, operator; cron `IncidentPattern` → `/pola` semantik (fallback kata kunci) → Problem + banner; dashboard (filter periode, tim, kategori); tautkan tiket ke Masalah | 3a/4a/7a ✅ | Diperbaiki (P1 #1) |
| UC-09 | Mengelola Knowledge Base | ✅ | Kandidat dari tiket Selesai + klaster AI, sunting & terbitkan artikel KB, revisi artikel bawaan GLPI (`KnowbaseItem_Revision`); langkah 7: hook `item_add/item_update/item_purge` KnowbaseItem & target visibilitas → `/reindex/artikel` (uji: artikel FAQ baru langsung ditemukan chat, setelah dihapus hilang; `ai/tests/test_reindex.py`) | 3a/3b perbarui/buat baru ✅; 5a draf ✅; gagal re-index → artikel tetap tersimpan, pesan "memakai indeks lama" | Diperbaiki (P1 #5) |
| UC-10 | Mengonfigurasi Platform ITSM | ✅ | Admin console `dimas`, RBAC, simpan tanpa kode, audit trail (`system_logs`) | 2a tanpa hak → 403 / menu tidak tampil ✅ (pencatatan percobaan akses mengikuti log GLPI); 5a validasi (mis. URL layanan AI, rentang ambang di `Config.php`) ✅ | 31 Okt: langkah 6 **pratinjau dampak** ambang AI (saran 30 hari yang berpindah tingkat) + log sebelum/sesudah & Catatan untuk Administrator saat Pengaturan AI, aturan SLA, SLA, atau kategori berubah (`src/ConfigAudit.php`); pratinjau aturan SLA/kategori belum |

## 5. Hasil & keputusan PoC (§2.4.7, hal. 48–60)

| Butir | Dokumen | Implementasi | Status | Catatan |
| --- | --- | --- | --- | --- |
| Model embedding | `paraphrase-multilingual-MiniLM-L12-v2` (hal. 54, 56) | `intfloat/multilingual-e5-base` (`ai/halosis_ai/search.py`, `/health`) | ✅ | Dibandingkan pada set uji yang sama ([`banding_embedding.md`](banding_embedding.md)): e5 Top-1 72,74% / Top-3 89,62% / MRR 0,8144 vs MiniLM 67,99% / 83,55% / 0,7650 (ekspor lama, 906 kueri. Indeks aktif (ekspor baru, 1.069 kueri Jul–Ags, aturan solusi baru): Top-1 72,50% / Top-3 89,06% / MRR 0,8115; 73,15% = aturan solusi lama pada ekspor baru ([`banding_solusi.md`](banding_solusi.md)). Korpus & kueri berbeda, jadi 73,15% vs 72,74% bukan selisih model (galat baku Top-1 ± 1,4 poin)) |
| LLM | Qwen2.5 3B via Ollama; keputusan akhir: RAG grounded, bukan LLM bebas (hal. 54–55) | Default **ekstraktif** (kutipan artikel, tanpa LLM); Claude opsional via `ANTHROPIC_API_KEY` | 🟡 | Sejalan dengan prinsip "grounded"; tidak ada LLM lokal |
| Metode triase + metrik | TF-IDF vs embedding, 39 grup: Top-1 68,33/70,43%, Top-3 90,89/90,29%, MRR 0,7989/0,8092; confidence-aware + HITL (hal. 54) | TF-IDF + regresi logistik terkalibrasi, 21 kelas (model `20261031`, history versi baru): Top-1 75,88%, Top-3 94,87%, MRR 0,8563, F1 makro 69,00%, ambang keyakinan 70% → akurasi 88,35% pada 50,67% tiket (`reports/triase.md`, `triage.metrics.json`) | ✅ | Model lama `20261028` pada set uji sama: 74,47% / 93,01% / MRR 0,8422 (74,41% / 0,8420 = angka ekspor lama, historis); jumlah kelas berbeda (tim < 30 tiket → "Lainnya") sehingga angka tidak sebanding langsung |
| Deteksi pola | Embedding + DBSCAN (eps 0,25; min 5) → 14 klaster; sliding window 1 jam, similarity 0,70, min. 3 insiden (hal. 56) | Embedding e5 dipusatkan + pengelompokan rakus average-link, ambang 0,50, jendela 60 menit, **min. 3 tiket** (`pattern_min_tickets`, sesuai PoC) (`patterns.py`, `/pola`); fallback kata kunci | ✅ | Metode bawaan rata-rata kemiripan + opsi **DBSCAN** (eps & min_samples di Pengaturan AI, 31 Okt); banding pada 666 insiden Jul–Ags: setara (7 vs 8 kelompok, kemurnian tim 0,905 vs 0,917; [`banding_pola.md`](banding_pola.md)); eps 0,50 / min_samples 3 vs PoC 0,25 / 5: eps PoC untuk MiniLM tanpa pemusatan, pada e5 dipusatkan jarak tiket bertopik sama ± 0,4; min 3 = aturan PoC "minimal 3 insiden" per jendela 1 jam (min 5 jarang tercapai, rata-rata 3,8 insiden per blok berisi) |
| HITL | Approval native GLPI + audit (hal. 57) | Panel Saran AI Terima/Ubah/Tolak + alasan + audit; Approve/Refuse solusi | ✅ | Melebihi PoC (keputusan per rekomendasi) |
| Evidence Maturity | Klasifikasi Proven PoC / Partially proven per area (hal. 59) | Tabel Evidence Maturity implementasi di README "Keputusan desain & keterbatasan" | ✅ | Diperbaiki (#6) |

## 6. Komponen arsitektur TO-BE (Tabel 2.10, hal. 22; BP-24/25, hal. 120–121)

| Komponen | Status | Bukti | Catatan |
| --- | --- | --- | --- |
| Frontend / web | ✅ | UI GLPI + halaman plugin (Chat, Riwayat, Dashboard, Kandidat) + palet HaloSIS | Prototipe Next.js `halosis-web 2` terpisah, tidak terhubung ke GLPI |
| Application / core ITSM | ✅ | GLPI 12.0.0 (`docker-compose.yml`, layanan `glpi`) | — |
| Database | ✅ | MySQL 8.4 (layanan `db`), tabel plugin `glpi_plugin_halosis_*` (`hook.php`) | — |
| Worker / scheduler | ✅ | Cron GLPI dalam container tiap 60 detik (mode CLI): `slaticket`, `queuednotification`, `IncidentPattern`, `TriageRetry` (NFR-03) | Tidak dipisah ke container sendiri; tugas plugin mengecualikan entitas arsip |
| AI integration | ✅ | `src/Ai/Service.php` → FastAPI `halosis-ai` (`/triage`, `/chat`, `/cari`, `/pola`, `/kandidat`, `/reindex/artikel`, `/reindex/layanan`, `/health`, `/metrics`) | — |
| Vector database | 🟡 | Indeks file `ai/index/chunks.parquet` + `vectors.npy`, kosinus di memori; pembaruan inkremental per artikel KB dengan lock + tulis atomik (`search.update_article`) | Bukan layanan vector DB (dokumen: "dapat memakai servis BPS") |
| Logging / monitoring | ✅ | `halosis.log`, log GLPI, Audit trail, `/health`, log latensi AI, `GET /metrics`; profile `monitoring`: Prometheus (target AI & MySQL) + Grafana dasbor terprovisi | Opsional (profile); belum metrik aplikasi GLPI & alert |
| Reverse proxy / load balancer | 🟡 | Profile `tls`: Caddy reverse proxy HTTPS https://localhost:8443 (HSTS, cookie `Secure`) | Belum load balancer/replika; sertifikat internal |
| CI / CD / registry | ⚪ | — | Pengganti: alur git `dev`/`master` di README |
| Backup / DR | ⚪ | Volume Docker `db_data`, `glpi_data`; prosedur & uji restore di [`keamanan_backup.md`](keamanan_backup.md) | Backup terjadwal & DR lintas lokasi di luar prototipe |

## 7. Matriks keterlacakan Aktor/Role → Use Case → fitur/menu

| Aktor (Tabel 6.1) | Akun & profil GLPI | Use case | Fitur / menu di sistem |
| --- | --- | --- | --- |
| Pegawai BPS (Requester) | budi, siti, maya · Pegawai (Helpdesk) | UC-01, UC-03, UC-07 | Tanya HaloSIS, Buat laporan, Laporan saya (Approve/Refuse), Pusat bantuan (FAQ), Riwayat chat |
| Petugas Layanan TI (abstrak) | — (diwariskan ke Operator & Tim Teknis) | UC-08 | Monitoring SLA, Pola insiden |
| Operator HaloSIS | rina · Operator | UC-05, UC-08 | Antrean validasi, Semua tiket, panel Saran AI (Terima/Ubah/Tolak), Pola insiden (ubah), Cari knowledge |
| Tim Teknis (Resolver) | andi, yoga, fajar, dedi · Tim Teknis; ketua tim hendra, agus, rudi, wati (supervisor grup) | UC-06, UC-08 | Tiket saya & tim, panel Saran AI (lihat, Kembalikan ke operator), solusi, Monitoring SLA, peringatan risiko SLA (ketua tim) |
| Manajemen / Pimpinan | sri · Manajemen (hanya-baca) | UC-08 | Dashboard kinerja, Kinerja AI, Monitoring SLA, Pola insiden, Laporan (Statistik) |
| Knowledge Manager | lina · Knowledge Manager | UC-09 | Kandidat knowledge (Jadikan artikel / Abaikan), Daftar artikel, Tulis artikel |
| Administrator Sistem | dimas · Administrator | UC-10 | Admin console, Service catalog, Kategori, SLA, Tim, Pengguna & role, Workflow & aturan, Pengaturan AI, Notifikasi, Audit trail |
| AI Engine (aktor sistem) | layanan `halosis-ai` | UC-02, UC-04 (+UC-08, UC-09) | `/chat` (retrieval), `/cari` (Cari knowledge, FR-03), `/triage`, `/pola` (deteksi pola semantik, UC-08), `/kandidat`, `/reindex/artikel` & `/reindex/layanan` (UC-09, BR-03) |
| (di luar dokumen) | glpi · Super-Admin | — | Pengelola instalasi: plugin, profil, pengaturan umum |

## 8. Ketidaksesuaian dengan dokumen & dampaknya

| Area | Dokumen | Sistem | Dampak |
| --- | --- | --- | --- |
| Embedding | MiniLM-L12-v2 | multilingual-e5-base | **Sudah dibandingkan** pada set uji yang sama (`banding_embedding.md`): e5 Top-1 72,74% / MRR 0,8144 vs MiniLM 67,99% / 0,7650 (ekspor lama, 906 kueri; indeks aktif ekspor baru 1.069 kueri Top-1 72,50%, set berbeda); biaya: model ±2× lebih besar, pengodean ±4× lebih lambat (8 ms/kueri) |
| LLM | Qwen2.5 3B (Ollama) untuk RAG | Tanpa LLM (ekstraktif); Claude opsional | Jawaban berupa kutipan, bukan ringkasan natural; risiko halusinasi nol; BR-06 tetap terpenuhi |
| Vector DB | Vector database (layanan) | File numpy di memori, update inkremental per artikel | Cukup untuk ±ribuan potongan; tanpa layanan terpisah, skala & konkurensi terbatas pada satu instans `halosis-ai` |
| Deteksi pola | Embedding + DBSCAN, similarity 0,70, min. 3 | Embedding e5 dipusatkan, rata-rata kemiripan ≥ 0,50, min. 3, jendela 60 menit; fallback kata kunci | DBSCAN tersedia sebagai opsi (eps 0,50 / min 3 vs PoC 0,25 / 5, alasan di `banding_pola.md`) dan dibandingkan; bawaan tetap rata-rata kemiripan karena setara, lebih cepat, dan tidak menarik tiket lain lewat efek rantai |
| Triase | Routing ke 39 grup | 21 kelas (tim kecil → "Lainnya"; Top-1 75,88% / Top-3 94,87%); urgensi insiden Rendah/Sedang dari model dengan ambang per kelas, dampak = urgensi + sinyal | Tim kecil tidak pernah disarankan; label urgensi history lemah (81% Medium); Rendah hanya ± 5% insiden Low |
| SSO | Pre-kondisi UC-03: login SSO BPS | SSO **Keycloak lokal** (realm `halosis`, password grant dari form HaloSIS) | Belum diuji ke SSO BPS; cukup ganti URL/realm/client |
| Frontend | Portal (prototipe Next.js) | UI GLPI + plugin bertema | Tampilan mengikuti prototipe, tetapi aplikasi Next.js tidak dipakai |

## 9. Daftar perbaikan berprioritas

### P1 — wajib sebelum demo/pengumpulan

| # | Perbaikan | Menutup | Usaha | File |
| --- | --- | --- | --- | --- |
| 1 | ✅ Selesai — Deteksi pola semantik: endpoint `/pola` di `halosis-ai` (embedding tiket baru dalam jendela 1 jam, similarity ≥ 0,70 atau DBSCAN eps 0,25), dipanggil `PatternDetector` dengan fallback kata kunci | BR-07, FR-04, UC-08, PoC | sedang | `ai/service/app.py`, `ai/halosis_ai/patterns.py` (baru), `ai/tests/test_patterns.py`, `plugins/halosis/src/PatternDetector.php`, `src/Config.php` |
| 2 | ✅ Selesai — Log retrieval + latensi terpisah (retrieval, generation, end-to-end) per permintaan `/chat` & `/triage`, plus laporan ringkas | UC-02 langkah 8, NFR-12, NFR-09 | kecil | `ai/service/app.py`, `plugins/halosis/src/Chatbot.php` (simpan skor & durasi), `reports/latensi.md` |
| 3 | ✅ Selesai — UC-07: kolom "Waktu untuk menyelesaikan" di Laporan saya + aktifkan survei kepuasan saat penutupan | UC-07 langkah 2 & 5 | kecil | `setup_list_columns.py`, skrip setup (konfigurasi entitas `inquest_config/inquest_rate`), README |
| 4 | ✅ Selesai — Eskalasi setelah SLA terlampaui (level SLA tepat di batas: Ticket Recall ke tim, ketua tim, Operator; prioritas tidak diubah) | FR-09 | kecil | `setup_sla_alerts.py`, README 5b |
| 5 | ✅ Selesai — Re-index knowledge setelah artikel diterbitkan/dihapus (`POST /reindex/artikel`, hook KnowbaseItem) | UC-09 langkah 7, BR-03 | sedang | `ai/service/app.py`, `ai/halosis_ai/search.py`, `plugins/halosis/src/KnowledgeIndex.php`, `setup.php`, `ai/tests/test_reindex.py` |
| 6 | ✅ Selesai — Dokumentasikan ketidaksesuaian teknologi (§8) + tabel Evidence Maturity implementasi | PoC, NFR-14 | kecil | `README.md`, `ai/README.md` |

### P2 — sebaiknya

| # | Perbaikan | Menutup | Usaha | File |
| --- | --- | --- | --- | --- |
| 7 | ✅ Selesai (1 Nov, dengan keterbatasan) — History versi baru memuat urgensi/dampak/prioritas: **satu model urgensi insiden** (Medium vs Low; dampak = urgensi 99,7%, prioritas = matriks) dengan ambang per kelas dari validasi silang 5 lipatan: Rendah bila P(Low) ≥ 0,90 → presisi 78,79% (Wilson 95% 62,25–89,32%; pembanding proporsi Low 18,76%), recall 5,12%, 33 tiket; Sedang bila P(Low) ≤ 0,45 → akurasi 84,30% (pembanding 81,24%), cakupan 76,70%; di antaranya aturan kata kunci. **Kedua kelas lolos gerbang per kelas**; dampak = urgensi + sinyal (tiket serupa / layanan kritis). Batas: 81% Medium kemungkinan nilai bawaan formulir, Rendah hanya ± 5% insiden Low (sisanya aturan); High/Critical & REQ tetap aturan (2.1.4: Priority P1, Urgency P2; E9) | BR-05, FR-08 | sedang | `ai/scripts/train_urgensi.py`, `reports/triase.md`, README Keputusan desain |
| 8 | ✅ Selesai — Pencarian semantik untuk agent (Operator/Tim Teknis) di halaman plugin | FR-03 | sedang | controller & template baru di plugin, `src/RoleMenu.php` |
| 9 | ✅ Selesai — Uji email notifikasi dengan SMTP lokal (mis. container Mailpit) | BR-02, UC-03 | kecil | `docker-compose.yml`, README |
| 10 | ✅ Selesai — Rencana uji performa & latensi (k6) + hasil Normal, Peak, Stress (AI) & Normal (API GLPI) | NFR-01, NFR-12 | sedang | [`reports/rencana_uji.md`](rencana_uji.md) |
| 11 | 🟡 Sebagian — Checklist keamanan & backup; TLS lewat profile `tls` (Caddy, lokal); password demo masih bawaan | NFR-05 | sedang | [`reports/keamanan_backup.md`](keamanan_backup.md) |
| 12 | 🟡 Sebagian — Template uji usability tersedia; **sesi dengan pegawai belum** dilakukan | NFR-08 | kecil | [`reports/usability.md`](usability.md) |
| 13 | ✅ Selesai — Endpoint metrik (`/metrics`) layanan AI | NFR-09 | kecil | `ai/service/app.py`, `ai/requirements-service.txt` |

### P3 — opsional

| # | Perbaikan | Menutup | Usaha | File |
| --- | --- | --- | --- | --- |
| 14 | Vector DB sungguhan (pgvector/Qdrant) | Arsitektur | sedang | `docker-compose.yml`, `ai/halosis_ai/search.py`, `build_index.py` |
| 15 | LLM lokal Qwen2.5 3B via Ollama sebagai perangkum RAG (tanpa biaya API) | PoC LLM | sedang | `docker-compose.yml`, `ai/service/app.py` |
| 16 | 🟡 Sebagian — Pratinjau dampak **ambang AI** ✅; jejak & pemberitahuan perubahan Pengaturan AI/aturan SLA/SLA/kategori ✅; pratinjau dampak **aturan SLA/kategori** belum (pakai Rules › Test) | UC-10 | besar | `src/ConfigAudit.php` |
| 17 | Memisahkan worker/cron ke container sendiri, CI, backup terjadwal | Arsitektur | sedang | `docker-compose.yml`, `.github/workflows/` |
| 18 | Menghubungkan prototipe Next.js ke API GLPI | Frontend | besar | `halosis-web 2/` |
