"""Tes pencarian dengan indeks rekaan; embedding diganti vektor tetap (tanpa memuat model)."""
import pytest
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

    hasil = search.cari('email saya budi@contoh.go.id penuh', k=2, index_dir=tmp_path)
    assert [h['sumber'] for h in hasil] == ['T-001', 'T-002']
    assert hasil[0]['skor'] > hasil[1]['skor']
    assert 'budi@contoh.go.id' not in seen[0]


def test_cari_satu_hasil_per_sumber_dengan_solusi_utuh(tmp_path, monkeypatch):
    pd.DataFrame({
        'sumber': ['T-001', 'T-001', 'T-002'], 'jenis_sumber': ['tiket'] * 3, 'judul': ['Email'] * 2 + ['Zoom'],
        'teks': ['Masalah: email Solusi: b1', 'Masalah: a Solusi: b2', 'Masalah: c Solusi: d'],
        'masalah': ['a', 'a', 'c'], 'solusi': ['b1 b2', 'b1 b2', 'd'],
    }).to_parquet(tmp_path / 'chunks.parquet')
    np.save(tmp_path / 'vectors.npy', np.eye(3, dtype=np.float32))
    monkeypatch.setattr(search, 'embed', lambda texts, kind: np.array([[0.9, 0.8, 0.1]], dtype=np.float32))
    hasil = search.cari('email', k=2, index_dir=tmp_path)
    assert [h['sumber'] for h in hasil] == ['T-001', 'T-002']
    assert hasil[0]['solusi'] == 'b1 b2'


def test_cari_filter_jenis_sumber(tmp_path, monkeypatch):
    """A.1: filter jenis (/chat) menyingkirkan potongan tiket walau skornya tertinggi; tanpa filter tetap ikut."""
    pd.DataFrame({'sumber': ['T-1', 'KB-1'], 'jenis_sumber': ['tiket', 'kb'], 'judul': ['a', 'b'], 'teks': ['kata uji a', 'kata uji b']})\
        .to_parquet(tmp_path / 'chunks.parquet')
    np.save(tmp_path / 'vectors.npy', np.array([[1.0, 0.0], [0.6, 0.8]], dtype=np.float32))
    monkeypatch.setattr(search, 'embed', lambda texts, kind: np.array([[1.0, 0.0]], dtype=np.float32))
    assert [h['sumber'] for h in search.cari('kata uji', k=2, index_dir=tmp_path)] == ['T-1', 'KB-1']
    assert [h['sumber'] for h in search.cari('kata uji', k=2, index_dir=tmp_path, jenis=('kb', 'layanan'))] == ['KB-1']


# ---- Guard kueri berbasis kosakata indeks (E1 lanjutan) ----
@pytest.fixture(scope='module')
def indeks_nyata():
    if not (search.INDEX_DIR / 'chunks.parquet').exists():
        pytest.skip('indeks nyata (ai/index) tidak ada')
    return search.INDEX_DIR


@pytest.mark.parametrize('q', ['cnfhjkcnfjkancfkww', 'asdfgh qwerty', 'yang apa', '<<>>', '123'])
def test_bermakna_menolak(q, indeks_nyata):
    assert search.bermakna(q, indeks_nyata) is False


@pytest.mark.parametrize('q', ['pasword sso', 'wfi kantor putus', 'printer macet', 'VPN', 'lupa sandi email'])
def test_bermakna_menerima(q, indeks_nyata):
    assert search.bermakna(q, indeks_nyata) is True


def test_bermakna_kasus_retrieval_poc(indeks_nyata):
    import json
    kasus = json.loads((Path(__file__).resolve().parents[1] / 'scripts' / 'kasus_retrieval_poc.json').read_text())['kasus']
    assert len(kasus) == 8
    assert all(search.bermakna(k['pertanyaan'], indeks_nyata) for k in kasus)
