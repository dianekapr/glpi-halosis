"""Tes klaster solusi berulang dengan data rekaan."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai.candidates import recurring_solutions  # noqa: E402

RESET = 'akun sso sudah direset silakan login kembali dengan password sementara lalu segera ganti password baru'
KUOTA = 'kuota mailbox sudah ditambah menjadi dua puluh gigabyte silakan hapus lampiran lama agar tidak penuh lagi'


def chunks(rows):
    return pd.DataFrame([
        {'sumber': f'T{i}', 'jenis_sumber': 'tiket', 'judul': judul, 'teks': f'Masalah: {judul} Solusi: {solusi}'}
        for i, (judul, solusi) in enumerate(rows)
    ] + [{'sumber': 'KB-1', 'jenis_sumber': 'kb', 'judul': 'x', 'teks': RESET}])


def test_klaster_terbesar_dulu_dan_kb_diabaikan():
    rows = [('SSO terkunci', RESET)] * 6 + [('Email penuh', KUOTA)] * 5 + [('Lain', 'sudah dibantu')] * 9
    hasil = recurring_solutions(chunks(rows), min_size=5)
    assert [c['jumlah'] for c in hasil] == [6, 5]
    assert hasil[0]['masalah'] == 'SSO terkunci' and hasil[0]['kunci'].startswith('ai:T')
    assert len(hasil[0]['contoh_tiket']) == 5


def test_solusi_pendek_dan_klaster_kecil_tidak_masuk():
    rows = [('Lain', 'sudah dibantu')] * 9 + [('Email penuh', KUOTA)] * 3
    assert recurring_solutions(chunks(rows), min_size=5) == []
