"""Tes endpoint layanan AI dengan model & pencarian tiruan (tanpa data history, tanpa memuat model)."""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from service import app as service  # noqa: E402


class FakeTriage:
    version = 'uji-v1'

    def predict(self, title, description, ticket_type):
        self.seen = (title, description, ticket_type)
        return {'tim': 'SSO', 'keyakinan': 0.8, 'perlu_penilaian_manual': False,
                'top3': [{'tim': 'SSO', 'keyakinan': 0.8}], 'tiket_mirip': [], 'versi_model': self.version}


def client(monkeypatch, hits, tmp_log=None):
    monkeypatch.setattr(service.search, 'cari', lambda q, k=3: hits)
    monkeypatch.setattr(service, 'LATENCY_LOG', tmp_log or Path('/dev/null'))
    monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
    service.state.clear()
    service.state.update({'triage': FakeTriage(), 'search': True})
    return TestClient(service.app)  # tanpa "with": lifespan (muat model asli) tidak dijalankan


def test_triage_dan_normalisasi_jenis(monkeypatch):
    c = client(monkeypatch, [])
    r = c.post('/triage', json={'judul': 'SSO gagal', 'deskripsi': 'x', 'jenis': 'Permintaan'}).json()
    assert r['tim'] == 'SSO' and r['versi_model'] == 'uji-v1' and 'tiket_mirip' in r['penjelasan']
    assert service.state['triage'].seen[2] == 'REQ'


def test_chat_skor_rendah_belum_ditemukan(monkeypatch):
    c = client(monkeypatch, [{'potongan': 'a', 'skor': 0.5, 'sumber': 'T1', 'jenis_sumber': 'tiket', 'judul': 'j'}])
    r = c.post('/chat', json={'pertanyaan': 'resep nasi goreng'}).json()
    assert r['ditemukan'] is False and r['sumber'] == []


def test_chat_ekstraktif_tanpa_key(monkeypatch):
    hit = {'potongan': 'Masalah: email penuh Solusi: hapus lampiran besar', 'skor': 0.9, 'sumber': 'T1',
           'jenis_sumber': 'tiket', 'judul': 'Email penuh'}
    c = client(monkeypatch, [hit, {**hit, 'sumber': 'T2'}])
    r = c.post('/chat', json={'pertanyaan': 'email penuh'}).json()
    assert r['ditemukan'] and r['mode'] == 'ekstraktif'
    assert 'hapus lampiran besar' in r['jawaban'] and [s['sumber'] for s in r['sumber']] == ['T1']


def test_log_latensi_tanpa_teks(monkeypatch, tmp_path):
    import json
    log_file = tmp_path / 'latency.jsonl'
    hit = {'potongan': 'Solusi: reset', 'skor': 0.9, 'sumber': 'KB1', 'jenis_sumber': 'kb', 'judul': 'Reset SSO'}
    c = client(monkeypatch, [hit], log_file)
    c.post('/chat', json={'pertanyaan': 'lupa password budi@contoh.go.id'})
    c.post('/triage', json={'judul': 'SSO gagal', 'deskripsi': 'tidak bisa login'})
    rows = [json.loads(line) for line in log_file.read_text().splitlines()]
    assert [r['endpoint'] for r in rows] == ['chat', 'triage']
    assert rows[0]['retrieval_ms'] >= 0 and rows[0]['total_ms'] >= rows[0]['retrieval_ms']
    assert rows[0]['generation_ms'] is None and rows[0]['skor_teratas'] == 0.9
    assert rows[1]['skor_teratas'] == 0.8
    text = log_file.read_text()
    for secret in ('budi', 'password', 'SSO gagal', 'Reset SSO'):
        assert secret not in text


def test_metrics_prometheus(monkeypatch):
    c = client(monkeypatch, [])
    c.post('/triage', json={'judul': 'SSO gagal rahasia-uji'})
    r = c.get('/metrics')
    assert r.status_code == 200
    for name in ('halosis_ai_requests_total', 'halosis_ai_request_duration_seconds', 'halosis_ai_index_chunks'):
        assert name in r.text
    assert 'endpoint="/triage"' in r.text and 'rahasia-uji' not in r.text
