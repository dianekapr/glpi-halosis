# Matriks uji BR-01..08 (C.9)

Kriteria PoC diambil dari dokumen hal. 48 (area validasi) dan hal. 51–57 (hasil per BR). Kolom *Kondisi implementasi* dan
status awal diambil dari `reports/audit_kelengkapan.md:97-104`. Baris yang bertanda **Menunggu C** dilengkapi di tahap
AKHIR dari laporan hasil skrip; status belum final sampai gate tes AKHIR lolos.

Status: **Terbukti** = bukti ada dan kriteria terpenuhi; **Sebagian** = ada keterbatasan yang tercatat;
**Menunggu C** = perlu hasil skrip C.7–C.9 atau isian tim.

| BR | Kriteria PoC | Hasil PoC (GLPI) | Kondisi implementasi | Bukti (file/log) | Hasil | Status |
| --- | --- | --- | --- | --- | --- | --- |
| BR-01 ITSM core | System of record: tiket, request/incident, status, prioritas, kategori, assignment, user, workflow, pelaporan, konfigurasi, API | Container berjalan, API root HTTP 200; skor 4/5 | Dikonfigurasi lewat plugin, tanpa mengubah inti GLPI | `reports/audit_kelengkapan.md:97`, `plugins/halosis/src/RoleMenu.php`, `docker-compose.yml` | Audit ✅ | Terbukti, ulang gate e2e AKHIR |
| BR-02 SLA | Hitung SLA, deadline, overdue, eskalasi, log perubahan, audit trail | Tiket #157: prioritas 3 → 5 setelah aksi scheduler, log tercatat; skor 4/5 | SLA resmi BPS dari history, peringatan risiko | `reports/audit_kelengkapan.md:98`, `config/sla_layanan.json`, `setup_sla_alerts.py` | Audit ✅ | Terbukti, ulang gate e2e AKHIR |
| BR-03 Knowledge | Artikel dapat dibuat, dicari, dibaca lewat UI, dipakai retrieval | Artikel "Lupa Password Akun BPS"; skor 4/5 | KB GLPI + Kandidat Knowledge + indeks ulang per artikel | `reports/audit_kelengkapan.md:99`, `plugins/halosis/src/KnowledgeCandidates.php`, `plugins/halosis/src/KnowledgeIndex.php` | Audit ✅ | Terbukti, ulang gate e2e AKHIR |
| BR-04 Retrieval | 8 kasus terkendali, Top-1/Top-3/MRR | 100% / 100% / 1,0000 pada PoC terkendali; skor 4/5 | e5 + `search.cari`, `/chat` memakai KB terbit + katalog layanan saja | `reports/replikasi_poc.md` (Retrieval), `reports/banding_embedding.md`, `reports/banding_solusi.md`, `ai/scripts/kasus_retrieval_poc.json` | Teks 8 kasus tidak ada di dokumen; menunggu isian tim | Menunggu C |
| BR-05 Triase | 1.339 tiket uji, 39 grup, TF-IDF vs embedding | Top-1 68,33/70,43%, Top-3 90,89/90,29%, MRR 0,7989/0,8092; skor 4/5 | LR TF-IDF terkalibrasi, 21 kelas, ambang 40/70, validasi Operator. Urgensi tidak lolos skema B, memakai aturan kata kunci | `reports/replikasi_poc.md` (Triase), `reports/replikasi_poc_per_grup.csv`, `reports/replikasi_poc_confusion.csv`, `reports/kalibrasi_ambang.md`, `reports/triase.md`, `logs/a3a4_metrik.log` | Audit 🟡 (urgensi); split dokumen tidak bisa diulang persis | Menunggu C, sementara Sebagian |
| BR-06 Percakapan | Ambil artikel, retrieval relevan, jawaban berbasis knowledge, unknown-answer | Similarity ±0,8592, Qwen menjawab, risiko halusinasi tercatat; skor 3/5 | RAG grounded: sumber tersetujui, tolak bila konteks kosong, sitasi; bawaan ekstraktif | `reports/replikasi_poc.md` (Ekstraktif vs Qwen), `reports/kalibrasi_ambang.md`, `logs/uji_llm.log`, `reports/banding_solusi.md` | Uji singkat B.6: 1 terjawab, 2 ditolak | Menunggu C |
| BR-07 Pola | DBSCAN eps 0,25, min 5, MiniLM atas 2.777 INC; sliding window 1 jam, 0,70, min 3 | 14 klaster, 1.073 noise, 1.704 terkluster; 23 → 17 episode; skor 4/5 | e5 dipusatkan, rata-rata ≥ 0,50 per jendela 1 jam; DBSCAN 0,50/3 opsional; ambang di Pengaturan AI | `reports/replikasi_poc.md` (Pola), `reports/banding_pola.md`, `ai/halosis_ai/patterns.py`, `logs/a4_pola_set.log` | Metode produksi berbeda dari PoC, sudah dicatat | Menunggu C |
| BR-08 HITL | Rekomendasi AI disetujui manusia lewat UI, tercatat di audit | Tiket #156: ACCEPTED, approval dan timestamp tercatat; skor 4/5 | Terima/Ubah/Tolak, alasan wajib ≥ 5 karakter, audit trail | `reports/audit_kelengkapan.md:104`, `plugins/halosis/src/Triage.php`, `plugins/halosis/src/Decision.php` | Audit ✅ | Terbukti, ulang gate e2e AKHIR |

## Yang masih terbuka

- BR-04: tim mengisi 8 kasus di `ai/scripts/kasus_retrieval_poc.json`. Tanpa itu, replikasi retrieval hal. 53 tidak bisa dinyatakan.
- BR-05: dokumen menulis 6.659 tiket, referensi 5.319, uji 1.339, 39 grup. Angka itu tidak saling cocok dan tidak bisa
  diperoleh dari data yang tersedia (6.668 tiket, 56 grup), jadi hasilnya pembanding, bukan replikasi identik.
- Relevansi: `reports/penilaian_relevansi.xlsx` diisi tim, lalu dipakai untuk menguji ambang chat.
