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


def test_cari_semantik_agent(monkeypatch):
    seen = {}
    hits = [{'potongan': 'Solusi: reset', 'skor': 0.71, 'sumber': 'KB1', 'jenis_sumber': 'kb', 'judul': 'Reset SSO'}]
    c = client(monkeypatch, hits)
    monkeypatch.setattr(service.search, 'cari', lambda q, k=3: seen.update(q=q, k=k) or hits)
    r = c.post('/cari', json={'q': 'sso budi@contoh.go.id', 'k': 5})
    assert r.status_code == 200 and r.json()['hasil'][0]['sumber'] == 'KB1'
    assert seen['k'] == 5 and 'budi@contoh.go.id' not in seen['q']  # disamarkan sebelum dicari


def test_chat_keyakinan_sedang_menawarkan_pilihan(monkeypatch):
    kb = {'potongan': 'langkah', 'jenis_sumber': 'kb', 'judul': 'Reset password SSO'}
    hits = [{**kb, 'skor': 0.80, 'sumber': 'KB-2'}, {**kb, 'skor': 0.79, 'sumber': 'KB-2'},
            {**kb, 'skor': 0.79, 'sumber': 'KB-6', 'judul': 'Lampiran email'},
            {'potongan': 'x', 'skor': 0.81, 'sumber': 'T9', 'jenis_sumber': 'tiket', 'judul': 'tiket'},
            {**kb, 'skor': 0.70, 'sumber': 'KB-4'}]
    body = client(monkeypatch, hits).post('/chat', json={'pertanyaan': 'sso error', 'riwayat': []}).json()
    assert body['ditemukan'] is False and body['mode'] == 'pilihan'
    assert [p['sumber'] for p in body['pilihan']] == ['KB-2', 'KB-6']  # hanya KB, tanpa duplikat, ≥ 0,78
    assert body['sumber'] == []  # tidak mengarang jawaban


class FakeJenis:
    classes_ = ['INC', 'REQ']

    def predict_proba(self, texts):
        return [[0.2, 0.8]] if 'akun zoom' in texts[0] else [[0.9, 0.1]]


def test_triage_saran_jenis_opsional(monkeypatch):
    """T4: tanpa model jenis → jenis_saran None (tidak error); dengan model → jenis + keyakinan."""
    c = client(monkeypatch, [])
    assert c.post('/triage', json={'judul': 'Minta akun zoom', 'deskripsi': 'rapat'}).json()['jenis_saran'] is None
    service.state['jenis'] = {'pipeline': FakeJenis(), 'version': 'jenis-uji',
                              'metrics': {'f1_makro': 0.67, 'f1_makro_pembanding': 0.36}}
    r = c.post('/triage', json={'judul': 'Minta akun zoom', 'deskripsi': 'rapat', 'jenis': 'INC'}).json()
    assert r['jenis_saran'] == {'jenis': 'REQ', 'keyakinan': 0.8, 'versi_model': 'jenis-uji'}


def test_rate_limit_per_klien(monkeypatch):
    """T26: klien melewati batas → 429 + Retry-After; /health tetap; klien lain tidak terpengaruh."""
    c = client(monkeypatch, [])
    monkeypatch.setattr(service, 'RATE_LIMIT', 3)
    service._hits.clear()
    codes = [c.post('/triage', json={'judul': 'x'}).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    r = c.post('/triage', json={'judul': 'x'})
    assert r.status_code == 429 and int(r.headers['Retry-After']) >= 1
    assert c.get('/health').status_code == 200
    assert service.rate_limited('klien-lain', 0.0) == 0
    service._hits.clear()


def test_gerbang_kualitas_model(monkeypatch):
    """T32: metrik artefak di bawah syarat → /health & /triage menyatakan tidak lolos."""
    c = client(monkeypatch, [])
    model = service.state['triage']
    monkeypatch.setattr(model, 'metadata', {'top1': 0.74, 'akurasi_yakin': 0.87, 'recall_tim_besar_min': 0.78}, raising=False)
    assert c.get('/health').json()['kualitas_model']['triase']['lolos'] is True
    assert c.post('/triage', json={'judul': 'x'}).json()['lolos_uji_kualitas'] is True
    monkeypatch.setattr(model, 'metadata', {'top1': 0.55, 'akurasi_yakin': 0.80, 'recall_tim_besar_min': 0.3}, raising=False)
    gate = c.get('/health').json()['kualitas_model']['triase']
    assert gate['lolos'] is False and len(gate['alasan']) == 3 and gate['syarat']['recall_tim_besar'] == 'gagal'
    assert c.post('/triage', json={'judul': 'x'}).json()['lolos_uji_kualitas'] is False


def test_prioritas_hanya_bila_lolos_dan_yakin(monkeypatch):
    """Saran prioritas insiden: model tidak unggul pembanding → None; unggul & yakin → prioritas GLPI; REQ → None."""
    c = client(monkeypatch, [])
    artifact = {'pipeline': FakeJenis(), 'version': 'prio-uji', 'threshold': 0.7, 'prioritas_glpi': {'INC': 3, 'REQ': 2},
                'metrics': {'f1_makro': 0.448, 'f1_makro_pembanding': 0.448}}
    service.state['prioritas'] = artifact
    body = {'judul': 'akun zoom', 'deskripsi': 'x', 'jenis': 'INC'}
    assert c.post('/triage', json=body).json()['prioritas_saran'] is None
    artifact['metrics'] = {'f1_makro': 0.6, 'f1_makro_pembanding': 0.448}
    assert c.post('/triage', json=body).json()['prioritas_saran']['prioritas'] == 2
    assert c.post('/triage', json={**body, 'jenis': 'REQ'}).json()['prioritas_saran'] is None
    assert c.get('/health').json()['kualitas_model']['prioritas']['lolos'] is True

