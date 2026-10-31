"""Tes pemecahan percakapan & pengambilan solusi. Semua teks rekaan (sudah dalam bentuk tersamarkan)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai.conversations import extract_solution, meaningful_note, split_conversation  # noqa: E402

RAW = (
    '2026-03-01 08:00:00 | Ysh. Bpk./Ibu [NAMA] terimakasih telah menghubungi HaloSIS. Laporan akan kami teruskan '
    'kepada tim teknis terkait. Jangan lupa bintang 5 ya || '
    '2026-03-01 08:10:00 | saya masih tidak bisa login sejak pagi tadi || '
    '2026-03-01 09:00:00 | Kepada Yth. Bapak/Ibu [NAMA]. Akun telah kami reset, silakan login dengan password '
    'sementara : [RAHASIA] lalu segera ganti kata sandi. Terima kasih || '
    '2026-03-01 09:05:00 | baik terima kasih'
)


def test_split_conversation():
    messages = split_conversation(RAW)
    assert len(messages) == 4
    assert messages[0].time == '2026-03-01 08:00:00'
    assert messages[-1].text == 'baik terima kasih'


def test_split_kosong():
    assert split_conversation(None) == []
    assert split_conversation('') == []


def test_solusi_petugas_terakhir_tanpa_template():
    solution = extract_solution(split_conversation(RAW))
    assert solution is not None
    assert 'Akun telah kami reset' in solution
    assert 'menghubungi HaloSIS' not in solution
    assert 'Terima kasih' not in solution


def test_hanya_template_tidak_ada_solusi():
    raw = ('2026-03-01 08:00:00 | Ysh. Bpk./Ibu [NAMA] terimakasih telah menghubungi HaloSIS. Akan kami teruskan '
           'kepada tim teknis terkait || 2026-03-01 08:05:00 | terima kasih')
    assert extract_solution(split_conversation(raw)) is None


def test_permintaan_informasi_bukan_solusi():
    raw = '2026-03-01 08:00:00 | Selamat pagi. Mohon infokan username dan NIP Bapak/Ibu'
    assert extract_solution(split_conversation(raw)) is None


def test_catatan_template_diabaikan():
    for note in ['solved', 'Done', '.', '', 'sudah diproses', 'dialihkan ke SDM', None]:
        assert meaningful_note(note) is None, note
    assert meaningful_note('akun telah direset') == 'akun telah direset'


def test_catatan_template_penutup_diabaikan():
    for note in ['Terimakasih telah menghubungi HaloSIS. Jangan lupa bintang 5',
                 'Permasalahan sudah diselesaikan oleh tim teknis, maka tiket kami tutup.',
                 'Jika masih ada kendala lainnya, infokan kembali melalui HaloSIS.']:
        assert meaningful_note(note) is None, note


def test_catatan_dibersihkan_dari_kalimat_template():
    note = 'Akun email sudah diaktifkan kembali oleh admin. Jika masih ada kendala lainnya, infokan kembali.'
    assert meaningful_note(note) == 'Akun email sudah diaktifkan kembali oleh admin.'


def test_pesan_setelah_resolved_dibuang():
    from datetime import datetime
    raw = RAW + (' || 2026-03-02 10:00:00 | Kepada Yth. Bapak/Ibu [NAMA]. Tiket dibuka kembali, kami sudah '
                 'memeriksa ulang konfigurasi akun dan semuanya normal')
    messages = split_conversation(raw)
    assert 'memeriksa ulang' in extract_solution(messages)
    # Selesai 08:58 → pesan 09:00 masih masuk toleransi 5 menit; 09:05 & hari berikutnya dibuang
    solution = extract_solution(messages, resolved=datetime(2026, 3, 1, 8, 58))
    assert 'Akun telah kami reset' in solution
    assert 'Akun telah kami reset' not in (extract_solution(messages, resolved=datetime(2026, 3, 1, 8, 50)) or '')


def test_pesan_terakhir_dari_pemohon_dilewati():
    raw = ('2026-03-01 08:00:00 | Akun telah kami reset, silakan login dengan password sementara lalu ganti || '
           '2026-03-01 08:30:00 | Sudah dicoba dan berhasil login, akun email kembali normal sekarang')
    messages = split_conversation(raw)
    assert 'berhasil login' in extract_solution(messages)
    assert 'Akun telah kami reset' in extract_solution(messages, last_by_requester=True)


def test_pesan_terakhir_menang_atas_petugas_sebelumnya():
    raw = ('2026-03-01 08:00:00 | Kami sudah mengirim formulir permohonan ke tim terkait untuk diproses || '
           '2026-03-01 09:00:00 | Hak akses folder bersama telah aktif, silakan buka ulang aplikasi berkas')
    assert 'Hak akses folder' in extract_solution(split_conversation(raw))


def test_kurang_dari_lima_kata_bukan_solusi():
    assert extract_solution(split_conversation('2026-03-01 08:00:00 | Sudah kami reset akunnya')) is None
