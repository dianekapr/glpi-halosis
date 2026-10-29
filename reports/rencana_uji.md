# Rencana uji performa & latensi HaloSIS (NFR-01, NFR-12)

Status: **rencana** + hasil satu pengguna. Uji beban penuh butuh lingkungan setara produksi BPS (lihat §7).

## 1. Tujuan

| Kode | Kebutuhan dokumen (§4.2.2) | Yang dibuktikan di sini |
| --- | --- | --- |
| NFR-01 | Pengujian portal dan API pada waktu normal, peak, dan stress overload yang telah ditetapkan | Skenario, beban, dan kriteria lulus untuk tiga kondisi; skrip k6 siap jalan |
| NFR-12 | Latensi AI untuk retrieval dan generation secara terpisah serta end-to-end | Sudah diukur per permintaan (`reports/latensi.md`); di sini ditambah latensi di bawah beban |

Dokumen tidak menetapkan angka beban atau target waktu respons. Angka di §3 dan §4 adalah **usulan tim**
dari data history tiket dan perlu disepakati dengan pemilik layanan BPS sebelum uji resmi.

## 2. Dasar perhitungan beban (data history)

| Data | Nilai | Sumber |
| --- | --- | --- |
| Tiket Jan–Agu 2026 | 6.682 tiket | Data history tiket |
| Rata-rata | ±27 tiket/hari kalender, ±40 tiket/hari kerja | 6.682 ÷ 243 hari; ÷ ±168 hari kerja |
| Jam sibuk (asumsi) | 20% tiket harian jatuh dalam 1 jam tersibuk → ±8 tiket/jam | Asumsi, perlu dicek dari kolom waktu buat tiket |
| Rasio chat : tiket (asumsi) | 3 percakapan chat per 1 tiket (sebagian selesai tanpa tiket, BR-06) | Asumsi |
| Pesan per percakapan (asumsi) | 3 pesan | Asumsi |

Dari angka di atas: jam sibuk ±8 tiket + ±24 percakapan × 3 pesan ≈ **72 permintaan `/chat` per jam**,
ditambah operator & tim teknis membuka daftar/tiket. Ini kecil, sehingga kondisi **peak** dan **stress** di
bawah sengaja dibuat berlipat agar ada ruang aman (mis. gangguan SSO massal yang memicu lonjakan laporan).

## 3. Kondisi beban

| Kondisi | Pengguna virtual (VU) bersamaan | Durasi | Gambaran |
| --- | ---: | --- | --- |
| Normal | 10 | 10 menit | Hari kerja biasa: pegawai bertanya, operator memvalidasi |
| Peak | 50 | 10 menit (naik bertahap 2 menit) | Lonjakan saat insiden massal (mis. SSO/FASIH bermasalah) |
| Stress | 50 → 200, naik 25 VU tiap 2 menit | sampai gagal / 20 menit | Mencari titik jenuh & memastikan sistem pulih |

Komposisi tiap VU (per iterasi, jeda 3–8 detik antar langkah agar menyerupai manusia):

| Peran | Porsi VU | Langkah |
| --- | ---: | --- |
| Pegawai | 70% | Login → buka Tanya HaloSIS → 3 pertanyaan chat → 30% di antaranya buat laporan |
| Operator | 15% | Login → Antrean validasi → buka 1 tiket (panel Saran AI) → Terima |
| Tim Teknis | 15% | Login → Tiket saya & tim → buka 1 tiket → tambah follow-up |

## 4. Kriteria lulus (usulan)

| Titik ukur | Normal | Peak | Stress |
| --- | --- | --- | --- |
| Halaman GLPI (daftar & tiket), p95 | ≤ 2 s | ≤ 3 s | dicatat |
| `/apirest.php` (buat tiket), p95 | ≤ 1 s | ≤ 2 s | dicatat |
| AI `/chat` retrieval (dalam layanan), p95 | ≤ 0,5 s | ≤ 1 s | dicatat |
| AI `/chat` end-to-end dari GLPI, p95 | ≤ 1,5 s | ≤ 3 s | dicatat |
| AI `/triage`, p95 | ≤ 0,2 s | ≤ 0,5 s | dicatat |
| Tingkat galat HTTP | < 1% | < 2% | titik jenuh = galat ≥ 5% atau p95 halaman > 10 s |
| Pemulihan | — | — | 2 menit setelah beban turun, p95 kembali ke angka Normal |
| Tiket tetap tersimpan saat AI lambat/mati | wajib | wajib | wajib (UC-03 alur alternatif) |

## 5. Alat & skrip

- **k6** (`brew install k6`) untuk beban HTTP; skrip ditaruh di `tests/load/` (usulan nama file di bawah).
- **Latensi AI** diambil dari `ai/logs/latency.jsonl` lalu diringkas dengan `ai/scripts/latency_report.py`,
  sehingga retrieval vs generation vs end-to-end tetap terpisah (NFR-12).
