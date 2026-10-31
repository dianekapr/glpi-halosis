"""T4: klasifier ringan jenis tiket (REQ permintaan / INC insiden) dari judul + deskripsi → ai/models/jenis.joblib.

Terpisah dari model triase (triage.joblib tidak disentuh). Pembagian waktu sama dengan train_triage.py
(latih < 1 Jul 2026, uji ≥ 1 Jul 2026). Fitur TF-IDF kata + karakter, Logistic Regression terkalibrasi.
Laporan (hanya angka) ditulis ke reports/triase.md di antara penanda "jenis".

Pakai: .venv/bin/python ai/scripts/train_jenis.py
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai.triage_model import build_pipeline, jenis_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data/processed/tickets_clean.parquet'
OUT = ROOT / 'ai/models/jenis.joblib'
REPORT = ROOT / 'reports/triase.md'
TRAIN_END = pd.Timestamp('2026-07-01')
THRESHOLD = 0.70  # sama dengan ambang keyakinan triase: di bawahnya saran jenis tidak ditampilkan
MARK_START, MARK_END = '<!-- jenis:mulai -->', '<!-- jenis:selesai -->'


def main() -> None:
    df = pd.read_parquet(SRC, columns=['ticket_type', 'short_description', 'description', 'opened'])
    df['jenis'] = df['ticket_type'].astype(str).str.upper().str[:3]
    df = df[df['jenis'].isin(['REQ', 'INC'])].copy()
    df['opened'] = pd.to_datetime(df['opened'], errors='coerce')
    df['text'] = [jenis_text(t, d) for t, d in zip(df['short_description'], df['description'])]
    train, test = df[df['opened'] < TRAIN_END], df[df['opened'] >= TRAIN_END]

    pipeline = build_pipeline(c=3.0, class_weight='balanced', calibrate=True).fit(train['text'], train['jenis'])
    probs = pipeline.predict_proba(test['text'])
    classes = np.array(pipeline.classes_)
    pred, conf = classes[probs.argmax(axis=1)], probs.max(axis=1)
    sure = conf >= THRESHOLD
    metrics = {
        'latih': len(train), 'uji': len(test),
        'akurasi': accuracy_score(test['jenis'], pred),
        'f1_makro': f1_score(test['jenis'], pred, average='macro'),
        'pembanding': float((test['jenis'] == train['jenis'].value_counts().index[0]).mean()),
        'cakupan_yakin': float(sure.mean()),
        'akurasi_yakin': accuracy_score(test['jenis'][sure], pred[sure]) if sure.any() else float('nan'),
        'beda_yakin': int((sure & (pred != test['jenis'].to_numpy())).sum()),
    }
    version = f'jenis-tfidf-lr-{date.today():%Y%m%d}'
    OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'pipeline': pipeline, 'version': version, 'threshold': THRESHOLD, 'metrics': metrics}, OUT, compress=3)

    pct = lambda v: f'{v * 100:.2f}%'.replace('.', ',')  # noqa: E731
    section = '\n'.join([
        MARK_START, '## Saran jenis tiket REQ/INC (T4)', '',
        f'Versi `{version}` · `ai/scripts/train_jenis.py` · artefak `ai/models/jenis.joblib` (di-ignore git). '
        f'Input judul + deskripsi (tersamar), tanpa token jenis; pembagian waktu sama dengan model tim.', '',
        '| Indikator | Nilai |', '| --- | --- |',
        f'| Data latih / uji | {metrics["latih"]:,} / {metrics["uji"]:,} tiket |'.replace(',', '.'),
        f'| **Akurasi** | **{pct(metrics["akurasi"])}** |',
        f'| F1 makro | {pct(metrics["f1_makro"])} |',
        f'| Pembanding: selalu jenis terbanyak | {pct(metrics["pembanding"])} |',
        f'| Keyakinan ≥ {int(THRESHOLD * 100)}% (saran ditampilkan) | akurasi {pct(metrics["akurasi_yakin"])} · cakupan {pct(metrics["cakupan_yakin"])} tiket |',
        f'| Tiket uji yang yakin tetapi berbeda dari jenis asli | {metrics["beda_yakin"]} |', '',
        'Panel Saran AI menampilkan "Jenis disarankan" hanya bila saran berbeda dari jenis tiket dan keyakinan ≥ ambang; '
        'Operator tetap memutuskan (ubah jenis di form tiket).', MARK_END])
    text = REPORT.read_text(encoding='utf-8')
    if MARK_START in text:
        text = re.sub(re.escape(MARK_START) + '.*?' + re.escape(MARK_END), section, text, flags=re.S)
    else:
        text = text.rstrip('\n') + '\n\n' + section + '\n'
    REPORT.write_text(text, encoding='utf-8')
    print(f'{version}: akurasi {pct(metrics["akurasi"])}, F1 makro {pct(metrics["f1_makro"])}, '
          f'yakin ≥ {THRESHOLD:.0%}: akurasi {pct(metrics["akurasi_yakin"])} cakupan {pct(metrics["cakupan_yakin"])}')


if __name__ == '__main__':
    main()
