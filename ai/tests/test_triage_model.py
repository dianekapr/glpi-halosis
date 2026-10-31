"""Tes model triase dengan data rekaan (bukan data history)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai.privacy import EMAIL, SECRET  # noqa: E402
from halosis_ai.triage_model import SimilarIndex, TriageModel, build_pipeline, model_text  # noqa: E402

DATA = [
    ('Tidak bisa login email', 'kotak masuk email tidak bisa dibuka', 'INC', 'Email'),
    ('Email penuh', 'kuota email penuh mohon ditambah', 'REQ', 'Email'),
    ('Lupa password email', 'reset password email kantor', 'REQ', 'Email'),
    ('SSO error', 'login SSO gagal terus', 'INC', 'SSO'),
    ('Akun SSO terkunci', 'akun SSO terkunci setelah salah sandi', 'INC', 'SSO'),
    ('Reset SSO', 'mohon reset akun SSO', 'REQ', 'SSO'),
] * 4


def test_model_text_menyamarkan_dan_menandai_jenis():
    text = model_text('Reset akun', 'email saya budi@bps.go.id password: Rahasia1', 'REQ')
    assert text.startswith('jenis_req ')
    assert EMAIL.lower() in text and SECRET.lower() in text
    assert 'budi@bps.go.id' not in text and 'rahasia1' not in text


def test_prediksi_lengkap_dan_konsisten():
    texts = [model_text(t, d, k) for t, d, k, _ in DATA]
    teams = [team for *_, team in DATA]
    pipeline = build_pipeline(calibrate=False).fit(texts, teams)
    similar = SimilarIndex.fit(texts, [f'T{i}' for i in range(len(DATA))], teams, [t for t, *_ in DATA])
    result = TriageModel(pipeline, similar, version='uji').predict('Login SSO gagal', 'tidak bisa masuk SSO', 'INC')
    assert result['tim'] == 'SSO'
    assert len(result['top3']) == 2  # hanya 2 kelas
    assert abs(sum(t['keyakinan'] for t in result['top3']) - 1) < 1e-3
    assert result['perlu_penilaian_manual'] == (result['keyakinan'] < 0.70)
    assert result['tiket_mirip'][0]['tim'] == 'SSO'
    assert result['versi_model'] == 'uji'


def test_lainnya_selalu_penilaian_manual():
    """Top-1 kelas gabungan "Lainnya" → perlu penilaian manual walau keyakinannya tinggi."""
    data = [(t, d, k, 'Lainnya' if team == 'Email' else team) for t, d, k, team in DATA]
    texts = [model_text(t, d, k) for t, d, k, _ in data]
    teams = [team for *_, team in data]
    pipeline = build_pipeline(calibrate=False).fit(texts, teams)
    similar = SimilarIndex.fit(texts, [f'T{i}' for i in range(len(data))], teams, [t for t, *_ in data])
    model = TriageModel(pipeline, similar, version='uji', threshold=0.0)  # ambang 0: hanya aturan Lainnya yang berlaku
    result = model.predict('Email penuh', 'kuota email penuh mohon ditambah', 'REQ')
    assert result['tim'] == 'Lainnya' and result['perlu_penilaian_manual'] is True
    assert model.predict('SSO error', 'login SSO gagal terus', 'INC')['perlu_penilaian_manual'] is False

