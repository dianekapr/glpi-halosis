"""Klasifier ringan prioritas INSIDEN (Medium vs Low) dari judul + deskripsi → ai/models/prioritas.joblib.

Label = tier `resolution_sla_name` history ESTIM (proksi prioritas: "SLA Incident Resolution Medium 8Days" /
"Low 15Days"); "Crit 2Days" hanya 9 tiket sehingga tetap lewat aturan. Urgensi & dampak tidak dimodelkan (2.1.4:
Urgency P2; E9). Pembagian waktu sama dengan model tim (latih < 1 Jul 2026, uji ≥ 1 Jul 2026).
Metrik (F1 makro, akurasi, pembanding kelas mayoritas, akurasi pada ambang, tanggal, versi) disimpan di artefak;
layanan AI hanya memakai model bila F1 makro mengungguli pembanding. Laporan (angka saja) → reports/triase.md.

Pakai: .venv/bin/python ai/scripts/train_prioritas.py
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import openpyxl
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import quality  # noqa: E402
from halosis_ai.triage_model import build_pipeline, jenis_text  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'data/raw/ticketing_history_202601_202608.xlsx'
SRC = ROOT / 'data/processed/tickets_clean.parquet'
OUT = ROOT / 'ai/models/prioritas.joblib'
REPORT = ROOT / 'reports/triase.md'
TRAIN_END = pd.Timestamp('2026-07-01')
THRESHOLD = 0.70
TIERS = {'Medium': 'SLA Incident Resolution Medium 8Days', 'Low': 'SLA Incident Resolution Low 15Days'}
MARK_START, MARK_END = '<!-- prioritas:mulai -->', '<!-- prioritas:selesai -->'


def sla_tiers() -> pd.Series:
    """Nomor tiket → tier (Medium/Low) dari kolom resolution_sla_name ekspor mentah (hanya dua kolom dibaca)."""
    ws = openpyxl.load_workbook(RAW, read_only=True).active
    rows = ws.iter_rows(values_only=True)
    head = list(next(rows))
    i_num, i_sla = head.index('ticket_number'), head.index('resolution_sla_name')
    names = {v: k for k, v in TIERS.items()}
    pairs = {r[i_num]: names[r[i_sla]] for r in rows if r[i_sla] in names}
    return pd.Series(pairs, name='tier')


def main() -> None:
    df = pd.read_parquet(SRC, columns=['ticket_number', 'ticket_type', 'short_description', 'description', 'opened'])
    df = df[df['ticket_type'].astype(str).str.upper().str.startswith('INC')].join(sla_tiers(), on='ticket_number', how='inner')
    df['opened'] = pd.to_datetime(df['opened'], errors='coerce')
    df['text'] = [jenis_text(t, d) for t, d in zip(df['short_description'], df['description'])]
    train, test = df[df['opened'] < TRAIN_END], df[df['opened'] >= TRAIN_END]

    pipeline = build_pipeline(c=3.0, class_weight='balanced', calibrate=True).fit(train['text'], train['tier'])
    probs = pipeline.predict_proba(test['text'])
    classes = np.array(pipeline.classes_)
    pred, conf = classes[probs.argmax(axis=1)], probs.max(axis=1)
    majority = train['tier'].value_counts().index[0]
    sure = conf >= THRESHOLD
    version = f'prioritas-tfidf-lr-{date.today():%Y%m%d}'
    metrics = {
        'versi': version, 'tanggal': date.today().isoformat(), 'latih': int(len(train)), 'uji': int(len(test)),
        'distribusi_latih': {k: int(v) for k, v in train['tier'].value_counts().items()},
        'akurasi': round(float(accuracy_score(test['tier'], pred)), 4),
        'f1_makro': round(float(f1_score(test['tier'], pred, average='macro')), 4),
        'pembanding_kelas': majority,
        'pembanding_akurasi': round(float((test['tier'] == majority).mean()), 4),
        'f1_makro_pembanding': round(float(f1_score(test['tier'], [majority] * len(test), average='macro')), 4),
        'ambang': THRESHOLD, 'cakupan_yakin': round(float(sure.mean()), 4),
        'akurasi_yakin': round(float(accuracy_score(test['tier'][sure], pred[sure])), 4) if sure.any() else None,
    }
    gate = quality.check('prioritas', metrics)
    # Tier history → nilai prioritas GLPI (sama dengan config/sla_layanan.json): Medium → Sedang (3), Low → Rendah (2)
    joblib.dump({'pipeline': pipeline, 'version': version, 'threshold': THRESHOLD, 'metrics': metrics,
                 'prioritas_glpi': {'Medium': 3, 'Low': 2}}, OUT, compress=3)

    pct = lambda v: '–' if v is None else f'{v * 100:.2f}%'.replace('.', ',')  # noqa: E731
    section = '\n'.join([
        MARK_START, '## Saran prioritas insiden (BR-05, 2.1.4 Priority P1)', '',
        f'Versi `{version}` · `ai/scripts/train_prioritas.py` · artefak `ai/models/prioritas.joblib` (di-ignore git). '
        'Label = tier `resolution_sla_name` history (Medium 8 hari / Low 15 hari) sebagai proksi prioritas; '
        'Crit (9 tiket) & urgensi/dampak tetap aturan.', '',
        '| Indikator | Nilai |', '| --- | --- |',
        f'| Data latih / uji (insiden) | {metrics["latih"]} / {metrics["uji"]} tiket |',
        f'| **F1 makro** | **{pct(metrics["f1_makro"])}** |',
        f'| Akurasi | {pct(metrics["akurasi"])} |',
        f'| Pembanding: selalu {majority} | akurasi {pct(metrics["pembanding_akurasi"])} · F1 makro {pct(metrics["f1_makro_pembanding"])} |',
        f'| Keyakinan ≥ {int(THRESHOLD * 100)}% | akurasi {pct(metrics["akurasi_yakin"])} · cakupan {pct(metrics["cakupan_yakin"])} tiket |',
        f'| Gerbang kualitas (F1 makro > pembanding) | {"lolos" if gate["lolos"] else "tidak lolos"} |', '',
        'Dipakai di saran prioritas insiden hanya bila gerbang lolos dan keyakinan ≥ ambang; selain itu prioritas dari '
        'matriks urgensi × dampak GLPI (aturan). Operator tetap memutuskan.', MARK_END])
    text = REPORT.read_text(encoding='utf-8')
    if MARK_START in text:
        text = re.sub(re.escape(MARK_START) + '.*?' + re.escape(MARK_END), section, text, flags=re.S)
    else:
        text = text.rstrip('\n') + '\n\n' + section + '\n'
    REPORT.write_text(text, encoding='utf-8')
    print({k: metrics[k] for k in ('latih', 'uji', 'akurasi', 'f1_makro', 'pembanding_akurasi', 'f1_makro_pembanding', 'akurasi_yakin', 'cakupan_yakin')}, 'lolos' if gate['lolos'] else 'tidak lolos')


if __name__ == '__main__':
    main()
