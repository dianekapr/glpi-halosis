"""Definisi gerbang final (tata_kelola_ai.md §2): urgensi skema B, pola peringatan, triase pada ambang aktif (A.3–A.4)."""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from halosis_ai import quality  # noqa: E402

spec = importlib.util.spec_from_file_location('train_urgensi', ROOT / 'scripts/train_urgensi.py')
train = importlib.util.module_from_spec(spec)
spec.loader.exec_module(train)


def test_rentang_ambang_stabil_dan_tidak_stabil():
    folds = [{'Low': 0.85, 'Medium': 0.45}, {'Low': 0.95, 'Medium': 0.45}, {'Low': 0.90, 'Medium': 0.20}]
    r = quality.threshold_spread(folds)
    assert r['rentang_ambang'] == {'Low': 0.10, 'Medium': 0.25} and r['tidak_stabil'] == ['Medium']  # 0,10 masih stabil


def test_tidak_stabil_tidak_mengubah_status_lolos():
    low = {'tiket': 40, 'pembanding': 0.2, 'presisi': 0.8, 'wilson_95': [0.65, 0.9]}
    r = quality.check('urgensi', {'kelas': {'Low': low}, 'skema': 'B', 'tidak_stabil': ['Low']})
    assert r['lolos'] and r['kelas_lolos'] == ['Low'] and r['tidak_stabil'] == ['Low'] and r['skema'] == 'B'


@pytest.mark.parametrize('kelompok, kemurnian, lolos', [(7, 0.905, True), (5, 0.85, True), (4, 0.95, False), (8, 0.80, False)])
def test_pola_peringatan_tidak_memblokir(kelompok, kemurnian, lolos):
    r = quality.check('pola', {'kelompok': kelompok, 'kemurnian_tim': kemurnian, 'tiket_terkelompok': 22})
    assert r['lolos'] is lolos and r['memblokir'] is False and r['tiket_terkelompok'] == 22


def triase(point):
    return {'top1': 0.75, 'recall_tim_besar_min': 0.78, 'kurva_ambang': {'70': point}}


def test_triase_ambang_aktif_lolos_gagal():
    assert quality.check('triase', triase({'akurasi': 0.88, 'cakupan': 0.5, 'tiket': 780}), threshold=0.70)['lolos']
    r = quality.check('triase', triase({'akurasi': 0.80, 'cakupan': 0.5, 'tiket': 780}), threshold=0.70)
    assert not r['lolos'] and r['syarat']['akurasi_yakin'] == 'gagal'
    assert quality.check('triase', triase({'akurasi': 0.9, 'cakupan': 0.5, 'tiket': 780}), threshold=0.5)['syarat'][
        'akurasi_yakin'] == 'tidak tercatat'


@pytest.mark.parametrize('point', [{'akurasi': 0.99, 'cakupan': 0.09, 'tiket': 500},
                                   {'akurasi': 0.99, 'cakupan': 0.5, 'tiket': 99}])
def test_triase_data_tidak_cukup_bukan_lolos(point):
    r = quality.check('triase', triase(point), threshold=0.70)
    assert not r['lolos'] and r['syarat']['akurasi_yakin'] == quality.NOT_ENOUGH_DATA


def incidents(n=240):
    rng = np.random.default_rng(0)
    low = rng.random(n) < 0.3
    tim = np.where(rng.random(n) < 0.5, 'TimA', 'TimB')
    teks = [f'{"remeh" if v else "gangguan"} kata{i % 7} sistem{i % 3}' for i, v in enumerate(low)]
    return pd.DataFrame({'label': np.where(low, 'Low', 'Medium'), 'teks': teks, 'teks_tim': [f'{t} {s}' for t, s in zip(tim, teks)],
                         'tim': tim})


@pytest.fixture
def quick(monkeypatch, tmp_path):
    monkeypatch.setattr(train, 'team_model', lambda: make_pipeline(TfidfVectorizer(), LogisticRegression()))
    monkeypatch.setattr(train, 'OUT', tmp_path / 'models/urgensi.joblib')
    monkeypatch.setattr(train, 'BACKUP', tmp_path / 'backup')
    monkeypatch.setattr(train, 'REPORT', tmp_path / 'triase.md')
    (tmp_path / 'models').mkdir()
    train.OUT.write_bytes(b'lama')
    train.OUT.with_suffix('.metrics.json').write_text('{"versi": "lama"}', encoding='utf-8')
    train.REPORT.write_text('# Laporan\n', encoding='utf-8')
    df = incidents()
    monkeypatch.setattr(train, 'load', lambda: (df.assign(urgency=df['label'], impact=df['label']),
                                                pd.DataFrame({'teks_tim': ['TimA minta akun'] * 40, 'tim': ['TimA'] * 40})))
    return tmp_path


def test_evaluasi_skema_b_ambang_per_lipatan(quick):
    r = train.evaluate_scheme(incidents(), pd.DataFrame({'teks_tim': [], 'tim': []}), 'B')
    assert [f['lipatan'] for f in r['per_lipatan']] == [1, 2, 3, 4, 5] and len(r['p_low']) == 240
    for k in ('Low', 'Medium'):
        assert len(r['kelas'][k]['ambang_per_lipatan']) == 5
        assert r['kelas'][k]['ambang'] == float(np.median(r['kelas'][k]['ambang_per_lipatan']))


