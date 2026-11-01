"""Tes deteksi pola semantik: "lemot" dan "lambat" satu kelompok, topik lain terpisah. Data rekaan.

Memakai model embedding asli bila sudah terunduh (lewati bila belum tersedia)."""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import patterns, search  # noqa: E402


def test_lemot_dan_lambat_satu_kelompok():
    try:
        index_mean = search.load_index()[1].mean(axis=0)
        search.encoder()
    except Exception:  # noqa: BLE001
        pytest.skip('Model embedding / indeks belum tersedia')
    tickets = [
        {'id': 1, 'judul': 'Internet kantor lemot sejak pagi', 'waktu': '2026-10-29 08:00:00'},
        {'id': 2, 'judul': 'Koneksi internet lambat sekali', 'waktu': '2026-10-29 08:10:00'},
        {'id': 3, 'judul': 'Jaringan wifi lemot tidak bisa buka web', 'waktu': '2026-10-29 08:20:00'},
        {'id': 4, 'judul': 'Printer tidak bisa mencetak dokumen', 'waktu': '2026-10-29 08:25:00'},
        {'id': 5, 'judul': 'Lupa password SSO tidak bisa login', 'waktu': '2026-10-29 08:30:00'},
        {'id': 6, 'judul': 'Koneksi internet lambat', 'waktu': '2026-10-29 10:30:00'},  # di luar jendela 60 menit
    ]
    vectors = patterns.center(search.embed([t['judul'] for t in tickets], 'query'), index_mean)
    groups = patterns.group(tickets, vectors, min_members=3, window_minutes=60)
    assert [g['ids'] for g in groups] == [[1, 2, 3]]
    assert groups[0]['skor_rata'] >= patterns.DEFAULT_THRESHOLD


def test_dbscan_kelompok_sama_dan_jendela_waktu():
    """Metode DBSCAN (PoC): kelompok sintetis terpisah jelas, anggota di luar jendela 60 menit dibuang."""
    rng = np.random.default_rng(0)
    base = rng.normal(size=(3, 16))
    rows = [base[0] + 0.05 * rng.normal(size=16) for _ in range(4)] + [base[1] + 0.05 * rng.normal(size=16) for _ in range(2)]
    rows += [base[2]]
    vectors = np.array(rows) / np.linalg.norm(rows, axis=1, keepdims=True)
    times = ['08:00', '08:10', '08:20', '10:30', '08:05', '08:15', '08:25']
    tickets = [{'id': i + 1, 'judul': f't{i + 1}', 'waktu': f'2026-10-29 {w}:00'} for i, w in enumerate(times)]
    groups = patterns.group_dbscan(tickets, vectors, eps=0.1, min_samples=2, min_members=3, window_minutes=60)
    assert [g['ids'] for g in groups] == [[1, 2, 3]]  # #4 di luar jendela; kelompok #5-#6 < 3 anggota
    assert patterns.group_dbscan(tickets[:1], vectors[:1]) == []

