# AI HaloSIS — pipeline data & layanan

Dibangun dari history tiket versi baru `data/raw/data_ticketing_202601_202608.xlsx` (6.681 tiket Jan–Ags 2026,
220 kolom termasuk `impact`/`urgency`/`priority`, rating, SLA diperluas; nama unduhan asli
`data ticketing (202601_202608).xlsx` juga dikenali). Tanggal di ekspor ini berupa angka serial Excel → datetime
lewat satu fungsi bersama `halosis_ai/dates.py`. Ekspor lama `ticketing_history_202601_202608.xlsx` hanya dipakai
`reconcile.py` untuk banding lama vs baru.

## Aturan data (wajib)

- `data/` (mentah & olahan), model, dan indeks **berisi/berasal dari data pribadi**: di-ignore git, jangan
  pernah di-commit atau dibagikan.
- Data mentah **tidak boleh** dikirim ke API eksternal; hanya teks yang sudah disamarkan.
- Jangan mencetak isi tiket (apalagi kata sandi) di log, laporan, atau terminal. Skrip hanya mencetak angka.

## AI-1 — Pembersihan & penyamaran

```bash
.venv/bin/pip install -r ai/requirements.txt
.venv/bin/python -m pytest -q ai/tests          # bukti pola data pribadi tersamarkan
.venv/bin/python ai/scripts/prepare_data.py     # → data/processed/tickets_clean.parquet, qa_pairs.parquet
```

Penyamaran (`ai/halosis_ai/privacy.py`), di semua kolom teks:

| Pola | Jadi |
| --- | --- |
| Email | `[EMAIL]` |
| NIP 18 digit (rapat / berkelompok) | `[NIP]` |
| NIP lama 9 digit, hanya setelah kata "NIP" ("NIP 340012345", "nip lama: …") | `[NIP]` |
| NIK 16 digit | `[NIK]` |
| Nomor HP (08…, +62…, 62…) | `[TELEPON]` |
| Nilai setelah password/pasw/pwd/sandi/PIN/OTP (termasuk "password sementara :") | `[RAHASIA]` |
| Nama setelah sapaan (Ysh./Yth. Bpk./Ibu, Pak, Bu, …) | `[NAMA]` |
| Nama lengkap & bagian nama dari kolom pengguna (requester/assigned/resolved_by/closed_by) | `[NAMA]` |

Kolom nama pengguna dihapus dan diganti ID samaran (`*_pid`, mis. `U00042`; pemetaan tidak disimpan).
Skrip **memindai ulang** keluaran dan menolak menyimpan bila masih ada pola data pribadi.

