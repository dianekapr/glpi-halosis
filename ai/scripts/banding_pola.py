"""C.8: reproduksi reports/banding_pola.md → blok berpenanda di laporan yang sama. Hanya angka, tanpa teks tiket.

Memakai set uji ai/index/pola_uji.npz (dibuat ai/scripts/gerbang_pola.py: 666 insiden Jul–Ags, vektor e5, nomor tim
anonim) dan rata-rata vektor indeks aktif untuk pemusatan, sama seperti /pola. Tidak ada artefak yang ditulis.

Metode rata-rata rakus, jadi bergantung urutan tiket: selain urutan waktu (produksi), 30 urutan acak dicatat.

Pakai: .venv/bin/python ai/scripts/banding_pola.py
Uji cepat: tambahkan --sampel 50 --keluar <folder sementara>
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eda import num  # noqa: E402
from halosis_ai import patterns, search  # noqa: E402
from train_triage import replace_section, table  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'reports/banding_pola.md'
TEST_SET = search.INDEX_DIR / 'pola_uji.npz'
MARKS = ('<!-- reproduksi:mulai -->', '<!-- reproduksi:selesai -->')
SEED, ORDERS, THRESHOLD, MINIMUM = 42, 30, 0.50, 3
METHODS = [('Rata-rata ≥ 0,50, urutan waktu', {'metode': 'rata', 'threshold': THRESHOLD}, '8 / 25 / 0,917 (catatan 6 Nov)'),
           ('DBSCAN eps 0,50, min_samples 3', {'metode': 'dbscan', 'eps': 0.50, 'min_samples': MINIMUM}, '8 / 25 / 0,917'),
           ('DBSCAN eps 0,40, min_samples 3', {'metode': 'dbscan', 'eps': 0.40, 'min_samples': MINIMUM}, '3 / 10 / 0,889')]


def shuffled_run(times: list[str], vectors: np.ndarray, rng: np.random.Generator) -> tuple[int, int]:
    """Satu urutan acak: tiket tiap blok diacak; tanpa waktu, group() mempertahankan urutan masukan."""
    blocks = pd.to_datetime(pd.Series(times), errors='coerce').dt.floor('60min')
    groups = members = 0
    for _, rows in blocks.groupby(blocks).groups.items():
        if len(rows) < MINIMUM:
            continue
        index = rng.permutation(list(rows))
        found = patterns.group([{'id': int(i), 'judul': '', 'waktu': None} for i in index], vectors[index], THRESHOLD, MINIMUM)
        groups += len(found)
        members += sum(len(c['ids']) for c in found)
    return groups, members


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
    if not TEST_SET.exists():
        raise SystemExit(f'{TEST_SET} tidak ada: jalankan ai/scripts/gerbang_pola.py dulu.')
    data = np.load(TEST_SET)
    vectors, times, teams = data['vektor'], data['waktu'].tolist(), data['tim']
    if args.sampel:
        vectors, times, teams = vectors[:args.sampel], times[:args.sampel], teams[:args.sampel]
    centered = patterns.center(vectors, search.load_index()[1].mean(axis=0))

    rows, blocks = [], 0
    for name, params, published in METHODS:
        start = time.perf_counter()
        result = patterns.replay(times, centered, teams, **params)
        elapsed = (time.perf_counter() - start) * 1000
        blocks = result['blok']
        purity = '–' if result['kemurnian_tim'] is None else num(result['kemurnian_tim'], 3)
        rows.append([name, published, f'{result["kelompok"]} / {result["tiket_terkelompok"]} / {purity}', num(elapsed, 0)])

    rng = np.random.default_rng(SEED)
    outcomes = Counter(shuffled_run(times, centered, rng) for _ in range(ORDERS))
    orders = [[f'{g} / {m}', count] for (g, m), count in outcomes.most_common()]
    replace_section(report, MARKS, '\n'.join([
        '## Reproduksi (C.8)', '',
        f'`ai/scripts/banding_pola.py`: {num(len(times))} insiden, {num(blocks)} blok berisi ≥ 3 insiden.', '',
        table(['Metode', 'Laporan: kelompok / tiket / kemurnian', 'Reproduksi', 'Waktu (ms)'], rows), '',
        f'Sebaran {ORDERS} urutan acak metode rata-rata (acuan laporan: 13× 7/22, 17× 8/25):', '',
        table(['Kelompok / tiket', 'Jumlah urutan'], orders), '',
        '**Selisih wajar.** Baris 7/22 di tabel awal berasal dari urutan non-waktu, jadi pembanding yang benar adalah baris '
        'urutan waktu. Benih acak uji awal tidak tercatat, sehingga sebaran urutan acak bisa bergeser tanpa mengubah '
        'kesimpulan. Waktu bergantung beban mesin. Vektor sama selama `pola_uji.npz` dan indeks aktif tidak dibangun ulang.',
    ]))
    print(f'→ {report}')


if __name__ == '__main__':
    main()
