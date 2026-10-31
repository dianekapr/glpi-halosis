# Audit end-to-end: dokumen *Kelompok 4 AKPSI-6* vs implementasi HaloSIS

Tanggal: 30 Okt 2026. Pembanding: README `dev` terbaru (SSO Keycloak, `/CariKnowledge`, `/metrics`, Mailpit) dan
`reports/audit_kelengkapan.md`. Audit ini membaca **seluruh bab** yang berdampak ke sistem, termasuk bagian yang
belum dicakup audit sebelumnya: Technical Requirements (§4.2.3), TO-BE & 25 Business Process (§5.2–5.3),
CRC card & class diagram (§7), sequence & state machine (§8), dan batas scope (§1.7).

Status: ✅ sesuai · 🟡 sebagian · ❌ belum · 🔍 perlu dicek di kode (README tidak menyebut) · ⚪ di luar prototipe.

**Pembaruan akhir 31 Okt 2026 (plugin 1.0.0):** §8 baru memetakan bab analisis & kelayakan: T21–T32 (11 ✅,
2 ✅ dokumen), risiko R1–R4 & risiko organisasi → mitigasi, KPI tabel 1.3 → tempat ukur, syarat 2.1.2–2.1.6 &
Skenario 2.

**Pembaruan 31 Okt 2026:** semua 🔍 sudah dicek di kode (bukti `file:baris`). Diperbaiki: T1/T19, T2, T6, T8,
T9, T12, T14, T15 (kode); T7, T16, T20, KR-01, DQR-05, §5, §6 (dokumentasi). Sisa: T3, T4, T5, T10 (otomatis),
T11, T13 (uji demo), T18, KR-03, KR-07, DQR-02, DQR-04, BP-13/17/19/21.

**Pembaruan 31 Okt 2026:** diperbaiki T3, T5, T10, T11, T13 (uji), T18, KR-07, DQR-02, DQR-04, BP-13/17/19;
T4 diputuskan sebagai keterbatasan terdokumentasi. Sisa: BP-25 ⚪.

**Pembaruan 31 Okt 2026 (lanjutan):** KR-03 (tanggal tinjau per artikel) dan BP-21 (tren pola 12 minggu) ✅;
katalog layanan & SOP masuk indeks chatbot (BR-03). Bukti uji baru: MRR triase, banding embedding, uji beban
Normal layanan AI, uji backup–restore (lihat `audit_kelengkapan.md`).

**Cakupan pembacaan.** Seluruh teks 212 halaman, ditambah **semua gambar yang memodelkan sistem**: arsitektur &
alur TO-BE (hal. 96–102, 106–108, 122), PoC (hal. 53–59), use case diagram (hal. 125), 10 activity diagram
(hal. 144–153), class diagram (hal. 170), 10 sequence diagram (hal. 176–185), 10 communication diagram
(hal. 185–190), 5 state machine (hal. 191–192), dan CRUDE matrix (hal. 193–198). Gambar yang tidak diperiksa
karena tidak menentukan perilaku sistem: alur AS-IS (hal. 87–94), kerangka evaluasi PoC (hal. 49, 51, 60),
serta WBS/jadwal.

## 1. Ringkasan

| Bagian dokumen | Hal. | Hasil |
| --- | --- | --- |
| BR-01..08, FR-01..10, UC-01..10 (normal flow) | 5–6, 77–78, 128–142 | Sudah tercakup audit lama; FR-01 (SSO) & FR-03 kini ✅ |
| NFR-01..14 | 78 | Sesuai audit lama; dokumen pendukung NFR-01/05/08/14 sudah ada |
| **Technical Requirements DQR/AIR/KR** | 79–80 | 17 butir (AIR-01..04 dihitung 4): 17 ✅ → §3 |
| **TO-BE detail (kebijakan confidence, self-service, pola)** | 96–102 | Confidence 3 tingkat, chatbot confidence sedang (T3), pola INC, saran jenis REQ/INC (T4) ✅ → §2 |
| **Business Process BP-01..25** | 103–121 | 24 ✅; BP-25 ⚪ → §4 |
| **Atribut kelas & state machine** | 155–170, 191–192 | 5 state machine ✅; atribut pengguna (T11) & beban kerja (T5) ✅ (31 Okt) → §2, §6 |
| **Batas scope (yang dilarang)** | 8, 96 | ✅ semua (akses DB `halosis-ai` dicek; Claude didokumentasikan) → §5 |

