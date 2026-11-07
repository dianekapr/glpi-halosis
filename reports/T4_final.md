# Tugas 4 HaloSIS: Use Scenario dan Real Use Case

Dokumen ini memuat use scenario dan real use case HaloSIS. Rujukan langkah mengikuti essential use case Tugas 3 versi final.

## A. Use Scenario

### A.0 Konvensi

**Use case yang dipilih.** Use scenario dibuat untuk proses utama yang paling sering dijalankan dan paling banyak punya variasi alur.

| UC | Alasan dipilih | Skenario |
|---|---|---:|
| UC-01 Berkonsultasi melalui AI Chatbot | Pintu masuk utama pegawai; hasilnya bisa selesai, menjadi tiket, atau berhenti | 5 |
| UC-03 Membuat Tiket | Semua masalah yang belum selesai berakhir di sini; sumber tiketnya beragam | 5 |
| UC-05 Memvalidasi Rekomendasi AI & Meneruskan Tiket | Inti human-in-the-loop (BR-08); dipakai Operator setiap hari | 6 |
| UC-06 Menangani & Menyelesaikan Tiket | Pekerjaan utama Tim Teknis | 3 |
| UC-07 Memantau Status & Mengonfirmasi Penyelesaian | Penutup siklus tiket; ada jalur tolak dan jalur tanpa respons | 4 |
| UC-09 Mengelola Knowledge Base | Mengubah solusi tiket menjadi knowledge | 6 |

UC-02 dan UC-04 tidak dibuatkan skenario karena merupakan use case sistem yang di-include dan tidak memuat keputusan pengguna. UC-08 dijalankan penjadwal dan aktor hanya meninjau hasilnya. UC-10 jarang dijalankan dan hanya oleh Administrator. Keempatnya tetap dijabarkan di Bagian B.

**Rujukan langkah.** Angka dalam kurung di akhir setiap langkah menunjuk langkah essential use case Tugas 3 versi AKPSI-6.

| Bentuk | Arti |
|---|---|
| `(3)` | Langkah 3 alur normal |
| `(3 & 4)` | Gabungan langkah 3 dan 4 |
| `(S-1, 2)` | Subflow S-1, lalu kembali ke langkah 2 |
| `(4a)` | Alur alternatif 4a |
| `(UC-04 6a)` | Langkah pada use case lain |
| `(†)` | Tidak ada padanan di Tugas 3; lihat subbab Penyesuaian terhadap Tugas 3 |

### A.1 UC-01 Berkonsultasi melalui AI Chatbot

#### SC-01.1 Pegawai menyelesaikan kendala secara mandiri

1. Pegawai menyampaikan kendala layanan TI kepada chatbot. (1)
2. Sistem mencatat percakapan. (2)
3. Sistem mencari solusi yang relevan. (3)
4. Sistem menyajikan solusi beserta sumber rujukannya. (4)
5. Pegawai mencoba solusi tersebut. (5)
6. Pegawai menyatakan masalah terselesaikan dan memberi penilaian. (6)
7. Sistem mengakhiri konsultasi dan mencatat solusi yang digunakan. (7)

#### SC-01.2 Pegawai tidak mendapat solusi lalu melaporkan kendala

1. Pegawai menyampaikan kendala layanan TI kepada chatbot. (1)
2. Sistem mencatat percakapan. (2)
3. Sistem mencari solusi yang relevan. (3)
4. Sistem tidak menemukan solusi dan menyampaikan bahwa jawaban belum tersedia. (4a)
5. Sistem menawarkan pelaporan tiket. (4a)
6. Pegawai menyetujui tawaran tersebut. (4a)
7. Sistem melanjutkan ke pembuatan tiket dengan membawa ringkasan konsultasi. (4a; UC-03 1a)

#### SC-01.3 Pegawai mendapat solusi yang tidak berhasil lalu melaporkan kendala

1. Pegawai menyampaikan kendala layanan TI kepada chatbot. (1)
2. Sistem mencatat percakapan. (2)
3. Sistem mencari solusi yang relevan. (3)
4. Sistem menyajikan solusi beserta sumber rujukannya. (4)
5. Pegawai mencoba solusi tersebut. (5)
6. Pegawai menyatakan masalah belum terselesaikan. (6a)
7. Sistem menawarkan pelaporan tiket dengan membawa ringkasan konsultasi. (6a)
8. Pegawai menyetujui tawaran tersebut. (6a)
9. Sistem melanjutkan ke pembuatan tiket. (6a; UC-03 1a)

#### SC-01.4 Pegawai tidak ingin membuat tiket setelah solusi gagal

1. Pegawai menyampaikan kendala layanan TI kepada chatbot. (1)
2. Sistem mencatat percakapan. (2)
3. Sistem mencari solusi yang relevan. (3)
4. Sistem menyajikan solusi beserta sumber rujukannya. (4)
5. Pegawai mencoba solusi tersebut. (5)
6. Pegawai menyatakan masalah belum terselesaikan. (6a)
7. Sistem menawarkan pelaporan tiket dengan membawa ringkasan konsultasi. (6a)
8. Pegawai menyatakan tidak ingin membuat tiket. (6b)
9. Sistem mengakhiri konsultasi dan menyimpan riwayatnya. (6b)

#### SC-01.5 Pegawai berkonsultasi saat sistem tidak dapat memberikan jawaban

1. Pegawai menyampaikan kendala layanan TI kepada chatbot. (1)
2. Sistem mencatat percakapan. (2)
3. Sistem tidak dapat memberikan jawaban saat itu. (3a)
4. Sistem memberi tahu pegawai. (3a)
5. Sistem mengarahkan pegawai untuk melaporkan tiket. (3a)

**Ringkasan perbedaan UC-01**

| Skenario | Titik beda | Jalur Tugas 3 | Hasil akhir |
|---|---|---|---|
| SC-01.1 | Tidak ada | 1–7 | Selesai mandiri |
| SC-01.2 | Langkah 4 | 4a | Lanjut ke UC-03 |
| SC-01.3 | Langkah 6 | 6a | Lanjut ke UC-03 |
| SC-01.4 | Langkah 6 dan 8 | 6a, 6b | Berakhir tanpa tiket |
| SC-01.5 | Langkah 3 | 3a | Diarahkan melaporkan tiket |

### A.2 UC-03 Membuat Tiket

#### SC-03.1 Pegawai melaporkan kendala langsung melalui portal

1. Pegawai memilih jenis layanan yang dibutuhkan. (1)
2. Pegawai menjelaskan permintaan atau masalah dan melampirkan bukti pendukung bila ada. (2)
3. Pegawai mengajukan tiket. (3)
4. Sistem memeriksa kelengkapan informasi. (4)
5. Sistem mencatat tiket dengan nomor unik dan status Baru. (5)
6. Sistem mulai menghitung batas waktu SLA, menyiapkan rekomendasi triase, dan mengirim konfirmasi kepada pegawai. (6)
7. Sistem menempatkan tiket dalam antrean validasi operator. (7)

#### SC-03.2 Pegawai membuat tiket dari konsultasi chatbot

1. Pegawai menyetujui tawaran pelaporan tiket dari konsultasi. (1a)
2. Sistem mengisi uraian masalah dari ringkasan konsultasi. (S-1)
3. Pegawai memeriksa dan melengkapi uraian tersebut. (S-1, 2)
4. Pegawai mengajukan tiket. (3)
5. Sistem memeriksa kelengkapan informasi. (4)
6. Sistem mencatat tiket dengan nomor unik dan status Baru. (5)
7. Sistem mulai menghitung batas waktu SLA, menyiapkan rekomendasi triase, dan mengirim konfirmasi kepada pegawai. (6)
8. Sistem menempatkan tiket dalam antrean validasi operator. (7)

#### SC-03.3 Pegawai melengkapi informasi tiket yang kurang

1. Pegawai memilih jenis layanan yang dibutuhkan. (1)
2. Pegawai menjelaskan masalah tanpa mengisi semua informasi. (2)
3. Pegawai mengajukan tiket. (3)
4. Sistem memeriksa kelengkapan informasi dan memberi tahu bagian yang kurang. (4a)
5. Pegawai melengkapi informasi dan mengajukan ulang. (4a)
6. Sistem memeriksa kelengkapan informasi. (4)
7. Sistem mencatat tiket dengan nomor unik dan status Baru. (5)
8. Sistem mulai menghitung batas waktu SLA, menyiapkan rekomendasi triase, dan mengirim konfirmasi kepada pegawai. (6)
9. Sistem menempatkan tiket dalam antrean validasi operator. (7)

#### SC-03.4 Pegawai membuat tiket saat rekomendasi triase tidak dapat disiapkan

1. Pegawai memilih jenis layanan yang dibutuhkan. (1)
2. Pegawai menjelaskan permintaan atau masalah dan melampirkan bukti pendukung bila ada. (2)
3. Pegawai mengajukan tiket. (3)
4. Sistem memeriksa kelengkapan informasi. (4)
5. Sistem mencatat tiket dengan nomor unik dan status Baru. (5)
6. Sistem mulai menghitung batas waktu SLA dan mengirim konfirmasi kepada pegawai. (6)
7. Sistem tidak dapat menyiapkan rekomendasi, tetapi tiket tetap tercatat untuk triase manual oleh operator. (6a)
8. Sistem menempatkan tiket dalam antrean validasi operator. (7)

#### SC-03.5 Operator mencatat laporan atas nama pegawai

1. Pegawai menyampaikan kendala kepada Operator di luar portal. (†)
2. Operator menjelaskan permasalahan pegawai pada tiket dan mencatat pemohon serta sumber laporan. (2 †)
3. Operator mengajukan tiket. (3 †)
4. Sistem memeriksa kelengkapan informasi. (4)
5. Sistem mencatat tiket dengan nomor unik dan status Baru. (5)
6. Sistem mulai menghitung batas waktu SLA, menyiapkan rekomendasi triase, dan mengirim konfirmasi kepada pegawai. (6)
7. Sistem menempatkan tiket dalam antrean validasi operator. (7)

