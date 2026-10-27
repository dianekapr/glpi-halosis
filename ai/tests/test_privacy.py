"""Tes penyamaran: setiap pola data pribadi tersamarkan. Semua data di sini rekaan."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai.privacy import (  # noqa: E402
    EMAIL, NAME, NIK, NIP, PHONE, SECRET, build_name_pattern, build_name_token_pattern, mask_text,
)


def test_email():
    assert mask_text('kirim ke budi.santoso@bps.go.id ya') == f'kirim ke {EMAIL} ya'


def test_nip_rapat_dan_berkelompok():
    assert mask_text('NIP 198701012010011001') == f'NIP {NIP}'
    assert mask_text('nip: 19870101 201001 1 001.') == f'nip: {NIP}.'


def test_nik():
    assert mask_text('NIK 3374012345678901') == f'NIK {NIK}'


def test_telepon():
    for nomor in ['081234567890', '+6281234567890', '0812-3456-7890', '0812 3456 7890']:
        assert PHONE in mask_text(f'hubungi {nomor}'), nomor


def test_password_berbagai_pola():
    cases = {
        'password: Rahasia123': f'password: {SECRET}',
        'pasw : abc123': f'pasw : {SECRET}',
        'pwd=Qwerty9': f'pwd={SECRET}',
        'kata sandi baru: Bps2026!': f'kata sandi baru: {SECRET}',
        'password sementara : Xy7kLm2pQr': f'password sementara : {SECRET}',
        'sandi:12345678': f'sandi:{SECRET}',
        'passwordnya Sensus2020': f'passwordnya {SECRET}',
    }
    for raw, expected in cases.items():
        assert mask_text(raw) == expected, raw


def test_password_tanpa_nilai_tidak_diubah():
    teks = 'saya lupa password akun SSO'
    assert mask_text(teks) == teks


def test_nama_setelah_sapaan():
    assert mask_text('Ysh. Bpk./Ibu Budi Santoso terimakasih') == f'Ysh. Bpk./Ibu {NAME} terimakasih'
    assert mask_text('Kepada Yth. Ibu Siti Rahma, mohon maaf') == f'Kepada Yth. Ibu {NAME}, mohon maaf'
    assert NAME in mask_text('terima kasih Pak Andi')


def test_nama_dari_kolom_pengguna():
    assert mask_text('sudah dibantu oleh rina wulandari kemarin', names=['Rina Wulandari']) == f'sudah dibantu oleh {NAME} kemarin'


def test_bukan_teks_dikembalikan_apa_adanya():
    assert mask_text(None) is None
    assert mask_text(12) == 12


def test_bagian_nama_tanpa_sapaan():
    names = ['Budi Santoso', 'Indah Bintang']
    patterns = [build_name_pattern(names), build_name_token_pattern(names, common_words={'bintang'})]
    assert mask_text('akun atas nama Budi terkunci', names=patterns) == f'akun atas nama {NAME} terkunci'
    assert mask_text('user SANTOSO tidak bisa login', names=patterns) == f'user {NAME} tidak bisa login'
    # Kata umum yang kebetulan juga bagian nama tidak ikut tersamar
    assert mask_text('Jangan lupa Bintang 5', names=patterns) == 'Jangan lupa Bintang 5'
    # Penanda yang sudah ada tidak disamarkan ulang
    assert mask_text('[NAMA] sudah dibantu', names=patterns) == '[NAMA] sudah dibantu'