Tidak ada yang bertentangan dengan inti dokumen. Temuan baru umumnya **detail aturan** yang tertulis di TO-BE,
CRC card, dan state machine, bukan fitur besar yang hilang.

## 2. Temuan baru (belum ada di audit lama), urut prioritas

| # | Dokumen menyebut | Hal. | Implementasi (dari README) | Status | Saran | Usaha |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | **SLA respons (TTO)** selain penyelesaian: `KebijakanSLA.targetRespons`; baseline Response 42,62% dipakai sebagai KPI | 114, 162 | **SLA resmi BPS dari history** (kolom `response_sla_name`: "SLA Incident Response 15Minutes" / "BPS-SLA Request Response 15Minutes", 6.655 tiket) → SLA *time to own* **15 menit** semua tiket (`config/sla_layanan.json`, `setup_sla_alerts.py`); kolom "Waktu untuk mengambil alih" di daftar Operator | ✅ | — | — |
| T2 | **Kebijakan confidence 3 tingkat** (tinggi/sedang/rendah): tinggi = Top-1 default; sedang = Top-3 + review; rendah = manual | 100 | **Diperbaiki:** ambang kedua `ai_threshold_low` 40% (`plugins/halosis/src/Config.php:36`, Pengaturan AI); `Suggestion::getConfidenceLevel()` (`plugins/halosis/src/Suggestion.php:74`) → panel "Disarankan" / "Pilih dari 3 kandidat" / "Perlu penilaian manual" (`plugins/halosis/templates/triase_panel.html.twig`) | ✅ | — | — |
| T3 | **Chatbot confidence sedang** → jawaban terbatas / pertanyaan klarifikasi / opsi lanjutan | 100 | **Diperbaiki (31 Okt):** skor 0,78–0,83 (`HALOSIS_CHAT_SUGGEST_MIN_SCORE`, `ai/service/app.py:46`, `:258`) → tidak menjawab, ≤ 3 judul artikel KB "Maksud Anda…?" + Buat laporan (`plugins/halosis/src/Chatbot.php:337`); tes `test_chat_keyakinan_sedang_menawarkan_pilihan` | ✅ | Jarang muncul selama KB sedikit (± 6 artikel vs ribuan potongan tiket) | — |
| T4 | **Triase merekomendasikan jenis REQ/INC** | 97, 100, 104 | **Diperbaiki (31 Okt):** klasifier ringan TF-IDF + LR dari kolom `ticket_type` history (`ai/scripts/train_jenis.py`, artefak `ai/models/jenis.joblib`): akurasi 68,25% (pembanding 57,28%), keyakinan ≥ 70% → akurasi 84,17% pada 40,92% tiket; panel menampilkan "Jenis disarankan" hanya bila berbeda dari jenis tiket & yakin (`plugins/halosis/src/TriagePanel.php` `typeHint`); tanpa artefak → diam | ✅ | Operator tetap memutuskan (ubah jenis di form tiket) | — |
| T5 | **Rekomendasi tim memperhitungkan beban kerja tim** (`hitungBebanKerja()`) | 133, 179 | **Diperbaiki (31 Okt):** 3 kandidat tim disimpan per saran (`suggestions.candidates`, `plugins/halosis/src/Triage.php:281`); panel menampilkan tiket aktif per kandidat → grup GLPI (`plugins/halosis/src/TriagePanel.php:90`, `:112`); ranking tetap dari model | ✅ | — | — |
| T6 | **Peninjauan berkala artikel** (`tanggalTinjauBerikut`, "artikel yang jatuh tempo ditinjau" muncul di daftar KM) | 139–140, 167, 192 | **Diperbaiki:** tab "Perlu ditinjau" di Kandidat knowledge = artikel terbit dengan `date_mod` > `kb_review_months` (bawaan 6) (`plugins/halosis/src/KnowledgeCandidates.php:161`, `plugins/halosis/src/Config.php:42`) | ✅ | — | — |
| T7 | **Arsip artikel** (soft delete, hapus dari indeks) + **kata kunci/tag** artikel | 140, 167, 192 | Hapus/tidak terbit → hapus dari indeks ✅; **didokumentasikan**: "tidak terbit = arsip, kategori KB = tag" (README › Keputusan desain) | ✅ | — | dok. |
| T8 | **Sesi chat berakhir otomatis setelah 30 menit tanpa aktivitas** | 192 | **Diperbaiki:** status `expired` setelah `Chat::IDLE_MINUTES` = 30 (`plugins/halosis/src/Chat.php:18`, `:24`, `:55`), dijalankan saat chat/riwayat/dashboard dibuka; riwayat menampilkan "Berakhir (tidak aktif)". Uji: sesi menganggur 40 menit → expired, pesan baru ditolak | ✅ | — | — |
| T9 | **Pola insiden dari tiket INC** (PoC 2.777 INC); pola baru **mengirim peringatan dini** (notifikasi) dan **tiket baru bisa ditambahkan** ke pola yang belum ditutup | 101, 183, 192 | **Diperbaiki:** hanya tiket Insiden (`plugins/halosis/src/PatternDetector.php:138`); tiket mirip baru ditautkan ke Problem pola terbuka yang sudah menaungi anggotanya (`:300`, `:392`); notifikasi "New problem" ke grup Operator, email + browser (`setup_sla_alerts.py:163`). Uji: REQ tidak ikut; setelah anggota tertua selesai, tiket baru masuk Problem yang sama | ✅ | — | — |
| T10 | **Keputusan Diubah/Ditolak dikirim sebagai umpan balik ke model** (`kirimUmpanBalik`) | 180, 191 | **Diperbaiki (31 Okt):** tombol **Ekspor koreksi (CSV, tersamar)** di dashboard, hak Pengaturan AI (`plugins/halosis/src/Controller/DashboardController.php:64`, `plugins/halosis/src/Stats.php:487`); penggabungan ke data latih tetap manual (`reports/tata_kelola_ai.md` §2 langkah 1b) | ✅ | Otomatisasi latih ulang di luar prototipe | — |
| T11 | **Atribut pengguna**: NIP, unit kerja, lokasi satker, jabatan | 156–157 | **Diperbaiki (31 Okt):** atribut `nip`, `unit_kerja`, `jabatan` di profil pengguna realm + mapper klaim, data contoh fiktif (`keycloak/halosis-realm.json`); disalin saat login ke NIP → nomor registrasi, jabatan → Jabatan, unit kerja → Lokasi (`plugins/halosis/src/KeycloakAuth.php:50`, `:295`) | ✅ | Keycloak yang sudah berjalan perlu impor ulang realm (README 6b) | — |
| T12 | **Sumber tiket** (portal/chatbot) tercatat di tiket | 163 | **Diperbaiki:** tiket dari chatbot memakai *Request source* GLPI "HaloSIS Chat" (dibuat otomatis) (`plugins/halosis/src/Chatbot.php:410`, `:425`); portal/form memakai sumber bawaan (Helpdesk) | ✅ | — | — |
| T13 | **Operator membuat tiket untuk pelapor telepon/email/walk-in** (EI "Input tiket oleh operator") | 7, 63 | **Diuji (31 Okt):** `rina` (Operator) membuat tiket dengan pemohon `siti` → pemohon siti, pencatat rina; masuk skenario demo (`plugins/halosis/README.md:160`) | ✅ | — | — |

