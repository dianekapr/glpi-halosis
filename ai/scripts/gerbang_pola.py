"""Set uji gerbang pola → ai/index/pola_uji.npz (angka saja, tanpa teks) + bukti parameter acuan.

Set sama dengan reports/banding_pola.md: insiden history Jul–Ags 2026, teks & embedding seperti POST /pola. Berkas
berisi vektor e5 (belum dipusatkan), waktu, dan nomor tim anonim. halosis-ai memakainya di POST /gerbang untuk menilai
parameter aktif Pengaturan AI; gerbang ini peringatan saja (tata_kelola_ai.md §2).

Pakai: .venv/bin/python ai/scripts/gerbang_pola.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import patterns, privacy, quality, search  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data/processed/tickets_clean.parquet'
OUT = search.INDEX_DIR / 'pola_uji.npz'
START, END = pd.Timestamp('2026-07-01'), pd.Timestamp('2026-09-01')
REFERENCE = [('rata 0,50', {'metode': 'rata', 'threshold': 0.50}),
             ('dbscan eps 0,50', {'metode': 'dbscan', 'eps': 0.50, 'min_samples': 3}),
             ('dbscan eps 0,40', {'metode': 'dbscan', 'eps': 0.40, 'min_samples': 3})]


def main() -> None:
    df = pd.read_parquet(SRC, columns=['ticket_type', 'short_description', 'description', 'assignment_group_name', 'opened'])
    df['opened'] = pd.to_datetime(df['opened'], errors='coerce')
    df = df[df['ticket_type'].astype(str).str.upper().str.startswith('INC') & df['opened'].between(START, END, inclusive='left')]
    df = df.sort_values('opened', kind='stable').reset_index(drop=True)
    texts = [str(privacy.mask_text(f'{t or ""}. {str(d or "")[:300]}')) for t, d in zip(df['short_description'], df['description'])]
    vectors = search.embed(texts, 'query')
    times = df['opened'].dt.strftime('%Y-%m-%d %H:%M:%S').to_numpy(dtype='U19')
    teams = pd.factorize(df['assignment_group_name'].astype('string').fillna('(kosong)'))[0]
    np.savez_compressed(OUT, vektor=vectors, waktu=times, tim=teams)
    mean = search.load_index()[1].mean(axis=0)
    centered = patterns.center(vectors, mean)
    print(f'Set uji: {len(df)} insiden → {OUT.relative_to(ROOT)}')
    for name, params in REFERENCE:
        result = patterns.replay(list(times), centered, teams, **params)
        print(name, result, 'lolos' if quality.check('pola', result)['lolos'] else 'peringatan')


if __name__ == '__main__':
    main()
