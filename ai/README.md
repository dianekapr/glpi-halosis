# AI HaloSIS — pipeline data & layanan

Dibangun dari history tiket `data/raw/ticketing_history_202601_202608.xlsx` (6.682 tiket Jan–Ags 2026).

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
| NIK 16 digit | `[NIK]` |
| Nomor HP (08…, +62…, 62…) | `[TELEPON]` |
| Nilai setelah password/pasw/pwd/sandi/PIN/OTP (termasuk "password sementara :") | `[RAHASIA]` |
| Nama setelah sapaan (Ysh./Yth. Bpk./Ibu, Pak, Bu, …) | `[NAMA]` |
| Nama lengkap & bagian nama dari kolom pengguna (requester/assigned/resolved_by/closed_by) | `[NAMA]` |

Kolom nama pengguna dihapus dan diganti ID samaran (`*_pid`, mis. `U00042`; pemetaan tidak disimpan).
Skrip **memindai ulang** keluaran dan menolak menyimpan bila masih ada pola data pribadi.

Solusi (`ai/halosis_ai/conversations.py`): `all_conversations` dipecah per pesan; kalimat template operator &
salam dibuang; pesan permintaan informasi dan pesan pegawai bukan solusi; pesan bercirikan petugas yang terakhir
dipilih. Bila tidak ada, dipakai `resolution` lalu `close_notes` yang bukan template ("solved", "done", ".").

**Batasan:** nama orang yang tidak ada di kolom pengguna dan ditulis tanpa sapaan tidak terdeteksi; bagian
nama yang juga kata umum (sering muncul berhuruf kecil) sengaja tidak disamarkan.

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

## AI-3 — Model saran triase (routing ke tim)

```bash
.venv/bin/python ai/scripts/train_triage.py     # → ai/models/triage.joblib + reports/triase.md (±1 menit)
.venv/bin/python -m pytest -q ai/tests          # tes dengan data rekaan
```

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

- Sumber: artikel KB GLPI yang terbit (punya target visibilitas) + `qa_pairs` (masalah + solusi tiket).
  Semua teks disamarkan ulang dan dipindai pola data pribadi sebelum di-embed.
- Embedding lokal `intfloat/multilingual-e5-base` (gratis, offline setelah unduhan pertama ±1 GB).
- `halosis_ai.search.cari(query, k)` → `[{potongan, skor, sumber (KB-<id> / no. tiket), jenis_sumber, judul}]`.
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