### 2b. Temuan tambahan dari gambar (activity, sequence, communication, CRUDE)

Detail di bawah hanya muncul di gambar atau tabel CRUDE, tidak di teks deskripsi use case.

| # | Dokumen menyebut | Hal. | Implementasi (dari README) | Status | Saran | Usaha |
| --- | --- | --- | --- | --- | --- | --- |
| T14 | **Tiket, RekomendasiAI, dan AuditLog tidak pernah dihapus**; satu-satunya *delete* adalah arsip artikel | 191, 198 | **Diperbaiki:** sebelumnya Administrator & Supervisor masih punya hapus/purge tiket; kini dicabut dari semua profil kecuali Super-Admin di `setup-roles` (`plugins/halosis/src/Roles.php:185`, `:265`). Tabel plugin hanya di-drop saat **uninstall**, bukan deaktivasi (`plugins/halosis/hook.php:185`) | ✅ | — | — |
| T15 | Setiap jawaban chatbot **mencatat pemakaian artikel** (`catatPemakaian()`, `jumlahDigunakan++`) + log interaksi | 144, 176, 193 | **Diperbaiki:** id artikel yang dikutip disimpan per jawaban (tabel `glpi_plugin_halosis_article_uses`, `plugins/halosis/src/Chatbot.php:352`); dashboard Kinerja AI menampilkan "Artikel yang paling sering dipakai chatbot" (`plugins/halosis/src/Stats.php:175`) | ✅ | — | — |
| T16 | **Log retrieval untuk audit berisi kueri, sumber, dan skor** | 145, 177, 186 | `latency.jsonl` sengaja **angka saja**; **didokumentasikan** di README: kueri tidak disimpan demi NFR-06 | ✅ (keputusan privasi) | — | dok. |
| T17 | Pencarian tiket historis hanya pada tiket **Closed & tervalidasi** | 177 | Indeks dari history yang sudah selesai; tiket GLPI baru masuk lewat Kandidat → artikel | ✅ | Cukup sebutkan di README AI | — |
| T18 | Dashboard UC-08 bisa **difilter per layanan, tim, dan periode** | 151 | **Diperbaiki (31 Okt):** filter tim (grup ditugaskan) & kategori layanan (termasuk subkategori) selain periode (`plugins/halosis/src/Stats.php:71`); berlaku untuk angka triase, salah tim, drift | ✅ | Angka chatbot tidak terkait tim/kategori | — |
| T19 | UC-03 SLA dimulai untuk **response & resolution time** | 146 | **Diperbaiki** bersama T1: aturan SLA memasang TTO & TTR | ✅ | — | — |
| T20 | UC-10: **pratinjau dampak**, **notifikasi perubahan konfigurasi**, dan **catat percobaan akses yang ditolak** | 153, 185 | **Minimal (31 Okt):** tombol *Pratinjau dampak* di Pengaturan AI (saran 30 hari yang berpindah tingkat, tanpa menyimpan); perubahan Pengaturan AI, aturan tiket/SLA, SLA, kategori → log sistem GLPI (sebelum → sesudah, aktor, waktu) + Catatan untuk profil Administrator (`plugins/halosis/src/ConfigAudit.php`); akses ditolak → log GLPI | ✅ | Pratinjau untuk aturan SLA/kategori belum (gunakan Rules › Test) | — |

