"""Tes pencarian dengan indeks rekaan; embedding diganti vektor tetap (tanpa memuat model)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import search  # noqa: E402


def test_cari_urut_skor_dan_menyamarkan_query(tmp_path, monkeypatch):
    pd.DataFrame({
        'sumber': ['KB-1', 'T-001', 'T-002'], 'jenis_sumber': ['kb', 'tiket', 'tiket'],
        'judul': ['SSO', 'Email', 'Zoom'], 'teks': ['reset SSO', 'kuota email', 'link zoom'],
    }).to_parquet(tmp_path / 'chunks.parquet')
    np.save(tmp_path / 'vectors.npy', np.eye(3, dtype=np.float32))

    seen = []
    def fake_embed(texts, kind):
        seen.extend(texts)
        return np.array([[0.1, 0.9, 0.3]], dtype=np.float32)
    monkeypatch.setattr(search, 'embed', fake_embed)

    hasil = search.cari('email saya budi@bps.go.id penuh', k=2, index_dir=tmp_path)
    assert [h['sumber'] for h in hasil] == ['T-001', 'T-002']
    assert hasil[0]['skor'] > hasil[1]['skor']
    assert 'budi@bps.go.id' not in seen[0]