Solusi (`ai/halosis_ai/conversations.py`): `all_conversations` dipecah per pesan (`waktu | teks || …`; tidak ada
penanda pengirim di teks). Solusi = **pesan terakhir yang dikirim ≤ `resolved` + 5 menit**, bukan dari pemohon
(pesan terakhir dilewati bila `last_conversation_user_id` = `requester_id`; pesan lain: pesan keluhan pegawai "saya
masih …" ditolak), setelah kalimat template & salam dibuang masih ≥ 5 kata, dan bukan sekadar permintaan informasi.
Bila tidak ada, dipakai `close_notes` lalu `resolution` yang bukan template ("solved", "done", "."). Pesan sesudah
tiket diselesaikan (terima kasih, survei, tiket dibuka lagi) dibuang; toleransi 5 menit karena petugas sering menulis
solusinya 1–3 menit sesudah menekan "selesai" (median 1,6 menit). Hasil uji retrieval: `reports/banding_solusi.md`.
Kolom `sla_imputasi` menandai hasil SLA yang memakai komponen imputasi (DQR-04).

**Batasan:** nama orang yang tidak ada di kolom pengguna dan ditulis tanpa sapaan tidak terdeteksi; bagian
nama yang juga kata umum (sering muncul berhuruf kecil) sengaja tidak disamarkan.

## FR-10 — Rekonsiliasi migrasi

```bash
.venv/bin/python ai/scripts/reconcile.py        # → reports/rekonsiliasi.md (±3 menit)
```

Menjalankan pembersihan & penyamaran yang sama dengan AI-1 (tanpa menulis ulang `data/processed/`), lalu
merekonsiliasi setiap baris sumber. Laporan **hanya berisi angka, bulan, dan nama tim**; isi tiket, nama orang,
dan nilai yang disamarkan tidak pernah ditulis atau dicetak.

| Bagian laporan | Definisi |
| --- | --- |
| Sumber = berhasil + gagal | Dicek otomatis di laporan |
| **Gagal** (per alasan) | Tanpa nomor tiket; tanggal dibuka tidak valid; status tidak dikenal (`UNKNOWN / STATE NOT FOUND`, tak bisa dipetakan ke status GLPI); masih memuat pola data pribadi setelah penyamaran. Baris gagal tetap ada di parquet untuk analisis AS-IS, tetapi tidak layak dimigrasikan |
| **Tidak lengkap** (dari yang berhasil) | Tanpa deskripsi; tanpa tim; status selesai tetapi solusi tidak bisa diambil |
| **Duplikat** (dari yang berhasil) | Nomor tiket ganda; isi identik (judul + deskripsi) dari pemohon yang sama. Baris pertama dianggap asli |
| **Nilai disamarkan per jenis** | Jumlah penanda `[EMAIL]`, `[NIP]`, `[NIK]`, `[TELEPON]`, `[RAHASIA]`, `[NAMA]` di kolom teks bebas keluaran dikurangi yang sudah ada di sumber |
| Rincian | Per bulan (tanggal dibuka) dan per tim (`assignment_group_name`, kosong = "(tanpa tim)") |

Hasil terakhir: 6.682 sumber → 6.671 berhasil, 11 gagal, 731 tidak lengkap, 65 duplikat isi; 16.518 nilai
disamarkan. Tes: `ai/tests/test_reconcile.py` (data rekaan).

Banding ekspor lama vs baru (baris, tiket hilang, status berubah, hasil SLA berimputasi) ditulis di bagian
"Banding ekspor lama vs baru" laporan yang sama.

```bash
.venv/bin/python ai/scripts/baseline.py         # → plugins/halosis/baseline.json + bagian "baseline" reports/eda.md
```

Baseline dashboard (angka saja): kepatuhan SLA `overall_sla_result_extended` MET ÷ (MET + OVERDUE) beserta jumlah
hasil berimputasi, dan kepuasan (rating 1–5, % ≥ 4). Dibaca `Stats.php` untuk kartu KPI.

## AI-2 — Analisis awal (angka AS-IS)

```bash
.venv/bin/python ai/scripts/eda.py              # → reports/eda.md
```

Hanya membaca `tickets_clean.parquet` (sudah disamarkan) dan hanya menulis angka agregat & label topik;
laporan dipindai pola data pribadi sebelum ditulis. Definisi yang dipakai:

- **Kepatuhan SLA** = PASS ÷ (PASS + BREACH); tiket IN PROGRESS & tanpa bukti SLA dikecualikan
  (cocok dengan angka dokumen 27,59%). Versi dengan seluruh tiket sebagai penyebut ikut dicantumkan.
- **Indikasi salah routing** = `potential_wrong_routing` ≠ NO (REVIEW + YES).
- **Waktu selesai** = `resolved − opened`, waktu kalender (bukan jam kerja).
- **20 masalah paling sering** = topik hasil TF-IDF judul+deskripsi → K-Means (40 kelompok, seed 42),
  topik kembar digabung, kelompok campuran (tim terbanyak < 25%) tidak diperingkat. Judul ditulis bebas,
  jadi judul identik hanya dicantumkan sebagai pembanding.

## AI-3 — Model saran triase (routing ke tim), jenis, urgensi

```bash
.venv/bin/python ai/scripts/train_triage.py     # → ai/models/triage.joblib + reports/triase.md (±1 menit)
.venv/bin/python ai/scripts/train_jenis.py      # → ai/models/jenis.joblib (bagian "jenis" di triase.md)
.venv/bin/python ai/scripts/train_urgensi.py    # → ai/models/urgensi.joblib + urgensi.metrics.json
.venv/bin/python -m pytest -q ai/tests          # tes dengan data rekaan
```

- **Gerbang latih ulang**: `train_triage.py` & `train_jenis.py` menilai model aktif dan kandidat pada set uji yang
  sama; artefak hanya diganti bila kandidat lolos `quality.check` (termasuk tidak turun > 2 poin dari versi aktif).
  Bila tidak lolos, artefak lama tetap dan laporan mencatat perbandingannya.
- **Urgensi insiden** (Medium vs Low, label kolom `urgency`; dampak = urgensi pada 99,7% insiden, prioritas = matriks):
  TF-IDF teks tersamar + one-hot nama tim, LR berbobot seimbang (label) + salinan terkalibrasi (keyakinan),
  validasi silang 5 lipatan. Dipakai layanan hanya bila F1 makro > pembanding "selalu Medium" dan keyakinan ≥ 70%.
  High/Critical & REQ tetap aturan + sinyal dampak di plugin. Menggantikan model prioritas (proksi tier SLA).

- **Input** hanya info saat tiket dibuat: judul + deskripsi + jenis (INC/REQ), disamarkan ulang lewat
  `privacy.mask_text` (juga saat dipakai layanan). Kolom routing/reassignment/SLA/resolusi tidak dipakai.
- **Target** `assignment_group_name` akhir; tim < 30 tiket di data latih → "Lainnya".
- **Split waktu**: latih Jan–Jun, uji Jul–Ags. Pengaturan (C, bobot kelas) dipilih dengan latih Jan–Mei /
  validasi Juni, jadi data uji tidak ikut memilih.
- **Model**: TF-IDF kata (1–2 gram) + karakter (3–5 gram) → Logistic Regression, dikalibrasi sigmoid 5-fold.
  "Keyakinan" = probabilitas tim teratas; < 70% → "Perlu penilaian manual".
- `halosis_ai.triage_model.TriageModel.predict(judul, deskripsi, jenis)` → `{tim, keyakinan,
  perlu_penilaian_manual, top3, tiket_mirip, versi_model}`; `tiket_mirip` diambil dari indeks TF-IDF data
  latih (no. tiket + judul tersamar). Fungsi ini yang dipakai layanan AI-5.
- File model ±40 MB di `ai/models/` (di-ignore git; berisi judul tiket tersamar, jangan dibagikan).

## AI-4 — Indeks pencarian (RAG)

```bash
docker compose up -d                            # agar artikel KB GLPI ikut terindeks
.venv/bin/python ai/scripts/build_index.py      # → ai/index/chunks.parquet + vectors.npy
```

- Sumber: artikel KB GLPI yang terbit (punya target visibilitas) + `qa_pairs` (masalah + solusi tiket) + potongan
  katalog layanan dari indeks sebelumnya (agar tidak hilang sampai GLPI mengirim ulang katalog).
  Semua teks disamarkan ulang dan dipindai pola data pribadi sebelum di-embed.
- Potongan tiket (`search.ticket_chunks`): solusi > 220 kata dipecah, teks masalah diulang di tiap potongan; kolom
  `masalah`/`solusi` menyimpan teks utuh (jawaban ekstraktif & `/kandidat`). Penggabungan solusi identik tersedia
  (`DEDUP` di `build_index.py`, `jumlah_tiket`) tetapi **mati**: Top-1 turun 1,96 poin
  (`.venv/bin/python ai/scripts/banding_solusi.py --qa-lama <qa_pairs lama>` → `reports/banding_solusi.md`).
- `cari` mengembalikan satu hasil per sumber (potongan terbaik).
- Embedding lokal `intfloat/multilingual-e5-base` (gratis, offline setelah unduhan pertama ±1 GB).
- `halosis_ai.search.cari(query, k)` → `[{potongan, skor, sumber (KB-<id> / no. tiket), jenis_sumber, judul, solusi?}]`.
- Skor kosinus E5 cenderung tinggi (≈0,8–0,9 untuk teks terkait), jadi ambang "belum menemukan jawaban"
  di AI-5 perlu sekitar 0,85, bukan 0,5.

## AI-5 — Layanan AI (FastAPI) + integrasi plugin

```bash
# Syarat: ai/models/triage.joblib (AI-3) dan ai/index/ (AI-4) sudah dibuat
docker compose up -d --build halosis-ai
curl http://localhost:8001/health              # dari laptop; GLPI memakai http://halosis-ai:8000
```

| Endpoint | Masukan | Keluaran |
| --- | --- | --- |
| `GET /health` | – | status model triase, indeks, mode generasi |
| `POST /triage` | `{judul, deskripsi, jenis}` (INC/REQ) | `{tim, top3, keyakinan, perlu_penilaian_manual, penjelasan{ringkas, tiket_mirip}, versi_model}` |
| `POST /chat` | `{pertanyaan, riwayat[{peran, teks}]}` | `{ditemukan, jawaban, sumber[{sumber, jenis_sumber, judul, skor}], mode}` |

- Semua input disamarkan (`privacy.mask_text`) sebelum diproses; plugin juga menyamarkan sebelum mengirim.
- `/chat`: skor teratas < `HALOSIS_CHAT_MIN_SCORE` (bawaan **0,83**) → "belum menemukan jawaban".
  Ambang dipilih dari uji: pertanyaan TI 0,85–0,89, pertanyaan di luar topik ≤ 0,81.
- Generasi jawaban: jika `ANTHROPIC_API_KEY` ada di `.env` → dirangkum Claude dari potongan; jika tidak
  (bawaan proyek ini) → **ekstraktif**: solusi teratas apa adanya + sumbernya. Tanpa key, tidak ada data keluar.
- Model & indeks di-mount read-only dari `ai/models` dan `ai/index` (tidak masuk image).

**Plugin** (Konfigurasi HaloSIS → *Layanan AI HaloSIS*: URL + batas waktu):
- Triase: layanan memilih **tim history** → dipetakan ke kategori & grup GLPI (`Triage::SERVICE_TEAM_MAP`;
  grup dengan nama sama persis didahulukan). Dampak/urgensi tetap dari aturan kata kunci. Penjelasan memuat
  top-3 tim dan nomor tiket lama yang mirip.
- Chatbot: layanan dulu; sumber tiket tampil "Tiket serupa <nomor>" (tanpa tautan), sumber KB ditautkan hanya
  jika pengguna boleh melihat artikelnya (jika tidak, jatuh ke pencarian KB lokal).
- Layanan mati / timeout / URL kosong → kembali ke mode sebelumnya (dummy atau AI penyedia), dicatat di
  `files/_log/halosis.log`; tiket tetap tersimpan.