**Ringkasan perbedaan UC-03**

| Skenario | Titik beda | Jalur Tugas 3 | Hasil akhir |
|---|---|---|---|
| SC-03.1 | Tidak ada | 1–7 | Tiket Baru dengan rekomendasi |
| SC-03.2 | Langkah 1 | 1a, S-1 | Tiket Baru berisi ringkasan konsultasi |
| SC-03.3 | Langkah 4 | 4a | Tiket Baru setelah informasi dilengkapi |
| SC-03.4 | Langkah 7 | 6a | Tiket Baru untuk triase manual |
| SC-03.5 | Langkah 1 | † | Tiket Baru dicatat Operator |

### A.3 UC-05 Memvalidasi Rekomendasi AI & Meneruskan Tiket

#### SC-05.1 Operator menyetujui rekomendasi lalu meneruskan tiket

1. Operator membuka daftar tiket yang menunggu validasi. (1)
2. Operator memilih tiket. (2)
3. Sistem menyajikan isi tiket, rekomendasi, tingkat keyakinan, alasan, dan tiket serupa. (3)
4. Operator menyetujui rekomendasi karena sudah tepat. (4)
5. Operator menilai tiket perlu ditangani tim teknis. (5)
6. Sistem menugaskan tiket kepada tim teknis tujuan. (6)
7. Sistem mencatat keputusan operator, memberi tahu tim teknis dan pegawai, serta menyimpan keputusan sebagai bahan evaluasi rekomendasi. (7)

#### SC-05.2 Operator mengoreksi rekomendasi yang kurang tepat

1. Operator membuka daftar tiket yang menunggu validasi. (1)
2. Operator memilih tiket. (2)
3. Sistem menyajikan isi tiket, rekomendasi, tingkat keyakinan, alasan, dan tiket serupa. (3)
4. Operator menilai rekomendasi kurang tepat tetapi dapat dikoreksi. (4a)
5. Operator mengoreksi kategori, prioritas, atau tim tujuan dan menuliskan alasan. (S-1)
6. Operator menilai tiket perlu ditangani tim teknis. (5)
7. Sistem menugaskan tiket kepada tim teknis tujuan. (6)
8. Sistem mencatat keputusan operator, memberi tahu tim teknis dan pegawai, serta menyimpan keputusan sebagai bahan evaluasi rekomendasi. (7)

#### SC-05.3 Operator menolak rekomendasi dan melakukan triase sendiri

1. Operator membuka daftar tiket yang menunggu validasi. (1)
2. Operator memilih tiket. (2)
3. Sistem menyajikan isi tiket, rekomendasi, tingkat keyakinan, alasan, dan tiket serupa. (3)
4. Operator menilai rekomendasi tidak dapat digunakan. (4b)
5. Operator menentukan triase sendiri dan menuliskan alasan. (S-2)
6. Operator menilai tiket perlu ditangani tim teknis. (5)
7. Sistem menugaskan tiket kepada tim teknis tujuan. (6)
8. Sistem mencatat keputusan operator, memberi tahu tim teknis dan pegawai, serta menyimpan keputusan sebagai bahan evaluasi rekomendasi. (7)

#### SC-05.4 Operator menyelesaikan tiket di level 1

1. Operator membuka daftar tiket yang menunggu validasi. (1)
2. Operator memilih tiket. (2)
3. Sistem menyajikan isi tiket, rekomendasi, tingkat keyakinan, alasan, dan tiket serupa. (3)
4. Operator menyetujui rekomendasi karena sudah tepat. (4)
5. Operator menilai tiket dapat diselesaikan sendiri dan memberikan solusi kepada pegawai. (5a)
6. Sistem mengubah status tiket menjadi terselesaikan. (5a)
7. Sistem mencatat keputusan operator, memberi tahu pegawai, serta menyimpan keputusan sebagai bahan evaluasi rekomendasi. (7)

#### SC-05.5 Operator menangani rekomendasi berkeyakinan rendah

1. Operator membuka daftar tiket yang menunggu validasi. (1)
2. Operator memilih tiket. (2)
3. Sistem menyajikan isi tiket dan rekomendasi yang ditandai perlu penilaian manual. (3; UC-04 6a)
4. Operator menilai rekomendasi tidak dapat digunakan. (4b)
5. Operator menentukan triase sendiri dan menuliskan alasan. (S-2)
6. Operator menilai tiket perlu ditangani tim teknis. (5)
7. Sistem menugaskan tiket kepada tim teknis tujuan. (6)
8. Sistem mencatat keputusan operator, memberi tahu tim teknis dan pegawai, serta menyimpan keputusan sebagai bahan evaluasi rekomendasi. (7)

#### SC-05.6 Operator menangani tiket tanpa rekomendasi

1. Operator membuka daftar tiket yang menunggu validasi. (1)
2. Operator memilih tiket. (2)
3. Sistem menyajikan isi tiket tanpa rekomendasi karena rekomendasi tidak dapat dibuat. (3; UC-04 1a)
4. Operator menentukan triase sendiri. (S-2)
5. Operator menilai tiket perlu ditangani tim teknis. (5)
6. Sistem menugaskan tiket kepada tim teknis tujuan. (6)
7. Sistem memberi tahu tim teknis dan pegawai. (7)

**Ringkasan perbedaan UC-05**

| Skenario | Titik beda | Jalur Tugas 3 | Hasil akhir |
|---|---|---|---|
| SC-05.1 | Tidak ada | 1–7 | Tiket ditugaskan sesuai rekomendasi |
| SC-05.2 | Langkah 4 | 4a, S-1 | Tiket ditugaskan dengan koreksi |
| SC-05.3 | Langkah 4 | 4b, S-2 | Tiket ditugaskan lewat triase sendiri |
| SC-05.4 | Langkah 5 | 5a | Tiket selesai di level 1 |
| SC-05.5 | Langkah 3 | UC-04 6a, 4b, S-2 | Tiket ditugaskan lewat triase sendiri |
| SC-05.6 | Langkah 3 | UC-04 1a, S-2 | Tiket ditugaskan tanpa rekomendasi |

### A.4 UC-06 Menangani & Menyelesaikan Tiket

#### SC-06.1 Tim Teknis menyelesaikan tiket yang ditugaskan

1. Tim Teknis membuka pemberitahuan tiket yang ditugaskan. (1)
2. Tim Teknis memeriksa tiket dan memastikan penugasannya sesuai. (2)
3. Tim Teknis mengambil tiket sehingga statusnya menjadi sedang ditangani. (3)
4. Sistem menyajikan referensi solusi dan tiket serupa. (4)
5. Tim Teknis menangani masalah. (5)
6. Tim Teknis mencatat penyelesaian dan menyatakan tiket selesai. (6)
7. Sistem memberi tahu pegawai, mencatat waktu penyelesaian terhadap SLA, dan menandai solusi sebagai calon knowledge. (7)

#### SC-06.2 Tim Teknis meminta informasi tambahan dari pegawai

1. Tim Teknis membuka pemberitahuan tiket yang ditugaskan. (1)
2. Tim Teknis memeriksa tiket dan memastikan penugasannya sesuai. (2)
3. Tim Teknis mengambil tiket sehingga statusnya menjadi sedang ditangani. (3)
4. Sistem menyajikan referensi solusi dan tiket serupa. (4)
5. Tim Teknis menilai informasi dari pegawai belum cukup dan mengajukan pertanyaan. (5a; S-1)
6. Sistem mengubah status tiket menjadi tertunda dan menjeda penghitungan SLA sesuai kebijakan. (S-1)
7. Pegawai memberikan informasi yang diminta. (S-1)
8. Tim Teknis melanjutkan penanganan masalah. (S-1, 5)
9. Tim Teknis mencatat penyelesaian dan menyatakan tiket selesai. (6)
10. Sistem memberi tahu pegawai, mencatat waktu penyelesaian terhadap SLA, dan menandai solusi sebagai calon knowledge. (7)

#### SC-06.3 Tim Teknis mengembalikan tiket yang salah penugasan

1. Tim Teknis membuka pemberitahuan tiket yang ditugaskan. (1)
2. Tim Teknis memeriksa tiket dan menilai penugasan tidak sesuai. (2a)
3. Tim Teknis mengembalikan tiket kepada operator beserta alasannya. (2a)
4. Sistem mencatat koreksi penugasan sebagai bahan evaluasi rekomendasi. (2a)

**Ringkasan perbedaan UC-06**

| Skenario | Titik beda | Jalur Tugas 3 | Hasil akhir |
|---|---|---|---|
| SC-06.1 | Tidak ada | 1–7 | Tiket terselesaikan |
| SC-06.2 | Langkah 5 | 5a, S-1 | Tiket terselesaikan setelah jeda |
| SC-06.3 | Langkah 2 | 2a | Tiket kembali ke Operator |

### A.5 UC-07 Memantau Status & Mengonfirmasi Penyelesaian

#### SC-07.1 Pegawai mengonfirmasi penyelesaian tiket

1. Pegawai melihat daftar tiket miliknya. (1)
2. Sistem menyajikan status, riwayat, dan sisa waktu SLA setiap tiket. (2)
3. Pegawai memilih tiket yang sudah diselesaikan. (3)
4. Pegawai memeriksa solusi yang diberikan. (4)
5. Pegawai mengonfirmasi masalah telah selesai dan memberi penilaian. (5)
6. Sistem menutup tiket. (6)
7. Sistem mencatat riwayat dan memberi tahu petugas terkait. (7)

#### SC-07.2 Pegawai menolak penutupan karena masalah belum selesai

1. Pegawai melihat daftar tiket miliknya. (1)
2. Sistem menyajikan status, riwayat, dan sisa waktu SLA setiap tiket. (2)
3. Pegawai memilih tiket yang sudah diselesaikan. (3)
4. Pegawai memeriksa solusi yang diberikan. (4)
5. Pegawai menolak penutupan dan menuliskan alasan. (5a)
6. Sistem membuka kembali tiket. (5a)
7. Sistem mencatat riwayat dan memberi tahu petugas terkait. (7)

