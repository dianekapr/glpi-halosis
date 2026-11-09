"""C.9: kalibrasi ambang → reports/kalibrasi_ambang.md. Read-only; hanya angka dan pertanyaan rekaan.

Chat 0,78/0,83 (bawaan HALOSIS_CHAT_SUGGEST_MIN_SCORE / HALOSIS_CHAT_MIN_SCORE): skor e5 atas sumber tersetujui diukur
pada tiga set proksi. Tidak ada label manusia, jadi ini bukti sebaran skor, bukan akurasi jawaban.
Triase 40/70 (ai_threshold_low / triage_threshold): dari `kurva_ambang` ai/models/triage.metrics.json.

Pakai: .venv/bin/python ai/scripts/kalibrasi_ambang.py
Uji cepat: tambahkan --sampel 50 --keluar <folder sementara>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

os.environ.setdefault('HF_HUB_OFFLINE', '1')

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eda import num  # noqa: E402
from halosis_ai import privacy, quality, search  # noqa: E402
from train_triage import f, table  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / 'data/processed/qa_pairs.parquet'
METRICS = ROOT / 'ai/models/triage.metrics.json'
REPORT = ROOT / 'reports/kalibrasi_ambang.md'
SPLIT = pd.Timestamp('2026-07-01')
CHAT_LOW, CHAT_HIGH = 0.78, 0.83
TRIAGE_LOW, TRIAGE_HIGH = 40, 70
CHAT_GRID = (0.74, 0.76, 0.78, 0.80, 0.82, 0.83, 0.84, 0.86, 0.88)
TRIAGE_GRID = (30, 40, 50, 60, 70, 80, 90)
UNANSWERABLE = [  # rekaan: di luar layanan TI, atau TI tetapi tidak dicakup sumber
    'Apa resep nasi goreng yang enak?', 'Berapa harga tiket pesawat Jakarta ke Medan besok?', 'Siapa juara liga sepak bola tahun lalu?',
    'Bagaimana cara merawat tanaman hias di kantor?', 'Rekomendasi film untuk akhir pekan', 'Bagaimana cuaca di Bandung hari ini?',
    'Berapa kurs dolar terhadap rupiah sekarang?', 'Cara membuat kopi susu gula aren', 'Di mana restoran padang terdekat?',
    'Bagaimana cara mengajukan kredit rumah?', 'Apa syarat membuat paspor baru?', 'Kapan libur nasional bulan depan?',
    'Cara mengganti oli sepeda motor', 'Berapa tinggi gunung Rinjani?', 'Apa obat untuk sakit kepala?',
    'Bagaimana cara memasang printer jaringan Epson L9999?', 'Bagaimana memasang kartu grafis di server rak nomor 77?',
    'Cara mengatur lisensi perangkat lunak desain 3D di kantor', 'Bagaimana memperbaiki proyektor ruang rapat yang bergaris?',
    'Cara memindahkan pangkalan data Oracle ke klaster baru', 'Bagaimana mengganti kipas pendingin laptop sendiri?',
    'Bagaimana mengatur ulang router rumah merek apa pun?', 'Cara memulihkan ponsel Android yang mati total',
    'Bagaimana memasang kamera pengawas di lobi kantor?',
]


def top_scores(queries: list[str], vectors: np.ndarray, kinds: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Skor teratas tiap kueri atas sumber tersetujui dan atas artikel KB saja (mode pilihan hanya untuk KB)."""
    encoded = search.embed(queries, 'query')
    approved = np.isin(kinds, ['kb', 'layanan'])
    kb = kinds == 'kb'
    return (encoded @ vectors[approved].T).max(axis=1), (encoded @ vectors[kb].T).max(axis=1)


def modes(top: np.ndarray, top_kb: np.ndarray, low: float, high: float) -> dict:
    answered = top >= high
    choices = ~answered & (top_kb >= low)
    return {'jawab': float(answered.mean()), 'pilihan': float(choices.mean()), 'tolak': float((~answered & ~choices).mean())}


