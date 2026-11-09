# Matriks uji BR-01..08 (C.9)

Kriteria PoC diambil dari dokumen hal. 48 (area validasi) dan hal. 51–57 (hasil per BR). Kolom *Kondisi implementasi* dan
status awal diambil dari `reports/audit_kelengkapan.md:97-104`. Hasil C dilengkapi di tahap AKHIR, 7 Nov 2026, setelah
keempat gate tes lolos.

Status: **Terbukti** = bukti ada dan kriteria terpenuhi; **Sebagian** = ada keterbatasan yang tercatat;
**Terbuka** = menunggu isian tim.

| BR | Kriteria PoC | Hasil PoC (GLPI) | Kondisi implementasi | Bukti (file/log) | Hasil | Status |
| --- | --- | --- | --- | --- | --- | --- |
| BR-01 ITSM core | System of record: tiket, request/incident, status, prioritas, kategori, assignment, user, workflow, pelaporan, konfigurasi, API | Container berjalan, API root HTTP 200; skor 4/5 | Dikonfigurasi lewat plugin, tanpa mengubah inti GLPI | `reports/audit_kelengkapan.md:97`, `plugins/halosis/src/RoleMenu.php`, `docker-compose.yml` | Audit ✅; e2e AKHIR lolos | Terbukti |
| BR-02 SLA | Hitung SLA, deadline, overdue, eskalasi, log perubahan, audit trail | Tiket #157: prioritas 3 → 5 setelah aksi scheduler, log tercatat; skor 4/5 | SLA resmi BPS dari history, peringatan risiko | `reports/audit_kelengkapan.md:98`, `config/sla_layanan.json`, `setup_sla_alerts.py` | Audit ✅; e2e AKHIR lolos (`fitur_penutup.js`: pratinjau SLA) | Terbukti |
| BR-03 Knowledge | Artikel dapat dibuat, dicari, dibaca lewat UI, dipakai retrieval | Artikel "Lupa Password Akun BPS"; skor 4/5 | KB GLPI + Kandidat Knowledge + indeks ulang per artikel | `reports/audit_kelengkapan.md:99`, `plugins/halosis/src/KnowledgeCandidates.php`, `plugins/halosis/src/KnowledgeIndex.php` | Audit ✅; e2e AKHIR lolos (UC-09 5a, draf templat saat LLM none) | Terbukti |
| BR-04 Retrieval | 8 kasus terkendali, Top-1/Top-3/MRR | 100% / 100% / 1,0000 pada PoC terkendali; skor 4/5 | e5 + `search.cari`, `/chat` memakai artikel KB yang terlihat pegawai (FAQ + target) + katalog layanan saja | `reports/replikasi_poc.md` (Retrieval), `reports/banding_embedding.md`, `reports/banding_solusi.md`, `ai/scripts/kasus_retrieval_poc.json` | 8 kasus real KB HaloSIS, 34 sumber: MiniLM Top-1 75%, Top-3 87,5%, MRR 0,8208; e5 62,5%, 87,5%, 0,7614. n=8, 1 kasus = 12,5 poin. e5 tetap dipilih dari 905 kueri (71,93 vs 68,29%). K8 gagal: istilah awam vs teknis | Sebagian: bukan kasus PoC asli |
| BR-05 Triase | 1.339 tiket uji, 39 grup, TF-IDF vs embedding | Top-1 68,33/70,43%, Top-3 90,89/90,29%, MRR 0,7989/0,8092; skor 4/5 | LR TF-IDF terkalibrasi, 21 kelas, ambang 40/70, validasi Operator. Urgensi tidak lolos skema B, memakai aturan kata kunci | `reports/replikasi_poc.md` (Triase), `reports/replikasi_poc_per_grup.csv`, `reports/replikasi_poc_confusion.csv`, `reports/kalibrasi_ambang.md`, `reports/triase.md`, `logs/a3a4_metrik.log` | 39 grup, label asli: Top-1 78,47%, Top-3 91,31%, MRR 0,8505, F1 makro 40,62%; k-NN rekonstruksi 67,67–68,88%, F1 45,45–50,16%. Rekonstruksi cocok k-NN (MRR 0,7991 vs 0,7989). Urgensi nonaktif, gagal skema B | Sebagian: rekonstruksi; F1 makro lebih rendah; urgensi nonaktif |
| BR-06 Percakapan | Ambil artikel, retrieval relevan, jawaban berbasis knowledge, unknown-answer | Similarity ±0,8592, Qwen menjawab, risiko halusinasi tercatat; skor 3/5 | RAG grounded: sumber tersetujui, tolak bila konteks kosong, sitasi; bawaan ekstraktif | `reports/replikasi_poc.md` (Ekstraktif vs Qwen), `reports/kalibrasi_ambang.md`, `logs/uji_llm.log`, `reports/banding_solusi.md` | 10 uji, 9 sesuai: ekstraktif 5/5, Qwen 4/5 (P2 ditolak LLM). Unknown-answer: tidak ada jawaban pada P3–P5. Kalibrasi 0,83 pada 34 sumber: 0% rekaan dijawab, 37,50% pilihan. Tawaran laporan tetap ada di mode pilihan (e2e) | Sebagian: uji kecil, relevansi menunggu tim |
| BR-07 Pola | DBSCAN eps 0,25, min 5, MiniLM atas 2.777 INC; sliding window 1 jam, 0,70, min 3 | 14 klaster, 1.073 noise, 1.704 terkluster; 23 → 17 episode; skor 4/5 | e5 dipusatkan, rata-rata ≥ 0,50 per jendela 1 jam; DBSCAN 0,50/3 opsional; ambang di Pengaturan AI | `reports/replikasi_poc.md` (Pola), `reports/banding_pola.md`, `ai/halosis_ai/patterns.py`, `logs/a4_pola_set.log` | Rekonstruksi metode PoC: 8 klaster, 1.011 noise, 1.766 terkluster; 19 → 19 atau 15 → 15. Metode produksi: 8 kelompok, 25 tiket, kemurnian 0,917, setara DBSCAN | Sebagian: hasil PoC tidak terulang; metode produksi berbeda |
| BR-08 HITL | Rekomendasi AI disetujui manusia lewat UI, tercatat di audit | Tiket #156: ACCEPTED, approval dan timestamp tercatat; skor 4/5 | Terima/Ubah/Tolak, alasan wajib ≥ 5 karakter, audit trail | `reports/audit_kelengkapan.md:104`, `plugins/halosis/src/Triage.php`, `plugins/halosis/src/Decision.php` | Audit ✅; e2e AKHIR lolos (UC-05, UC-06, UC-07) | Terbukti |

