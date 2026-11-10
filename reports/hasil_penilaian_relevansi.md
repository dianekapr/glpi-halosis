# Hasil penilaian relevansi "Cari pengetahuan petugas"

Sumber: `reports/penilaian_relevansi.xlsx`, sheet "Wahid" (satu penilai ahli domain). 20 kueri × 5 hasil = 100 baris, semuanya
solusi tiket lama (bukan `/chat`). Isi tiket dan teks kueri tidak dikutip di sini. Data hanya dibaca, tidak diubah.

Kategori catatan penilai: 48 baris "butuh tindakan petugas" (nilai 0), 9 "belum ada solusi" (nilai 0), 6 "bisa himbauan"
(nilai 1, sebagian), 28 "sudah sesuai" (nilai 2), 9 usulan perbaikan teks (nilai 2). Sebaran nilai: 0 = 57, 1 = 6, 2 = 37.

## 1. Relevansi untuk petugas

Relevan = nilai 2 atau 1, ditambah nilai 0 berkategori "butuh tindakan petugas" (solusi memang relevan bagi petugas, hanya
tidak bisa dijalankan sendiri oleh pegawai). 91 dari 100 baris relevan. Satu-satunya yang tidak relevan: 9 baris "belum ada solusi".

| Metrik (n = 20 kueri) | Nilai |
| --- | ---: |
| Precision@1 | 90,00% |
| Precision@3 | 91,67% |
| Precision@5 | 91,00% |
| nDCG@5 | 0,9622 |
| MRR | 0,9375 |

Per pita skor: semua 100 baris berskor 0,8387–0,9298, jadi seluruhnya masuk pita ≥ 0,83. Pita < 0,78 dan 0,78–0,83 kosong
(0 baris), sehingga tidak ada perbandingan antarpita yang bisa dihitung. Di pita ≥ 0,83: P@1 90,00%, P@3 91,67%, P@5 91,00%,
nDCG@5 0,9622, MRR 0,9375 (sama dengan tabel di atas). Skor rata-rata baris relevan 0,8827 vs 0,8714 untuk tidak relevan, selisih
kecil, jadi skor tidak membedakan keduanya di rentang ini.

## 2. Kelayakan self-service

Layak = nilai 2 dan bukan kategori "butuh tindakan petugas". 37 dari 100 baris (37,00%) layak.

| Metrik | Nilai |
| --- | ---: |
| Precision@1 | 30,00% (6 dari 20 kueri) |
| Precision@3 | 35,00% |
| Proporsi baris layak | 37,00% |
| Kueri dengan ≥ 1 hasil layak di 5 teratas | 13 dari 20 (65%) |

Sensitivitas: bila 9 baris nilai 2 yang masih perlu perbaikan teks tidak dihitung, tersisa 28 baris (28,00%) yang layak apa adanya.

## 3. Kaitan dengan keputusan dan ambang

- **Keputusan A.1 terdukung.** Relevan untuk petugas 91% tetapi layak self-service hanya 37%. Mayoritas solusi tiket (48%)
  berupa informasi bahwa tindakan sudah dilakukan petugas. Itu berguna bagi petugas, tetapi bila dijawab mentah di `/chat`
  pegawai menerima kalimat yang tidak bisa dijalankan. Maka `/chat` hanya memakai KB terbit + katalog, sedangkan solusi
  tiket tetap untuk petugas dan Kandidat → artikel.
- **Ambang 0,83 / 0,78 belum bisa dikalibrasi dari data ini.** Seluruh skor ≥ 0,83, jadi data tidak menguji area di bawah
  ambang. Skor juga tidak memisahkan relevan dari tidak relevan. Ambang tetap berstatus belum terkalibrasi; yang bisa
  dikatakan hanya bahwa untuk petugas, hasil di atas 0,83 hampir selalu relevan.
- **Bahan kurasi KM** (usulan perbaikan teks dari penilai, ringkas): hapus kalimat yang menyatakan tindakan sudah dilakukan
  ("akun telah direset", "permintaan telah dipenuhi", "password sudah direset"); hapus password sementara dan data pribadi
  (nama pegawai, email, nama perangkat, tanggal kejadian); ganti "kami telah mengirimkan link ke email …" dengan langkah
  yang dilakukan pegawai; buang sisa format markdown. Solusi bertipe "hanya informasi" perlu ditulis ulang sebagai langkah
  mandiri sebelum jadi artikel KB; 9 baris "belum ada solusi" tidak layak dijadikan kandidat.

## 4. Keterbatasan

- Satu penilai, jadi tidak ada kesepakatan antarpenilai (kappa tidak dapat dihitung); penilaian bisa bias ke satu sudut pandang.
- Hanya 20 kueri; satu kueri = 5 poin persentase pada P@1. Interval kepercayaan lebar, angka bersifat indikatif.
- Rentang skor sempit (0,84–0,93), tanpa data di bawah ambang.
- Kueri dan hasil berkonsentrasi pada topik akun/password, tidak mewakili seluruh layanan.
- Definisi "relevan untuk petugas" memasukkan nilai 0 berkategori butuh tindakan; tanpa aturan itu P@1 hanya 30,00% dan MRR 0,4517.