#### SC-07.3 Pegawai menambahkan keterangan pada tiket yang masih berjalan

1. Pegawai melihat daftar tiket miliknya. (1)
2. Sistem menyajikan status, riwayat, dan sisa waktu SLA setiap tiket. (2)
3. Pegawai memilih tiket yang belum diselesaikan. (3a)
4. Pegawai menambahkan keterangan. (3a)
5. Sistem meneruskan keterangan kepada petugas yang menangani. (3a)

#### SC-07.4 Operator menutup tiket karena pegawai tidak merespons

1. Sistem mendapati tiket yang sudah diselesaikan tidak mendapat respons pegawai melewati batas waktu. (†)
2. Sistem memasukkan tiket ke daftar tiket yang siap ditutup. (†)
3. Operator memeriksa tiket tersebut. (†)
4. Operator menutup tiket. (†)
5. Sistem menutup tiket. (6)
6. Sistem mencatat riwayat dan memberi tahu petugas terkait. (7)

**Ringkasan perbedaan UC-07**

| Skenario | Titik beda | Jalur Tugas 3 | Hasil akhir |
|---|---|---|---|
| SC-07.1 | Tidak ada | 1–7 | Tiket ditutup dengan penilaian |
| SC-07.2 | Langkah 5 | 5a | Tiket dibuka kembali |
| SC-07.3 | Langkah 3 | 3a | Keterangan diteruskan |
| SC-07.4 | Langkah 1 | †, 6, 7 | Tiket ditutup oleh Operator |

### A.6 UC-09 Mengelola Knowledge Base

#### SC-09.1 Knowledge Manager menerbitkan calon knowledge

1. Knowledge Manager membuka daftar calon knowledge dan artikel yang perlu ditinjau. (1)
2. Sistem menyajikan calon knowledge dari tiket yang telah diselesaikan dan artikel yang jatuh tempo ditinjau. (2)
3. Knowledge Manager meninjau calon knowledge dari catatan penyelesaian tiket. (3)
4. Knowledge Manager menyunting isi, kategori, dan kata kunci artikel. (4)
5. Knowledge Manager menyetujui artikel untuk diterbitkan. (5)
6. Sistem menerbitkan artikel sebagai versi baru dan menjadikannya dapat ditemukan dalam pencarian solusi. (6)
7. Sistem mencatat perubahan artikel. (7)

#### SC-09.2 Knowledge Manager menyimpan artikel sebagai draf

1. Knowledge Manager membuka daftar calon knowledge dan artikel yang perlu ditinjau. (1)
2. Sistem menyajikan calon knowledge dari tiket yang telah diselesaikan dan artikel yang jatuh tempo ditinjau. (2)
3. Knowledge Manager meninjau calon knowledge dari catatan penyelesaian tiket. (3)
4. Knowledge Manager menyunting isi, kategori, dan kata kunci artikel. (4)
5. Knowledge Manager menilai artikel belum layak terbit. (5a)
6. Sistem menyimpan artikel sebagai draf. (5a)
7. Sistem mencatat perubahan artikel. (7)

#### SC-09.3 Knowledge Manager memperbarui artikel yang jatuh tempo ditinjau

1. Knowledge Manager membuka daftar calon knowledge dan artikel yang perlu ditinjau. (1)
2. Sistem menyajikan calon knowledge dari tiket yang telah diselesaikan dan artikel yang jatuh tempo ditinjau. (2)
3. Knowledge Manager mendapati tidak ada calon knowledge dan memilih artikel yang sudah ada. (3a; S-1)
4. Knowledge Manager memperbarui isi artikel. (S-1, 4)
5. Knowledge Manager menyetujui artikel untuk diterbitkan. (5)
6. Sistem menerbitkan artikel sebagai versi baru dan menjadikannya dapat ditemukan dalam pencarian solusi. (6)
7. Sistem mencatat perubahan artikel. (7)

#### SC-09.4 Knowledge Manager menulis artikel baru

1. Knowledge Manager membuka daftar calon knowledge dan artikel yang perlu ditinjau. (1)
2. Sistem menyajikan calon knowledge dari tiket yang telah diselesaikan dan artikel yang jatuh tempo ditinjau. (2)
3. Knowledge Manager mendapati tidak ada calon knowledge dan artikel belum ada, lalu menulis artikel baru. (3b; S-2)
4. Knowledge Manager melengkapi isi, kategori, dan kata kunci artikel. (4)
5. Knowledge Manager menyetujui artikel untuk diterbitkan. (5)
6. Sistem menerbitkan artikel sebagai versi baru dan menjadikannya dapat ditemukan dalam pencarian solusi. (6)
7. Sistem mencatat perubahan artikel. (7)

#### SC-09.5 Knowledge Manager menolak calon yang tidak layak

1. Knowledge Manager membuka daftar calon knowledge dan artikel yang perlu ditinjau. (1)
2. Sistem menyajikan calon knowledge dari tiket yang telah diselesaikan dan artikel yang jatuh tempo ditinjau. (2)
3. Knowledge Manager meninjau calon knowledge dari catatan penyelesaian tiket. (3)
4. Knowledge Manager menilai calon tidak layak dan menuliskan catatan. (5a)
5. Sistem menandai calon sebagai ditolak. (5a)
6. Sistem mencatat perubahan artikel. (7)

#### SC-09.6 Knowledge Manager mengarsipkan artikel usang

1. Knowledge Manager membuka daftar calon knowledge dan artikel yang perlu ditinjau. (1)
2. Sistem menyajikan calon knowledge dari tiket yang telah diselesaikan dan artikel yang jatuh tempo ditinjau. (2)
3. Knowledge Manager mendapati tidak ada calon knowledge dan memilih artikel yang sudah ada. (3a; S-1)
4. Knowledge Manager mengarsipkan artikel. (S-1)
5. Sistem mencatat perubahan artikel. (7)

**Ringkasan perbedaan UC-09**

| Skenario | Titik beda | Jalur Tugas 3 | Hasil akhir |
|---|---|---|---|
| SC-09.1 | Tidak ada | 1–7 | Artikel terbit |
| SC-09.2 | Langkah 5 | 5a | Artikel menjadi draf |
| SC-09.3 | Langkah 3 | 3a, S-1 | Artikel diperbarui |
| SC-09.4 | Langkah 3 | 3b, S-2 | Artikel baru terbit |
| SC-09.5 | Langkah 4 | 5a | Calon ditolak |
| SC-09.6 | Langkah 4 | 3a, S-1 | Artikel diarsipkan |

---

## B. Real Use Case

### B.0 Konvensi

- Alur ditulis dalam bahasa antarmuka. Label dalam **huruf tebal** mengikuti tampilan saat ini.
- Nomor alur alternatif mengikuti nomor langkah Real pada use case yang sama, bukan nomor Tugas 3 versi AKPSI-6.
- Nama kelas, tabel, dan endpoint hanya muncul pada baris **Implementasi**.
- Sebagian kecil teks bawaan GLPI yang belum diterjemahkan ditulis apa adanya.

| Aspek | Keterangan |
|---|---|
| Platform | GLPI 12, plugin `halosis` (PHP), layanan `halosis-ai` (FastAPI) |
| Autentikasi | Keycloak untuk SSO; sesi dan hak akses dikelola GLPI |
| Hak plugin | `plugin_halosis_chatbot`, `_triase`, `_kandidat`, `_dashboard`, `_config` |
| Pola aksi | `public/js/*.js` memanggil `plugins/halosis/ajax/*.php`; balasan berupa JSON |
| Aturan tulis | Nilai AI masuk ke tiket lewat `Ticket::update()` setelah keputusan petugas |
| Privasi | Teks disamarkan oleh `Privacy::mask()` sebelum disimpan atau dikirim ke AI |

### B.1 UC-01 Berkonsultasi melalui AI Chatbot

| Atribut | Isi |
|---|---|
| Use-Case Name | Berkonsultasi melalui AI Chatbot |
| ID | UC-01 |
| Importance Level | Tinggi |
| Primary Actor | Pegawai BPS (Requester) |
| Secondary Actor | AI Engine |
| Use-Case Type | Detail, Real |
| Stakeholders and Interests | **Pegawai BPS:** ingin solusi cepat tanpa harus membuat tiket untuk masalah umum.<br>**Operator HaloSIS:** ingin volume tiket berulang berkurang.<br>**Knowledge Manager:** ingin knowledge yang dikurasi benar-benar dipakai dan dinilai kegunaannya. |
| Brief Description | Pegawai bertanya kepada asisten di halaman **Tanya HaloSIS** dan menerima jawaban dari panduan resmi BPS. Bila masalah belum selesai, pegawai dapat melanjutkan ke pembuatan laporan. |
| Trigger | Pegawai mengalami kendala layanan TI dan ingin mencari solusi secara mandiri. |
| Type | External |
| Relationships | **Association:** Pegawai BPS<br>**Include:** UC-02 Mencari Knowledge Relevan<br>**Extend:** base use case bagi UC-03 Membuat Tiket<br>**Generalization:** – |
| Pre-kondisi | Pegawai terdaftar dan memiliki hak asisten; fitur chat aktif; knowledge base berisi artikel terbit. |
| Post-kondisi | Percakapan tersimpan. Masalah selesai secara mandiri, atau pegawai diarahkan ke pembuatan laporan. |
| Halaman | **Tanya HaloSIS**, widget **Tanya asisten**, **Riwayat percakapan** |
| Keterkaitan | FR-01, FR-02, FR-03; NFR-06, NFR-08, NFR-12; BR-04, BR-06 |

**Normal Flow of Events**

