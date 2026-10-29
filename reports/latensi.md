# Latensi layanan AI HaloSIS (NFR-12)

Dibuat `ai/scripts/latency_report.py` · 2026-10-29 12:47 · 40 permintaan · periode 2026-10-29T05:47:28+00:00 s.d. 2026-10-29T05:47:31+00:00 (UTC)

Durasi diukur di dalam layanan `halosis-ai` (tanpa waktu jaringan GLPI ↔ layanan). Generation hanya ada bila jawaban dirangkum Claude; mode ekstraktif tidak memiliki langkah generation.

| Langkah | n | Rata-rata (ms) | p50 (ms) | p95 (ms) | Maks (ms) |
| --- | ---: | ---: | ---: | ---: | ---: |
| Chat · retrieval | 20 | 150.7 | 91.0 | 453.8 | 691.8 |
| Chat · generation (Claude) | 0 | – | – | – | – |
| Chat · end-to-end | 20 | 150.7 | 91.1 | 453.8 | 691.8 |
| Triase · inferensi + tiket mirip | 20 | 15.5 | 13.2 | 23.6 | 51.3 |
| Triase · end-to-end | 20 | 15.5 | 13.2 | 23.6 | 51.3 |

Mode jawaban chat: ekstraktif 18, tidak-ditemukan 2.
