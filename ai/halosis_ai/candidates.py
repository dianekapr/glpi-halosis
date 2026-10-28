"""Solusi yang sering berulang di history tiket → kandidat knowledge (UC-09, BP-16).

Solusi tiket (sudah tersamar, dari indeks pencarian AI-4) dikelompokkan dengan TF-IDF + kosinus secara
greedy: tiket dengan tetangga mirip terbanyak menjadi pusat klaster, anggotanya tidak dipakai lagi.
Klaster dengan anggota ≥ min_size dikembalikan, terbesar dulu.
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
    tickets = chunks[chunks['jenis_sumber'] == 'tiket'].reset_index(drop=True)
    if tickets.empty:
        return []
    parts = [_split(str(t)) for t in tickets['teks']]
    solutions = [s.lower() for _, s in parts]

    matrix = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True).fit_transform(solutions)
    neighbors = (matrix @ matrix.T).toarray() >= similarity
    order = np.argsort(-neighbors.sum(axis=1), kind='stable')

    used = np.zeros(len(tickets), dtype=bool)
    clusters = []
    for center in order:
        if used[center] or len(parts[center][1].split()) < MIN_WORDS:
            continue
        members = np.flatnonzero(neighbors[center] & ~used)
        if len(members) < min_size:
            continue
        used[members] = True
        problem, solution = parts[center]
        clusters.append({
            'kunci': f'ai:{tickets.at[center, "sumber"]}',
            'judul': str(tickets.at[center, 'judul']).strip().split('\n', 1)[0][:120],
            'masalah': problem[:1000],
            'solusi': solution[:2000],
            'jumlah': int(len(members)),
            'contoh_tiket': [str(tickets.at[i, 'sumber']) for i in members[:5]],
        })
        if len(clusters) >= limit:
            break
    return sorted(clusters, key=lambda c: -c['jumlah'])
