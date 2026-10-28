"""Tes rekonsiliasi migrasi (FR-10): kategori gagal, tidak lengkap, duplikat, hitungan penyamaran,
dan laporan tanpa data pribadi. Semua data di sini rekaan."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import reconcile  # noqa: E402
from prepare_data import KEEP, USER_COLUMNS, clean  # noqa: E402


def make_raw() -> pd.DataFrame:
    rows = [
        # 0: normal, berisi email + HP → disamarkan
        dict(ticket_number='INC1', state_name='Closed', description='Hubungi budi.rekaan@contoh.go.id atau 081234567890',
             assignment_group_name='Tim A', resolution='Server dipulihkan, silakan sinkron ulang aplikasi.'),
        # 1: tanpa nomor tiket → gagal
        dict(ticket_number=None, state_name='Closed', description='Aplikasi error', assignment_group_name='Tim A',
             resolution='Cache dibersihkan dan aplikasi dipasang ulang.'),
        # 2: status tidak dikenal → gagal
        dict(ticket_number='INC3', state_name='UNKNOWN / STATE NOT FOUND', description='Lain', assignment_group_name='Tim B'),
        # 3: tanpa deskripsi & tanpa tim → tidak lengkap
        dict(ticket_number='INC4', state_name='Assigned', description=None, assignment_group_name=None),
        # 4: salinan isi baris 0 dari pemohon sama → duplikat
        dict(ticket_number='INC5', state_name='Closed', description='Hubungi budi.rekaan@contoh.go.id atau 081234567890',
             assignment_group_name='Tim A', resolution='Server dipulihkan, silakan sinkron ulang aplikasi.'),
    ]
    df = pd.DataFrame(rows)
    df['short_description'] = 'Gagal sinkron'
    df['ticket_type'] = 'INC'
    df['opened'] = pd.to_datetime(['2026-01-05', '2026-01-06', '2026-02-01', '2026-02-02', '2026-02-03'])
    for col in KEEP:
        if col not in df:
            df[col] = None
    for name_col, id_col in USER_COLUMNS.items():
        df[name_col] = 'Rekaan Satu'
        df[id_col] = 'u1'
    return df


def test_kategori_dan_penyamaran(tmp_path, monkeypatch):
    raw = make_raw()
    cleaned = clean(raw)
    f = reconcile.flags(raw, cleaned)
    assert f['failed'].tolist() == [False, True, True, False, False]
    assert int(f['no_number'].sum()) == 1 and int(f['unknown_state'].sum()) == 1
    assert int(f['residual_pii'].sum()) == 0
    assert f['incomplete'].tolist() == [False, False, False, True, False]
    assert f['duplicate'].tolist() == [False, False, False, False, True]
    assert len(f) == int(f['processed'].sum()) + int(f['failed'].sum())

    before = reconcile.placeholder_counts(raw[[c for c in cleaned.columns if c in raw.columns]])
    after = reconcile.placeholder_counts(cleaned)
    assert after['Email'] - before['Email'] == 2
    assert after['Telepon'] - before['Telepon'] == 2

    monkeypatch.setattr(reconcile, 'REPORT', tmp_path / 'rekonsiliasi.md')
    reconcile.write_report(raw, f, {k: after[k] - before[k] for k in reconcile.PLACEHOLDERS})
    text = (tmp_path / 'rekonsiliasi.md').read_text(encoding='utf-8')
    assert '| 2026-01 |' in text and '| Tim A |' in text
    for secret in ('budi.rekaan', '081234567890', 'Rekaan'):
        assert secret not in text