Konsisten dengan implementasi (tidak perlu tindakan): use case diagram (6 aktor + AI Engine, include/extend),
class diagram (20 kelas, 4 enumerasi), UC-04 tim default dari layanan (`getTimDefault()` = grup di kategori
GLPI), UC-06 notifikasi saat ditugaskan, UC-07 komentar diteruskan ke petugas, UC-10 nonaktifkan layanan lama,
AuditLog menyimpan nilai sebelum/sesudah (Riwayat GLPI).

## 3. Technical Requirements (§4.2.3, hal. 79–80) — belum pernah diaudit

| Kode | Kebutuhan | Status | Bukti / catatan |
| --- | --- | --- | --- |
| DQR-01 | Data konsisten: bebas duplikat, field wajib terisi | ✅ | `prepare_data.py`, `reconcile.py` (duplikat & tidak lengkap dilaporkan) |
| DQR-02 | Timestamp valid & konsisten | ✅ | Tanggal dibuka tidak valid → gagal (`ai/scripts/reconcile.py:92`); **urutan selesai/ditutup < dibuka** ditandai `bad_order` (`ai/scripts/prepare_data.py:146`, dipakai `reconcile.py:95`); data nyata: 0 baris |
| DQR-03 | Penanganan data yang melanggar DQR-01 | ✅ | Baris gagal dicatat di rekonsiliasi |
| DQR-04 | Data historis kurang lengkap diberi flag | ✅ | Kolom `tidak_lengkap` + `alasan_tidak_lengkap` di `tickets_clean.parquet` (`ai/scripts/prepare_data.py`); history versi baru: 790 dari 6.681 tiket ditandai (`reports/rekonsiliasi.md`); **hasil SLA berimputasi ditandai** kolom `sla_imputasi` (1.819 tiket, `overall_sla_result_basis` = IMPUTED) dan dicatat di baseline dashboard |
| DQR-05 | Definisi populasi data latih/evaluasi eksplisit | ✅ | **Diperbaiki:** definisi populasi (sumber, status, jenis, filter tim, periode) di `reports/triase.md` › Input & metode (juga di generator `train_triage.py`) |
| AIR-01..04 | Retrieval, triage, conversational, pattern | ✅ | `/chat`, `/triage`, chatbot, `/pola` |
| KR-01 | Pemilik per **domain** knowledge | ✅ | **Diperbaiki:** tabel domain → pemilik di `reports/tata_kelola_ai.md` §4b |
| KR-02 | Siklus hidup knowledge konkret | ✅ | Draf → terbit → tidak terbit (arsip) ✅; tinjau berkala (T6) ✅ |
| KR-03 | Metadata knowledge | ✅ | Kategori (= tag, T7), FAQ; **tanggal tinjau berikut eksplisit per artikel** (tabel `glpi_plugin_halosis_kb_reviews`, diatur di tab "Perlu ditinjau"; tanpa tanggal = `date_mod` + `kb_review_months`) (`plugins/halosis/src/KnowledgeCandidates.php:156`, `:205`); SOP = kategori KB "SOP" |
| KR-04 | Keyword **dan** semantic retrieval | ✅ | Semantik + fallback kata kunci (`/CariKnowledge`) |
| KR-05 | Jawaban AI memakai retrieved context | ✅ | Jawaban ekstraktif dari sumber |
| KR-06 | Konteks kurang → nyatakan belum tersedia + tawarkan handoff | ✅ | UC-01 4a |
| KR-07 | **User/agent** menandai jawaban membantu/tidak | ✅ | Pegawai: rating chat; agent: tombol **Membantu / Tidak membantu** per hasil `/CariKnowledge`, disimpan (pengguna, waktu, sumber, skor; tanpa teks kueri) di `glpi_plugin_halosis_feedback` (`plugins/halosis/hook.php:113`, `plugins/halosis/ajax/feedback.php:35`) |
| KR-08 | Perubahan knowledge dapat ditelusuri | ✅ | Revisi artikel GLPI + log |