- **Sumber daya**: `docker stats --no-stream` tiap 30 detik ke file selama uji (CPU & memori `glpi`, `db`,
  `halosis-ai`).

Kerangka skrip `tests/load/halosis.js` (alur Pegawai; alur Operator/Tim Teknis mengikuti pola yang sama):

```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE || 'http://localhost:8080';
const AI = __ENV.AI || 'http://localhost:8001';

export const options = {
  scenarios: {
    normal: { executor: 'constant-vus', vus: 10, duration: '10m' },
    // peak:   { executor: 'ramping-vus', stages: [{ duration: '2m', target: 50 }, { duration: '8m', target: 50 }] },
    // stress: { executor: 'ramping-vus', stages: [ /* +25 VU tiap 2 menit sampai 200 */ ] },
  },
  thresholds: {
    'http_req_failed': ['rate<0.01'],
    'http_req_duration{tipe:ai_chat}': ['p(95)<500'],
    'http_req_duration{tipe:ai_triage}': ['p(95)<200'],
  },
};

const PERTANYAAN = ['kuota email saya penuh', 'tidak bisa login SSO', 'cara pengajuan cuti di SiPecut'];

export default function () {
  for (const q of PERTANYAAN) {
    const r = http.post(`${AI}/chat`, JSON.stringify({ pertanyaan: q }),
      { headers: { 'Content-Type': 'application/json' }, tags: { tipe: 'ai_chat' } });
    check(r, { 'chat 200': (x) => x.status === 200 });
    sleep(3 + Math.random() * 5);
  }
  const t = http.post(`${AI}/triage`, JSON.stringify({ judul: 'tidak bisa login SSO', deskripsi: 'muncul galat' }),
    { headers: { 'Content-Type': 'application/json' }, tags: { tipe: 'ai_triage' } });
  check(t, { 'triage 200': (x) => x.status === 200 });
}
```

Catatan skrip:
- Sesuaikan nama field JSON (`pertanyaan`, `judul`, `deskripsi`) dengan skema `ai/service/app.py`.
- Langkah halaman GLPI (login, daftar, buka tiket) memakai sesi `glpi_*` + token CSRF; untuk prototipe
  boleh dimulai dari `/apirest.php` (`initSession` → `Ticket` POST → `killSession`) dengan akun uji.
- **Jangan** memakai teks dari data history asli sebagai isi permintaan (PII); gunakan kalimat buatan.
- Jalankan: `k6 run tests/load/halosis.js` (Normal), lalu aktifkan skenario `peak` / `stress`.

## 6. Hasil satu pengguna (prototipe lokal)

Diukur di laptop pengembang (MacBook Air, Docker Desktop), 40 permintaan, di dalam layanan `halosis-ai`
(belum termasuk jaringan GLPI ↔ layanan). Sumber: `reports/latensi.md`.

| Titik ukur | Rata-rata | p50 | p95 | Maks | Target Normal | Lulus? |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| `/chat` retrieval | 150,7 ms | 91 ms | 453,8 ms | 691,8 ms | p95 ≤ 500 ms | ✅ |
| `/chat` generation | — | — | — | — | — | n/a (mode ekstraktif, tanpa LLM) |
| `/triage` | 15,5 ms | 13,2 ms | 23,6 ms | — | p95 ≤ 200 ms | ✅ |

Mode jawaban chat: ekstraktif 18, tidak ditemukan 2.

## 7. Hasil uji beban (diisi saat uji)

Lingkungan: ____ (CPU/RAM server, versi image, jumlah data tiket & potongan indeks) · Tanggal: ____ · Penguji: ____

| Kondisi | VU | Permintaan | Galat % | Halaman p95 | API tiket p95 | `/chat` e2e p95 | `/triage` p95 | CPU maks (glpi/db/ai) | Lulus? |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| Normal | 10 | | | | | | | | |
| Peak | 50 | | | | | | | | |
| Stress | sampai ___ | | | | | | | | titik jenuh: ___ VU |

Temuan & tindak lanjut:

| # | Temuan | Dampak | Tindak lanjut (mis. replika `halosis-ai`, indeks DB, cache) |
| --- | --- | --- | --- |
| 1 | | | |

## 8. Batasan

- Laptop pengembang tidak mewakili server BPS; angka uji lokal hanya untuk membandingkan antar versi.
- Uji ketersediaan (NFR-02) dan scale-out (NFR-04) di luar cakupan prototipe; rancangannya: replika
  `halosis-ai` di belakang load balancer (layanan sudah stateless kecuali indeks file), DB dengan replika baca.
- Uji tidak boleh diarahkan ke sistem produksi BPS tanpa izin pemilik layanan.
