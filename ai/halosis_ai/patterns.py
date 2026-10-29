"""Deteksi pola insiden semantik (BR-07, FR-04, UC-08): kelompokkan tiket baru yang maknanya mirip.

Embedding E5 memberi kosinus tinggi (±0,85–0,94) bahkan untuk tiket yang tidak berhubungan, sehingga ambang
PoC 0,70 (MiniLM) tidak bisa dipakai apa adanya. Vektor dipusatkan dulu (dikurangi rata-rata vektor indeks
pencarian) lalu dinormalkan; setelah itu rata-rata kemiripan tiket bertopik sama ±0,6 dan yang tidak
berhubungan ±0,4–0,47, sehingga ambang bawaan 0,50 (rata-rata ke semua anggota kelompok).

Pengelompokan rakus (tanpa DBSCAN): tiket urut waktu masuk ke kelompok dengan rata-rata kemiripan tertinggi ke
semua anggotanya, bila ≥ ambang dan masih dalam jendela waktu dari anggota pertama; selain itu membuka kelompok baru.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np

DEFAULT_THRESHOLD = 0.50
DEFAULT_MIN_MEMBERS = 3
DEFAULT_WINDOW_MINUTES = 60


def center(vectors: np.ndarray, mean: np.ndarray | None) -> np.ndarray:
    """Kurangi rata-rata korpus lalu normalkan ulang (kemiripan kosinus = hasil kali titik)."""
    out = vectors - mean if mean is not None else vectors.copy()
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    return out / np.where(norms == 0, 1, norms)


def group(tickets: list[dict], vectors: np.ndarray, threshold: float = DEFAULT_THRESHOLD,
          min_members: int = DEFAULT_MIN_MEMBERS, window_minutes: int = DEFAULT_WINDOW_MINUTES) -> list[dict]:
    """tickets[i] = {id, judul, waktu (ISO)}; vectors[i] = vektor ternormalisasi tiket i.

    Kembalikan kelompok ≥ min_members: {ids, judul_wakil, skor_rata}, urut dari yang terbesar.
    """
    order = sorted(range(len(tickets)), key=lambda i: str(tickets[i].get('waktu') or ''))
    window = timedelta(minutes=window_minutes)
    clusters: list[dict] = []
    for i in order:
        when = _parse(tickets[i].get('waktu'))
        best, best_score = None, threshold
        for cluster in clusters:
            if when and cluster['start'] and when - cluster['start'] > window:
                continue
            score = float(np.mean(vectors[cluster['members']] @ vectors[i]))
            if score >= best_score:
                best, best_score = cluster, score
        if best is None:
            clusters.append({'members': [i], 'start': when})
        else:
            best['members'].append(i)

    result = []
    for cluster in clusters:
        members = cluster['members']
        if len(members) < min_members:
            continue
        sims = vectors[members] @ vectors[members].T
        # Rata-rata kemiripan antar-anggota (tanpa diagonal); wakil = anggota paling mirip dengan yang lain
        pair_mean = (sims.sum(axis=1) - 1) / (len(members) - 1)
        result.append({
            'ids': [tickets[m]['id'] for m in members],
            'judul_wakil': tickets[members[int(np.argmax(pair_mean))]]['judul'],
            'skor_rata': round(float(pair_mean.mean()), 4),
        })
    return sorted(result, key=lambda c: len(c['ids']), reverse=True)


def _parse(value) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value).replace(' ', 'T')) if value else None
    except ValueError:
        return None
