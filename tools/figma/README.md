# tools/figma — memperbarui prototype Figma dari aplikasi HaloSIS

File Figma: `VKBzfkB7mwadHYHz7qIwOU`, halaman "Prototype HaloSIS" (id `49:2`). Section: 01 Pegawai `49:5`, 02 Operator `49:6`, Alur Demo `49:4`.
Butuh: docker compose hidup (GLPI :8080), `tests/e2e/node_modules` (playwright-core), akun uji kata sandi `halosis`.

| alat | fungsi | cara pakai |
|---|---|---|
| `capture.js` | tangkap halaman app (akun, URL, aksi) → frame Figma 1440 px | minta `captureId` (satu per tangkapan) lewat MCP `generate_figma_design`, lalu `node tools/figma/capture.js --user rina --url '<path>' --h 1109 --ids <id1>[,<id2>] [--steps steps/x.js] [--png logs/x]` (kutip URL ber-`?`). Id `x` = lewati. Cek selesai dengan memanggil `generate_figma_design` + `captureId` sampai `completed`. Frame mendarat di halaman Figma sebagai frame tingkat-halaman (id tertera di hasil). |
| `inject_icons.js` | glyph webfont Tabler kosong → SVG inline (Tabler 3.19.0) | otomatis dipanggil `capture.js` sebelum tangkap. Ikon tak dikenal dilaporkan di `tidakAda`. |
| `steps/*.js` | skenario aksi: `module.exports = async ({page, cap, BASE}) => {…; await cap(i)}` | contoh `steps/op_ubah.js` (env `TICKET`). |
| `testdata.js` | `create <pemohon> "<judul>"` / `cleanup` tiket uji; dicatat di `logs/figma_testdata.json`, cleanup mengembalikan DB | selalu jalankan `cleanup` di akhir; ia mencetak jumlah tiket/chat sebelum & sesudah. |
| `figma_snapshot.js` | **rewire 1**: catat semua reaction keluar & masuk sebuah frame (read-only) | tempel ke `use_figma`, isi `CFG.target`; simpan hasil ke `logs/<nama>_rewire.json` SEBELUM mengganti frame. |
| `figma_place.js` | **swap_nav + rewire 2 + link**: pasang tangkapan ke frame lama (ID/nama/posisi tetap) atau jadi frame baru; ganti sidebar dengan instance komponen peran (varian = garis aktif); pasang ulang reaction dari `CFG.snapshot.keluar` dengan mencocokkan teks (yang gagal → `tidakCocok`); `CFG.links` menambah tautan teks → frame | tempel ke `use_figma`, isi `CFG`. |
| `figma_navbar.js` | **swap_nav Pegawai**: buang header tangkapan ("Banner"), pasang instance **Navbar · Pegawai** `88:3` di induk & urutan yang sama, garis aktif (`CFG.aktif`: Tanya HaloSIS / Buat laporan / Laporan saya / Tanya Jawab (FAQ) / Riwayat percakapan), reaction menu → frame Section 01 (menu aktif tanpa reaction), Chip/BPS/Avatar disalin dari instance acuan | tempel ke `use_figma` SETELAH `figma_place.js` (nav.type tidak diisi); isi `CFG.frame`, `CFG.aktif`. |
| `figma_verify.js` | lintas peran, menggantung, self-link per Section + keterjangkauan Alur Demo 01→12 | tempel ke `use_figma` (read-only). |

Aturan rewire baris data (tiket, percakapan, artikel): sambungkan **per pola baris**, bukan per teks/ID. Semua elemen baris sejenis di satu tabel/daftar (kolom ID + judul tiket; tautan artikel; baris percakapan) diberi SATU tujuan yang sama dengan baris lain di daftar itu (mis. semua baris tiket PG-06 → PG-R05 detail tiket; semua tautan artikel PG-01 → PG-R01). Baris yang bergeser/bertambah karena data berubah (halaman daftar tiket berubah saat tiket baru dibuat) bukan kehilangan reaction. Elemen non-baris (Cari, Muat ulang, paginasi, tombol) tetap direwire per teks/nama lewat `figma_place.js`.
- Tangkapan beruntun dengan akun yang sama: jalankan `capture.js` SATU per satu (paralel → "Akses Ditolak").
- `steps/pg_form_kirim.js` (galat Judul wajib + hasil Kirim; membuat 1 tiket uji, id dicatat ke `logs/figma_testdata.json` → `testdata.js cleanup`), `steps/pg_chat_tidak.js` (env `Q`; membuat 1 chat uji → hapus chat id > baseline lewat skrip cleanup di logs/).

Catatan:
- `captureForDesign` kadang tidak kembali walau data terkirim; `capture.js` menunggu maks. 30 dtk lalu lanjut.
- Frame tangkapan berisi auto-layout: `figma_place.js` menjadikan instance sidebar `ABSOLUTE` agar tidak terdorong.
- Navbar Pegawai: pakai `figma_navbar.js` (garis aktif = override warna Rectangle oranye/putih; komponen 88:3 tanpa varian). Peringatan: halaman daftar tiket berubah bila data bertambah — baris yang bergeser dari halaman 1 membuat reaction lama tidak cocok (bukan galat alat).
- Ikon FontAwesome (bila ada) belum ditangani; hanya Tabler (`ti ti-*`).
- Pakai skill `figma-use` + `figma-generate-design` (nama di `skillNames`) saat memanggil `use_figma`.