## Catatan gate AKHIR

Gate 7 Nov 2026: `pytest ai/tests` 83 lolos; `php -l` 6 file lolos; e2e `alur_alternatif.js` 11/11, `fitur_penutup.js` 6/6,
`revisi_t4.js` 5/5; `scripts/demo_snapshot.sh simpan` lolos. Bukti: `logs/akhir_*`.

E2E diulang karena image `halosis-ai` belum dibangun ulang setelah commit B, sehingga `/kandidat/draf` menjawab 404 pada
putaran pertama. Hasil di atas memakai image baru. Pada ulangan, kalimat uji UC-01 4a / UC-02 5a diganti karena kalimat lama
kini masuk mode `pilihan`; assert tidak diubah, dan ditambah 1 uji bahwa tawaran laporan tetap ada di mode itu.
`fitur_penutup.js` dan `revisi_t4.js` tidak diulang setelah perubahan kalimat uji karena berkasnya tidak berubah.

## Yang masih terbuka

- BR-04: 8 kasus PoC asli tidak tersedia. Yang diuji adalah kasus real dari KB HaloSIS.
- BR-05: dokumen menulis 6.659 tiket, referensi 5.319, uji 1.339, 39 grup. Angka itu tidak saling cocok dan tidak bisa
  diperoleh dari data yang tersedia (6.668 tiket, 56 grup), jadi hasilnya pembanding, bukan replikasi identik.
- Relevansi: `reports/penilaian_relevansi.xlsx` diisi tim, lalu dipakai untuk menguji ambang chat.
- NFR-08: uji usability belum dilakukan.
