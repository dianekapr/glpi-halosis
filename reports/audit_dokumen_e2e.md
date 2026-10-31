# Audit end-to-end: dokumen *Kelompok 4 AKPSI-6* vs implementasi HaloSIS

Tanggal: 30 Okt 2026. Pembanding: README `dev` terbaru (SSO Keycloak, `/CariKnowledge`, `/metrics`, Mailpit) dan
`reports/audit_kelengkapan.md`. Audit ini membaca **seluruh bab** yang berdampak ke sistem, termasuk bagian yang
belum dicakup audit sebelumnya: Technical Requirements (§4.2.3), TO-BE & 25 Business Process (§5.2–5.3),
CRC card & class diagram (§7), sequence & state machine (§8), dan batas scope (§1.7).

Status: ✅ sesuai · 🟡 sebagian · ❌ belum · 🔍 perlu dicek di kode (README tidak menyebut) · ⚪ di luar prototipe.

**Pembaruan 31 Okt 2026:** semua 🔍 sudah dicek di kode (bukti `file:baris`). Diperbaiki: T1/T19, T2, T6, T8,
T9, T12, T14, T15 (kode); T7, T16, T20, KR-01, DQR-05, §5, §6 (dokumentasi). Sisa: T3, T4, T5, T10 (otomatis),
T11, T13 (uji demo), T18, KR-03, KR-07, DQR-02, DQR-04, BP-13/17/19/21.

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
| **Technical Requirements DQR/AIR/KR** | 79–80 | 17 butir (AIR-01..04 dihitung 4): 13 ✅, 4 🟡 (DQR-02/04, KR-03, KR-07) → §3 |
| **TO-BE detail (kebijakan confidence, self-service, pola)** | 96–102 | Confidence 3 tingkat & pola INC ✅; chatbot confidence sedang (T3) & jenis REQ/INC (T4) belum → §2 |
| **Business Process BP-01..25** | 103–121 | Sebagian besar ✅; BP-13, BP-17, BP-19 🟡 → §4 |
| **Atribut kelas & state machine** | 155–170, 191–192 | 5 state machine ✅ (31 Okt); atribut pengguna (T11) & beban kerja (T5) belum → §2, §6 |
| **Batas scope (yang dilarang)** | 8, 96 | ✅ semua (akses DB `halosis-ai` dicek; Claude didokumentasikan) → §5 |

Tidak ada yang bertentangan dengan inti dokumen. Temuan baru umumnya **detail aturan** yang tertulis di TO-BE,
CRC card, dan state machine, bukan fitur besar yang hilang.

## 2. Temuan baru (belum ada di audit lama), urut prioritas

