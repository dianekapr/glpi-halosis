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
