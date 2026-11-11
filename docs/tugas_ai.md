TUGAS: Perbaikan AI HaloSIS (gabungan dokumentasi_ai.md §5.3 + revisi tim), branch dev

Dikerjakan per sesi. Setiap sesi HANYA mengerjakan bagian yang diminta di prompt sesi.

ATURAN EKSEKUSI (WAJIB)
Branch: dev. JANGAN git add/commit/push. JANGAN ubah inti GLPI. JANGAN docker compose down -v.
Ubah hanya file yang relevan dengan tiap butir; sebutkan semua file yang diubah/dibuat di laporan.
Urutan kerja: A → B → C → AKHIR. Jangan mulai C sebelum A selesai dan terverifikasi.
C bersifat READ-ONLY terhadap model aktif. Hanya A.3 yang boleh menulis artefak model, dan hanya bila lolos gerbang.
Redaksi: jangan cetak/tulis isi tiket, nama orang, atau data pribadi ke chat, log, file reports, atau pesan apa pun. Terapkan penyamaran otomatis pada output skrip.
Jika ada ambiguitas yang tidak terjawab oleh repo atau dokumen, TANYA dan BERHENTI. Jangan berasumsi.
Jika salah satu gate tes gagal: BERHENTI, laporkan kegagalan, jangan update dokumentasi final.
Laporan chat per sesi maks. 8 baris. File reports/*.md TIDAK dibatasi.
ATURAN HEMAT TOKEN (WAJIB)
Arahkan output panjang ke file (> logs/<nama>.log 2>&1) dan tampilkan hanya tail -20.
Jangan baca file besar utuh: pakai grep, head, sed -n, atau wc. Jangan buka PDF/xlsx utuh; untuk dokumen pakai grep di docs/dokumen.txt.
Jangan ambil screenshot; bukti cukup berupa log atau teks.
Pengunduhan model dan pelatihan/replikasi yang lama: tulis skrip & beri perintahnya, saya yang menjalankan (kecuali prompt sesi meminta Anda menjalankan).
Tes e2e (Playwright) hanya sekali, di bagian AKHIR.
Jangan ulangi perintah yang gagal lebih dari 2×; laporkan dan lanjut atau berhenti.
Folder logs/ harus di-ignore git (tambahkan ke .gitignore bila belum).
DEFINISI GERBANG
Pakai gerbang di reports/tata_kelola_ai.md & ai/halosis_ai/quality.py. Jika tidak mencakup skema baru (urgensi skema B), usulkan definisi (metrik + ambang + skema) dan BERHENTI untuk approval.
Gerbang urgensi memakai skema B (tim prediksi out-of-fold), ambang dipilih di lipatan dalam.
Gerbang triase & pola memakai ambang aktif yang diatur di Pengaturan AI.
BACKUP SEBELUM GANTI MODEL AKTIF
Salin artefak model aktif ke backup/model-<YYYYMMDD-HHMMSS>/ (folder backup/ di-ignore git) dan catat sha256 setiap file di MANIFEST.txt dalam folder itu.
Jika gagal gerbang: kembalikan artefak lama dari backup dan laporkan.
A. KEPATUHAN

A.1 Chatbot pegawai (/chat) HANYA menjawab dari sumber tersetujui: artikel KB berstatus terbit + katalog layanan (= indeks layanan yang sudah ada: /reindex/layanan, KnowledgeIndex). Solusi tiket mentah TETAP dipakai untuk "Cari pengetahuan" (petugas) dan "Kandidat → artikel", TIDAK untuk /chat. Ukur dampak sebelum/sesudah dan tulis ke reports/banding_solusi.md (metrik + contoh tersamar).

A.2 build_index.py mengambil artikel KB lewat REST API GLPI / dorongan plugin, BUKAN koneksi DB langsung. Jika API mati: gagal dengan pesan jelas (exit code non-zero + pesan), bukan fallback diam-diam. Tunjukkan bukti (log).

A.3 Urgensi: evaluasi dua skema — A: tim aktual; B: tim prediksi out-of-fold. Ambang & gerbang memakai B; ambang dipilih di lipatan dalam. train_urgensi.py hanya menulis artefak bila lolos gerbang (lihat BACKUP + DEFINISI GERBANG). Tulis hasil A vs B ke reports/triase.md.

A.4 Ambang pola & ambang triase aktif dapat diatur di Pengaturan AI; gerbang memakai ambang aktif tersebut. Buktikan dengan log.

Uji A: .venv/bin/python -m pytest ai/tests -q > logs/pytest_a.log 2>&1; tail -20 logs/pytest_a.log dan php -l pada file PHP yang diubah.

B. KONFIGURASI MODEL (siap pindah ke server AI BPS)

B.5 Tambahkan dukungan env agar NANTI pindah ke server AI BPS cukup ubah env, tanpa ubah kode:

EMBEDDING_PROVIDER=local|openai, EMBEDDING_BASE_URL, EMBEDDING_MODEL, EMBEDDING_API_KEY
LLM_PROVIDER=none|openai|anthropic, LLM_BASE_URL, LLM_MODEL, LLM_API_KEY
Embedding remote memakai /v1/embeddings dengan prefix e5 tetap konsisten (query: / passage:).
Bila model/dimensi berubah: layanan MENOLAK indeks lama dengan pesan "bangun ulang indeks".
Bawaan: e5 lokal, LLM none (ekstraktif). Tambahkan variabel ke .env.example (nilai kosong).

B.6 Profile compose llm: Ollama + qwen2.5:3b (sesuai PoC), dipakai via LLM_PROVIDER=openai (http://ollama:11434/v1). Di Mac, dokumentasikan & dukung opsi Ollama native (http://host.docker.internal:11434/v1) karena Docker Mac tanpa GPU; saya sudah memasang Ollama native dan mengunduh qwen2.5:3b. RAG grounded: hanya dari sumber tersetujui, tolak bila konteks kosong, sertakan sitasi sumber. Uji singkat 3 pertanyaan (1 ada jawabannya, 1 tidak ada, 1 di luar TI) dan simpan hasilnya di log.

Uji B: pytest (output ke log) dan php -l bila ada PHP yang diubah.

C. BUKTI & REPLIKASI POC (model aktif TIDAK berubah)

TULIS skripnya saja, JANGAN jalankan pelatihan/replikasi yang lama. Beri saya urutan perintah untuk menjalankannya (output ke logs/), lalu berhenti.

C.7 ai/scripts/replikasi_poc.py → reports/replikasi_poc.md:

Triase pengaturan PoC persis: split acak rs42 20%, 39 grup, TF-IDF vs embedding MiniLM & e5, metrik Top-1/Top-3/ MRR + F1 makro, presisi/recall, confusion matrix. Lalu model HaloSIS pada split yang sama.
Pola: DBSCAN eps=0,25 min_samples=5 MiniLM atas 2.777 INC + sliding window 1 jam (bandingkan vs 14 klaster / 23→17 episode).
Retrieval: 8 kasus dari docs/dokumen.txt hal. 53 (cari dengan grep), untuk MiniLM & e5.
Uji ekstraktif vs Qwen grounded + unknown-answer.
Siapkan reports/penilaian_relevansi.xlsx (20 kueri × 5 hasil, teks tersamar, kolom nilai 0–2 kosong) untuk diisi tim; JANGAN isi nilainya.

C.8 Simpan ulang ai/scripts/banding_embedding.py & ai/scripts/banding_pola.py yang mereproduksi angka laporan masing-masing (selisih wajar dijelaskan).

C.9 reports/kalibrasi_ambang.md (chat 0,78/0,83; triase 40/70) dan reports/matriks_uji_br.md: BR-01..08 × kriteria PoC, kondisi implementasi, bukti (file/log), hasil, status. Bagian yang butuh hasil skrip C.7/C.8 diisi dari laporan yang dihasilkan saat skrip dijalankan.

AKHIR (setelah A, B, C selesai & skrip C sudah saya jalankan)
Gate tes (semua wajib lolos sebelum update dokumen final; output ke logs/, tampilkan tail -20):
.venv/bin/python -m pytest ai/tests
php -l pada semua file PHP yang diubah
semua tes di tests/e2e/ (node) — sekali saja
scripts/demo_snapshot.sh simpan (ulang)
Jika ada gate gagal: BERHENTI, laporkan perintah + error ringkas, jangan update dokumen final.
Setelah lolos: perbarui reports/dokumentasi_ai.md §4–5, kedua audit, README (cara pakai env model & profile llm), CHANGELOG (tetap versi 1.0.0), dan lengkapi reports/matriks_uji_br.md dari hasil C.
Ringkasan akhir chat maks. 12 baris: status A/B/C, gate tes, file yang dibuat/diubah, hal yang menunggu approval.