1. Pegawai masuk lewat SSO BPS dan sistem membuka halaman **Tanya HaloSIS**.
2. Sistem menampilkan sapaan "Halo …! Apa yang Anda butuhkan hari ini?", kartu **Ajukan permintaan** dan **Laporkan masalah**, serta contoh di bawah **Coba tanyakan:**.
3. Pegawai mengetik kendala di kotak **Tulis kendala Anda…** atau memilih salah satu contoh, lalu mengklik ikon **Kirim** atau menekan Enter.
4. Sistem mencatat percakapan, menyamarkan data pribadi, dan mencari jawaban (include UC-02).
5. Sistem menampilkan jawaban berlabel **Dijawab oleh AI** beserta tautan sumber, disusul "Apakah jawaban ini membantu?" dengan tombol **Masalah terselesaikan** dan **Belum terselesaikan**.
6. Pegawai mencoba solusi tersebut.
7. Pegawai mengklik **Masalah terselesaikan**.
8. Sistem menampilkan "Seberapa membantu asisten ini?" dengan bintang 1–5, lalu pegawai memilih satu bintang.
9. Sistem menampilkan "Terima kasih! Kami senang masalah Anda sudah terselesaikan." dan mengakhiri percakapan.

**Subflows:** –

**Alternate/Exceptional Flows**

- **1a. Fitur chat dimatikan.** Halaman menampilkan **Asisten Sedang Tidak Tersedia**, "Laporkan kendala Anda dan petugas akan membantu.", tombol **Buat laporan**, dan tautan **Tanya Jawab (FAQ)**.
- **1b. Pegawai tanpa hak asisten.** Sistem menampilkan "Asisten tidak tersedia untuk akun Anda."
- **3a. Pesan kosong.** Sistem menampilkan "Silakan ketik pertanyaan."
- **3b. Percakapan sudah terlalu panjang.** Sistem menampilkan "Percakapan terlalu panjang. Buat laporan atau mulai percakapan baru."
- **3c. Percakapan sudah berakhir.** Sistem menampilkan "Percakapan ini sudah selesai. Mulai percakapan baru untuk bertanya lagi."
- **4a. Layanan AI gagal menjawab.** Sistem mencari dengan kata kunci di artikel, lalu menampilkan jawaban berlabel **Dari Pusat Bantuan**. Bila kosong, alur lanjut ke 5a.
- **4b. Permintaan ke server gagal.** Sistem menampilkan "Asisten sedang tidak tersedia. Anda tetap dapat membuat laporan." beserta kartu laporan.
- **5a. Solusi tidak ditemukan.** Sistem menampilkan "Maaf, saya belum menemukan jawabannya di Pusat Bantuan…" dan kartu "Saya belum menemukan jawabannya. Apakah Anda ingin saya buatkan laporan…" dengan tombol **Ya, buat laporan** dan **Tidak, terima kasih**. **Ya, buat laporan** melanjutkan ke UC-03 S-1. **Tidak, terima kasih** hanya menutup kartu, dan pegawai tetap dapat bertanya lagi.
- **5b. Keyakinan jawaban sedang.** Sistem menampilkan "Apakah yang Anda maksud salah satu artikel berikut?…" dengan tautan artikel.
- **5c. Pertanyaan di luar layanan TI.** Sistem mengarahkan pegawai ke unit terkait tanpa tawaran laporan.
- **7a. Pegawai mengklik Belum terselesaikan.** Sistem menampilkan kartu "Masalah belum selesai? Saya akan membuatkan laporan…" dengan tombol **Ya, buat laporan** dan **Tidak, terima kasih**. **Ya, buat laporan** melanjutkan ke UC-03 S-1.
- **7b. Pada kartu alur 7a, pegawai mengklik Tidak, terima kasih.** Tiket tidak dibuat. Sistem menampilkan "Percakapan diakhiri. Anda dapat membacanya lagi di Riwayat percakapan." dan menutup kotak ketik. **Riwayat percakapan** menandainya **Berakhir tanpa laporan**.

**Implementasi.** `ChatController`, `Chatbot::ask()`, `Chatbot::resolve()`, `Chatbot::decline()`, `Chat`, `Privacy`, `KnowledgeSearch`, `Ai\Service`; `ajax/chat.php`; `public/js/chat.js`; tabel `glpi_plugin_halosis_chats`, `glpi_plugin_halosis_article_uses`.

### B.2 UC-02 Mencari Knowledge Relevan

| Atribut | Isi |
|---|---|
| Use-Case Name | Mencari Knowledge Relevan |
| ID | UC-02 |
| Importance Level | Tinggi |
| Primary Actor | AI Engine |
| Use-Case Type | Detail, Real |
| Stakeholders and Interests | **Pegawai BPS:** ingin jawaban relevan dan dapat ditelusuri sumbernya.<br>**Operator dan Tim Teknis:** ingin referensi solusi tanpa pencarian manual.<br>**Security/Tata Kelola:** ingin data pribadi terlindungi dan setiap pencarian tercatat. |
| Brief Description | AI Engine mencari sumber yang paling relevan berdasarkan makna, lalu mengembalikan hasil beserta skor dan sumber. Jawaban untuk pegawai hanya bersumber dari artikel KB terbit dan katalog layanan; tiket lama hanya dipakai untuk pencarian petugas. |
| Trigger | Pegawai, Operator, atau Tim Teknis membutuhkan referensi solusi. Dipanggil dari **Tanya HaloSIS** (UC-01) atau **Cari Pengetahuan**. |
| Type | External |
| Relationships | **Association:** AI Engine<br>**Include:** –<br>**Extend:** –<br>**Generalization:** – |
| Pre-kondisi | Artikel terbit, katalog layanan, dan tiket historis sudah diindeks; permintaan berasal dari pengguna atau proses yang terautentikasi. |
| Post-kondisi | Hasil, skor, dan sumber dikembalikan ke pemanggil; waktu proses tercatat. |
| Halaman | **Tanya HaloSIS**, **Cari Pengetahuan** |
| Keterkaitan | FR-03; NFR-06, NFR-07, NFR-09, NFR-12; BR-03, BR-04, BR-08 |

**Normal Flow of Events**

1. Pegawai mengirim pertanyaan dari halaman **Tanya HaloSIS** dan sistem meneruskannya ke AI Engine.
2. AI Engine menyamarkan data pribadi sekali lagi.
3. AI Engine mengubah pertanyaan menjadi vektor dan membandingkannya dengan indeks artikel KB terbit dan katalog layanan. Tiket lama tidak dipakai untuk jawaban pegawai.
4. AI Engine memberi skor pada setiap potongan dan mengurutkan hasil.
5. AI Engine mengambil hasil yang memenuhi ambang dan menyusun jawaban beserta sumber.
6. AI Engine mencatat waktu proses dan mengembalikan hasil ke halaman **Tanya HaloSIS**.

**Subflows**

- **S-1 Pencarian oleh petugas.** Operator atau Tim Teknis membuka **Cari pengetahuan**, mengetik uraian di kotak "Jelaskan masalahnya, misalnya FASIH tidak dapat sinkronisasi", dan mengklik **Cari**. Pencarian petugas juga mencakup tiket lama. Sistem menampilkan semua hasil dengan lencana **Artikel**, **Katalog layanan**, atau **Tiket serupa …**, nilai **Relevansi x%**, serta pertanyaan "Apakah ini membantu?" dengan tombol **Membantu** dan **Tidak membantu**.

**Alternate/Exceptional Flows**

- **3a. Indeks belum tersedia atau layanan mati.** AI Engine mengembalikan status gagal dan pemanggil beralih ke pencarian kata kunci. Halaman **Cari Pengetahuan** menampilkan "Layanan AI HaloSIS tidak dapat dihubungi: hanya menampilkan hasil kata kunci…".
- **5a. Tidak ada hasil yang memenuhi ambang.** AI Engine mengembalikan status tidak ditemukan, atau sampai tiga artikel bila skornya berada di zona sedang. Pencarian tetap dicatat.
- **S-1a. Hasil pencarian kosong.** Halaman **Cari Pengetahuan** menampilkan "Pengetahuan tidak ditemukan. Silakan coba kata lain."
- **S-1b. Petugas memberi umpan balik.** Setelah tombol **Membantu** atau **Tidak membantu** diklik, sistem menampilkan "Terima kasih, umpan balik Anda tersimpan." Teks pertanyaan tidak disimpan.

**Implementasi.** `ai/service/app.py` (`POST /chat`, `POST /cari`), `ai/halosis_ai/search.py` (model `intfloat/multilingual-e5-base`), `ai/halosis_ai/privacy.py`; `CariKnowledgeController`; `ajax/feedback.php`; tabel `glpi_plugin_halosis_feedback`.

### B.3 UC-03 Membuat Tiket

| Atribut | Isi |
|---|---|
| Use-Case Name | Membuat Tiket |
| ID | UC-03 |
| Importance Level | Tinggi |
| Primary Actor | Pegawai BPS (Requester) |
| Secondary Actor | AI Engine; Operator HaloSIS pada alur 1b |
| Use-Case Type | Detail, Real |
| Stakeholders and Interests | **Pegawai BPS:** ingin tiket tercatat dengan mudah tanpa mengulang penjelasan.<br>**Operator HaloSIS:** ingin tiket masuk dengan informasi lengkap dan rekomendasi awal.<br>**Manajemen:** ingin SLA terhitung sejak tiket dibuat. |
| Brief Description | Pegawai melaporkan masalah atau permintaan layanan melalui **Katalog layanan** atau kartu laporan di **Tanya HaloSIS**. Saat tiket tersimpan, sistem memulai SLA dan meminta saran triase. |
| Trigger | Pegawai ingin melaporkan permintaan atau masalah layanan TI lewat **Buat laporan**, atau menyetujui tawaran **Ya, buat laporan** dari asisten. |
| Type | External |
| Relationships | **Association:** Pegawai BPS<br>**Include:** UC-04 Menghasilkan Rekomendasi Triase & Routing<br>**Extend:** meng-extend UC-01 pada extension point [solusi tidak ditemukan]<br>**Generalization:** – |
| Pre-kondisi | Pegawai sudah masuk lewat SSO dan berhak membuat tiket; katalog layanan sudah dikonfigurasi (UC-10). |
| Post-kondisi | Tiket berstatus **Baru** dengan nomor unik; SLA berjalan; saran AI tersimpan, atau tiket menunggu triase manual. |
| Halaman | **Buat laporan** (**Katalog layanan**), **Laporkan Masalah**, **Ajukan Permintaan**, kartu laporan di **Tanya HaloSIS**, **Semua tiket** untuk Operator |
| Keterkaitan | FR-06, FR-09; NFR-03, NFR-13; BR-01, BR-02, BR-05, BR-06 |

