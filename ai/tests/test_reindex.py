"""Tes re-index artikel KB (UC-09 langkah 7): artikel baru langsung ditemukan /chat, setelah dihapus tidak.

Indeks & embedding tiruan (folder sementara, embedding bag-of-words) — tanpa model asli dan tanpa ai/index."""
import sys
import zlib
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import search  # noqa: E402
from service import app as service  # noqa: E402


def fake_embed(texts, kind):
    out = np.zeros((len(texts), 256), dtype=np.float32)
    for row, text in enumerate(texts):
        for word in text.lower().replace('.', ' ').replace(':', ' ').split():
            if word not in ('query', 'passage'):
                out[row, zlib.crc32(word.encode()) % 256] += 1
    return out / np.maximum(np.linalg.norm(out, axis=1, keepdims=True), 1e-9)


def test_artikel_baru_ditemukan_lalu_hilang(monkeypatch, tmp_path):
    monkeypatch.setattr(search, 'embed', fake_embed)
    monkeypatch.setattr(search, 'INDEX_DIR', tmp_path)
    search._indexes.clear()
    history = pd.DataFrame([{'sumber': 'T1', 'jenis_sumber': 'tiket', 'judul': 'Email penuh',
                             'teks': 'Masalah: email penuh Solusi: hapus lampiran besar'}])
    history.to_parquet(tmp_path / 'chunks.parquet', index=False)
    np.save(tmp_path / 'vectors.npy', fake_embed(history['teks'].tolist(), 'passage'))

    monkeypatch.setattr(service, 'LATENCY_LOG', tmp_path / 'latency.jsonl')
    monkeypatch.setattr(service, 'CHAT_MIN_SCORE', 0.5)
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    service.state.clear()
    service.state['search'] = True
    client = TestClient(service.app)
    ask = lambda: client.post('/chat', json={'pertanyaan': 'printer macet kertas'}).json()  # noqa: E731

    assert ask()['ditemukan'] is False
    r = client.post('/reindex/artikel', json={'id': 42, 'judul': 'Printer macet kertas',
                                              'isi': '<p>Buka penutup printer lalu tarik kertas yang macet.</p>',
                                              'aksi': 'simpan'})
    assert r.json() == {'ok': True, 'aksi': 'simpan', 'potongan': 1}
    found = ask()
    assert found['ditemukan'] and found['sumber'][0]['sumber'] == 'KB-42'

    client.post('/reindex/artikel', json={'id': 42, 'aksi': 'hapus'})
    assert ask()['ditemukan'] is False
    # Disimpan ke disk (atomik) dan potongan tiket historis tetap
    saved = pd.read_parquet(tmp_path / 'chunks.parquet')
    assert saved['sumber'].tolist() == ['T1'] and len(np.load(tmp_path / 'vectors.npy')) == 1
    assert not list(tmp_path.glob('.*.tmp'))


def test_katalog_layanan_diindeks_dan_diganti(monkeypatch, tmp_path):
    """BR-03: katalog layanan masuk indeks, chatbot mengarahkan ke layanan; sinkron ulang mengganti seluruhnya."""
    monkeypatch.setattr(search, 'embed', fake_embed)
    monkeypatch.setattr(search, 'INDEX_DIR', tmp_path)
    search._indexes.clear()
    history = pd.DataFrame([{'sumber': 'T1', 'jenis_sumber': 'tiket', 'judul': 'Email penuh',
                             'teks': 'Masalah: email penuh Solusi: hapus lampiran besar'}])
    history.to_parquet(tmp_path / 'chunks.parquet', index=False)
    np.save(tmp_path / 'vectors.npy', fake_embed(history['teks'].tolist(), 'passage'))
    monkeypatch.setattr(service, 'LATENCY_LOG', tmp_path / 'latency.jsonl')
    monkeypatch.setattr(service, 'CHAT_MIN_SCORE', 0.5)
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    service.state.clear()
    service.state['search'] = True
    client = TestClient(service.app)

    r = client.post('/reindex/layanan', json={'layanan': [
        {'id': 'F3', 'nama': 'Permintaan akun Zoom', 'deskripsi': '<p>Ajukan akun zoom untuk rapat daring</p>'},
        {'id': 'C7', 'nama': 'Printer', 'deskripsi': 'Kerusakan printer kantor'}]})
    assert r.json() == {'ok': True, 'potongan': 2}
    answer = client.post('/chat', json={'pertanyaan': 'ajukan akun zoom rapat daring'}).json()
    assert answer['ditemukan'] and answer['sumber'][0]['sumber'] == 'LAYANAN-F3'
    assert 'katalog layanan' in answer['jawaban']

    client.post('/reindex/layanan', json={'layanan': [{'id': 'C7', 'nama': 'Printer', 'deskripsi': ''}]})
    saved = pd.read_parquet(tmp_path / 'chunks.parquet')
    assert saved['sumber'].tolist() == ['T1', 'LAYANAN-C7']
    assert client.post('/reindex/layanan', json={'layanan': [{'id': 'X1', 'nama': 'x'}]}).status_code == 422



def test_artikel_internal_hanya_untuk_cari(monkeypatch, tmp_path):
    """chat=false → jenis 'kb_internal': ditemukan /cari (semua jenis), TIDAK dijawab /chat; chat=true memindahkannya."""
    monkeypatch.setattr(search, 'embed', fake_embed)
    monkeypatch.setattr(search, 'INDEX_DIR', tmp_path)
    search._indexes.clear()
    history = pd.DataFrame([{'sumber': 'T1', 'jenis_sumber': 'tiket', 'judul': 'Email penuh',
                             'teks': 'Masalah: email penuh Solusi: hapus lampiran besar'}])
    history.to_parquet(tmp_path / 'chunks.parquet', index=False)
    np.save(tmp_path / 'vectors.npy', fake_embed(history['teks'].tolist(), 'passage'))
    monkeypatch.setattr(service, 'LATENCY_LOG', tmp_path / 'latency.jsonl')
    monkeypatch.setattr(service, 'CHAT_MIN_SCORE', 0.5)
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    service.state.clear()
    service.state['search'] = True
    client = TestClient(service.app)
    ask = lambda: client.post('/chat', json={'pertanyaan': 'restart sinkronisasi fasih'}).json()  # noqa: E731
    body = {'id': 7, 'judul': 'Restart sinkronisasi FASIH', 'isi': '<p>Jalankan restart layanan sinkronisasi FASIH.</p>',
            'aksi': 'simpan'}

    client.post('/reindex/artikel', json={**body, 'chat': False})
    assert ask()['ditemukan'] is False
    assert [h['jenis_sumber'] for h in search.cari('restart sinkronisasi fasih', k=1)] == ['kb_internal']
    assert client.post('/cari', json={'q': 'restart sinkronisasi fasih', 'k': 1}).json()['hasil'][0]['sumber'] == 'KB-7'

    client.post('/reindex/artikel', json={**body, 'chat': True})  # jadi FAQ bertarget → terlihat pegawai
    assert ask()['sumber'][0]['sumber'] == 'KB-7'
    client.post('/reindex/artikel', json={**body, 'chat': False})  # FAQ dicabut / target dihapus → keluar dari /chat
    assert ask()['ditemukan'] is False
    assert sorted(pd.read_parquet(tmp_path / 'chunks.parquet')['sumber']) == ['KB-7', 'T1']  # tetap di /cari