| # | Dokumen menyebut | Hal. | Implementasi (dari README) | Status | Saran | Usaha |
| --- | --- | --- | --- | --- | --- | --- |
| T1 | **SLA respons (TTO)** selain penyelesaian: `KebijakanSLA.targetRespons`; baseline Response 42,62% dipakai sebagai KPI | 114, 162 | **Diperbaiki:** SLA *time to own* per prioritas (Kritis 15 mnt … Rendah 4 jam) + aksi `slas_id_tto` di aturan "SLA <prioritas>" (`setup_sla_alerts.py:41`, `:125`); kolom "Waktu untuk mengambil alih" di daftar Operator (`setup_list_columns.py:34`). Uji: tiket prioritas 5 → TTO 15 menit jam kerja | ✅ | Target menit masih asumsi; samakan dengan SLA resmi | — |
| T2 | **Kebijakan confidence 3 tingkat** (tinggi/sedang/rendah): tinggi = Top-1 default; sedang = Top-3 + review; rendah = manual | 100 | **Diperbaiki:** ambang kedua `ai_threshold_low` 40% (`plugins/halosis/src/Config.php:36`, Pengaturan AI); `Suggestion::getConfidenceLevel()` (`plugins/halosis/src/Suggestion.php:74`) → panel "Disarankan" / "Pilih dari 3 kandidat" / "Perlu penilaian manual" (`plugins/halosis/templates/triase_panel.html.twig`) | ✅ | — | — |
| T3 | **Chatbot confidence sedang** → jawaban terbatas / pertanyaan klarifikasi / opsi lanjutan | 100 | Satu ambang 0,83: jawab atau "belum menemukan" | 🟡 | Rentang skor tengah → tampilkan 2–3 judul artikel sebagai pilihan "Maksud Anda…?" + tombol lapor | kecil–sedang |
| T4 | **Triase merekomendasikan jenis REQ/INC** | 97, 100, 104 | Jenis adalah **input** model, bukan keluaran (`ai/halosis_ai/triage_model.py:85`, `plugins/halosis/src/Triage.php:260`); skema saran LLM tanpa jenis (`plugins/halosis/src/Triage.php:230`). Jenis ditentukan form (permintaan) / chatbot (insiden) | ❌ | Tulis sebagai keterbatasan, atau tambah klasifier REQ vs INC | kecil |
| T5 | **Rekomendasi tim memperhitungkan beban kerja tim** (`hitungBebanKerja()`) | 133, 179 | Tidak ada: panel hanya menampilkan 3 tim teratas dari model (`plugins/halosis/src/Triage.php:287`), tanpa jumlah tiket aktif | ❌ | Tampilkan jumlah tiket aktif per kandidat tim (info, tidak mengubah ranking) | kecil |
| T6 | **Peninjauan berkala artikel** (`tanggalTinjauBerikut`, "artikel yang jatuh tempo ditinjau" muncul di daftar KM) | 139–140, 167, 192 | **Diperbaiki:** tab "Perlu ditinjau" di Kandidat knowledge = artikel terbit dengan `date_mod` > `kb_review_months` (bawaan 6) (`plugins/halosis/src/KnowledgeCandidates.php:161`, `plugins/halosis/src/Config.php:42`) | ✅ | — | — |
| T7 | **Arsip artikel** (soft delete, hapus dari indeks) + **kata kunci/tag** artikel | 140, 167, 192 | Hapus/tidak terbit → hapus dari indeks ✅; **didokumentasikan**: "tidak terbit = arsip, kategori KB = tag" (README › Keputusan desain) | ✅ | — | dok. |
| T8 | **Sesi chat berakhir otomatis setelah 30 menit tanpa aktivitas** | 192 | **Diperbaiki:** status `expired` setelah `Chat::IDLE_MINUTES` = 30 (`plugins/halosis/src/Chat.php:18`, `:24`, `:55`), dijalankan saat chat/riwayat/dashboard dibuka; riwayat menampilkan "Berakhir (tidak aktif)". Uji: sesi menganggur 40 menit → expired, pesan baru ditolak | ✅ | — | — |
| T9 | **Pola insiden dari tiket INC** (PoC 2.777 INC); pola baru **mengirim peringatan dini** (notifikasi) dan **tiket baru bisa ditambahkan** ke pola yang belum ditutup | 101, 183, 192 | **Diperbaiki:** hanya tiket Insiden (`plugins/halosis/src/PatternDetector.php:138`); tiket mirip baru ditautkan ke Problem pola terbuka yang sudah menaungi anggotanya (`:300`, `:392`); notifikasi "New problem" ke grup Operator, email + browser (`setup_sla_alerts.py:163`). Uji: REQ tidak ikut; setelah anggota tertua selesai, tiket baru masuk Problem yang sama | ✅ | — | — |
| T10 | **Keputusan Diubah/Ditolak dikirim sebagai umpan balik ke model** (`kirimUmpanBalik`) | 180, 191 | Keputusan tersimpan & dipakai dashboard; **proses manual** ekspor koreksi → data latih berikutnya ditulis di `reports/tata_kelola_ai.md` §2 langkah 1b | 🟡 | Otomatisasi ekspor ke `train_triage.py` bila perlu | kecil |
| T11 | **Atribut pengguna**: NIP, unit kerja, lokasi satker, jabatan | 156–157 | Keycloak → nama & email | 🟡 | Tambah atribut di realm Keycloak + sinkron ke field GLPI (registration number, location) | kecil |
| T12 | **Sumber tiket** (portal/chatbot) tercatat di tiket | 163 | **Diperbaiki:** tiket dari chatbot memakai *Request source* GLPI "HaloSIS Chat" (dibuat otomatis) (`plugins/halosis/src/Chatbot.php:410`, `:425`); portal/form memakai sumber bawaan (Helpdesk) | ✅ | — | — |
| T13 | **Operator membuat tiket untuk pelapor telepon/email/walk-in** (EI "Input tiket oleh operator") | 7, 63 | Profil Operator (Hotliner) punya hak buat tiket (DB: `ticket` & CREATE); form tiket baru saat login dimatikan tapi hak tetap (`plugins/halosis/src/Roles.php:240`) | 🟡 | Uji 1 kali (pemohon = pegawai lain) dan masukkan ke skenario demo | — |

