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



def test_ambang_urgensi_per_kelas():
    """Low: ambang terendah dengan presisi ≥ 75% (recall terbesar); Medium: ambang tertinggi dengan akurasi >
    pembanding + 3 poin (cakupan terbesar). Data rekaan: P(Low) tinggi hanya untuk sebagian kecil insiden Low."""
    import numpy as np
    from halosis_ai import quality
    from halosis_ai.triage_model import pick_urgency_thresholds

    # 200 insiden: 40 Low, 160 Medium
    y = np.array(['Low'] * 40 + ['Medium'] * 160)
    p_low = np.concatenate([np.full(32, 0.92), np.full(8, 0.6),  # Low: 32 sangat yakin, 8 ragu
                            np.full(8, 0.92), np.full(32, 0.6), np.full(120, 0.1)])  # Medium
    kelas = pick_urgency_thresholds(p_low, y)
    low, med = kelas['Low'], kelas['Medium']
    assert low['lolos'] and low['ambang'] == 0.65 and low['tiket'] == 40 and low['presisi'] == 0.8
    assert low['recall'] == 0.8 and low['wilson_95'][0] > low['pembanding']
    assert med['lolos'] and med['ambang'] == 0.5 and med['akurasi'] == 1.0 and med['cakupan'] == 0.6
    assert quality.check('urgensi', {'kelas': kelas})['kelas_lolos'] == ['Low', 'Medium']
    # Low tidak pernah cukup presisi → tidak lolos, kelas lain tetap bisa lolos
    kelas = pick_urgency_thresholds(np.where(y == 'Low', 0.6, np.where(np.arange(200) < 100, 0.6, 0.1)), y)
    assert not kelas['Low']['lolos'] and kelas['Medium']['lolos']
    assert quality.check('urgensi', {'kelas': kelas})['kelas_lolos'] == ['Medium']


def test_wilson():
    from halosis_ai.quality import wilson

    low, high = wilson(35, 44)
    assert 0.65 < low < 0.80 < high < 0.90
    assert wilson(0, 0) is None
