# Usulan definisi gerbang untuk A.3 dan A.4

**Status: disetujui 6 Nov 2026 dengan tambahan.** Definisi final ada di `reports/tata_kelola_ai.md` §2 dan `ai/halosis_ai/quality.py`; dokumen ini hanya riwayat usulan.

`docs/tugas_ai.md` meminta usulan + berhenti bila gerbang yang ada tidak mencakup skema baru. Dua hal belum tercakup:
`tata_kelola_ai.md` §2 mendefinisikan gerbang urgensi pada "validasi silang 5 lipatan" dengan tim aktual, dan belum ada
gerbang pola di `quality.py` maupun tata kelola. Gerbang triase hanya memeriksa ambang tetap 70%. Belum ada kode A.3/A.4
yang diubah, dan model aktif tidak berubah.

## Usulan 1: gerbang urgensi skema B

- **Skema**: validasi silang bertingkat. Lipatan luar 5 (bertingkat, seed 42). Di tiap data latih luar, fitur `tim` =
  prediksi tim out-of-fold (5 lipatan dalam, `triage_model.build_pipeline`); pada data uji luar, `tim` = prediksi model
  tim yang dilatih pada seluruh data latih luar.
- **Pemilihan ambang**: `pick_urgency_thresholds` hanya pada P(Low) lipatan dalam, lalu ambang itu diterapkan ke data uji
  luar yang belum pernah dilihat.
- **Metrik & batas** (tidak berubah): Low presisi ≥ 75%, batas bawah Wilson 95% > proporsi Low, ≥ 30 tiket; Medium
  akurasi > proporsi Medium + 3 poin, ≥ 30 tiket. Dihitung dari gabungan prediksi lipatan luar.
- **Lolos**: minimal satu kelas lolos (aturan `quality.check` saat ini); hanya kelas lolos yang disarankan.
- **Artefak**: ambang akhir = median ambang lima lipatan luar. Skema A (tim aktual) dilaporkan sebagai pembanding saja.
- **Risiko**: Medium saat ini lolos tipis (84,30% vs syarat 84,24%) dengan tim aktual. Skema B memakai tim prediksi, jadi
  kelas ini mungkin gagal; bila kedua kelas gagal, artefak lama tetap dipakai dan saran urgensi tetap dari aturan.

## Usulan 2: gerbang pola pada ambang aktif

Tidak ada label pola manual, jadi satu-satunya metrik yang sudah tersedia adalah kemurnian tim (`banding_pola.md`).

- **Skema**: putar ulang history insiden memakai parameter aktif Pengaturan AI (`pattern_method`, ambang/`pattern_eps`,
  `pattern_min_samples`, `pattern_window`, `pattern_min_tickets`).
- **Metrik & batas**: kemurnian tim rata-rata ≥ 0,85 dan ≥ 1 kelompok. Acuan saat ini: 0,905 (bawaan) dan 0,917 (DBSCAN).
- **Bila gagal**: tampil peringatan di Pengaturan AI, deteksi tetap berjalan (nilai 0,85 usulan, belum punya dasar uji).
- **Keterbatasan**: kemurnian tim hanya proksi, bukan kebenaran pola.

## Usulan 3: gerbang triase pada ambang aktif

- **Metrik**: syarat "akurasi pada keyakinan ≥ ambang ≥ 85%" dihitung pada `triage_threshold` aktif, bukan 70% tetap.
- **Cara**: `model_metrics.py` menyimpan kurva akurasi & cakupan per 1 poin ambang (dari set uji yang sama); GLPI
  mengirim ambang aktif ke `/triage`.
- **Ambang rendah** (`ai_threshold_low`): tidak digerbang, karena hanya memisahkan penilaian manual dari pilih kandidat.
- **Bila gagal**: panel menandai "belum lolos uji kualitas", sehingga menurunkan ambang di bawah titik 85% akan memunculkan
  tanda itu. Formulir Pengaturan AI menampilkan peringatan saat menyimpan.

## Keputusan yang dibutuhkan

1. Setujui, ubah, atau tolak ketiga usulan di atas.
2. Pelatihan skema B butuh ±30 kali latih model tim (5 lipatan luar × 6; durasi belum diukur), jadi menurut aturan hemat token saya menulis skripnya dan Anda
   yang menjalankan. Konfirmasi bila ingin saya yang menjalankan.