## 4. Business Process BP-01..25 (hal. 103–121)

✅ sudah tercermin: BP-01..20, 22–24 (BP-13/17/19 sejak 31 Okt) (alur chat → tiket → triase → HITL → SLA → kandidat
knowledge → closure; pola insiden; admin; operasi GLPI + AI).

| BP | Isi dokumen | Status | Celah |
| --- | --- | --- | --- |
| BP-13 Feedback/Rating | Feedback dipakai untuk evaluasi layanan, **evaluasi AI**, perbaikan knowledge | ✅ | Dashboard: artikel paling sering dinilai tidak membantu (chat jadi laporan / rating ≤ 2 + penilaian agent KR-07) (`plugins/halosis/src/Stats.php:292`) |
| BP-17 Reporting | Dashboard: volume, SLA, **response**, resolution, assignment, rekomendasi AI, acceptance, override, deteksi pola, governance | ✅ | SLA respons (T1) di daftar & Statistik GLPI; dashboard plugin: pola terdeteksi vs dikonfirmasi vs ditutup (`plugins/halosis/src/Stats.php:264`) |
| BP-19 AI Model Mgmt | Evaluasi → approval → rilis → monitoring → **drift / hallucination monitoring** → revalidasi | ✅ | Proses di `tata_kelola_ai.md`; indikator drift = % Ubah+Tolak per bulan (6 bulan) di dashboard (`plugins/halosis/src/Stats.php:235`); halusinasi: jawaban ekstraktif (tanpa generasi bebas) |
| BP-21 Incident Trend Analysis | Analisis semantik + temporal **kontinu** | ✅ | Jendela 60 menit (cron 15 menit) + **tren pola per minggu per topik, 12 minggu** di dashboard (`plugins/halosis/src/Stats.php:293`) |
| BP-25 AI Infrastructure | GPU, model serving, vector DB, monitoring | ⚪ | `/metrics` + profile `monitoring` (Prometheus + Grafana, 31 Okt) ✅; uji beban Peak/Stress layanan AI ✅; GPU & vector DB layanan di luar prototipe |

## 5. Kepatuhan batas scope & arsitektur

