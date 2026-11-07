"""C.8: reproduksi reports/banding_embedding.md (MiniLM vs e5) → blok berpenanda di laporan yang sama. Hanya angka.

Set uji laporan memakai ekspor lama + aturan solusi lama. Keduanya dibangun ulang di folder sementara: skrip
prepare_data.py versi commit bb32006 dijalankan atas data/raw/ticketing_history_202601_202608.xlsx, sehingga
data/processed/ tidak tersentuh. Baris kedua memakai qa_pairs aktif (ekspor baru) sebagai pembanding.

Korpus: Masalah + Solusi tiket dibuka Jan–Jun. Kueri: masalah tiket Jul–Ags. Relevan: tiket korpus dari tim yang sama.
Top-1/Top-3/MRR@10 per kosinus; e5 memakai awalan query:/passage:. Indeks aktif tidak dipakai atau diubah.

Pakai: .venv/bin/python ai/scripts/banding_embedding.py
Uji cepat: tambahkan --sampel 50 --keluar <folder sementara>
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tarfile
import tempfile
import time
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eda import num  # noqa: E402
from halosis_ai import search  # noqa: E402
from replikasi_poc import minilm  # noqa: E402
from train_triage import f, replace_section, table  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / 'data/processed/qa_pairs.parquet'
REPORT = ROOT / 'reports/banding_embedding.md'
OLD_COMMIT = 'bb32006'
OLD_PATHS = ('ai/halosis_ai', 'ai/scripts/prepare_data.py')
SPLIT = pd.Timestamp('2026-07-01')
K, BATCH = 10, 256
PUBLISHED = {'MiniLM': (0.6799, 0.8355, 0.7650), 'e5': (0.7274, 0.8962, 0.8144)}
MARKS = ('<!-- reproduksi:mulai -->', '<!-- reproduksi:selesai -->')


def old_pairs() -> pd.DataFrame:
    """qa_pairs ekspor lama + aturan lama, dibangun dengan kode commit lama di folder sementara."""
    with tempfile.TemporaryDirectory(prefix='qa-lama-') as folder:
        work = Path(folder)
        archive = subprocess.run(['git', '-C', str(ROOT), 'archive', '--format=tar', OLD_COMMIT, *OLD_PATHS],
                                 check=True, capture_output=True).stdout
        with tarfile.open(fileobj=BytesIO(archive)) as tar:
            tar.extractall(work, filter='data')
        (work / 'data').mkdir()
        (work / 'data/raw').symlink_to(ROOT / 'data/raw')
        done = subprocess.run([sys.executable, str(work / 'ai/scripts/prepare_data.py')], capture_output=True, text=True,
                              env={**os.environ, 'PYTHONWARNINGS': 'ignore'})
        if done.returncode:  # stderr bisa memuat cuplikan data, jadi hanya baris terakhir jenis galatnya
            last = done.stderr.strip().splitlines()[-1].split(':')[0] if done.stderr.strip() else 'tidak diketahui'
            raise SystemExit(f'prepare_data lama gagal (exit {done.returncode}, {last})')
        return pd.read_parquet(work / 'data/processed/qa_pairs.parquet')


def split_set(qa: pd.DataFrame, sample: int | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    qa = qa[qa['solusi'].fillna('').str.strip().str.len() > 0].copy()
    qa['tanggal'] = pd.to_datetime(qa['tanggal'], errors='coerce')
    corpus, queries = qa[qa['tanggal'] < SPLIT], qa[qa['tanggal'] >= SPLIT]
    print(f'Set penuh: korpus {len(corpus)}, kueri {len(queries)}')
    if sample:
        corpus, queries = corpus.head(sample), queries.head(max(sample // 5, 2))
    return corpus.reset_index(drop=True), queries.reset_index(drop=True)


def rank_metrics(queries: np.ndarray, corpus: np.ndarray, query_teams: np.ndarray, corpus_teams: np.ndarray) -> tuple:
    ranks = []
    for start in range(0, len(queries), BATCH):
        scores = queries[start:start + BATCH] @ corpus.T
        k = min(K, corpus.shape[0])
        top = np.argsort(-scores, axis=1, kind='stable')[:, :k]
        hit = corpus_teams[top] == query_teams[start:start + BATCH, None]
        ranks.extend(np.where(hit.any(axis=1), hit.argmax(axis=1) + 1, 0))
    ranks = np.asarray(ranks)
    return float((ranks == 1).mean()), float(((ranks > 0) & (ranks <= 3)).mean()), \
        float(np.where(ranks > 0, 1.0 / np.maximum(ranks, 1), 0.0).mean())


def evaluate(name: str, qa: pd.DataFrame, sample: int | None) -> list[list]:
    corpus, queries = split_set(qa, sample)
    corpus_text = [f'Masalah: {m} Solusi: {s}' for m, s in zip(corpus['masalah'], corpus['solusi'])]
    query_text = queries['masalah'].astype(str).tolist()
    corpus_teams = corpus['tim'].astype(str).to_numpy()
    query_teams = queries['tim'].astype(str).to_numpy()
    print(f'{name}: korpus {len(corpus)}, kueri {len(queries)}, tim {pd.Series(corpus_teams).nunique()}')
    rows = []
    for model, encode_corpus, encode_query in (('MiniLM', minilm, minilm),
                                               ('e5', lambda t: search.embed(t, 'passage'), lambda t: search.embed(t, 'query'))):
        start = time.perf_counter()
        corpus_vectors = encode_corpus(corpus_text)
        index_seconds = time.perf_counter() - start
        start = time.perf_counter()
        query_vectors = encode_query(query_text)
        query_ms = (time.perf_counter() - start) * 1000 / max(len(query_text), 1)
        top1, top3, mrr = rank_metrics(query_vectors, corpus_vectors, query_teams, corpus_teams)
        rows.append([name, model, num(len(corpus)), num(len(queries)), f(top1), f(top3), num(mrr, 4),
                     num(index_seconds, 1), num(query_ms, 1)])
    return rows


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
    rows = evaluate('Ekspor lama + aturan lama', old_pairs(), args.sampel)
    rows += evaluate('Ekspor aktif', pd.read_parquet(QA), args.sampel)
    published = [[k, f(v[0]), f(v[1]), num(v[2], 4)] for k, v in PUBLISHED.items()]
    replace_section(report, MARKS, '\n'.join([
        '## Reproduksi (C.8)', '',
        f'`ai/scripts/banding_embedding.py`. Baris *ekspor lama* dibangun dari kode `{OLD_COMMIT}` di folder sementara.', '',
        table(['Set', 'Model', 'Korpus', 'Kueri', 'Top-1', 'Top-3', 'MRR', 'Indeks (dtk)', 'Per kueri (ms)'], rows), '',
        'Angka laporan awal (31 Okt 2026):', '', table(['Model', 'Top-1', 'Top-3', 'MRR'], published), '',
        '**Selisih wajar.** Baris ekspor lama diharapkan sama atau hanya berbeda kecil, karena versi sentence-transformers/'
        'torch dan perangkat bisa mengubah digit akhir vektor. Waktu proses bergantung beban mesin. Bentuk teks korpus '
        'mengikuti deskripsi laporan, bukan skrip aslinya yang tidak tersimpan. Baris ekspor aktif berbeda karena korpus, '
        'kueri, dan aturan solusinya berbeda, jadi bukan selisih model.',
    ]))
    print(f'→ {report}')


if __name__ == '__main__':
    main()
