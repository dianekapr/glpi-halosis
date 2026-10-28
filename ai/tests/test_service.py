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


def client(monkeypatch, hits):
    monkeypatch.setattr(service.search, 'cari', lambda q, k=3: hits)
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