### 2b. Temuan tambahan dari gambar (activity, sequence, communication, CRUDE)

Detail di bawah hanya muncul di gambar atau tabel CRUDE, tidak di teks deskripsi use case.

| # | Dokumen menyebut | Hal. | Implementasi (dari README) | Status | Saran | Usaha |
| --- | --- | --- | --- | --- | --- | --- |
| T14 | **Tiket, RekomendasiAI, dan AuditLog tidak pernah dihapus**; satu-satunya *delete* adalah arsip artikel | 191, 198 | **Diperbaiki:** sebelumnya Administrator & Supervisor masih punya hapus/purge tiket; kini dicabut dari semua profil kecuali Super-Admin di `setup-roles` (`plugins/halosis/src/Roles.php:185`, `:265`). Tabel plugin hanya di-drop saat **uninstall**, bukan deaktivasi (`plugins/halosis/hook.php:185`) | ✅ | — | — |
| T15 | Setiap jawaban chatbot **mencatat pemakaian artikel** (`catatPemakaian()`, `jumlahDigunakan++`) + log interaksi | 144, 176, 193 | **Diperbaiki:** id artikel yang dikutip disimpan per jawaban (tabel `glpi_plugin_halosis_article_uses`, `plugins/halosis/src/Chatbot.php:352`); dashboard Kinerja AI menampilkan "Artikel yang paling sering dipakai chatbot" (`plugins/halosis/src/Stats.php:175`) | ✅ | — | — |
| T16 | **Log retrieval untuk audit berisi kueri, sumber, dan skor** | 145, 177, 186 | `latency.jsonl` sengaja **angka saja**; **didokumentasikan** di README: kueri tidak disimpan demi NFR-06 | ✅ (keputusan privasi) | — | dok. |
| T17 | Pencarian tiket historis hanya pada tiket **Closed & tervalidasi** | 177 | Indeks dari history yang sudah selesai; tiket GLPI baru masuk lewat Kandidat → artikel | ✅ | Cukup sebutkan di README AI | — |
| T18 | Dashboard UC-08 bisa **difilter per layanan, tim, dan periode** | 151 | Hanya filter **periode** 4/8/12 minggu (`plugins/halosis/src/Stats.php:13`) | 🟡 | Tambah filter tim & kategori di dashboard plugin | kecil |
| T19 | UC-03 SLA dimulai untuk **response & resolution time** | 146 | **Diperbaiki** bersama T1: aturan SLA memasang TTO & TTR | ✅ | — | — |
| T20 | UC-10: **pratinjau dampak**, **notifikasi perubahan konfigurasi**, dan **catat percobaan akses yang ditolak** | 153, 185 | Pratinjau & notifikasi belum ada; **didokumentasikan** sebagai keterbatasan + alternatif (Rules › Test, Setup › Log) di README | 🟡 | — | dok. |

Konsisten dengan implementasi (tidak perlu tindakan): use case diagram (6 aktor + AI Engine, include/extend),
class diagram (20 kelas, 4 enumerasi), UC-04 tim default dari layanan (`getTimDefault()` = grup di kategori
GLPI), UC-06 notifikasi saat ditugaskan, UC-07 komentar diteruskan ke petugas, UC-10 nonaktifkan layanan lama,
AuditLog menyimpan nilai sebelum/sesudah (Riwayat GLPI).

## 3. Technical Requirements (§4.2.3, hal. 79–80) — belum pernah diaudit

