"""NFR-12: ringkasan latensi layanan AI dari ai/logs/latency.jsonl → reports/latensi.md.

Log ditulis ai/service/app.py per permintaan /chat dan /triage (hanya angka; tanpa teks pengguna).
Pakai (dari folder induk proyek):  .venv/bin/python ai/scripts/latency_report.py [path-log]
"""
from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'ai/logs/latency.jsonl'
REPORT = ROOT / 'reports/latensi.md'
# (endpoint, kolom durasi, label)
METRICS = [
    ('chat', 'retrieval_ms', 'Chat · retrieval'),
    ('chat', 'generation_ms', 'Chat · generation (Claude)'),
    ('chat', 'total_ms', 'Chat · end-to-end'),
    ('triage', 'inferensi_ms', 'Triase · inferensi + tiket mirip'),
    ('triage', 'total_ms', 'Triase · end-to-end'),
]


def percentile(values: list[float], p: float) -> float:
    """Persentil dengan interpolasi linear (p dalam 0–100)."""
    ordered = sorted(values)
    k = (len(ordered) - 1) * p / 100
    low, high = int(k), min(int(k) + 1, len(ordered) - 1)
    return ordered[low] + (ordered[high] - ordered[low]) * (k - low)


def summarize(entries: list[dict]) -> list[str]:
    rows = ['| Langkah | n | Rata-rata (ms) | p50 (ms) | p95 (ms) | Maks (ms) |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    for endpoint, field, label in METRICS:
        values = [e[field] for e in entries if e.get('endpoint') == endpoint and isinstance(e.get(field), (int, float))]
        if not values:
            rows.append(f'| {label} | 0 | – | – | – | – |')
            continue
        rows.append(f'| {label} | {len(values)} | {statistics.mean(values):.1f} | {percentile(values, 50):.1f} | '
                    f'{percentile(values, 95):.1f} | {max(values):.1f} |')
    return rows


def main() -> None:
    if not LOG.exists():
        raise SystemExit(f'Log belum ada: {LOG}. Pakai chatbot/triase dulu (layanan halosis-ai menulis log ini).')
    entries = [json.loads(line) for line in LOG.read_text(encoding='utf-8').splitlines() if line.strip()]
    chat = [e for e in entries if e.get('endpoint') == 'chat']
    modes = {}
    for e in chat:
        modes[e.get('mode')] = modes.get(e.get('mode'), 0) + 1
    period = f'{entries[0]["waktu"]} s.d. {entries[-1]["waktu"]}' if entries else '–'
    lines = [
        '# Latensi layanan AI HaloSIS (NFR-12)',
        '',
        f'Dibuat `ai/scripts/latency_report.py` · {datetime.now():%Y-%m-%d %H:%M} · {len(entries)} permintaan · periode {period} (UTC)',
        '',
        'Durasi diukur di dalam layanan `halosis-ai` (tanpa waktu jaringan GLPI ↔ layanan). Generation hanya ada '
        'bila jawaban dirangkum Claude; mode ekstraktif tidak memiliki langkah generation.',
        '',
        *summarize(entries),
        '',
        f'Mode jawaban chat: {", ".join(f"{k} {v}" for k, v in sorted(modes.items(), key=str)) or "–"}.',
        '',
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(lines), encoding='utf-8')
    print(f'{len(entries)} permintaan → {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
