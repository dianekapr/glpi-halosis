"""Solusi yang sering berulang di history tiket → kandidat knowledge (UC-09, BP-16).

Solusi tiket (sudah tersamar, dari indeks pencarian AI-4) dikelompokkan dengan TF-IDF + kosinus secara
greedy: tiket dengan tetangga mirip terbanyak menjadi pusat klaster, anggotanya tidak dipakai lagi.
Klaster dengan anggota ≥ min_size dikembalikan, terbesar dulu. Indeks menggabungkan solusi identik menjadi satu
potongan (kolom `jumlah_tiket`, `tiket`), jadi anggota dihitung per tiket, bukan per potongan.
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

SIMILARITY = 0.75
# Solusi pusat klaster minimal sekian kata; jawaban pendek ("sudah dibantu") tidak layak jadi artikel
MIN_WORDS = 10


def _split(text: str) -> tuple[str, str]:
    """Teks potongan tiket 'Masalah: … Solusi: …' → (masalah, solusi)."""
    match = re.match(r'\s*Masalah:\s*(.*?)\s*Solusi:\s*(.*)\s*$', text, flags=re.S)
    return (match.group(1), match.group(2)) if match else ('', text)


def recurring_solutions(chunks: pd.DataFrame, min_size: int = 5, limit: int = 20,
                        similarity: float = SIMILARITY) -> list[dict]:
    # Potongan lanjutan (solusi > 220 kata dipecah) punya sumber sama: satu baris per tiket/solusi
    tickets = chunks[chunks['jenis_sumber'] == 'tiket'].drop_duplicates('sumber').reset_index(drop=True)
    if tickets.empty:
        return []
    if 'solusi' in tickets:
        parts = [(str(m), str(v)) for m, v in zip(tickets['masalah'].fillna(''), tickets['solusi'].fillna(''))]
    else:
        parts = [_split(str(t)) for t in tickets['teks']]
    solutions = [s.lower() for _, s in parts]
    weights = (tickets['jumlah_tiket'].fillna(1).astype(int) if 'jumlah_tiket' in tickets
               else pd.Series(1, index=tickets.index)).to_numpy()
    numbers = [str(t).split(',') if 'tiket' in tickets and isinstance(t, str) and t else [str(s)]
               for t, s in zip(tickets['tiket'] if 'tiket' in tickets else tickets['sumber'], tickets['sumber'])]

    # min_df=1: solusi identik sudah digabung, jadi kata khas solusi itu muncul di satu baris saja
    matrix = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True).fit_transform(solutions)
    neighbors = (matrix @ matrix.T).toarray() >= similarity
    order = np.argsort(-(neighbors * weights).sum(axis=1), kind='stable')

    used = np.zeros(len(tickets), dtype=bool)
    clusters = []
    for center in order:
        if used[center] or len(parts[center][1].split()) < MIN_WORDS:
            continue
        members = np.flatnonzero(neighbors[center] & ~used)
        if weights[members].sum() < min_size:
            continue
        used[members] = True
        problem, solution = parts[center]
        clusters.append({
            'kunci': f'ai:{tickets.at[center, "sumber"]}',
            'judul': str(tickets.at[center, 'judul']).strip().split('\n', 1)[0][:120],
            'masalah': problem[:1000],
            'solusi': solution[:2000],
            'jumlah': int(weights[members].sum()),
            'contoh_tiket': [n for i in members for n in numbers[i]][:5],
        })
        if len(clusters) >= limit:
            break
    return sorted(clusters, key=lambda c: -c['jumlah'])