| Aturan dokumen | Hal. | Status | Catatan |
| --- | --- | --- | --- |
| **AI tidak boleh mengakses/menulis langsung database GLPI** ("AI direct write ke database core ITSM" di luar scope) | 8, 96 | ✅ | Container `halosis-ai` hanya punya `ANTHROPIC_API_KEY` & `HALOSIS_CHAT_MIN_SCORE` + volume model/indeks/log (`docker-compose.yml:41-54`); tanpa kredensial DB. Data masuk lewat API dari plugin |
| **Tanpa GenAI publik eksternal tanpa batas untuk data internal BPS** | 8 | ✅ | Claude = GenAI eksternal, **nonaktif secara bawaan**, data disamarkan; **didokumentasikan** di README: mengaktifkan butuh persetujuan tata kelola BPS; alternatif LLM lokal (Ollama) |
| Tanpa routing otomatis penuh tanpa HITL | 8 | ✅ | Semua saran menunggu keputusan Operator |
| Tanpa tindakan pemulihan otomatis dari pola | 5, 8 | ✅ | Pola hanya Problem + peringatan |
| Arsitektur: Self-Service → Internal AI → API layer (REST, SSO/Keycloak) → GLPI | 96 | ✅ | Sesuai; Teams & Grafana bertanda "jika ada" |
| Klaim akurasi produksi hanya dari PoC tidak boleh | 8 | ✅ | Evidence Maturity membedakan Proven / Partially proven |

## 6. State machine (hal. 191–192) vs status GLPI

| Kelas | Dokumen | GLPI/plugin | Status |
| --- | --- | --- | --- |
| Tiket | Baru → Assigned (setelah validasi) → Dalam Penanganan ⇄ Pending → Resolved → Closed / Reopened; Baru → Resolved (L1); kembalikan → Baru | Baru, Diproses (ditugaskan/direncanakan), Menunggu, Selesai, Ditutup; Refuse → diproses lagi; Kembalikan ke operator | ✅ (tabel padanan di README › Keputusan desain) |
| RekomendasiAI | MenungguValidasi / PerluPenilaianManual → Diterima / Diubah / Ditolak | Sama + alasan | ✅ |
| ArtikelKnowledge | Draf → Terbit (versi++, pemakaian++) → Diarsipkan; when(tanggalTinjau) → daftar tinjau | Draf (tanpa target), terbit, revisi, tidak terbit = arsip; pemakaian chatbot dihitung (T15); daftar "Perlu ditinjau" (T6) | ✅ |
| PolaInsiden | Terdeteksi → Dikonfirmasi → Ditutup; tambahTiket selama belum ditutup | Problem: Baru → dikonfirmasi/ditutup; tiket mirip baru ditautkan selama Problem terbuka (T9) | ✅ |
| SesiChat | Aktif → Selesai (termasuk 30 menit idle) / DikonversiKeTiket | open → resolved / ticket / **expired** (30 menit idle, T8) | ✅ |

## 7. Rekomendasi urutan kerja

Semua butir T1–T20 sudah ✅ (31 Okt). Sisa opsional di luar audit ini: LLM lokal (profile `llm`, Ollama + Qwen2.5 3B)
sebagai perangkum grounded, pratinjau dampak untuk aturan SLA/kategori, dan uji di lingkungan BPS.

## 8. Bab analisis & kelayakan (§1.3–1.6, §2.1–2.4, §5.1–5.2)

Ditambahkan 31 Okt 2026. Label T28–T29 diberikan di sini untuk dua butir dokumen yang belum bernomor.

### 8.1 Temuan T21–T32