def chat_section(sample: int | None) -> str:
    chunks, vectors = search.load_index()
    kinds = chunks['jenis_sumber'].to_numpy()
    sources = chunks[np.isin(kinds, ['kb', 'layanan'])].drop_duplicates('sumber')
    qa = pd.read_parquet(QA, columns=['tanggal', 'masalah'])
    tickets = [str(privacy.mask_text(str(m)))[:500] for m in qa.loc[pd.to_datetime(qa['tanggal'], errors='coerce') >= SPLIT, 'masalah']]
    titles = sources['judul'].astype(str).tolist()
    unknown = UNANSWERABLE
    if sample:
        tickets, titles, unknown = tickets[:sample], titles[:5], unknown[:5]
    sets = {'Judul sumber (harus terjawab)': top_scores(titles, vectors, kinds),
            'Rekaan tak terjawab (harus ditolak)': top_scores(unknown, vectors, kinds),
            'Masalah tiket Jul–Ags (sebaran nyata)': top_scores(tickets, vectors, kinds)}
    names = list(sets)
    active = [[name, num(len(top)), *[f(v) for v in modes(top, kb, CHAT_LOW, CHAT_HIGH).values()], num(float(np.median(top)), 4)]
              for name, (top, kb) in sets.items()]
    grid = []
    for high in CHAT_GRID:
        cells = [f(float((sets[n][0] >= high).mean())) for n in names]
        grid.append([num(high, 2), *cells])
    wrong = float((sets[names[1]][0] >= CHAT_HIGH).mean())
    missed = float((sets[names[0]][0] < CHAT_HIGH).mean())
    return '\n'.join([
        '## Chat: 0,78 / 0,83', '',
        '`/chat` menjawab bila skor ≥ 0,83, menawarkan artikel KB bila skor KB ≥ 0,78, selain itu menolak. Skor e5 atas '
        f'{num(len(sources))} sumber (artikel KB yang terlihat pegawai di Tanya Jawab = FAQ + bertarget, dan katalog layanan) pada indeks aktif.', '',
        table(['Set proksi', 'Kueri', 'Dijawab', 'Pilihan', 'Ditolak', 'Median skor'], active), '',
        'Porsi kueri yang dijawab bila ambang atas diubah:', '',
        table(['Ambang atas', *names], grid), '',
        f'Pada 0,83: {f(wrong)} kueri rekaan tak terjawab lolos ke jawaban, dan {f(missed)} judul sumber gagal terjawab.', '',
        'Keterbatasan: judul sumber memihak skor tinggi karena teksnya ada di sumber; set rekaan ditulis tangan dan kecil; set '
        'tiket tidak punya label relevansi. Ambang belum boleh dinyatakan terkalibrasi sebelum penilaian tim '
        '(`reports/penilaian_relevansi.xlsx`) tersedia dan hasil UAT menentukan biaya salah jawab.',
    ])


def triage_section() -> str:
    metrics = json.loads(METRICS.read_text(encoding='utf-8'))
    curve = metrics['kurva_ambang']
    total = metrics['tiket_uji']
    rows = []
    for point in TRIAGE_GRID:
        p = curve[str(point)]
        passed = quality.triage_point(metrics, point / 100)[0]
        status = {True: 'lolos', False: 'tidak lolos'}.get(passed, str(passed))
        accuracy = f(p['akurasi']) if p['akurasi'] is not None else '–'  # tidak ada tiket di atas ambang ini
        rows.append([f'{point}%', accuracy, f(p['cakupan']), num(p['tiket']), status])
    low, high = curve[str(TRIAGE_LOW)], curve[str(TRIAGE_HIGH)]
    band_tickets = low['tiket'] - high['tiket']
    band_hits = low['akurasi'] * low['tiket'] - high['akurasi'] * high['tiket']
    bands = [['≥ 70%', num(high['tiket']), f(high['tiket'] / total), f(high['akurasi'])],
             ['40% sampai < 70%', num(band_tickets), f(band_tickets / total), f(band_hits / band_tickets) if band_tickets else '–'],
             ['< 40%', num(total - low['tiket']), f(1 - low['tiket'] / total), '–']]
    return '\n'.join([
        '## Triase: 40 / 70', '',
        f'Model aktif `{metrics["versi"]}`, {num(total)} tiket uji Jul–Ags 2026 (`kurva_ambang`). Status memakai gerbang '
        f'`quality.triage_point` (akurasi ≥ {f(quality.MIN_ACC_CONFIDENT, 0)}, cakupan ≥ {f(quality.MIN_POINT_COVERAGE, 0)}, '
        f'≥ {num(quality.MIN_POINT_TICKETS)} tiket).', '',
        table(['Ambang', 'Akurasi di atas ambang', 'Cakupan', 'Tiket', 'Gerbang'], rows), '',
        'Per pita keyakinan aktif:', '',
        table(['Pita', 'Tiket', 'Porsi', 'Akurasi'], bands), '',
        'Akurasi pita tengah diturunkan dari kurva yang dibulatkan 4 digit. Akurasi pita < 40% tidak tersedia karena kurva '
        'hanya memuat tiket di atas ambang. Dokumen hal. 100 meminta ambang ditentukan dari validation dataset, cost of '
        'error, dan hasil UAT; laporan ini baru mencakup yang pertama. Kurva berasal dari split waktu, jadi tidak boleh '
        'dicampur dengan split acak `replikasi_poc.md`.',
    ])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--sampel', type=int, help='uji cepat; wajib bersama --keluar')
    parser.add_argument('--keluar', type=Path, help='folder keluaran laporan (bawaan reports/)')
    args = parser.parse_args()
    if args.sampel and not args.keluar:
        parser.error('--sampel wajib bersama --keluar agar laporan asli tidak tertimpa angka sampel')
    report = (args.keluar / REPORT.name) if args.keluar else REPORT
    if args.keluar:
        args.keluar.mkdir(parents=True, exist_ok=True)
    report.write_text('\n\n'.join([
        '# Kalibrasi ambang (C.9)',
        f'Dihasilkan `ai/scripts/kalibrasi_ambang.py`, {date.today():%d-%m-%Y}. Tidak mengubah ambang aktif; pemilik ambang: '
        '`reports/tata_kelola_ai.md` §1.',
        chat_section(args.sampel), triage_section(),
    ]) + '\n', encoding='utf-8')
    print(f'→ {report}')


if __name__ == '__main__':
    main()