**Normal Flow of Events**

1. Pegawai mengklik menu **Buat laporan** dan sistem menampilkan **Katalog layanan**.
2. Pegawai memilih **Laporkan Masalah** untuk masalah, atau **Ajukan Permintaan** untuk permintaan layanan.
3. Pegawai mengisi **Judul** dan **Deskripsi** yang wajib, memilih **Kategori** dan **Urgensi**, lalu menambahkan **Lampiran** bila ada.
4. Pegawai mengklik **Kirim**.
5. Sistem memeriksa kolom wajib, membuat tiket berstatus **Baru** dengan nomor unik, dan membuka halaman tiket tersebut.
6. Sistem memasang SLA, mengirim notifikasi konfirmasi ke pegawai, dan membuat saran triase (include UC-04).
7. Tiket muncul di menu **Antrean validasi** Operator, diurutkan menurut **Waktu untuk menyelesaikan**.

**Subflows**

- **S-1 Tiket dari konsultasi.** Pegawai mengklik **Ya, buat laporan**. Sistem menampilkan **Judul laporan** yang sudah terisi dari pertanyaan terakhir dan blok **Ringkasan yang dilampirkan**. Pegawai menyunting judul bila perlu lalu mengklik **Kirim laporan**, atau mengklik **Batal**. Sistem menampilkan "Laporan #… sudah dibuat. Petugas akan segera menindaklanjutinya." dan tombol **Buka laporan**. Alur lanjut ke langkah 6.

**Alternate/Exceptional Flows**

- **1a. Tiket berasal dari UC-01.** Jalankan S-1.
- **1b. Operator mencatat laporan telepon, email, atau tatap muka.** Operator membuka **Semua tiket**, mengklik **Tambah**, mengisi **Pemohon**, **Sumber permintaan** (**Phone**, **E-Mail**, atau **Direct**), **Judul**, dan **Deskripsi**, lalu mengklik **Tambah**. Alur lanjut ke langkah 6.
- **5a. Kolom wajib kosong.** Form menandai **Judul** atau **Deskripsi** dan tiket tidak dibuat. Pegawai melengkapi isian dan mengklik **Kirim** lagi. Pada S-1, judul pendek menghasilkan pesan "Judul laporan minimal 5 karakter."
- **5b. Pegawai tanpa hak membuat tiket.** Pada S-1 sistem menampilkan "Anda tidak berhak membuat tiket."
- **6a. Saran triase tidak dapat dibuat.** Tiket tetap tersimpan tanpa saran. Sistem mencoba lagi secara berkala, dan panel menampilkan "Belum ada saran AI untuk tiket ini." dengan tombol **Buat saran AI** (lihat UC-05 alur 3b).

**Implementasi.** Form katalog GLPI, `FormCatalog::localize()`; `ajax/chat.php` (`action=ticket`), `Chatbot::createTicket()`, `Triage::onTicketAdd()`, `TriageRetry`; aturan `RuleTicket` untuk SLA; tabel `glpi_tickets`, `glpi_plugin_halosis_chats`.

### B.4 UC-04 Menghasilkan Rekomendasi Triase & Routing

| Atribut | Isi |
|---|---|
| Use-Case Name | Menghasilkan Rekomendasi Triase & Routing |
| ID | UC-04 |
| Importance Level | Tinggi |
| Primary Actor | AI Engine |
| Use-Case Type | Detail, Real |
| Stakeholders and Interests | **Operator HaloSIS:** ingin waktu triase lebih singkat dan saran yang dapat dipercaya.<br>**Tim Teknis:** ingin salah penugasan berkurang.<br>**Security/Tata Kelola:** ingin setiap saran tercatat dan dapat diaudit. |
| Brief Description | Sistem menghasilkan saran kategori, dampak, urgensi, prioritas, dan tim, lengkap dengan keyakinan dan penjelasan. Saran tidak dijalankan otomatis dan menunggu keputusan Operator. |
| Trigger | Tiket baru tercatat (di-include oleh UC-03). |
| Type | External |
| Relationships | **Association:** AI Engine<br>**Include:** UC-02 Mencari Knowledge Relevan pada Tugas 3; aplikasi memakai pencarian tiket serupa milik model triase<br>**Extend:** –<br>**Generalization:** – |
| Pre-kondisi | Tiket baru tersimpan; fitur triase aktif; model lolos uji kualitas. |
| Post-kondisi | Satu saran berstatus **Menunggu keputusan** tersimpan untuk tiket, atau tiket tetap tanpa saran. |
| Halaman | Panel **Saran AI** pada detail tiket |
| Keterkaitan | FR-04, FR-08; NFR-07, NFR-11, NFR-12, NFR-14; BR-04, BR-05, BR-08 |

**Normal Flow of Events**

1. Sistem mengirim judul, deskripsi, dan jenis tiket baru ke AI Engine.
2. AI Engine memprediksi tiga tim teratas beserta keyakinan, mencari tiket lama yang mirip, dan menyusun penjelasan.
3. Sistem memetakan tim teratas ke **Grup** dan **Kategori**. Bila selisih dua kandidat teratas kurang dari 5 poin, sistem memilih tim dengan tiket aktif lebih sedikit.
4. Sistem menentukan **Urgensi** dari aturan kata kunci dan **Dampak** dari urgensi ditambah sinyal (tiket serupa atau layanan kritis), lalu menghitung **Prioritas**. Model urgensi tidak dipakai karena belum lolos uji kualitas; Operator memvalidasi nilainya.
5. Sistem mendapati **Keyakinan** mencapai ambang, sehingga saran diberi tanda **Disarankan · keyakinan mencapai ambang**.
6. Sistem menyimpan saran dan menampilkan panel **Saran AI** berlabel **Menunggu keputusan** di detail tiket.

**Subflows:** –

**Alternate/Exceptional Flows**

- **1a. Layanan AI tidak tersedia.** Sistem mencatat kegagalan di log. Bila penyedia AI eksternal dikonfigurasi, sistem mencobanya. Bila tetap gagal, tiket tetap tanpa saran dan dicoba lagi setiap 15 menit sampai lima kali, selama tiket berumur maksimal tiga hari.
- **1b. Layanan AI belum dikonfigurasi dan mode demo aktif.** Sistem membuat saran dari aturan kata kunci.
- **5a. Keyakinan berada di antara dua ambang.** Saran diberi tanda **Pilih dari 3 kandidat · periksa tiga tim teratas di penjelasan sebelum memutuskan**.
- **5b. Keyakinan di bawah ambang rendah.** Saran diberi tanda **Perlu penilaian manual · keyakinan di bawah ambang**.
- **5c. Model belum lolos uji kualitas, atau tim teratas adalah kelas Lainnya.** Saran diberi tanda **Perlu penilaian manual**. Pada model yang belum lolos, panel juga menampilkan "Model belum lolos uji kualitas · lakukan triase manual; saran hanya sebagai rujukan".

**Implementasi.** `Triage::generate()`, `Triage::suggestService()`, `Triage::applyImpactSignals()`, `Suggestion`, `TriageRetry`; `POST /triage`; `ai/halosis_ai/triage_model.py`; `templates/triase_panel.html.twig`; tabel `glpi_plugin_halosis_suggestions`, `glpi_plugin_halosis_triage_retries`.

### B.5 UC-05 Memvalidasi Rekomendasi AI & Meneruskan Tiket

| Atribut | Isi |
|---|---|
| Use-Case Name | Memvalidasi Rekomendasi AI & Meneruskan Tiket |
| ID | UC-05 |
| Importance Level | Tinggi |
| Primary Actor | Operator HaloSIS |
| Secondary Actor | Tim Teknis, Pegawai BPS (penerima notifikasi) |
| Use-Case Type | Detail, Real |
| Stakeholders and Interests | **Operator HaloSIS:** tetap menjadi pengambil keputusan akhir atas triase.<br>**Tim Teknis:** menerima tiket yang tepat sasaran.<br>**Security/Tata Kelola:** membutuhkan jejak keputusan beserta alasan koreksinya. |
| Brief Description | Operator meninjau panel **Saran AI**, lalu memilih **Terima**, **Ubah**, atau **Tolak**. Operator kemudian menyelesaikan tiket sendiri atau meneruskannya ke tim teknis. |
| Trigger | Tiket baru beserta rekomendasinya masuk ke **Antrean validasi**. |
| Type | External |
| Relationships | **Association:** Operator HaloSIS<br>**Include:** –<br>**Extend:** –<br>**Generalization:** Operator HaloSIS merupakan spesialisasi dari aktor Petugas Layanan TI |
| Pre-kondisi | Operator sudah masuk dan berhak memutuskan saran; ada tiket **Baru** dengan saran **Menunggu keputusan**. |
| Post-kondisi | Triase final diterapkan dan tiket berstatus **Sedang proses (ditugaskan)** atau **Dipecahkan**; keputusan tercatat. |
| Halaman | **Antrean validasi**, detail tiket dengan panel **Saran AI** |
| Keterkaitan | FR-05, FR-07; NFR-05, NFR-07, NFR-14; BR-05, BR-08 |

**Normal Flow of Events**

1. Operator mengklik menu **Antrean validasi**.
2. Sistem menampilkan tiket berstatus **Baru**, diurutkan menurut **Waktu untuk menyelesaikan**.
3. Operator mengklik satu tiket.
4. Sistem menampilkan detail tiket dan panel **Saran AI**: **Keyakinan**, **Kategori**, **Dampak**, **Urgensi**, **Prioritas**, **Grup**, **Tiket aktif per kandidat tim**, penjelasan beserta tiket lama yang mirip, dan **Model**.
5. Operator menilai saran sudah tepat dan mengklik **Terima**.
6. Sistem menerapkan nilai saran ke tiket, menugaskan **Grup** tujuan, dan menampilkan "Saran AI diterima dan diterapkan ke tiket."
7. Sistem mengubah status tiket menjadi **Sedang proses (ditugaskan)**, mengirim notifikasi ke tim dan pemohon, serta mencatat keputusan di **Riwayat** tiket.

