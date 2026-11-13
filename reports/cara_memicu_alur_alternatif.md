# Cara memicu alur alternatif UC-01 … UC-10 (demo)

Sumber: bagian B (Real Use Case) di [T4_final.md](T4_final.md). Dokumen ini hanya panduan; tidak ada data yang diubah olehnya.
Semua akun memakai kata sandi `halosis`. Peran: `budi`/`siti`/`maya` Pegawai · `rina` Operator · `andi`/`fajar`/`dedi`/`rudi` Tim Teknis
(`hendra` ketua) · `lina` Knowledge Manager · `sri` Manajemen · `dimas` Administrator.

**Aturan umum pengembalian:** sebelum mencoba, jalankan `scripts/demo_snapshot.sh simpan`; setelah selesai `scripts/demo_snapshot.sh pulihkan`
(±15 dtk; mengembalikan DB, Keycloak, indeks AI). Bila hanya layanan AI yang dihentikan: `docker compose start halosis-ai`.
Tanda: ✅ dapat dipicu manual · ⚠️ perlu persiapan/alat bantu · ❌ tidak dapat dipicu manual dari UI.
Alur yang sudah otomatis diuji: `tests/e2e/alur_alternatif.js` (UC-01 4a, UC-02 5a, UC-03 4a, UC-04 1a, UC-05, UC-06, UC-07 5a, UC-09 5a).

## UC-01 Berkonsultasi melalui AI Chatbot (akun `budi`, menu Tanya HaloSIS)
| Alur | Memicu | Tampilan yang diharapkan | Mengembalikan |
|---|---|---|---|
| 1a ✅ | Login `dimas` → Pengaturan AI → matikan sakelar fitur *chat* → simpan. Login `budi`, buka Tanya HaloSIS. | **Asisten Sedang Tidak Tersedia**, tombol Buat laporan, tautan FAQ. | Nyalakan sakelar lagi (atau pulihkan snapshot). |
| 1b ✅ | Login `pegawai_tanpa_asisten` (Pegawai tanpa hak asisten), buka alamat `/plugins/halosis/front/chat.php` atau menu Tanya HaloSIS bila tampil. | "Asisten tidak tersedia untuk akun Anda." | – (akun demo khusus, tidak perlu dikembalikan). |
| 2a ✅ | Klik kartu **Laporkan masalah**. | Kotak ketik difokuskan; asisten: "Ceritakan masalah yang Anda alami…". Tiket tidak dibuat. | Tidak perlu. |
| 2b ✅ | Klik kartu **Ajukan permintaan**. | Form **Ajukan Permintaan** terbuka. | Tidak perlu. |
| 3a ✅ | Kirim pesan kosong (tekan Kirim tanpa isi; bila tombol nonaktif, kirim hanya spasi lewat tampilan lain tidak mungkin). | "Silakan ketik pertanyaan." Pada UI normal tombol Kirim memang tidak mengirim pesan kosong, jadi pesan ini terutama muncul dari panggilan langsung ke server. | – |
| 3b ⚠️ | Kirim 20 pesan pengguna dalam satu percakapan (`Chat::MAX_USER_MESSAGES`), lalu pesan ke-21. | "Percakapan terlalu panjang. Buat laporan atau mulai percakapan baru." | Klik **Percakapan baru**. |
| 3c ✅ | Akhiri percakapan: dari kartu 7a klik **Tidak, terima kasih**; lalu muat ulang halaman riwayat dan coba ketik lagi (kotak ketik terkunci). | "Percakapan ini sudah selesai. Klik tombol Percakapan baru (ikon ⟳ di kanan atas) untuk bertanya lagi." | Klik **Percakapan baru**. |
| 4a ⚠️ | `docker compose stop halosis-ai` lalu ajukan pertanyaan. | Hasil pencarian kata kunci berlabel **Dari Pusat Bantuan**; bila kosong → 5a. | `docker compose start halosis-ai`. |
| 4b ⚠️ | Putuskan jaringan ke server web saat mengirim (mode offline di DevTools peramban). | "Asisten sedang tidak tersedia. Anda tetap dapat membuat laporan." + kartu laporan. | Aktifkan jaringan lagi. |
| 5a ✅ | Tanyakan hal TI yang tidak ada di artikel, mis. "Kursi kantor saya patah" (tidak lolos ambang). | "Maaf, saya belum menemukan jawabannya…" + kartu "Saya belum menemukan jawabannya… Atau ketik ulang kendala Anda dengan kata lain." (**Ya, buat laporan** / **Tidak, terima kasih**). | Pulihkan snapshot bila memilih membuat laporan. |
| 5b ⚠️ | Pertanyaan dengan kemiripan di zona sedang (antara ambang 0,78 dan 0,83 pada skor chat); butuh percobaan beberapa kata kunci. Tidak ada jaminan: bergantung skor model. | "Apakah yang Anda maksud salah satu artikel berikut?" + tautan, kartu: "Bila tidak ada artikel yang cocok, saya bisa membuatkan laporan…". | – |
| 5c ✅ | Tanyakan hal non-TI, mis. "Cara mengajukan cuti". | Diarahkan ke unit terkait, tanpa tawaran laporan. | – |
| 7a ✅ | Setelah jawaban, klik **Belum terselesaikan**. | Kartu "Masalah belum selesai? Saya akan membuatkan laporan…" + petunjuk ketik ulang; kotak ketik aktif. | – |
| 7b ✅ | Pada kartu 7a klik **Tidak, terima kasih**. | "Percakapan diakhiri…"; kotak ketik terkunci; riwayat: **Berakhir tanpa laporan**. | Pulihkan snapshot (menambah baris chat). |

