# Audit kelengkapan HaloSIS terhadap dokumen perancangan

Sumber: *Kelompok 4 AKPSI-5.pdf* (212 halaman; ekstrak teks `docs/dokumen.txt`, di-ignore git).
Objek audit: repo `glpi-halosis` (plugin `plugins/halosis`, `ai/`, skrip setup/seed, `docker-compose.yml`, README)
dan aplikasi lokal `http://localhost:8080`. Tanggal audit: 29 Okt 2026. Audit saja, tidak ada perubahan kode.

Status: ✅ Ada · 🟡 Sebagian · ❌ Belum · ⚪ Di luar cakupan prototipe.
Bukti "uji skenario" merujuk ke uji end-to-end 12 langkah yang lolos (tiket #55 dan #57), uji peringatan SLA
(tiket #58), dan tangkapan layar di `screenshot/modernisasi/`.

## Ringkasan

| Kelompok | Jumlah | ✅ | 🟡 | ❌ | ⚪ |
| --- | ---: | ---: | ---: | ---: | ---: |
| Business Requirements (BR-01..08) | 8 | 5 | 3 | 0 | 0 |
| Functional Requirements (FR-01..10) | 10 | 7 | 3 | 0 | 0 |
| Non-Functional Requirements (NFR-01..14) | 14 | 5 | 6 | 0 | 3 |
| Use Case (UC-01..10, termasuk alur alternatif) | 10 | 7 | 3 | 0 | 0 |
| Hasil & keputusan PoC (2.4.7) | 6 | 3 | 2 | 1 | 0 |
| Komponen arsitektur TO-BE (Tabel 2.10) | 10 | 5 | 2 | 0 | 3 |
| **Total** | **58** | **32** | **19** | **1** | **6** |

**Pembaruan 29 Okt 2026:** P1 #2, #3, #4, #6 sudah dikerjakan (lihat status "Diperbaiki" di tabel); sisa P1: #1
(deteksi pola semantik) dan #5 (re-index otomatis).

Kesimpulan awal: alur inti dokumen (chat → tiket → triase AI + HITL → penanganan → konfirmasi → SLA → knowledge)
berjalan end-to-end. Celah terbesar ada di **deteksi pola semantik** (dokumen: embedding + DBSCAN; sistem:
kata kunci judul/kategori), **pencatatan retrieval & latensi AI**, **re-index otomatis knowledge**, dan beberapa
teknologi yang berbeda dari PoC (embedding, LLM, vector DB).

## 1. Business Requirements (Tabel 1.2, hal. 5–6)

| Kode | Kebutuhan (ringkas) | Status | Bukti | Catatan |
| --- | --- | --- | --- | --- |
| BR-01 | Konfigurasi service catalog, workflow, role, tim, SLA, notifikasi, rule tanpa ubah source core | ✅ | Menu Administrator `dimas` (`src/RoleMenu.php::admin`): Service catalog, Kategori, SLA, Tim, Pengguna & role, Workflow & aturan, Notifikasi; `setup-roles`, `setup_sla_alerts.py`, `setup_list_columns.py` hanya memakai API/konfigurasi GLPI | Template notifikasi butuh hak `config` (Super-Admin); dijelaskan di README UC-10 |
| BR-02 | SLA otomatis, status & risiko keterlambatan, peringatan ke operator/tim | ✅ | `setup_sla_alerts.py`: aturan "SLA <prioritas>" + level "Peringatan risiko SLA" (−1 jam s.d. −24 jam) + notifikasi *Ticket Recall* ke teknisi, grup, supervisor; uji tiket #58 → penerima andi, yoga, hendra; menu Monitoring SLA | Email belum diuji (SMTP belum ada); notifikasi browser terbukti |
| BR-03 | Knowledge management: KB, SOP, service catalog, solusi historis, hasil tiket; dapat dikurasi | 🟡 | KB GLPI + Kandidat Knowledge (`src/KnowledgeCandidates.php`, `/plugins/halosis/Kandidat`): solusi tiket selesai & klaster solusi history (`ai/halosis_ai/candidates.py`) → draf artikel | SOP & service catalog tidak masuk indeks; indeks dibangun ulang manual (`ai/scripts/build_index.py`) |
| BR-04 | Semantic retrieval knowledge/tiket historis | ✅ | `ai/halosis_ai/search.py::cari` (embedding `intfloat/multilingual-e5-base`); `/chat` mengembalikan sumber artikel & "Tiket serupa …"; `ai/tests/test_search.py` | Model berbeda dari PoC (lihat §7) |
| BR-05 | Rekomendasi kategori, dampak, urgensi, prioritas, routing + validasi | 🟡 | Panel Saran AI (`src/TriagePanel.php`, `src/Triage.php::suggestService`), model `triase-tfidf-lr` (`reports/triase.md`) | Model memprediksi **tim**; kategori dipetakan dari tim, dampak/urgensi dari aturan kata kunci (`suggestDemo`), prioritas dari matriks GLPI |
| BR-06 | Percakapan self-service cek knowledge sebelum tiket, lanjut tiket bila belum selesai | ✅ | `/plugins/halosis/Chat` (`src/Chatbot.php`, `public/js/chat.js`); tawaran laporan + ringkasan percakapan (`Chatbot::summaryHtml`); uji skenario UC-01..03 | Jawaban ekstraktif (tanpa LLM) sesuai keputusan "tanpa API berbayar" |
| BR-07 | Deteksi kemiripan/pengelompokan/lonjakan tiket → peringatan dini | 🟡 | `src/PatternDetector.php` (tugas `IncidentPattern` tiap 15 menit, jendela `pattern_window` 60 menit, ambang `pattern_min_tickets` 10) → Problem "Pola insiden" + banner beranda | Kemiripan = kategori sama / judul mirip (kata kunci), **bukan semantik**; tanpa analisis tren temporal |
| BR-08 | Terima/ubah/tolak rekomendasi AI, penjelasan, audit trail | ✅ | `Triage::decide` (alasan wajib ≥ 5 karakter untuk Ubah/Tolak), tabel `glpi_plugin_halosis_decisions`, `Log::history` di tab Riwayat tiket, penjelasan + 3 tim teratas di panel | — |

## 2. Functional Requirements (§4.2.1, hal. 77–78)

| Kode | Kebutuhan (ringkas) | Status | Bukti | Catatan |
| --- | --- | --- | --- | --- |
| FR-01 | Satu pintu masuk utama: Self-Service Conversation | ✅ | Pegawai (Helpdesk) diarahkan ke `/plugins/halosis/Chat` (`src/HelpdeskHome.php`); menu Tanya HaloSIS paling atas | — |
| FR-02 | Self-service melalui AI chatbot | ✅ | `src/Chatbot.php`, `ai/service/app.py` `/chat`; riwayat & lanjut otomatis (`src/Chat.php`, `/plugins/halosis/ChatHistory`) | — |
| FR-03 | Pencarian knowledge berbasis keyword **dan** semantic untuk pengguna/agent | 🟡 | Pengguna: semantik (`/chat`); agent: menu "Cari knowledge" = pencarian kata kunci bawaan GLPI; mode demo `src/KnowledgeSearch.php` | Agent belum punya pencarian semantik; tidak ada penggabungan (hybrid) skor |
| FR-04 | Analisis pola kemiripan request/incident dalam time window, dikirim ke operator untuk validasi | 🟡 | `PatternDetector::detect` (jendela waktu), Problem ditugaskan ke grup Operator, operator konfirmasi/tutup (hak ubah Masalah) | Kemiripan berbasis kata kunci, bukan semantik |
| FR-05 | Agent menerima, menolak, mengubah rekomendasi AI | ✅ | Tombol Terima/Ubah/Tolak (`templates/triase_panel.html.twig`, `ajax/triase.php`); uji skenario UC-04/05 | — |
| FR-06 | Tiket Request/Incident dari percakapan; status, assignment, update, resolution, closure, history | ✅ | `Chatbot` membuat tiket dengan ringkasan; siklus tiket GLPI; uji skenario (#57: Baru → Diproses → Selesai → Ditutup) | — |
| FR-07 | Mengarahkan, memantau, mengonfirmasi penyelesaian | ✅ | "Laporan saya", Approve/Refuse solusi (Refuse wajib alasan, ditegakkan GLPI); uji UC-07 | — |
| FR-08 | Mencatat rekomendasi kategori & impact/urgency yang terpercaya | ✅ | Tabel `glpi_plugin_halosis_suggestions` (model, keyakinan, penjelasan); kalibrasi di `reports/triase.md` (keyakinan ≥ 70% → akurasi 87,03%) | Impact/urgency berbasis aturan (lihat BR-05) |
| FR-09 | Hitung & pantau SLA sesuai policy; eskalasi saat melewati threshold | ✅ | Aturan SLA per prioritas + peringatan sebelum batas + level "Eskalasi SLA terlewati" (Ticket Recall ke ketua tim & Operator, prioritas → Sangat tinggi) di `setup_sla_alerts.py`; tiket uji #59: prioritas 3 → 5, penerima rina, andi, yoga, hendra | Diperbaiki (#4) |
| FR-10 | Pelaporan operasional & SLA; loading & reconciliation data migrasi | 🟡 | Laporan: dashboard kinerja AI, Statistik GLPI; rekonsiliasi: `ai/scripts/reconcile.py` → `reports/rekonsiliasi.md` | Data history tidak di-*load* ke GLPI (hanya dibersihkan & direkonsiliasi); seed memakai data contoh |

## 3. Non-Functional Requirements (§4.2.2, hal. 78–79)

| Kode | Kebutuhan (ringkas) | Status | Bukti | Catatan / pengganti |
| --- | --- | --- | --- | --- |
| NFR-01 | Uji portal & API pada beban normal, peak, stress | ⚪ | — | Butuh lingkungan produksi. Pengganti: rencana uji (k6/Locust untuk `/front/ticket.php`, `/apirest.php`, `/chat`) + pengukuran satu pengguna |
| NFR-02 | Target ketersediaan core ITSM sesuai SLA internal | ⚪ | `restart: unless-stopped` di `docker-compose.yml` | Butuh HA/infra BPS. Pengganti: rancangan HA (replika DB, 2 node GLPI di balik load balancer) |
| NFR-03 | Timeout, retry, error handling, idempotency | 🟡 | Timeout `service_timeout`/`ai_timeout` (`src/Ai/Service.php`, `src/Ai/Client.php`); AI gagal → tiket tetap tersimpan, mode demo; skrip setup & seed idempoten; `UNIQUE(source, source_ref)` kandidat | Sengaja tanpa retry (tiket menunggu); tidak ada antrean ulang triase otomatis |
| NFR-04 | Scale-out API, worker, AI | ⚪ | Layanan `halosis-ai` terpisah (`docker-compose.yml`) | Pengganti: AI sudah stateless & terpisah → bisa direplikasi; worker = cron GLPI dalam container |
| NFR-05 | Autentikasi, otorisasi, enkripsi, API security, vulnerability testing | 🟡 | Login GLPI + RBAC per profil (`src/Roles.php`), re-auth area sensitif, CSRF/`X-Requested-With`, API key AI terenkripsi (`src/Config.php`), klien API dibatasi IP, port AI hanya `127.0.0.1` | Belum TLS, belum SSO BPS, password demo bawaan, belum uji kerentanan |
| NFR-06 | Data ke AI mengikuti data minimization | ✅ | `ai/halosis_ai/privacy.py` (email, NIP, NIK, HP, rahasia, nama), pindai ulang sebelum simpan (`prepare_data.py::residual_pii`), `src/Privacy.php` sebelum kirim; `ai/tests/test_privacy.py`; `.gitignore` data | Batasan: nama tanpa sapaan & tidak ada di kolom pengguna tidak terdeteksi |
| NFR-07 | Rekomendasi & keputusan dapat ditelusuri ke aktor & waktu | ✅ | `glpi_plugin_halosis_decisions` (users_id, date_creation), `reassignments`, keputusan kandidat (`users_id`, `date_decision`), tab Riwayat, Audit trail `/front/event.php` | — |
| NFR-08 | Self-service tanpa pemahaman teknis ITSM | 🟡 | Menu Helpdesk ringkas (5 item), chat dengan saran pertanyaan, tampilan HP 390px (`screenshot/modernisasi/`) | Belum ada uji usability dengan pengguna |
| NFR-09 | Monitoring/logging aplikasi, API, AI, DB, infra | 🟡 | `files/_log/halosis.log`, log GLPI, `GET /health` layanan AI, log latensi AI (`ai/logs/latency.jsonl`), `docker compose logs` | Belum ada metrik/monitoring terpusat (Prometheus/Grafana/Loki disebut di dokumen) |
| NFR-10 | Kustomisasi GLPI minimal | ✅ | Tidak ada perubahan kode inti; kustomisasi = plugin + palet `themes/halosis.scss` + konfigurasi | — |
| NFR-11 | Integrasi via API; AI dapat diganti tanpa ganti core | ✅ | Plugin → HTTP `service_url` (`src/Ai/Service.php`) → FastAPI; penyedia Claude/OpenAI-kompatibel opsional (`src/Ai/Client.php`); fallback demo | — |
| NFR-12 | Latensi AI: retrieval, generation, end-to-end terpisah | ✅ | `ai/service/app.py::record_latency` → `ai/logs/latency.jsonl` (angka saja); `ai/scripts/latency_report.py` → `reports/latensi.md` (chat retrieval p50 91 ms / p95 454 ms; triase p50 13 ms); `ai/tests/test_service.py::test_log_latensi_tanpa_teks` | Diperbaiki (#2); generation hanya bila Claude aktif |
| NFR-13 | Referential integrity & audit trail pada migrasi/transaksi | 🟡 | Transaksi lewat API/ORM GLPI; rekonsiliasi `reconcile.py` (sumber = berhasil + gagal ✓) | Migrasi nyata ke GLPI belum dilakukan |
| NFR-14 | Kepemilikan AI release, threshold, knowledge source, override, audit | 🟡 | Ambang & fitur di Pengaturan AI (hak `plugin_halosis_config`), versi model tercatat per saran, human override + audit | Belum ada dokumen/proses rilis model & pemilik sumber knowledge |

## 4. Use Case UC-01..UC-10 (Tabel 6.4–6.13, hal. 128–142)

| UC | Nama | Status | Bukti (normal flow) | Alur alternatif/pengecualian | Catatan |
| --- | --- | --- | --- | --- | --- |
| UC-01 | Berkonsultasi melalui AI Chatbot | ✅ | `/plugins/halosis/Chat`: catat percakapan, jawaban + sumber, rating (`glpi_plugin_halosis_chats.rating`) | 4a tidak ditemukan → tawaran laporan ✅; 6a belum selesai → laporan + ringkasan ✅; 6b tidak lapor → riwayat tersimpan ✅; 3a AI tidak tersedia → pemberitahuan + arah ke portal (`.hc-unavailable`) ✅ | — |
| UC-02 | Mencari Knowledge Relevan | ✅ | Masking → embedding → cari KB & tiket historis → skor `CHAT_MIN_SCORE` 0,83 → sumber (`ai/service/app.py`, `search.py`) | 7a skor di bawah ambang → "belum menemukan" ✅; **4a vector DB tidak merespons** → `AiException` → kutipan KB mode demo (`Chatbot.php`) ✅ | Langkah 8 diperbaiki (#2): log retrieval per permintaan (skor teratas, mode, durasi) di `latency.jsonl` |
| UC-03 | Membuat Tiket | ✅ | "Buat laporan" (`/ServiceCatalog`) atau dari chat; status Baru; SLA mulai (aturan SLA); triase AI; antrean validasi | 1a dari chat → S-1 ringkasan otomatis ✅; 4a data belum lengkap → validasi (judul min. 5 karakter / form GLPI) ✅; AI tidak tersedia → tiket tersimpan, triase manual ✅ | Notifikasi konfirmasi: hanya browser (SMTP belum) |
| UC-04 | Rekomendasi Triase & Routing | ✅ | `Triage::generate` saat `item_add`; keyakinan, penjelasan, tiket mirip; disimpan di `suggestions` | AI tidak tersedia → tanpa saran, tombol "Buat saran AI" ✅; keyakinan < ambang → "Perlu penilaian manual" ✅ | Dampak/urgensi berbasis aturan |
| UC-05 | Validasi Rekomendasi & Meneruskan | ✅ | Menu Antrean validasi (urut waktu penyelesaian), Terima → tiket ditugaskan, keputusan tercatat | S-1 Ubah + alasan ✅; S-2 Tolak + alasan ✅; operator menyelesaikan langsung (solusi GLPI) ✅ | — |
| UC-06 | Menangani & Menyelesaikan Tiket | ✅ | Menu Tiket saya & tim; panel Saran AI (tiket mirip); solusi → Selesai; solusi masuk Kandidat knowledge | Penugasan tidak sesuai → **Kembalikan ke operator** + alasan, `reassignments.kind=return` ✅; S-1 Pending (status Menunggu GLPI) ✅ | — |
| UC-07 | Memantau Status & Konfirmasi | ✅ | "Laporan saya" dengan kolom Waktu untuk menyelesaikan, Approve → Ditutup, survei kepuasan GLPI 100% tiket ditutup (`setup_list_columns.py`) | 3a follow-up ✅; 5a Refuse wajib alasan → diproses lagi ✅ | Diperbaiki (#3) |
| UC-08 | Memantau SLA & Pola Insiden | 🟡 | Cron `slaticket` + peringatan ke petugas & ketua tim ✅; cron `IncidentPattern` → Problem + banner; dashboard (filter periode `/plugins/halosis/Dashboard`); tautkan tiket ke Masalah (Operator) | 3a/4a tanpa peringatan bila tidak ada risiko/lonjakan ✅; 7a ✅ | Pengelompokan **bukan semantik** (dokumen: "AI Engine mengelompokkan berdasarkan kemiripan semantik") |
| UC-09 | Mengelola Knowledge Base | 🟡 | Kandidat dari tiket Selesai + klaster AI, sunting & terbitkan artikel KB, revisi artikel bawaan GLPI (`KnowbaseItem_Revision`) | 3a/3b perbarui/buat baru ✅; 5a draf (Jadikan artikel = draf tanpa target) ✅ | Langkah 7 **re-index embedding otomatis** belum ada (manual `build_index.py` + restart `halosis-ai`) |
| UC-10 | Mengonfigurasi Platform ITSM | 🟡 | Admin console `dimas`, RBAC, simpan tanpa kode, audit trail (`system_logs`) | 2a tanpa hak → 403 / menu tidak tampil ✅ (pencatatan percobaan akses mengikuti log GLPI); 5a validasi (mis. URL layanan AI, rentang ambang di `Config.php`) ✅ | Langkah 6 **pratinjau dampak** & notifikasi perubahan ke pihak terkait belum ada; template notifikasi butuh `config` |

## 5. Hasil & keputusan PoC (§2.4.7, hal. 48–60)

| Butir | Dokumen | Implementasi | Status | Catatan |
| --- | --- | --- | --- | --- |
| Model embedding | `paraphrase-multilingual-MiniLM-L12-v2` (hal. 54, 56) | `intfloat/multilingual-e5-base` (`ai/halosis_ai/search.py`, `/health`) | 🟡 | Model lebih besar, sama-sama multilingual & lokal; belum ada perbandingan terdokumentasi |
| LLM | Qwen2.5 3B via Ollama; keputusan akhir: RAG grounded, bukan LLM bebas (hal. 54–55) | Default **ekstraktif** (kutipan artikel, tanpa LLM); Claude opsional via `ANTHROPIC_API_KEY` | 🟡 | Sejalan dengan prinsip "grounded"; tidak ada LLM lokal |
| Metode triase + metrik | TF-IDF vs embedding, 39 grup: Top-1 68,33/70,43%, Top-3 90,89/90,29%, MRR 0,7989/0,8092; confidence-aware + HITL (hal. 54) | TF-IDF + regresi logistik terkalibrasi, 21 kelas: Top-1 74,41%, Top-3 93,07%, F1 makro 67,69%, ambang keyakinan 70% (`reports/triase.md`) | ✅ | MRR tidak dilaporkan; jumlah kelas berbeda (tim < 30 tiket → "Lainnya") sehingga angka tidak sebanding langsung |
| Deteksi pola | Embedding + DBSCAN (eps 0,25; min 5) → 14 klaster; sliding window 1 jam, similarity 0,70, min. 3 insiden (hal. 56) | Kategori sama / kemiripan judul kata kunci, jendela 60 menit, min. 10 tiket (`PatternDetector.php`) | ❌ | Metode berbeda: tanpa embedding, tanpa DBSCAN, tanpa threshold similarity 0,70 |
| HITL | Approval native GLPI + audit (hal. 57) | Panel Saran AI Terima/Ubah/Tolak + alasan + audit; Approve/Refuse solusi | ✅ | Melebihi PoC (keputusan per rekomendasi) |
| Evidence Maturity | Klasifikasi Proven PoC / Partially proven per area (hal. 59) | Tabel Evidence Maturity implementasi di README "Keputusan desain & keterbatasan" | ✅ | Diperbaiki (#6) |

## 6. Komponen arsitektur TO-BE (Tabel 2.10, hal. 22; BP-24/25, hal. 120–121)

| Komponen | Status | Bukti | Catatan |
| --- | --- | --- | --- |
| Frontend / web | ✅ | UI GLPI + halaman plugin (Chat, Riwayat, Dashboard, Kandidat) + palet HaloSIS | Prototipe Next.js `halosis-web 2` terpisah, tidak terhubung ke GLPI |
| Application / core ITSM | ✅ | GLPI 12.0.0 (`docker-compose.yml`, layanan `glpi`) | — |
| Database | ✅ | MySQL 8.4 (layanan `db`), tabel plugin `glpi_plugin_halosis_*` (`hook.php`) | — |
| Worker / scheduler | ✅ | Cron GLPI dalam container tiap 60 detik (mode CLI): `slaticket`, `queuednotification`, `IncidentPattern` | Tidak dipisah ke container sendiri |
| AI integration | ✅ | `src/Ai/Service.php` → FastAPI `halosis-ai` (`/triage`, `/chat`, `/kandidat`, `/health`) | — |
| Vector database | 🟡 | Indeks file `ai/index/chunks.parquet` + `vectors.npy`, pencarian kosinus di memori | Bukan layanan vector DB (dokumen: "dapat memakai servis BPS") |
| Logging / monitoring | 🟡 | `halosis.log`, log GLPI, Audit trail, `/health` | Tanpa metrik & dashboard observability |
| Reverse proxy / load balancer | ⚪ | — | Infra produksi; lokal cukup port 8080 |
| CI / CD / registry | ⚪ | — | Pengganti: alur git `dev`/`master` di README |
| Backup / DR | ⚪ | Volume Docker `db_data`, `glpi_data` | Pengganti: prosedur `mysqldump` + uji restore (rencana) |

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
| AI Engine (aktor sistem) | layanan `halosis-ai` | UC-02, UC-04 (+UC-08, UC-09) | `/chat` (retrieval), `/triage`, `/kandidat`; deteksi pola **tidak** memakai AI Engine |
| (di luar dokumen) | glpi · Super-Admin | — | Pengelola instalasi: plugin, profil, pengaturan umum |

## 8. Ketidaksesuaian dengan dokumen & dampaknya

| Area | Dokumen | Sistem | Dampak |
| --- | --- | --- | --- |
| Embedding | MiniLM-L12-v2 | multilingual-e5-base | Hasil retrieval tidak bisa dibandingkan langsung dengan PoC; model ±2× lebih besar (unduhan ±1 GB, startup lebih lama). Perlu disebut sebagai keputusan desain |
| LLM | Qwen2.5 3B (Ollama) untuk RAG | Tanpa LLM (ekstraktif); Claude opsional | Jawaban berupa kutipan, bukan ringkasan natural; risiko halusinasi nol; BR-06 tetap terpenuhi |
| Vector DB | Vector database (layanan) | File numpy di memori | Cukup untuk ±ribuan potongan; tidak ada update inkremental → re-index manual (UC-09 langkah 7) |
| Deteksi pola | Semantik (DBSCAN / similarity 0,70) + temporal | Kata kunci kategori/judul + jendela waktu | Laporan bertema sama tetapi berbeda kata ("lemot" vs "lambat") tidak terkelompok; BR-07, FR-04, UC-08 hanya sebagian |
| Triase | Routing ke 39 grup | 21 kelas (tim kecil → "Lainnya"); dampak/urgensi berbasis aturan | Tim kecil tidak pernah disarankan; BR-05 sebagian untuk dampak/urgensi |
| SSO | Pre-kondisi UC-03: login SSO BPS | Login lokal GLPI | Hanya untuk prototipe |
| Frontend | Portal (prototipe Next.js) | UI GLPI + plugin bertema | Tampilan mengikuti prototipe, tetapi aplikasi Next.js tidak dipakai |

## 9. Daftar perbaikan berprioritas

### P1 — wajib sebelum demo/pengumpulan

| # | Perbaikan | Menutup | Usaha | File |
| --- | --- | --- | --- | --- |
| 1 | Deteksi pola semantik: endpoint `/pola` di `halosis-ai` (embedding tiket baru dalam jendela 1 jam, similarity ≥ 0,70 atau DBSCAN eps 0,25), dipanggil `PatternDetector` dengan fallback kata kunci | BR-07, FR-04, UC-08, PoC | sedang | `ai/service/app.py`, `ai/halosis_ai/patterns.py` (baru), `ai/tests/test_patterns.py`, `plugins/halosis/src/PatternDetector.php`, `src/Config.php` |
| 2 | ✅ Selesai — Log retrieval + latensi terpisah (retrieval, generation, end-to-end) per permintaan `/chat` & `/triage`, plus laporan ringkas | UC-02 langkah 8, NFR-12, NFR-09 | kecil | `ai/service/app.py`, `plugins/halosis/src/Chatbot.php` (simpan skor & durasi), `reports/latensi.md` |
| 3 | ✅ Selesai — UC-07: kolom "Waktu untuk menyelesaikan" di Laporan saya + aktifkan survei kepuasan saat penutupan | UC-07 langkah 2 & 5 | kecil | `setup_list_columns.py`, skrip setup (konfigurasi entitas `inquest_config/inquest_rate`), README |
| 4 | ✅ Selesai — Eskalasi setelah SLA terlampaui (level SLA pada t = batas: notifikasi ke ketua tim / naikkan prioritas) | FR-09 | kecil | `setup_sla_alerts.py`, README 5b |
| 5 | Re-index knowledge setelah artikel diterbitkan (endpoint `/reindex` atau tugas terjadwal + muat ulang indeks) | UC-09 langkah 7, BR-03 | sedang | `ai/service/app.py`, `ai/scripts/build_index.py`, `plugins/halosis/hook.php`/`setup.php` (hook `item_update` KnowbaseItem) |
| 6 | ✅ Selesai — Dokumentasikan ketidaksesuaian teknologi (§8) + tabel Evidence Maturity implementasi | PoC, NFR-14 | kecil | `README.md`, `ai/README.md` |

### P2 — sebaiknya

| # | Perbaikan | Menutup | Usaha | File |
| --- | --- | --- | --- | --- |
| 7 | Model dampak/urgensi dari history (bukan aturan) | BR-05, FR-08 | sedang | `ai/halosis_ai/triage_model.py`, `ai/scripts/train_triage.py`, `src/Triage.php` |
| 8 | Pencarian semantik untuk agent (Operator/Tim Teknis) di halaman plugin | FR-03 | sedang | controller & template baru di plugin, `src/RoleMenu.php` |
| 9 | Uji email notifikasi dengan SMTP lokal (mis. container Mailpit) | BR-02, UC-03 | kecil | `docker-compose.yml`, README |
| 10 | Rencana uji performa & latensi (k6/Locust) + hasil satu pengguna | NFR-01, NFR-12 | sedang | `docs/` atau `reports/rencana_uji.md`, skrip uji |
| 11 | Hardening: ganti password bawaan, TLS reverse proxy, checklist keamanan | NFR-05 | sedang | `docker-compose.yml`, README |
| 12 | Uji usability singkat (5 pegawai, tugas UC-01/03/07) | NFR-08 | kecil | `reports/usability.md` |
| 13 | Endpoint metrik (`/metrics`) layanan AI | NFR-09 | kecil | `ai/service/app.py`, `ai/requirements-service.txt` |

### P3 — opsional

| # | Perbaikan | Menutup | Usaha | File |
| --- | --- | --- | --- | --- |
| 14 | Vector DB sungguhan (pgvector/Qdrant) | Arsitektur | sedang | `docker-compose.yml`, `ai/halosis_ai/search.py`, `build_index.py` |
| 15 | LLM lokal Qwen2.5 3B via Ollama sebagai perangkum RAG (tanpa biaya API) | PoC LLM | sedang | `docker-compose.yml`, `ai/service/app.py` |
| 16 | Pratinjau dampak perubahan konfigurasi (UC-10 langkah 6) | UC-10 | besar | plugin (halaman baru) |
| 17 | Memisahkan worker/cron ke container sendiri, CI, backup terjadwal | Arsitektur | sedang | `docker-compose.yml`, `.github/workflows/` |
| 18 | Menghubungkan prototipe Next.js ke API GLPI | Frontend | besar | `halosis-web 2/` |