| # | Dokumen menyebut | Hal./bagian | Implementasi | Status |
| --- | --- | --- | --- | --- |
| T21 | Rekomendasi penutupan; hilangkan tiket menggantung (Activity Elimination/Duration) | 5.1, 5.2.3.2, E18 | Menu Operator **Siap ditutup**: Selesai > 48 jam tanpa respons pemohon, tutup per tiket/massal, tanpa otomatis (`plugins/halosis/src/Closure.php`) | ✅ |
| T22 | SLA per layanan (KebijakanSLA dari LayananTI) | E3, CRC, 5.2.1.5 | **SLA resmi BPS dari history** (`resolution_/fulfillment_sla_name`): insiden Crit 2 hari (9 tiket), Medium 8 (2.201), Low 15 (500) per prioritas; permintaan 7 hari (1.666), 14 hari (138) untuk layanan tim > 50% 14 hari (Server Hosting 52/55, SOBAT 36/41, LAN 27/27, WAN 2/2, Container 1/1); kategori contoh "Server Hosting" diuji → 15 menit + 14 hari; kalender jam kerja, peringatan ±20% | ✅ |
| T23 | Notifikasi tidak hanya sekali (balasan sampai ke petugas) | 5.1 akar masalah | "New followup" → teknisi & grup ditugaskan (uji Mailpit: andi + anggota tim) | ✅ |
| T24 | KPI SLA breach, waktu sampai diterima tim, first-level resolution | Tabel 1.3 | Dashboard **KPI layanan** (`Stats::serviceKpi`) | ✅ |
| T25 | Volume tiket per minggu/kategori | E8, Tabel 1.3 | Dashboard volume 12 minggu per jenis & 5 kategori (`Stats::ticketVolume`) | ✅ |
| T26 | Pengamanan API layanan AI | 2.1.5 | Rate limit per klien `HALOSIS_RATE_LIMIT_PER_MIN` (429 + Retry-After), tes | ✅ |
| T27 | Uji upgrade platform | 2.4.2 | GLPI 12.0.0 → 12.0.1 di lingkungan terpisah dari snapshot: migrasi otomatis, skema OK, plugin 1.0.0 Enabled, data utuh (`reports/uji_upgrade.md`) | ✅ |
| T28 | Pemisahan dev/staging/produksi, pilot, parallel run, cutover, hypercare | 2.1.5, WBS 5–7 | `reports/rencana_implementasi.md` | ✅ (dok.) |
| T29 | Pelatihan per peran | WBS 6.3, 7.3 | `reports/panduan_peran.md` | ✅ (dok.) |
| T30 | Self-service dimulai dari Email, SSO, SiPecut (48,2% tiket) | 5.1 Outcome | FAQ ketiga layanan (9 artikel KB terindeks; SiPecut ditambah 2) | ✅ |
| T31 | Pertanyaan di luar layanan TI | wawancara Operator | Chatbot mengarahkan ke Kepegawaian/Keuangan/Umum tanpa tawaran laporan | ✅ |
| T32 | Model harus lolos uji sebelum dipakai (pre-kondisi UC-04) | 2.1.4 | Gerbang memeriksa **semua** syarat `tata_kelola_ai.md` dari metrik tersimpan (`ai/halosis_ai/quality.py`): triase (dilatih ulang dari history versi baru) Top-1 0,7588 ≥ 0,68, akurasi pada ambang 0,8835 ≥ 0,85, tidak turun dari model aktif pada set uji sama (0,7447) → dipakai; jenis & urgensi F1 makro > pembanding dan tidak turun > 2 poin dari versi aktif; urgensi F1 0,5797 > 0,4482 → lolos. Latih ulang hanya mengganti artefak bila lolos. `/health` → status per model; panel "belum lolos uji kualitas" | ✅ |

### 8.2 Risiko R1–R4 (Tabel 1.4) & risiko organisasi (Tabel 2.21) → mitigasi di sistem

| Risiko | Mitigasi di HaloSIS | Bukti |
| --- | --- | --- |
| R1 AI memberi rekomendasi salah | HITL Terima/Ubah/Tolak + alasan, 3 tingkat keyakinan, Top-3 kandidat, gerbang kualitas model, audit trail | `uji_regresi_demo.md`, `triase.md` |
| R2 Data historis tidak rapi | `prepare_data.py` (penyamaran, flag `tidak_lengkap`), `reconcile.py` (duplikat, tanggal), migrasi idempoten | `rekonsiliasi.md` |
| R3 Kemampuan tim internal | Plugin tanpa ubah inti GLPI, README langkah demi langkah, panduan per peran, CHANGELOG | `panduan_peran.md`, README C3 |
| R4 Integrasi sulit | REST API GLPI, SSO Keycloak (OIDC), layanan AI terpisah ber-API, uji beban & integrasi | `rencana_uji.md` §7 |
| Pengguna tidak terbiasa | Chatbot sebagai pintu masuk, pilot bertahap | `rencana_implementasi.md` |
| Operator tidak percaya AI | Penjelasan, beban tim, kalibrasi keyakinan di dashboard | Dashboard Kinerja AI |
| Ownership knowledge tidak jelas | RACI & pemilik domain, tab Perlu ditinjau + tanggal tinjau | `tata_kelola_ai.md` §4b |
| Kompetensi baru | Panduan peran, dokumentasi | `panduan_peran.md` |
| Perubahan terlalu besar | Fitur AI bisa dimatikan per fitur; pilot 3 layanan | Pengaturan AI |
| Routing dinilai tidak sesuai | Kembalikan ke operator, ekspor koreksi → latih ulang | `tata_kelola_ai.md` §2 |