## UC-02 Mencari Knowledge Relevan (akun `rina`/`andi`, menu Cari pengetahuan)
| Alur | Memicu | Tampilan | Mengembalikan |
|---|---|---|---|
| 3a ⚠️ | `docker compose stop halosis-ai`, cari apa saja. | "Layanan AI HaloSIS tidak dapat dihubungi: hanya menampilkan hasil kata kunci…". | `docker compose start halosis-ai`. |
| 5a ✅ | Cari frasa tanpa kemiripan; atau kata di zona sedang (maks. 3 artikel). | Tanpa hasil ambang / ≤3 artikel; pencarian tercatat. | Pulihkan snapshot (log pencarian bertambah). |
| S-1a ✅ | Cari kata tak bermakna ("zzqx"). | "Pengetahuan tidak ditemukan. Silakan coba kata lain." | – |
| S-1b ✅ | Klik **Membantu**/**Tidak membantu** pada hasil. | "Terima kasih, umpan balik Anda tersimpan." | Pulihkan snapshot. |

## UC-03 Membuat Tiket (`budi`)
| Alur | Memicu | Tampilan | Mengembalikan |
|---|---|---|---|
| 1a ✅ | Dari chat klik **Ya, buat laporan** (jalankan S-1). | Judul terisi + **Ringkasan yang dilampirkan**; setelah Kirim: "Laporan #… sudah dibuat…". | Hapus tiket / pulihkan snapshot. |
| 1b ✅ | `rina` → Semua tiket → **Tambah**, isi Pemohon, Sumber permintaan (Phone/E-Mail/Direct), Judul, Deskripsi. | Tiket dibuat atas nama pemohon. | Hapus tiket / pulihkan. |
| 5a ✅ | Form **Laporkan Masalah**: kosongkan Judul atau Deskripsi, Kirim. Pada kartu laporan chat: judul "abc". | Kolom ditandai, tiket tidak dibuat; "Judul laporan minimal 5 karakter." | – |
| 5b ✅ | Login `pegawai_tanpa_tiket` (bisa chat, tanpa hak membuat tiket), jalankan S-1 hingga tombol **Buat laporan**. | "Anda tidak berhak membuat tiket." | – (akun demo khusus). |
| 6a ⚠️ | `docker compose stop halosis-ai`, buat tiket baru. | Tiket tersimpan; panel: "Belum ada saran AI untuk tiket ini." + **Buat saran AI**. | `docker compose start halosis-ai`; hapus tiket uji. |

## UC-04 Menghasilkan Rekomendasi Triase & Routing
| Alur | Memicu | Tampilan | Mengembalikan |
|---|---|---|---|
| 1a ⚠️ | Hentikan `halosis-ai`, buat tiket; pengulangan otomatis tiap 15 menit (maks. 5×, tiket ≤3 hari) lewat cron TriageRetry. | Tiket tanpa saran; log kegagalan di `files/_log/halosis.log`. | Nyalakan lagi layanan. |
| 1b ❌ | Mode demo hanya aktif bila layanan AI lokal **dan** kunci API tidak tersedia; di lingkungan ini layanan AI lokal selalu terpasang, jadi tidak dapat dipicu tanpa menghapus konfigurasi (bukan alur untuk demo). | Saran dari aturan kata kunci. | – |
| 5a ⚠️ | Buat tiket yang keyakinannya 40–70 (judul ambigu, mis. campuran jaringan & aplikasi). Tidak dapat dipastikan; ambang dapat digeser di Pengaturan AI (`dimas`) agar tiket yang ada masuk zona sedang. | Tanda **Pilih dari 3 kandidat…**. | Kembalikan ambang. |
| 5b ⚠️ | Tiket tidak jelas / di luar domain, atau naikkan ambang bawah di Pengaturan AI. | **Perlu penilaian manual · keyakinan di bawah ambang**. | Kembalikan ambang. |
| 5c ⚠️ | Tiket yang tim teratasnya "Lainnya", atau model belum lolos uji kualitas (tidak dapat dipicu tanpa mengganti model). | **Perlu penilaian manual** (+ "Model belum lolos uji kualitas…"). | – |

## UC-05 Memvalidasi Rekomendasi AI (`rina`; tiket baru berstatus Baru dengan saran)
| Alur | Memicu | Tampilan | Mengembalikan |
|---|---|---|---|
| S-1 / 5a ✅ | Klik **Ubah**, ubah Kategori/Dampak/Urgensi/Prioritas/Grup, isi alasan, **Terapkan perubahan**. | "Nilai yang diubah diterapkan ke tiket." | Pulihkan snapshot. |
| S-2 / 5b ✅ | Klik **Tolak**, isi alasan, **Tolak & triase manual**. | "Saran AI ditolak. Silakan triase tiket secara manual." | Pulihkan. |
| 3a ✅ | Login `operator_lihat` (Operator tanpa hak memutuskan saran AI), buka tiket bersaran AI. | Tombol keputusan tidak tampil; "Menunggu keputusan Operator." Server juga menolak. | – (akun demo khusus). |
| 3b ✅ | Buka tiket tanpa saran (lihat UC-03 6a) → **Buat saran AI**. | "Saran AI dibuat." atau pesan gagal (layanan mati: "AI belum dapat memberikan saran…"). | Nyalakan layanan. |
| 5c ✅ | Setelah keputusan, **Balas ▾ → Tambah solusi**. | Status **Dipecahkan**, pemohon diberi tahu. | Pulihkan. |
| 5d ✅ | Buka kembali tiket yang saran sudah diputuskan lalu kirim keputusan lagi (dua tab). | "Saran ini sudah diputuskan." | – |
| S-1a ✅ | Pada Ubah, biarkan nilai sama dengan saran. | "Nilainya sama dengan saran. Gunakan tombol Terima." | – |
| S-1b ✅ | Alasan < 5 karakter. | "Alasan wajib diisi, minimal 5 karakter." | – |

## UC-06 Menangani & Menyelesaikan Tiket (`andi`/`hendra`)
| Alur | Memicu | Tampilan | Mengembalikan |
|---|---|---|---|
| 2a ✅ | Tiket yang ditugaskan ke tim `andi`: **Kembalikan ke Operator (salah tim)**, alasan ≥5 karakter. | "Tiket dikembalikan ke antrean validasi Operator.", penugasan kosong, status Baru. | Pulihkan. |
| 2b ✅ | Akun tim lain (mis. `dedi`) membuka tiket tim `andi` yang masih diproses. | "Hanya tim yang ditugaskan yang dapat mengembalikan tiket ini selama masih diproses." | – |
| 4a ⚠️ | Hentikan `halosis-ai`, buka Cari Pengetahuan. | "Layanan AI HaloSIS tidak dapat dihubungi: hanya menampilkan hasil kata kunci…". | Nyalakan layanan. |
| 5a / S-1 ✅ | **Balas**, ubah Status ke **Tertunda**, Simpan; pemohon membalas. | SLA dijeda; setelah balasan tiket keluar dari Tertunda. | Pulihkan. |
| 7a ✅ | Lihat UC-07 5a. | Tiket kembali diproses. | Pulihkan. |

## UC-07 Memantau Status & Konfirmasi (`budi` sebagai pemohon)
| Alur | Memicu | Tampilan | Mengembalikan |
|---|---|---|---|
| 3a ✅ | Pada tiket belum Dipecahkan klik **Balas**, simpan. | Petugas diberi tahu; pada tiket Dipecahkan tombol Balas tidak ada. | Pulihkan. |
| 5a ✅ | Pada tiket Dipecahkan tulis Komentar, klik **Tolak**. | Tiket kembali diproses. | Pulihkan. |
| 5b ✅ | Klik **Tolak** tanpa komentar. | GLPI: alasan wajib diisi; solusi tidak ditolak. | – |
| 5c ⚠️ | Tiket Dipecahkan lewat batas "Siap ditutup setelah" (bawaan 48 jam): turunkan batas ke 0 di Pengaturan AI, atau mundurkan tanggal solusi (alat demo `seed_demo.py --mundurkan-tanggal`). Lalu `rina` → **Siap ditutup** → **Tutup** / **Tutup yang dipilih**. | Daftar dengan kolom Tiket, Pemohon, Terselesaikan, Jam tanpa respons; alasan penutupan jadi tindak lanjut. | Kembalikan batas; pulihkan snapshot. |

## UC-08 Memantau SLA & Pola Insiden (`rina`, `sri`, `dimas`)
| Alur | Memicu | Tampilan | Mengembalikan |
|---|---|---|---|
| 2a ⚠️ | Hentikan `halosis-ai`, jalankan cron pola (`docker compose exec glpi php bin/console glpi:cron:run ...` atau tunggu), dengan ≥3 tiket mirip. | Pengelompokan cadangan (kategori + kemiripan judul); metode tercatat di Masalah. | Nyalakan layanan; pulihkan. |
| 3a ✅ | Tidak ada tiket berisiko saat cron SLA berjalan (kondisi bawaan bila semua tiket aman). | Tidak ada peringatan terkirim (Mailpit kosong). | – |
| 4a ✅ | Jalankan deteksi dengan kurang dari 3 tiket mirip dalam 60 menit. | Tidak ada Masalah baru. | – |
| 4b ⚠️ | Buat tiket mirip tambahan sementara pola Wi-Fi (Masalah [DEMO]) masih terbuka. | Tiket baru hanya ditautkan, tak ada Masalah baru. | Pulihkan. |
| 6a ✅ | `andi` (tanpa hak) membuka alamat Kinerja AI langsung. | Akses ditolak. | – |
| 7a ✅ | Tinjau data lalu keluar tanpa tindakan. | Use case selesai. | – |

## UC-09 Mengelola Knowledge Base (`lina`)
| Alur | Memicu | Tampilan | Mengembalikan |
|---|---|---|---|
| 1a ⚠️ | Hentikan `halosis-ai`, buka Kandidat pengetahuan. | Kandidat tiket tetap tampil + pemberitahuan layanan AI. | Nyalakan layanan. |
| 1b ✅ | Akun dengan hak baca saja (profil Read-Only). | Tombol **Jadikan artikel**/**Abaikan** tidak tampil. | – |
| 3a / 3b ✅ | Saring ke target tanpa kandidat. | "Belum ada kandidat di sini." → S-1 (artikel ada) atau S-2 (belum ada). | – |
| 4a ✅ | **Abaikan** dengan alasan <5 karakter / sah. | "Tuliskan alasan minimal 5 karakter." / "Kandidat diabaikan." | Pulihkan. |
| 4b ⚠️ | Dua sesi (dua peramban) pada kandidat yang sama; putuskan di sesi pertama lalu sesi kedua. | "Kandidat ini sudah diputuskan." | Pulihkan. |
| 5a ⚠️ | Aktifkan LLM (profil `llm`, `LLM_PROVIDER=openai`) lalu **Jadikan artikel**. Bawaan LLM mati → templat. | Draf berlabel "Disusun AI, wajib ditinjau…" (hanya dengan LLM). | Kembalikan `.env`. |
| 7a ✅ | Simpan artikel tanpa target. | Draf tak muncul di pencarian; "Item ini belum diterbitkan". | Hapus artikel. |
| 8a ⚠️ | Hentikan `halosis-ai` lalu terbitkan artikel. | "Gagal memperbarui indeks pencarian; indeks sebelumnya tetap dipakai." | Nyalakan layanan; pulihkan. |
| S-1a ✅ | Isi tanggal tinjau di masa lalu. | "Pilih tanggal tinjau setelah hari ini." | – |

