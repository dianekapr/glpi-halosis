# Uji regresi skenario demo (plugins/halosis/README.md)

Tanggal: 31 Okt 2026 · Lingkungan: docker-compose lokal (GLPI 12, plugin HaloSIS 0.8.0, `halosis-ai` hidup,
Keycloak lokal) · Alat: Chromium headless (Playwright) untuk langkah UI, skrip PHP di container GLPI untuk langkah
sisi server · Katalog layanan disinkronkan dulu ke indeks AI (16 layanan: kategori Helpdesk + form aktif).

Data uji (tiket #78–#82, percakapan #31–#35, Problem #6, tanggal tinjau KB-2) **sudah dihapus** setelah uji.

| Langkah | Cara uji | Hasil | Catatan |
| --- | --- | --- | --- |
| 1.1 Login `budi` → Tanya HaloSIS | UI | ✅ | SSO Keycloak; masuk `/plugins/halosis/Chat`, pilihan *Ajukan permintaan* tampil |
| 1.2 Chip FASIH → jawaban + sumber | UI | ✅ | Sumber "FASIH: sinkronisasi gagal" |
| 1.3 Peringatan privasi | UI | ✅ | "password saya: abc123" → pesan penyamaran |
| 1.4–1.5 Belum terselesaikan → laporan | UI | ✅ | Tiket dibuat dari chat, tautan *Buka laporan* |
| 1 variasi: "Kursi kantor saya patah" | server | ✅ | Tidak ditemukan → tawaran laporan |
| 1 keyakinan sedang: "lampiran besar" | UI | ✅ | "Maksud Anda…?" + artikel "Lampiran email lebih dari 10 MB" + kartu Buat laporan |
| 2.2 Panel Saran AI (`rina`) | UI | ✅ | Tingkat *Pilih dari 3 kandidat* (40%), tiket aktif per kandidat tim tampil |
| 2.3 Terima | UI | ✅ | Nilai diterapkan, status *Diterima* |
| 2.4 Riwayat | server | ✅ | Baris log "HaloSIS: Saran AI diterima" ada |
| 2b Operator atas nama `siti` | server | ✅ | Pemohon siti, sumber *Phone*, 1 saran AI dibuat |
| 3.2 Panel Tim Teknis (`andi`) | UI | ✅ | Tanpa tombol keputusan |
| 3.3 Solusi | server | ✅ | Status *Terselesaikan* |
| 4 Approve (`budi`) | server | ✅ | Status *Ditutup* |
| 5 Dashboard (`sri`) | UI | ✅ | Filter tim/kategori diterapkan (`group=` di URL), kartu drift & tren pola tampil; tombol ekspor tidak tampil untuk Manajemen |
| 5.4 Ekspor CSV (`dimas`) | UI | ✅ | HTTP 200, `text/csv` |
| Bonus pola (3 insiden SSO) | server + UI | ✅ | Problem pola baru, 7 notifikasi antre; banner *Pola insiden terdeteksi* di beranda `rina` |
| Tab Perlu ditinjau (`lina`) | UI | ✅ | Artikel jatuh tempo + form tanggal tinjau berikut |

## Bug kecil yang ditemukan & diperbaiki

| # | Temuan | Perbaikan |
| --- | --- | --- |
| 1 | Tabel tren pola terlalu sempit: topik terlipat, kolom Total terpotong | Kartu tren selebar grid (`.hd-span-all`), kolom topik min. 14rem; drift dipindah ke samping kartu Pola insiden |
| 2 | Label "< 70% (perlu penilaian manual)" tidak tepat sejak ada 3 tingkat keyakinan | Menjadi "< 70% (di bawah ambang)" |
| 3 | Teks pengantar tab Perlu ditinjau masih menyebut "menyunting artikel" saja | Menyebut tanggal tinjau yang diatur (KR-03) atau 6 bulan bawaan; label form disejajarkan |

Catatan: setelah mengubah template/CSS plugin di mode produksi, jalankan
`docker compose exec glpi php bin/console cache:clear` agar Twig tidak memakai cache lama.
Tangkapan layar baru: `screenshot/11-operator-panel-saran-ai.png`, `12-manajemen-kinerja-ai.png`,
`13-km-perlu-ditinjau.png`, `14-pegawai-chat-maksud-anda.png`; `8-masalah-pola-insiden.png` diperbarui (banner pola).

## Regresi 31 Okt 2026 — data history versi baru, urgensi & sinyal dampak

Model triase/jenis dilatih ulang, model urgensi baru, indeks dibangun ulang (4.923 potongan), `halosis-ai` di-build
ulang, `plugin:install --force` (kolom `urgency_confidence`, `impact_reason`). Data uji (tiket #1046–#1071, Problem
#8, 2 pemberitahuan konfigurasi uji, 39 notifikasi antre) **sudah dihapus**; snapshot `backup/demo-20261031-224501`.

| Langkah | Cara uji | Hasil | Catatan |
| --- | --- | --- | --- |
| 2.2 Panel Saran AI (`rina`) | UI | ✅ | "Email … segera … pagi ini": urgensi Tinggi (aturan; model tidak menimpa High), "Dampak Sangat Tinggi: layanan kritis (Email)", prioritas = matriks |
| 2.3 Terima | UI | ✅ | Status *Diterima* |
| Bonus pola (3 insiden SSO) | server + UI | ✅ | Tiket ke-3: "Dampak Tinggi: 3 tiket serupa dalam 1 jam; layanan kritis (SSO)"; Problem pola baru; banner *Pola insiden terdeteksi* di beranda `rina` |
| Dashboard (`sri`) | UI | ✅ | "baseline ESTIM 28,87% (1.819 dengan SLA berimputasi)", kartu *Kepuasan pemohon (nilai ≥ 4)* + baseline 95,76% |
| Pengaturan *Layanan kritis* | server (render Twig + simpan) | ✅ | Bawaan "SSO, Email, Jaringan"; daftar dinormalisasi; nilai dikembalikan. Halaman UI diblok prompt autentikasi ulang GLPI di Playwright |
| /chat Email, SSO, SiPecut | API | ✅ | 6 pertanyaan menjawab (FAQ KB-13/14/15 & tiket historis) |

Bug yang ditemukan & diperbaiki: (1) "tidak **mendesak**" terbaca desakan → negasi diabaikan; (2) kata gangguan
"mati" cocok di "oto**mati**s" → pencocokan per kata utuh; (3) model urgensi (hanya Medium/Low) menimpa urgensi
Tinggi dari aturan → model hanya dipakai bila aturan ≤ Sedang.
