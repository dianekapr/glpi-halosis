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
    monkeypatch.setattr(service.search, 'cari', lambda q, k=3, jenis=None: [
        h for h in hits if jenis is None or h['jenis_sumber'] in jenis])
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
    hit = {'potongan': 'Email penuh. Hapus lampiran besar', 'skor': 0.9, 'sumber': 'KB-1',
           'jenis_sumber': 'kb', 'judul': 'Email penuh'}
    c = client(monkeypatch, [hit, {**hit, 'sumber': 'KB-2'}])
    r = c.post('/chat', json={'pertanyaan': 'email penuh'}).json()
    assert r['ditemukan'] and r['mode'] == 'ekstraktif'
    assert 'Hapus lampiran besar' in r['jawaban'] and [s['sumber'] for s in r['sumber']] == ['KB-1']


def test_chat_tidak_memakai_solusi_tiket(monkeypatch):
    """A.1: skor tiket setinggi apa pun tidak dijawabkan ke pegawai; petugas (/cari) tetap melihatnya."""
    tiket = {'potongan': 'Masalah: vpn Solusi: rahasia-tiket', 'skor': 0.99, 'sumber': 'T1', 'jenis_sumber': 'tiket',
             'judul': 'VPN', 'solusi': 'rahasia-tiket'}
    layanan = {'potongan': 'Layanan VPN.', 'skor': 0.9, 'sumber': 'LAYANAN-C1', 'jenis_sumber': 'layanan', 'judul': 'VPN'}
    c = client(monkeypatch, [tiket])
    r = c.post('/chat', json={'pertanyaan': 'vpn putus'}).json()
    assert r['ditemukan'] is False and 'rahasia-tiket' not in str(r)
    r = client(monkeypatch, [tiket, layanan]).post('/chat', json={'pertanyaan': 'vpn putus'}).json()
    assert r['ditemukan'] and [s['sumber'] for s in r['sumber']] == ['LAYANAN-C1'] and 'rahasia-tiket' not in r['jawaban']
    assert client(monkeypatch, [tiket]).post('/cari', json={'q': 'vpn'}).json()['hasil'][0]['sumber'] == 'T1'


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
    monkeypatch.setattr(service.search, 'cari', lambda q, k=3, jenis=None: seen.update(q=q, k=k, jenis=jenis) or hits)
    r = c.post('/cari', json={'q': 'sso budi@contoh.go.id', 'k': 5})
    assert r.status_code == 200 and r.json()['hasil'][0]['sumber'] == 'KB1'
    assert seen['jenis'] is None and seen['k'] == 5 and 'budi@contoh.go.id' not in seen['q']  # disamarkan sebelum dicari


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


def test_chat_kecualikan_sumber_tetap_kena_ambang(monkeypatch):
    """Plugin membuang sumber yang tidak terlihat pengguna: pengganti hanya sah bila skornya sendiri ≥ ambang."""
    kb = {'potongan': 'langkah', 'jenis_sumber': 'kb'}
    hits = [{**kb, 'skor': 0.95, 'sumber': 'KB-9', 'judul': 'Tersembunyi'},
            {**kb, 'skor': 0.84, 'sumber': 'KB-2', 'judul': 'Cukup relevan'},
            {**kb, 'skor': 0.70, 'sumber': 'KB-6', 'judul': 'Kurang relevan'}]
    c = client(monkeypatch, hits)
    ask = lambda **k: c.post('/chat', json={'pertanyaan': 'x', 'riwayat': [], **k}).json()  # noqa: E731
    assert ask()['sumber'][0]['sumber'] == 'KB-9'
    assert ask(kecualikan=['KB-9'])['sumber'][0]['sumber'] == 'KB-2'  # pengganti lolos ambang yang sama
    body = ask(kecualikan=['KB-9', 'KB-2'])  # sisanya di bawah ambang → tidak ditemukan, bukan KB-6
    assert body['ditemukan'] is False and body['sumber'] == []


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


class FakeUrgency:
    classes_ = ['Low', 'Medium']

    def __init__(self, p_low):
        self.p_low, self.frames = p_low, []

    def predict_proba(self, frame):
        self.frames.append(frame)
        return [[self.p_low, 1 - self.p_low]]