### 8.3 KPI Tabel 1.3 → tempat diukur

| KPI | Diukur di |
| --- | --- |
| Waktu perubahan; % perubahan oleh tim internal | Log konfigurasi (`ConfigAudit`, Administrasi › Log); konfigurasi tanpa kode |
| % tiket SLA breach; waktu monitoring | Dashboard **KPI layanan** (respons & penyelesaian); Monitoring SLA + peringatan otomatis |
| Waktu pencarian solusi; % selesai tanpa eskalasi | Cari knowledge (latensi `latensi.md`); KPI "% diselesaikan Operator tanpa eskalasi" |
| % tiket tidak dibuat lewat self-service | Kartu Chatbot: "Terbantu tanpa tiket" |
| % tiket dipindah ke tim lain; waktu sampai diterima tim | "Dipindah ke tim lain setelah triase"; KPI "median waktu sampai diambil/ditugaskan" |
| Waktu mengetahui masalah; jumlah terdampak | Pola insiden (cron 15 menit, jendela 60 menit), jumlah tiket per pola, tren 12 minggu |
| Waktu pembuatan laporan; jumlah indikator; pembaruan data | Dashboard Kinerja AI langsung dari DB (tanpa ekspor), Grafana (profile `monitoring`) |

### 8.4 Syarat kelayakan teknis & integrasi (2.1.2–2.1.6) dan Skenario 2 (2.4.2)

| Syarat | Status | Bukti / catatan |
| --- | --- | --- |
| 2.1.2 Arsitektur: ITSM + layanan AI terpisah ber-API | ✅ | GLPI + plugin + `halosis-ai` (FastAPI) |
| 2.1.3 Data: profiling, cleansing, masking | ✅ | `prepare_data.py`, `reconcile.py`, `eda.md` |
| 2.1.4 AI/ML: uji akurasi sebelum pakai; prioritas P1, urgensi P2 dengan validasi | 🟡 | Model tim, jenis, dan **urgensi insiden** lolos gerbang (`/health`). **History versi baru memuat urgensi/dampak/prioritas**; dampak = urgensi pada 99,7% insiden dan prioritas = matriks keduanya, jadi satu model urgensi (Medium vs Low): F1 makro 57,97% vs pembanding 44,82%, akurasi 74,30%. **81% Medium kemungkinan nilai bawaan** formulir, sehingga pada keyakinan ≥ 70% semua saran = Medium. Dampak = urgensi + sinyal (tiket serupa / layanan kritis), prioritas = matriks GLPI; Operator memvalidasi (Terima/Ubah) |
| 2.1.5 Integrasi: SSO, data historis, notifikasi, monitoring, pemisahan lingkungan, uji beban | 🟡 | SSO Keycloak lokal ✅, migrasi sampel ✅, notifikasi ✅, monitoring profile ✅, uji beban ✅ (laptop); SSO BPS & lingkungan staging/produksi = rencana (`rencana_implementasi.md`) |
| 2.1.6 Infrastruktur: VM/OpenShift, sizing | ⚪ | Docker lokal; sizing dari uji beban (AI ±8,7 core pada 200 VU) |
| Skenario 2: kandidat platform & fit-gap BR-01..08 | ✅ | GLPI 12 + plugin; audit BR/FR/UC (`audit_kelengkapan.md`) |
| Skenario 2: uji API & SSO | ✅ | `tests/load/glpi_api.js`, login SSO di regresi demo |
| Skenario 2: deployment VM/OpenShift | ⚪ | Di luar prototipe |
| Skenario 2: PoC integrasi AI | ✅ | `/triage`, `/chat`, `/pola`, `/cari` |
| Skenario 2: uji upgrade | ✅ | `uji_upgrade.md` (12.0.0 → 12.0.1) |