def test_gerbang_gagal_metrik_diganti_artefak_tetap(quick, monkeypatch):
    monkeypatch.setattr(train.quality, 'MIN_SUPPORT', 10_000)
    with pytest.raises(SystemExit) as e:
        train.main([])
    assert e.value.code == 2 and train.OUT.read_bytes() == b'lama'  # artefak tetap untuk rollback
    metrics = json.loads(train.OUT.with_suffix('.metrics.json').read_text(encoding='utf-8'))
    assert metrics['lolos_gerbang'] is False and metrics['kelas_lolos'] == [] and metrics['artefak_versi'] == 'lama'
    assert quality.check('urgensi', metrics)['kelas_lolos'] == []  # layanan berhenti menyarankan
    folder = next(train.BACKUP.glob('model-*'))
    assert json.loads((folder / 'urgensi.metrics.json').read_text(encoding='utf-8')) == {'versi': 'lama'}
    assert 'tidak dipakai' in train.REPORT.read_text(encoding='utf-8')


def test_gerbang_lolos_cadangan_dulu_lalu_tulis(quick):
    train.main([])
    assert train.OUT.read_bytes() != b'lama'
    folder = next(train.BACKUP.glob('model-*'))
    assert (folder / 'urgensi.joblib').read_bytes() == b'lama'
    manifest = (folder / 'MANIFEST.txt').read_text(encoding='utf-8')
    assert 'urgensi.joblib' in manifest and 'urgensi.metrics.json' in manifest
    metrics = json.loads(train.OUT.with_suffix('.metrics.json').read_text(encoding='utf-8'))
    assert metrics['skema'] == 'B' and metrics['lolos_gerbang'] and 'tidak_stabil' in metrics
    assert 'Skema A vs B' in train.REPORT.read_text(encoding='utf-8')


def test_kering_tidak_menulis(quick):
    train.main(['--kering', '200'])
    assert train.OUT.read_bytes() == b'lama' and not train.BACKUP.exists()
    assert train.REPORT.read_text(encoding='utf-8') == '# Laporan\n'


def test_kurva_ambang():
    curve = quality.threshold_curve(np.array([0.9, 0.8, 0.5, 0.2]), np.array([True, True, False, False]))
    assert curve['70'] == {'akurasi': 1.0, 'cakupan': 0.5, 'tiket': 2}
    assert curve['100'] == {'akurasi': None, 'cakupan': 0.0, 'tiket': 0}


def test_replay_kemurnian_per_kelompok():
    from halosis_ai import patterns
    vectors = np.array([[1.0, 0], [1, 0], [1, 0], [0, 1], [0, 1], [0, 1]])
    times = [f'2026-07-01 08:{m:02d}:00' for m in range(3)] + [f'2026-07-01 10:{m:02d}:00' for m in range(3)]
    r = patterns.replay(times, vectors, np.array([1, 1, 2, 3, 3, 3]), threshold=0.5, min_members=3, window_minutes=60)
    assert r == {'kelompok': 2, 'tiket_terkelompok': 6, 'blok': 2, 'kemurnian_tim': round((2 / 3 + 1) / 2, 3)}


def service_client(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient
    from service import app as service
    vectors = np.array([[1.0, 0], [1, 0], [1, 0], [0, 1], [0, 1], [0, 1]], dtype=np.float32)
    times = np.array([f'2026-07-01 08:{m:02d}:00' for m in range(3)] + [f'2026-07-01 10:{m:02d}:00' for m in range(3)])
    np.savez(tmp_path / 'pola_uji.npz', vektor=vectors, waktu=times, tim=np.array([1, 1, 1, 2, 2, 2]))
    monkeypatch.setattr(service.search, 'INDEX_DIR', tmp_path)
    monkeypatch.setattr(service, 'LATENCY_LOG', Path('/dev/null'))
    service.state.clear()
    service.state.update({'search': True, 'triage': object(), 'metrics': {'triase': triase({'akurasi': 0.88, 'cakupan': 0.5, 'tiket': 780})}})
    return TestClient(service.app)


def test_gerbang_mengikuti_nilai_aktif(monkeypatch, tmp_path):
    c = service_client(monkeypatch, tmp_path)
    body = c.post('/gerbang', json={'ambang_triase': 0.70, 'min_anggota': 3}).json()
    assert body['triase']['lolos'] and body['pola']['lolos'] is False and body['pola']['memblokir'] is False
    assert body['pola']['tiket_terkelompok'] == 6 and body['pola']['syarat']['kelompok'] == 'gagal'  # 2 < 5 kelompok
    assert c.post('/gerbang', json={'ambang_triase': 0.40}).json()['triase']['syarat']['akurasi_yakin'] == 'tidak tercatat'


def test_gerbang_pola_tanpa_set_uji(monkeypatch, tmp_path):
    c = service_client(monkeypatch, tmp_path)
    (tmp_path / 'pola_uji.npz').unlink()
    assert 'belum dibangun' in c.post('/gerbang', json={'ambang_triase': 0.70}).json()['pola']['alasan'][0]
