"""Klasifier urgensi INSIDEN (Medium vs Low) → ai/models/urgensi.joblib + urgensi.metrics.json (BR-05, 2.1.4).

Label = kolom `urgency` ekspor history versi baru. Dampak (`impact`) sama dengan urgensi pada 99,7% insiden dan
`priority` = matriks keduanya, jadi satu model urgensi cukup; dampak & prioritas diturunkan aturan (lihat Triage.php:
dampak = urgensi, naik satu tingkat bila banyak tiket serupa atau layanan kritis). High/Critical (± 21 tiket) dan
permintaan (REQ, hampir semuanya Medium) tidak dimodelkan: tetap aturan + sinyal.

Fitur: teks judul + deskripsi tersamar (TF-IDF kata + karakter) + nama tim (one-hot; saat dipakai = tim saran triase).
Model: Logistic Regression class_weight=balanced (label) + salinan terkalibrasi sigmoid (keyakinan). Evaluasi: validasi silang 5 lipatan
bertingkat (StratifiedKFold, seed tetap) pada seluruh insiden berlabel; model akhir dilatih pada semua data.
Gerbang (quality.check 'urgensi'): F1 makro harus mengungguli pembanding "selalu Medium". Layanan hanya menyarankan
bila lolos dan keyakinan ≥ ambang. Laporan (angka saja) → reports/triase.md (penanda "urgensi").

Pakai: .venv/bin/python ai/scripts/train_urgensi.py
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, recall_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import quality  # noqa: E402
from halosis_ai.triage_model import build_urgency_pipeline, jenis_text, urgency_confidence  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data/processed/tickets_clean.parquet'
OUT = ROOT / 'ai/models/urgensi.joblib'
REPORT = ROOT / 'reports/triase.md'
THRESHOLD = 0.70
LABELS = ('Medium', 'Low')
URGENCY_GLPI = {'Medium': 3, 'Low': 2}  # skala GLPI: 3 sedang, 2 rendah
FOLDS, SEED = 5, 42
MARK_START, MARK_END = '<!-- urgensi:mulai -->', '<!-- urgensi:selesai -->'
OLD_MARKS = ('<!-- prioritas:mulai -->', '<!-- prioritas:selesai -->')  # bagian model prioritas lama (dihapus)


def load() -> pd.DataFrame:
    df = pd.read_parquet(SRC, columns=['ticket_type', 'short_description', 'description', 'assignment_group_name',
                                       'urgency', 'impact'])
    df = df[df['ticket_type'].astype(str).str.upper().str.startswith('INC')].copy()
    df['label'] = df['urgency'].astype('string')
    df['teks'] = [jenis_text(t, d) for t, d in zip(df['short_description'], df['description'])]
    df['tim'] = df['assignment_group_name'].astype('string').fillna('').str.strip()
    return df


def main() -> None:
    all_inc = load()
    df = all_inc[all_inc['label'].isin(LABELS)].reset_index(drop=True)
    x, y = df[['teks', 'tim']], df['label'].to_numpy()
    folds = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    # Label dari LR seimbang (C=3, sama dengan model jenis; tidak di-tuning), keyakinan dari LR terkalibrasi
    pred = cross_val_predict(build_urgency_pipeline(), x, y, cv=folds)
    probs = cross_val_predict(build_urgency_pipeline(calibrate=True), x, y, cv=folds, method='predict_proba')
    classes = np.array(sorted(LABELS))  # urutan kelas sklearn
    conf = urgency_confidence(pred, probs, classes)
    argmax_pred = classes[probs.argmax(axis=1)]
    sure = conf >= THRESHOLD
    majority = pd.Series(y).value_counts().index[0]
    version = f'urgensi-tfidf-tim-lr-{date.today():%Y%m%d}'
    metrics = {
        'versi': version, 'tanggal': date.today().isoformat(), 'evaluasi': f'validasi silang {FOLDS} lipatan bertingkat',
        'insiden_berlabel': int(len(df)), 'distribusi': {k: int(v) for k, v in pd.Series(y).value_counts().items()},
        'tidak_dimodelkan': {k: int(v) for k, v in all_inc['label'].fillna('(kosong)').value_counts().items()
                             if k not in LABELS},
        'dampak_sama_urgensi': round(float((all_inc['impact'] == all_inc['urgency'])[
            all_inc['impact'].notna() & all_inc['urgency'].notna()].mean()), 4),
        'akurasi': round(float(accuracy_score(y, pred)), 4),
        'f1_makro': round(float(f1_score(y, pred, average='macro')), 4),
        'recall_low': round(float(recall_score(y, pred, labels=['Low'], average=None)[0]), 4),
        'recall_medium': round(float(recall_score(y, pred, labels=['Medium'], average=None)[0]), 4),
        'pembanding_kelas': majority,
        'pembanding_akurasi': round(float((y == majority).mean()), 4),
        'f1_makro_pembanding': round(float(f1_score(y, [majority] * len(y), average='macro')), 4),
        'ambang': THRESHOLD, 'cakupan_yakin': round(float(sure.mean()), 4),
        'akurasi_yakin': round(float(accuracy_score(y[sure], pred[sure])), 4) if sure.any() else None,
        'recall_low_yakin': round(float(((pred == 'Low') & sure & (y == 'Low')).sum() / max((y == 'Low').sum(), 1)), 4),
        'presisi_low': round(float(((pred == 'Low') & (y == 'Low')).sum() / max((pred == 'Low').sum(), 1)), 4),
        'f1_makro_argmax_terkalibrasi': round(float(f1_score(y, argmax_pred, average='macro')), 4),
    }
    gate = quality.check('urgensi', metrics)
    metrics['lolos_gerbang'] = gate['lolos']

    pipeline = build_urgency_pipeline().fit(x, y)
    calibrated = build_urgency_pipeline(calibrate=True).fit(x, y)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'pipeline': pipeline, 'kalibrasi': calibrated, 'version': version, 'threshold': THRESHOLD,
                 'metrics': metrics, 'urgensi_glpi': URGENCY_GLPI}, OUT, compress=3)
    OUT.with_suffix('.metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    pct = lambda v: '–' if v is None else f'{v * 100:.2f}%'.replace('.', ',')  # noqa: E731
    num = lambda v: f'{v:,}'.replace(',', '.')  # noqa: E731
    section = '\n'.join([
        MARK_START, '## Saran urgensi insiden (BR-05, 2.1.4 Urgency/Impact/Priority)', '',
        f'Versi `{version}` · `ai/scripts/train_urgensi.py` · artefak `ai/models/urgensi.joblib` + `urgensi.metrics.json` '
        '(di-ignore git). Label = kolom `urgency` history versi baru (insiden Medium vs Low). Dampak = urgensi pada '
        f'{pct(metrics["dampak_sama_urgensi"])} insiden dan prioritas = matriks keduanya, jadi satu model; '
        'model prioritas lama (proksi tier SLA) dihapus.', '',
        '| Indikator | Nilai |', '| --- | --- |',
        f'| Insiden berlabel (Medium / Low) | {num(metrics["distribusi"].get("Medium", 0))} / '
        f'{num(metrics["distribusi"].get("Low", 0))} |',
        f'| Evaluasi | {metrics["evaluasi"]} (seed {SEED}) |',
        f'| **F1 makro** | **{pct(metrics["f1_makro"])}** |',
        f'| Akurasi | {pct(metrics["akurasi"])} |',
        f'| Recall Low / Medium · presisi Low | {pct(metrics["recall_low"])} / {pct(metrics["recall_medium"])} · '
        f'{pct(metrics["presisi_low"])} |',
        f'| Pembanding: selalu {majority} | akurasi {pct(metrics["pembanding_akurasi"])} · F1 makro '
        f'{pct(metrics["f1_makro_pembanding"])} |',
        f'| Keyakinan ≥ {int(THRESHOLD * 100)}% (saran ditampilkan) | akurasi {pct(metrics["akurasi_yakin"])} · cakupan '
        f'{pct(metrics["cakupan_yakin"])} insiden · Low tertangkap {pct(metrics["recall_low_yakin"])} |',
        f'| Gerbang kualitas (F1 makro > pembanding) | **{"lolos" if gate["lolos"] else "tidak lolos"}** |', '',
        'Tidak dimodelkan (tetap aturan + sinyal): '
        + ', '.join(f'{k} {num(v)}' for k, v in metrics['tidak_dimodelkan'].items()) + ' insiden; permintaan (REQ).',
        f'Catatan label: {pct(metrics["pembanding_akurasi"])} insiden berlabel Medium; sebagian besar kemungkinan nilai '
        'bawaan formulir, bukan penilaian petugas, sehingga batas atas akurasi model terbatas.',
        'Label = LR berbobot kelas seimbang (C = 3, sama dengan model jenis); keyakinan = probabilitas model '
        'terkalibrasi (sigmoid) untuk label itu. Argmax model terkalibrasi saja hampir selalu memilih Medium '
        f'(F1 makro {pct(metrics["f1_makro_argmax_terkalibrasi"])}).', '',
        'Panel Saran AI menampilkan "Urgensi disarankan" + keyakinan hanya bila gerbang lolos dan keyakinan ≥ ambang; '
        'selain itu urgensi dari aturan kata kunci. Dampak = urgensi, naik satu tingkat bila ≥ 3 tiket serupa dalam '
        '60 menit atau layanan kritis (konfigurasi). Operator tetap memutuskan.', MARK_END])
    text = REPORT.read_text(encoding='utf-8')
    text = re.sub(re.escape(OLD_MARKS[0]) + '.*?' + re.escape(OLD_MARKS[1]) + r'\n?', '', text, flags=re.S)
    if MARK_START in text:
        text = re.sub(re.escape(MARK_START) + '.*?' + re.escape(MARK_END), lambda _: section, text, flags=re.S)
    else:
        text = text.rstrip('\n') + '\n\n' + section + '\n'
    REPORT.write_text(text, encoding='utf-8')
    print({k: metrics[k] for k in ('insiden_berlabel', 'akurasi', 'f1_makro', 'recall_low', 'pembanding_akurasi',
                                   'f1_makro_pembanding', 'akurasi_yakin', 'cakupan_yakin', 'recall_low_yakin')},
          'lolos' if gate['lolos'] else f'tidak lolos {gate["alasan"]}')


if __name__ == '__main__':
    main()