**Subflows**

- **S-1 Ubah.** Operator mengklik **Ubah**, mengoreksi **Kategori**, **Dampak**, **Urgensi**, **Prioritas**, atau **Grup**, mengisi **Alasan (wajib)** pada kolom "Mengapa saran ini diubah?", lalu mengklik **Terapkan perubahan**. Sistem menampilkan "Nilai yang diubah diterapkan ke tiket." Alur lanjut ke langkah 7.
- **S-2 Tolak.** Operator mengklik **Tolak**, mengisi alasan pada kolom "Mengapa saran ini salah?", lalu mengklik **Tolak & triase manual**. Sistem menampilkan "Saran AI ditolak. Silakan triase tiket secara manual." Isian tiket tidak berubah. Operator mengisi field tiket dan **Grup** secara manual, lalu mengklik **Simpan**.

**Alternate/Exceptional Flows**

- **3a. Operator tanpa hak memutuskan.** Tombol keputusan tidak tampil dan panel menampilkan "Menunggu keputusan Operator."
- **3b. Tiket belum memiliki saran.** Panel menampilkan "Belum ada saran AI untuk tiket ini." Operator mengklik **Buat saran AI**. Bila berhasil, sistem menampilkan "Saran AI dibuat." Bila gagal, sistem menampilkan "AI belum dapat memberikan saran. Tiket tidak berubah; periksa files/_log/halosis.log." dan Operator melakukan triase manual.
- **5a. Saran kurang tepat tetapi dapat dikoreksi.** Jalankan S-1.
- **5b. Saran tidak dapat digunakan.** Jalankan S-2.
- **5c. Tiket dapat diselesaikan di level 1.** Setelah keputusan saran, Operator mengklik **Balas ▾**, memilih **Tambah solusi**, menulis solusi, dan menyimpan. Sistem mengubah status menjadi **Dipecahkan** dan memberi tahu pemohon.
- **5d. Saran sudah diputuskan.** Sistem menampilkan "Saran ini sudah diputuskan."
- **S-1a. Nilai sama dengan saran.** Sistem menampilkan "Nilainya sama dengan saran. Gunakan tombol Terima."
- **S-1b. Alasan kurang dari 5 karakter.** Sistem menampilkan "Alasan wajib diisi, minimal 5 karakter."

**Implementasi.** `TriagePanel`, `Triage::decide()`, `Triage::applyToTicket()`, `Decision`, `Suggestion`; `ajax/triase.php`; `public/js/triase.js`; tabel `glpi_plugin_halosis_decisions`, `glpi_plugin_halosis_suggestions`, `glpi_plugin_halosis_reassignments`.

### B.6 UC-06 Menangani & Menyelesaikan Tiket

| Atribut | Isi |
|---|---|
| Use-Case Name | Menangani & Menyelesaikan Tiket |
| ID | UC-06 |
| Importance Level | Tinggi |
| Primary Actor | Tim Teknis (Resolver) |
| Secondary Actor | Pegawai BPS, Operator HaloSIS |
| Use-Case Type | Detail, Real |
| Stakeholders and Interests | **Tim Teknis:** ingin referensi solusi tersedia dan beban kerja sesuai kompetensi.<br>**Pegawai BPS:** ingin masalah selesai dalam batas SLA.<br>**Knowledge Manager:** ingin solusi baru terdokumentasi untuk digunakan kembali. |
| Brief Description | Tim Teknis menangani tiket yang ditugaskan dengan bantuan **Cari pengetahuan**, meminta informasi tambahan bila perlu, lalu mencatat solusi. |
| Trigger | Tim Teknis menerima notifikasi penugasan tiket. |
| Type | External |
| Relationships | **Association:** Tim Teknis<br>**Include:** –<br>**Extend:** –<br>**Generalization:** Tim Teknis merupakan spesialisasi dari aktor Petugas Layanan TI |
| Pre-kondisi | Tiket berstatus **Sedang proses (ditugaskan)** pada grup terkait; anggota tim sudah masuk dengan peran **Tim Teknis**. |
| Post-kondisi | Tiket berstatus **Dipecahkan** dengan solusi; waktu penyelesaian terukur terhadap SLA; solusi masuk **Kandidat pengetahuan**. |
| Halaman | **Tiket saya & tim**, detail tiket, **Cari pengetahuan** |
| Keterkaitan | FR-06, FR-07, FR-09; NFR-07; BR-02, BR-03, BR-08 |

**Normal Flow of Events**

1. Tim Teknis menerima notifikasi penugasan, lalu mengklik menu **Tiket saya & tim**.
2. Tim Teknis mengklik tiket dan memeriksa panel **Saran AI**, yang tampil tanpa tombol keputusan.
3. Tim Teknis mengklik **Tambahkan saya** pada bagian aktor tiket dan mengklik **Simpan**. Status tetap **Sedang proses (ditugaskan)**.
4. Tim Teknis membuka **Cari pengetahuan**, mengetik uraian masalah, dan mengklik **Cari** untuk melihat artikel serta tiket serupa.
5. Tim Teknis menangani masalah dan mencatat perkembangan lewat **Balas**.
6. Tim Teknis mengklik **Balas ▾**, memilih **Tambah solusi**, menulis solusi, dan menyimpan.
7. Sistem mengubah status menjadi **Dipecahkan**, mencatat waktu penyelesaian terhadap SLA, dan memberi tahu pemohon. Tugas terjadwal setiap jam memasukkan solusi tersebut ke **Kandidat pengetahuan**.

**Subflows**

- **S-1 Meminta informasi tambahan.** Tim Teknis menulis pertanyaan lewat **Balas**, mengubah **Status** menjadi **Tertunda**, dan mengklik **Simpan**. Penghitungan SLA dijeda. Saat pemohon membalas, tiket keluar dari status **Tertunda** dan alur kembali ke langkah 5.

**Alternate/Exceptional Flows**

- **2a. Penugasan tidak sesuai.** Tim Teknis mengklik **Kembalikan ke Operator (salah tim)**, mengisi alasan minimal 5 karakter pada kolom "Mengapa tiket ini bukan untuk tim Anda?", lalu mengklik **Kembalikan ke Operator**. Sistem menampilkan "Tiket dikembalikan ke antrean validasi Operator.", mengosongkan penugasan, dan mengubah status menjadi **Baru**. Use case berakhir.
- **2b. Pengguna bukan tim yang ditugaskan.** Sistem menampilkan "Hanya tim yang ditugaskan yang dapat mengembalikan tiket ini selama masih diproses."
- **4a. Layanan AI mati.** **Cari Pengetahuan** menampilkan "Layanan AI HaloSIS tidak dapat dihubungi: hanya menampilkan hasil kata kunci…".
- **5a. Informasi dari pegawai belum cukup.** Jalankan S-1.
- **7a. Pegawai menolak solusi (UC-07 alur 4a).** Tiket kembali ke proses dan Tim Teknis melanjutkan dari langkah 5.

**Implementasi.** `Reassignment::canReturn()`, `Reassignment::returnToOperator()`; `ajax/triase.php` (`action=return`); `ITILSolution`, `ITILFollowup` GLPI; tugas terjadwal `KnowledgeCandidates` (`Candidate::cronKnowledgeCandidates()`); tabel `glpi_plugin_halosis_reassignments`, `glpi_itilsolutions`, `glpi_itilfollowups`.

### B.7 UC-07 Memantau Status & Mengonfirmasi Penyelesaian

| Atribut | Isi |
|---|---|
| Use-Case Name | Memantau Status & Mengonfirmasi Penyelesaian |
| ID | UC-07 |
| Importance Level | Sedang |
| Primary Actor | Pegawai BPS (Requester) |
| Secondary Actor | Operator HaloSIS, Tim Teknis (penerima notifikasi) |
| Use-Case Type | Detail, Real |
| Stakeholders and Interests | **Pegawai BPS:** ingin transparansi status tanpa harus menghubungi operator.<br>**Operator dan Tim Teknis:** ingin konfirmasi penutupan yang jelas.<br>**Manajemen:** ingin data kepuasan pengguna. |
| Brief Description | Pegawai memantau tiket di **Laporan saya**, menambah keterangan, serta menyetujui atau menolak solusi. Operator menutup tiket yang tidak mendapat respons melalui **Siap ditutup**. |
| Trigger | Pegawai ingin mengetahui perkembangan tiketnya lewat **Laporan saya**, atau menerima pemberitahuan bahwa tiket telah diselesaikan. |
| Type | External |
| Relationships | **Association:** Pegawai BPS<br>**Include:** –<br>**Extend:** –<br>**Generalization:** – |
| Pre-kondisi | Pegawai sudah masuk lewat SSO dan memiliki minimal satu tiket. |
| Post-kondisi | Tiket berstatus **Ditutup**, atau kembali ke proses beserta alasan; riwayat diperbarui dan petugas menerima notifikasi. |
| Halaman | **Laporan saya**, detail tiket, tab **Kepuasan**, **Siap ditutup** untuk Operator |
| Keterkaitan | FR-06, FR-07; NFR-07, NFR-08; BR-02 |

**Normal Flow of Events**

1. Pegawai mengklik menu **Laporan saya**.
2. Sistem menampilkan daftar dengan kolom **ID**, **Judul**, **Status**, **Kategori**, **Waktu untuk menyelesaikan**, dan **Terakhir diperbarui**.
3. Pegawai mengklik tiket berstatus **Dipecahkan**.
4. Pegawai membaca solusi pada linimasa tiket.
5. Pegawai mengklik **Setujui** pada kotak **Persetujuan atas solusi**. Kolom **Komentar** boleh dikosongkan.
6. Sistem mengubah status tiket menjadi **Ditutup**.
7. Sistem menyimpan riwayat dan mengirim notifikasi ke petugas.
8. Setelah survei tersedia, pegawai membuka tab **Kepuasan**, mengisi penilaian, dan menyimpannya.