## UC-10 Mengonfigurasi Platform ITSM (`dimas`)
| Alur | Memicu | Tampilan | Mengembalikan |
|---|---|---|---|
| 1a ✅ | Login `budi`/`rina`, buka alamat Pengaturan AI langsung. | Menu tidak tampil; akses ditolak. | – |
| 6a ✅ | Pengaturan AI → Pratinjau dampak SLA → Hitung tanpa memilih SLA/target. | "Pilih SLA atau aturan SLA dan target barunya." | – |
| 8a ✅ | Isi URL layanan AI `ftp://x` → Simpan. | "URL layanan AI harus diawali http:// atau https://." (nilai lain tetap tersimpan) | Kembalikan URL (`http://halosis-ai:8000`). |
| 8b ✅ | Biarkan kolom API key kosong → Simpan. | Nilai lama tetap dipakai. | – |

## Aktif/nonaktif fitur (tanpa menghapus data)
Akun `dimas` → menu **Pengaturan AI** → bagian **Fitur AI** (sakelar geser) → **Simpan**. Sakelar yang dipakai:
| Tujuan | Sakelar / cara | Memicu | Mengembalikan |
|---|---|---|---|
| Fitur chat mati (UC-01 1a) | **Asisten layanan mandiri untuk pegawai** → mati | **Asisten Sedang Tidak Tersedia** untuk `budi` | Nyalakan sakelar yang sama → Simpan |
| Layanan AI mati (UC-01 4a/4b, UC-06 4a) | Bukan sakelar: `docker compose stop halosis-ai` | Chat/Cari Pengetahuan memakai pencarian kata kunci berlabel **Dari Pusat Bantuan**; UC-06 4a: pesan layanan AI tidak dapat dihubungi | `docker compose start halosis-ai` |
| Triase mati (UC-03 6a, UC-05 3b) | **Saran triase AI untuk tiket baru** → mati | Tiket baru tanpa saran: "Belum ada saran AI untuk tiket ini." + **Buat saran AI** | Nyalakan sakelar yang sama → Simpan |

Akun demo khusus (kata sandi `halosis`, dibuat `python setup_akun_demo_khusus.py`, idempoten): `pegawai_tanpa_asisten` (profil *Pegawai (tanpa asisten)*) → UC-01 1b · `pegawai_tanpa_tiket` (*Pegawai (tanpa buat tiket)*) → UC-03 5b · `operator_lihat` (*Operator (lihat saja)*) → UC-05 3a.

## Ringkasan yang tidak dapat dipicu manual (❌)
- **UC-04 1b** (mode demo tanpa layanan AI): layanan AI lokal selalu terpasang di demo; memicu butuh menghapus konfigurasi layanan.
- **UC-01 3a** pada UI normal: tombol Kirim tidak mengirim pesan kosong; pesan hanya muncul bila diminta langsung ke server.
- **UC-04 5c (model belum lolos)**: hanya terjadi bila model aktif diganti dengan model yang gagal gerbang (tidak boleh diubah di demo).