| Kode | Kebutuhan | Status | Bukti / catatan |
| --- | --- | --- | --- |
| DQR-01 | Data konsisten: bebas duplikat, field wajib terisi | ✅ | `prepare_data.py`, `reconcile.py` (duplikat & tidak lengkap dilaporkan) |
| DQR-02 | Timestamp valid & konsisten | 🟡 | Tanggal dibuka tidak valid ditandai `bad_date` & dihitung gagal (`ai/scripts/reconcile.py:92`); urutan dibuka > selesai belum diperiksa |
| DQR-03 | Penanganan data yang melanggar DQR-01 | ✅ | Baris gagal dicatat di rekonsiliasi |
| DQR-04 | Data historis kurang lengkap diberi flag | 🟡 | Flag per baris `incomplete` (tanpa deskripsi/tim/solusi) di `ai/scripts/reconcile.py:100`, dilaporkan di `reports/rekonsiliasi.md`; di parquet hanya `solusi_sumber` kosong (`ai/scripts/prepare_data.py:114`), belum kolom flag |
| DQR-05 | Definisi populasi data latih/evaluasi eksplisit | ✅ | **Diperbaiki:** definisi populasi (sumber, status, jenis, filter tim, periode) di `reports/triase.md` › Input & metode (juga di generator `train_triage.py`) |
| AIR-01..04 | Retrieval, triage, conversational, pattern | ✅ | `/chat`, `/triage`, chatbot, `/pola` |
| KR-01 | Pemilik per **domain** knowledge | ✅ | **Diperbaiki:** tabel domain → pemilik di `reports/tata_kelola_ai.md` §4b |
| KR-02 | Siklus hidup knowledge konkret | ✅ | Draf → terbit → tidak terbit (arsip) ✅; tinjau berkala (T6) ✅ |
| KR-03 | Metadata knowledge | 🟡 | Kategori (= tag, T7), FAQ, `date_mod` untuk tinjau ✅; tanggal tinjau eksplisit per artikel belum |
| KR-04 | Keyword **dan** semantic retrieval | ✅ | Semantik + fallback kata kunci (`/CariKnowledge`) |
| KR-05 | Jawaban AI memakai retrieved context | ✅ | Jawaban ekstraktif dari sumber |
| KR-06 | Konteks kurang → nyatakan belum tersedia + tawarkan handoff | ✅ | UC-01 4a |
| KR-07 | **User/agent** menandai jawaban membantu/tidak | 🟡 | Pegawai: rating chat ✅ (`plugins/halosis/src/Chatbot.php` `resolve()`); agent di `/CariKnowledge`: **tidak ada** tombol membantu/tidak (`plugins/halosis/src/Controller/CariKnowledgeController.php`) |
| KR-08 | Perubahan knowledge dapat ditelusuri | ✅ | Revisi artikel GLPI + log |

## 4. Business Process BP-01..25 (hal. 103–121)

✅ sudah tercermin: BP-01..12, 14–16, 18, 20, 22–24 (alur chat → tiket → triase → HITL → SLA → kandidat
knowledge → closure; pola insiden; admin; operasi GLPI + AI).

| BP | Isi dokumen | Status | Celah |
| --- | --- | --- | --- |
| BP-13 Feedback/Rating | Feedback dipakai untuk evaluasi layanan, **evaluasi AI**, perbaikan knowledge | 🟡 | Rating chat & survei tersimpan; tampilkan di dashboard Kinerja AI ("jawaban tidak membantu" per artikel) |
| BP-17 Reporting | Dashboard: volume, SLA, **response**, resolution, assignment, rekomendasi AI, acceptance, override, deteksi pola, governance | 🟡 | *Response* bergantung T1; pastikan dashboard punya baris "pola terdeteksi vs dikonfirmasi" |
| BP-19 AI Model Mgmt | Evaluasi → approval → rilis → monitoring → **drift / hallucination monitoring** → revalidasi | 🟡 | Proses tertulis di `tata_kelola_ai.md`; drift (tren rasio Ubah/Tolak per bulan) bisa jadi grafik dashboard |
| BP-21 Incident Trend Analysis | Analisis semantik + temporal **kontinu** | 🟡 | Jendela 60 menit ✅; tren antar-periode belum (sudah tercatat di README) |
| BP-25 AI Infrastructure | GPU, model serving, vector DB, monitoring | ⚪ | `/metrics` ✅; GPU & vector DB layanan di luar prototipe |

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

Langkah 1–3 versi 30 Okt sudah dikerjakan 31 Okt (lihat pembaruan di atas). Sisa, urut prioritas:

1. **Uji demo:** T13 (Operator membuat tiket atas nama pegawai) — tanpa coding.
2. **Coding kecil:** T5 (jumlah tiket aktif per kandidat tim), T18 (filter tim & kategori di dashboard),
   KR-07 (tombol membantu/tidak di `/CariKnowledge`), DQR-02 (cek urutan tanggal), DQR-04 (kolom flag di parquet).
3. **Keputusan/dokumentasi:** T4 (klasifier REQ/INC atau keterbatasan), T10 otomatis, KR-03.
4. Bila waktu tersisa: T3, T11, BP-13/17/19/21.