**Subflows:** –

**Alternate/Exceptional Flows**

- **3a. Tiket belum berstatus Dipecahkan.** Pegawai mengklik **Balas**, menulis keterangan, dan menyimpan. Sistem memberi tahu petugas yang menangani. Use case berakhir. Pada tiket **Dipecahkan**, tombol **Balas** tidak tersedia dan keterangan disampaikan lewat **Tolak**.
- **5a. Masalah belum selesai.** Pegawai menulis alasan di kolom **Komentar**, lalu mengklik **Tolak**. Tiket kembali ke proses dan alur lanjut ke langkah 7.
- **5b. Pegawai mengklik Tolak tanpa alasan.** GLPI menampilkan pesan bahwa alasan wajib diisi dan solusi tidak ditolak.
- **5c. Pegawai tidak merespons.** Tiket **Dipecahkan** yang melewati batas **Siap ditutup setelah (jam tanpa respons pemohon)**, bawaan 48 jam, muncul di menu **Siap ditutup** dengan kolom **Tiket**, **Pemohon**, **Terselesaikan**, dan **Jam tanpa respons**. Operator mengklik **Tutup** pada satu tiket, atau mencentang beberapa tiket lalu mengklik **Tutup yang dipilih**. Sistem menulis alasan penutupan sebagai tindak lanjut privat dan menampilkan jumlah tiket yang ditutup dan dilewati. Tidak ada penutupan otomatis.

**Implementasi.** `Closure::readyToClose()`, `Closure::close()`, `SiapDitutupController`; `ajax/siap_ditutup.php`; form persetujuan GLPI `approbation_form.html.twig`; tabel `glpi_ticketsatisfactions`.

### B.8 UC-08 Memantau SLA & Pola Insiden

| Atribut | Isi |
|---|---|
| Use-Case Name | Memantau SLA & Pola Insiden |
| ID | UC-08 |
| Importance Level | Tinggi |
| Primary Actor | Petugas Layanan TI (Operator, Tim Teknis), Manajemen/Pimpinan |
| Secondary Actor | AI Engine |
| Use-Case Type | Detail, Real |
| Stakeholders and Interests | **Operator dan Tim Teknis:** ingin peringatan dini sebelum SLA dilanggar.<br>**Manajemen:** ingin gambaran kinerja layanan dan pola insiden.<br>**Pegawai BPS:** terdampak lebih sedikit bila insiden massal diketahui lebih awal. |
| Brief Description | Tugas terjadwal memeriksa eskalasi SLA dan mengelompokkan tiket serupa. Hasilnya berupa notifikasi, Masalah **Pola insiden: …**, dan halaman pantau. |
| Trigger | Waktu pemantauan berkala tiba, atau aktor ingin meninjau kinerja layanan. |
| Type | Temporal |
| Relationships | **Association:** Petugas Layanan TI, Manajemen/Pimpinan<br>**Include:** –<br>**Extend:** –<br>**Generalization:** Operator HaloSIS dan Tim Teknis mewarisi asosiasi dari Petugas Layanan TI |
| Pre-kondisi | Aturan SLA dan ambang pola dikonfigurasi (UC-10); ada tiket aktif. |
| Post-kondisi | Peringatan terkirim, Masalah pola terbuat atau diperbarui, dan tindak lanjut tercatat. |
| Halaman | **Pemantauan SLA**, **Pola insiden**, **Dasbor**, **Kinerja AI** |
| Keterkaitan | FR-04, FR-09, FR-10; NFR-02, NFR-07, NFR-09; BR-02, BR-07, BR-08 |

**Normal Flow of Events**

1. Tugas terjadwal berjalan. Pemeriksaan eskalasi SLA berjalan setiap menit dan deteksi pola setiap 15 menit.
2. AI Engine mengelompokkan tiket Insiden yang baru dan belum selesai berdasarkan kemiripan makna.
3. Sistem mendapati tiket mendekati batas SLA dan mengirim notifikasi ke teknisi, grup yang ditugaskan, supervisor grup, dan grup Operator.
4. Sistem mendapati kelompok yang mencapai ambang, lalu membuat Masalah **Pola insiden: …**, menautkan tiketnya, menugaskannya ke grup Operator, dan mengirim notifikasi.
5. Operator membuka **Dasbor** dan melihat banner **Pola insiden terdeteksi** dengan jumlah tiket tertaut.
6. Aktor membuka **Pemantauan SLA**, **Pola insiden**, atau **Kinerja AI**. Pada **Kinerja AI**, aktor memilih **Periode**, **Tim**, dan **Kategori layanan**, lalu mengklik **Terapkan**.
7. Aktor membuka tiket atau Masalah terkait, lalu mengeskalasi tiket, mengonfirmasi pola, atau menautkan tiket.
8. Sistem mencatat perubahan pada riwayat tiket atau Masalah.

**Subflows:** –

**Alternate/Exceptional Flows**

- **2a. Layanan AI gagal.** Sistem memakai pengelompokan cadangan berdasarkan kategori dan kemiripan judul. Metode yang dipakai dicatat di Masalah.
- **3a. Tidak ada tiket berisiko.** Tidak ada peringatan SLA yang dikirim.
- **4a. Tidak ada kelompok yang mencapai ambang.** Tidak ada Masalah baru yang dibuat.
- **4b. Pola sudah memiliki Masalah terbuka.** Sistem hanya menautkan tiket baru tanpa membuat Masalah baru.
- **6a. Pengguna tanpa hak melihat Kinerja AI.** Sistem menolak akses.
- **7a. Aktor menilai tidak perlu tindak lanjut.** Use case berakhir setelah data ditinjau.

**Implementasi.** `PatternDetector`, `Stats`, `ProgressReminder`, `DashboardController`; `POST /pola`; tugas `slaticket` dan `IncidentPattern`; `setup_sla_alerts.py`; tabel `glpi_plugin_halosis_patterns`, `glpi_slalevels_tickets`, `glpi_problems`.

### B.9 UC-09 Mengelola Knowledge Base

| Atribut | Isi |
|---|---|
| Use-Case Name | Mengelola Knowledge Base |
| ID | UC-09 |
| Importance Level | Sedang |
| Primary Actor | Knowledge Manager |
| Secondary Actor | AI Engine |
| Use-Case Type | Detail, Real |
| Stakeholders and Interests | **Knowledge Manager:** ingin knowledge akurat, mutakhir, dan memiliki penanggung jawab.<br>**Pegawai, Operator, Tim Teknis:** ingin jawaban chatbot dan referensi solusi tidak usang.<br>**Security/Tata Kelola:** ingin setiap perubahan knowledge tercatat. |
| Brief Description | Knowledge Manager mengubah kandidat menjadi artikel, memperbarui atau mengarsipkan artikel, dan menulis artikel baru. Artikel terbit masuk indeks AI. |
| Trigger | Terdapat calon knowledge dari tiket yang diselesaikan, artikel yang jatuh tempo ditinjau, atau kebutuhan artikel baru. |
| Type | External |
| Relationships | **Association:** Knowledge Manager<br>**Include:** –<br>**Extend:** –<br>**Generalization:** – |
| Pre-kondisi | Pengguna masuk dengan peran **Knowledge Manager**. |
| Post-kondisi | Artikel terbit dan terindeks, tersimpan sebagai draf, atau kandidat diabaikan; keputusan tercatat. |
| Halaman | **Kandidat pengetahuan**, **Daftar artikel**, **Tulis artikel**, halaman artikel |
| Keterkaitan | FR-03; NFR-07, NFR-13; BR-03, BR-04 |

**Normal Flow of Events**

1. Knowledge Manager mengklik menu **Kandidat pengetahuan**.
2. Sistem menampilkan halaman **Kandidat Pengetahuan**, berisi kandidat dari sinkron terjadwal setiap jam dan sinkron saat halaman dibuka, dengan tab **Menunggu**, **Dijadikan artikel**, **Diabaikan**, dan **Perlu ditinjau**.
3. Knowledge Manager membaca **Masalah**, **Solusi**, dan **Contoh tiket** pada kartu kandidat.
4. Knowledge Manager mengklik **Jadikan artikel**.
5. Sistem menyusun draf dari templat berisi **Masalah**, **Solusi**, dan tiket sumber, lalu menampilkan "Draf artikel dibuat. Tinjau, lalu terbitkan agar dapat dilihat." dan tautan **Buka draf artikel**.
6. Knowledge Manager membuka draf, mengklik **Sunting**, memperbaiki judul, isi, dan **Katalog layanan**, lalu mengklik **Simpan**.
7. Knowledge Manager menerbitkan artikel lewat **Tindakan lain** > **Tambahkan ke Tanya Jawab (FAQ)**, atau menambah target baca lewat **Bagikan**.
8. Sistem menampilkan "Indeks pencarian diperbarui." dan AI Engine mengganti isi artikel pada indeks.
9. Sistem mencatat revisi dan pelakunya di riwayat artikel.

**Subflows**

- **S-1 Memperbarui atau mengarsipkan.** Pada tab **Perlu ditinjau**, Knowledge Manager membuka artikel, lalu menyuntingnya atau mencabut target bacanya. Knowledge Manager mengisi **Sudah ditinjau; tinjau lagi pada**, lalu mengklik **Simpan tanggal**. Sistem menampilkan "Tanggal tinjau berikutnya tersimpan."
- **S-2 Menulis artikel baru.** Knowledge Manager mengklik **Tulis artikel**, mengisi judul pada **Artikel tanpa judul** dan isi artikel, lalu mengklik **Tambah artikel**. Alur lanjut ke langkah 7.

**Alternate/Exceptional Flows**