def urgency_metrics(low_ok=True, medium_ok=True):
    """Metrik per kelas seperti train_urgensi.py; *_ok=False → kelas itu gagal syarat gerbang."""
    return {'kelas': {
        'Low': {'ambang': 0.8, 'tiket': 44, 'pembanding': 0.188, 'presisi': 0.795 if low_ok else 0.55,
                'wilson_95': [0.65, 0.89] if low_ok else [0.40, 0.69], 'recall': 0.07},
        'Medium': {'ambang': 0.3, 'tiket': 1000, 'pembanding': 0.812, 'akurasi': 0.861 if medium_ok else 0.83}}}


def test_urgensi_ambang_per_kelas(monkeypatch):
    """Low hanya bila P(Low) ≥ ambang Low, Medium hanya bila P(Low) ≤ ambang Medium, di antaranya / REQ → None;
    kelas yang tidak lolos gerbang tidak pernah disarankan."""
    c = client(monkeypatch, [])
    model = FakeUrgency(0.85)
    artifact = {'pipeline': model, 'version': 'urg-uji', 'ambang': {'Low': 0.8, 'Medium': 0.3},
                'urgensi_glpi': {'Medium': 3, 'Low': 2}, 'metrics': urgency_metrics()}
    service.state['urgensi'] = artifact
    body = {'judul': 'akun zoom', 'deskripsi': 'x', 'jenis': 'INC'}
    saran = lambda **kw: c.post('/triage', json={**body, **kw}).json()['urgensi_saran']  # noqa: E731
    assert saran() == {'urgensi': 'Low', 'nilai_glpi': 2, 'keyakinan': 0.85, 'versi_model': 'urg-uji'}
    # Tim: dari permintaan bila diisi, selain itu tim saran triase
    saran(tim='Tim Email')
    assert model.frames[-1]['tim'].iloc[0] == 'Tim Email'
    model.p_low = 0.5  # di antara ambang → aturan
    assert saran() is None
    model.p_low = 0.2
    assert saran() == {'urgensi': 'Medium', 'nilai_glpi': 3, 'keyakinan': 0.8, 'versi_model': 'urg-uji'}
    assert saran(jenis='REQ') is None
    gate = c.get('/health').json()['kualitas_model']['urgensi']
    assert gate['lolos'] is True and gate['kelas_lolos'] == ['Low', 'Medium']
    # Medium tidak lolos (akurasi ≤ pembanding + 3 poin) → hanya Low yang boleh disarankan
    artifact['metrics'] = urgency_metrics(medium_ok=False)
    assert saran() is None
    model.p_low = 0.9
    assert saran()['urgensi'] == 'Low'
    # Kedua kelas gagal → model tidak lolos, tidak ada saran
    artifact['metrics'] = urgency_metrics(low_ok=False, medium_ok=False)
    assert saran() is None
    assert c.get('/health').json()['kualitas_model']['urgensi']['lolos'] is False
    # Metrik versi lama (tanpa per kelas) → tidak tercatat → tidak lolos
    artifact['metrics'] = {'f1_makro': 0.58, 'f1_makro_pembanding': 0.448}
    assert saran() is None



def test_indeks_tidak_cocok_muncul_di_health(monkeypatch):
    c = client(monkeypatch, [])
    monkeypatch.setattr(service, 'quality_gate', lambda *a, **k: {})
    assert c.get('/health').json()['peringatan'] == []
    assert c.post('/indeks/tidak-cocok', json={'sumber': 'KB-7'}).json()['jumlah'] == 1
    assert c.post('/indeks/tidak-cocok', json={'sumber': 'bukan-kb'}).status_code == 422
    health = c.get('/health').json()
    assert health['peringatan'] == [service.INDEX_MISMATCH_WARNING] and health['indeks_tidak_cocok'] == ['KB-7']


def test_chat_sumber_membawa_judul_potongan_yang_sama_dengan_jawaban(monkeypatch):
    hit = {'potongan': 'Reset lewat portal SSO', 'skor': 0.9, 'sumber': 'KB-5', 'jenis_sumber': 'kb',
           'judul': 'Mengatur ulang kata sandi SSO BPS'}
    r = client(monkeypatch, [hit]).post('/chat', json={'pertanyaan': 'lupa sandi sso'}).json()
    assert 'Mengatur ulang kata sandi SSO BPS' in r['jawaban']
    assert r['sumber'][0]['judul'] == 'Mengatur ulang kata sandi SSO BPS'