- **1a. Layanan AI mati.** Halaman tetap tampil dengan kandidat dari tiket dan menampilkan pemberitahuan "Layanan AI HaloSIS tidak dapat dihubungi sehingga…".
- **1b. Pengguna hanya berhak melihat.** Tombol **Jadikan artikel** dan **Abaikan** tidak tampil.
- **3a. Tidak ada kandidat dan artikel sudah ada.** Halaman menampilkan "Belum ada kandidat di sini." Jalankan S-1.
- **3b. Tidak ada kandidat dan artikel belum ada.** Jalankan S-2.
- **4a. Kandidat tidak layak.** Knowledge Manager mengklik **Abaikan**, mengisi **Alasan pengabaian**, lalu mengklik **Abaikan kandidat**. Sistem menampilkan "Kandidat diabaikan." Alasan kurang dari 5 karakter menghasilkan "Tuliskan alasan minimal 5 karakter."
- **4b. Kandidat sudah diputuskan pengguna lain.** Sistem menampilkan "Kandidat ini sudah diputuskan."
- **5a. Penyusun draf AI (LLM) diaktifkan.** AI Engine menyusun ulang masalah dan solusi menjadi artikel berbahasa formal (judul, gejala, langkah penyelesaian) hanya dari teks sumber, dengan sitasi tiket sumber dan tanda "Disusun AI, wajib ditinjau Knowledge Manager". Bila LLM gagal atau tidak tersedia, draf memakai templat seperti langkah 5. Alur lanjut ke langkah 6.
- **7a. Artikel belum layak terbit.** Draf dibiarkan tanpa target dan tidak muncul pada pencarian. Daftar artikel menandainya "Item ini belum diterbitkan".
- **8a. Pembaruan indeks gagal.** Sistem menampilkan "Gagal memperbarui indeks pencarian; indeks sebelumnya tetap dipakai."
- **S-1a. Tanggal tinjau tidak valid.** Sistem menampilkan "Pilih tanggal tinjau setelah hari ini."

**Implementasi.** `KandidatController`, `Candidate::cronKnowledgeCandidates()`, `KnowledgeCandidates::sync()`, `::makeArticle()`, `::aiDraft()`, `::ignore()`, `::dueForReview()`, `::setReviewDate()`, `KnowledgeIndex`; `ajax/kandidat.php`; `GET /kandidat`, `POST /kandidat/draf`, `POST /reindex/artikel`; tabel `glpi_plugin_halosis_candidates`, `glpi_plugin_halosis_kb_reviews`, `glpi_knowbaseitems`.

### B.10 UC-10 Mengonfigurasi Platform ITSM

| Atribut | Isi |
|---|---|
| Use-Case Name | Mengonfigurasi Platform ITSM |
| ID | UC-10 |
| Importance Level | Tinggi |
| Primary Actor | Administrator Sistem |
| Use-Case Type | Detail, Real |
| Stakeholders and Interests | **Administrator Sistem:** ingin perubahan cepat tanpa bergantung pada vendor.<br>**PM Internal/Pemilik Proses:** ingin platform selaras dengan kebutuhan bisnis yang berubah.<br>**Security/Tata Kelola:** ingin perubahan konfigurasi terkendali dan tercatat. |
| Brief Description | Administrator mengubah katalog, SLA, tim, peran, aturan, notifikasi, dan Pengaturan AI lewat menu administrasi tanpa mengubah kode. |
| Trigger | Ada kebutuhan perubahan layanan, alur kerja, SLA, peran, notifikasi, atau aturan. |
| Type | External |
| Relationships | **Association:** Administrator Sistem<br>**Include:** –<br>**Extend:** –<br>**Generalization:** – |
| Pre-kondisi | Administrator sudah masuk dan memiliki hak konfigurasi. |
| Post-kondisi | Konfigurasi baru berlaku tanpa perubahan kode; perubahan tercatat dan Administrator diberi tahu lewat Catatan. |
| Halaman | **Panel administrasi**, **Katalog layanan**, **Kategori layanan**, **Kebijakan SLA**, **Tim teknis**, **Pengguna & peran**, **Alur kerja & aturan**, **Pengaturan AI**, **Notifikasi**, **Jejak audit** |
| Keterkaitan | FR-09, FR-10; NFR-05, NFR-07, NFR-10, NFR-14; BR-01, BR-02 |

**Normal Flow of Events**

1. Administrator mengklik menu **Pengaturan AI**.
2. Sistem memeriksa hak akses dan menampilkan **Konfirmasi diperlukan** · **Area sensitif**.
3. Administrator mengklik **Verifikasi**.
4. Sistem menampilkan formulir Pengaturan AI.
5. Administrator mengubah nilai, misalnya **Ambang keyakinan**, **Ambang keyakinan rendah**, atau **Siap ditutup setelah (jam tanpa respons pemohon)**.
6. Administrator mengklik **Pratinjau dampak** dan sistem menampilkan dampaknya tanpa menyimpan perubahan.
7. Administrator mengklik **Simpan**.
8. Sistem memeriksa nilai, menyimpan konfigurasi, dan menampilkan "Konfigurasi HaloSIS berhasil disimpan."
9. Sistem mencatat perubahan di log sistem dan membuat Catatan untuk profil Administrator yang tampil 7 hari di Beranda.

**Subflows**

- **S-1 Mengubah SLA.** Administrator membuka **Kebijakan SLA** atau **Alur kerja & aturan**, mengubah target atau aturan, lalu menyimpan. Sebelumnya, Administrator dapat memakai **Pratinjau dampak perubahan SLA** pada Pengaturan AI dengan **SLA atau aturan SLA**, **Target baru (SLA)**, dan **SLA pengganti (aturan)**. Hasilnya menampilkan jumlah tiket **Aman**, **Berisiko**, dan **Terlewati**.
- **S-2 Mengubah objek lain.** Administrator membuka menu objek terkait, mengubah data, lalu menyimpan lewat halaman GLPI. Perubahan aturan, SLA, kategori, dan form katalog dicatat dengan cara yang sama pada langkah 9.

**Alternate/Exceptional Flows**

- **1a. Pengguna tidak berhak.** Menu tidak tampil dan akses langsung ditolak. Use case berakhir.
- **6a. Pratinjau SLA tanpa pilihan lengkap.** Sistem menampilkan "Pilih SLA atau aturan SLA dan target barunya."
- **8a. URL tidak valid.** Sistem menampilkan "URL layanan AI harus diawali http:// atau https://." Nilai lain yang valid tetap tersimpan.
- **8b. Kolom API key dikosongkan.** Nilai lama tetap dipakai.

**Implementasi.** `front/config.form.php`, `Config::saveFromForm()`, `ConfigAudit::previewThresholds()`, `::previewSla()`, `::previewSlaRule()`, `::onConfigSaved()`, `RoleMenu`; `templates/config.html.twig`; tabel `glpi_configs`, `glpi_events`, `glpi_reminders`.

### B.11 Keterlacakan

| UC | FR | NFR | Implementasi utama |
|---|---|---|---|
| UC-01 | FR-01, FR-02, FR-03 | NFR-06, NFR-08, NFR-12 | `Chatbot`, `Chat`, `Privacy` |
| UC-02 | FR-03 | NFR-06, NFR-07, NFR-09, NFR-12 | `ai/service/app.py`, `search.py` |
| UC-03 | FR-06, FR-09 | NFR-03, NFR-13 | `Chatbot::createTicket()`, hook tiket |
| UC-04 | FR-04, FR-08 | NFR-07, NFR-11, NFR-12, NFR-14 | `Triage::generate()`, `Ai\Service` |
| UC-05 | FR-05, FR-07 | NFR-05, NFR-07, NFR-14 | `Triage::decide()`, `Decision` |
| UC-06 | FR-06, FR-07, FR-09 | NFR-07 | `Reassignment`, Cari Pengetahuan |
| UC-07 | FR-06, FR-07 | NFR-07, NFR-08 | Persetujuan GLPI, `Closure` |
| UC-08 | FR-04, FR-09, FR-10 | NFR-02, NFR-09 | `PatternDetector`, `Stats` |
| UC-09 | FR-03 | NFR-07, NFR-13 | `KnowledgeCandidates`, `KnowledgeIndex` |
| UC-10 | FR-09, FR-10 | NFR-05, NFR-07, NFR-10 | `Config`, `ConfigAudit` |

---

## Penyesuaian terhadap Tugas 3

- **Status tiket:** Resolved menjadi Dipecahkan, Assigned dan Dalam Penanganan menjadi Sedang proses, Pending menjadi Tertunda, Closed menjadi Ditutup.
- **Jalur baru (†):** Operator dapat mencatat tiket atas nama pegawai dan menutup tiket yang tidak direspons pegawai.
- **UC-01:** bila pencarian utama gagal, sistem beralih ke pencarian kata kunci tanpa pemberitahuan.
- **UC-03:** tiket dari konsultasi hanya dapat disunting judulnya, tanpa lampiran. Tiket tanpa rekomendasi tidak diberi penanda khusus.
- **UC-02:** jawaban asisten untuk pegawai hanya memakai artikel KB terbit dan katalog layanan; tiket lama hanya dipakai pada Cari pengetahuan petugas.
- **UC-04:** tim diprediksi lebih dulu, lalu kategori diturunkan dari tim. Tiket serupa berasal dari model triase, bukan UC-02. Urgensi ditentukan aturan kata kunci karena model urgensi belum lolos uji kualitas.
- **UC-05:** bahan evaluasi masih digabungkan manual ke data latih, dan tiket dapat diproses tanpa keputusan atas rekomendasi.
- **UC-06:** status proses berlaku sejak penugasan, dan referensi dicari sendiri lewat Cari pengetahuan.
- **UC-07:** daftar tiket menampilkan batas waktu, dan penilaian diberikan lewat survei setelah tiket ditutup.
- **UC-08:** filter layanan, tim, dan periode hanya tersedia di Kinerja AI.
- **UC-09:** artikel terbit bila menjadi FAQ atau memiliki target baca, arsip berarti mencabut target, dan kolom kata kunci tidak ada. Draf dapat disusun AI (opsional) dan tetap wajib ditinjau Knowledge Manager.
- **UC-10:** pratinjau bersifat opsional, konflik aturan tidak diperiksa, dan pemberitahuan berupa Catatan untuk Administrator.
