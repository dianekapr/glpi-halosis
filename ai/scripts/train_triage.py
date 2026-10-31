"""AI-3: latih & evaluasi model saran triase → ai/models/triage.joblib + reports/triase.md.

- Target  : assignment_group_name akhir; tim < 30 tiket (di data latih) → "Lainnya".
- Input   : judul + deskripsi + jenis saja (info saat tiket dibuat). Kolom routing/reassignment/SLA/resolusi
            TIDAK dipakai.
- Split   : latih Jan–Jun, uji Jul–Ags. Pemilihan pengaturan: latih Jan–Mei, validasi Jun (data uji tidak ikut).
- Model   : TF-IDF kata + karakter → Logistic Regression, probabilitas terkalibrasi (sigmoid, 5-fold).

Hanya angka yang dicetak/ditulis ke laporan; model & indeks tiket mirip (berisi judul tersamar) disimpan di
ai/models/ yang di-ignore git.

Pakai (dari folder induk proyek):  .venv/bin/python ai/scripts/train_triage.py
"""
from __future__ import annotations

import sys
from collections import Counter
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import privacy  # noqa: E402
from halosis_ai.triage_model import (  # noqa: E402
    MANUAL_REVIEW_THRESHOLD, MIN_TEAM_TICKETS, OTHER, SimilarIndex, TriageModel, build_pipeline, model_text,
)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eda import num, pct  # noqa: E402  (format angka Indonesia)

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data/processed/tickets_clean.parquet'
MODEL_OUT = ROOT / 'ai/models/triage.joblib'
REPORT_OUT = ROOT / 'reports/triase.md'

TRAIN_END = pd.Timestamp('2026-07-01')   # latih: < 1 Jul (Jan–Jun), uji: ≥ 1 Jul (Jul–Ags)
VALID_START = pd.Timestamp('2026-06-01')  # pemilihan pengaturan: latih Jan–Mei, validasi Jun
GRID = [{'c': c, 'class_weight': w} for c in (3.0, 10.0, 30.0) for w in (None, 'balanced')]
VERSION = f'triase-tfidf-lr-{date.today():%Y%m%d}'


def load() -> pd.DataFrame:
    df = pd.read_parquet(SRC, columns=['ticket_number', 'ticket_type', 'short_description', 'description',
                                       'assignment_group_name', 'opened'])
    df = df[df['assignment_group_name'].notna()].copy()
    df['text'] = [model_text(t, d, k) for t, d, k in zip(df['short_description'], df['description'], df['ticket_type'])]
    return df


def label_teams(df: pd.DataFrame, reference: pd.DataFrame) -> pd.Series:
    """Tim dengan < MIN_TEAM_TICKETS tiket di data acuan (latih) digabung 'Lainnya'."""
    counts = reference['assignment_group_name'].value_counts()
    keep = set(counts[counts >= MIN_TEAM_TICKETS].index)
    return df['assignment_group_name'].where(df['assignment_group_name'].isin(keep), OTHER)


def evaluate(pipeline, texts: pd.Series, labels: pd.Series) -> dict:
    probs = pipeline.predict_proba(texts)
    classes = np.array(pipeline.classes_)
    predicted = classes[probs.argmax(axis=1)]
    confidence = probs.max(axis=1)
    # Top-3: tim sebenarnya ada di 3 probabilitas teratas (label yang tak dikenal model otomatis salah)
    top3_classes = classes[np.argsort(probs, axis=1)[:, ::-1][:, :3]]
    top3 = float((top3_classes == np.asarray(labels)[:, None]).any(axis=1).mean())
    return {
        'probs': probs, 'classes': classes, 'predicted': predicted, 'confidence': confidence,
        'top1': accuracy_score(labels, predicted), 'top3': top3,
        'f1_macro': f1_score(labels, predicted, average='macro', zero_division=0),
        'f1_weighted': f1_score(labels, predicted, average='weighted', zero_division=0),
    }


def select_settings(train: pd.DataFrame) -> tuple[dict, list[dict]]:
    fit = train[train['opened'] < VALID_START]
    valid = train[train['opened'] >= VALID_START]
    y_fit, y_valid = label_teams(fit, fit), label_teams(valid, fit)
    results = []
    for settings in GRID:
        pipeline = build_pipeline(calibrate=False, **settings).fit(fit['text'], y_fit)
        scores = evaluate(pipeline, valid['text'], y_valid)
        results.append({**settings, 'top1': scores['top1'], 'f1_macro': scores['f1_macro']})
    best = max(results, key=lambda r: (round(r['top1'], 3), r['f1_macro']))
    return {'c': best['c'], 'class_weight': best['class_weight']}, results


def table(headers, rows) -> str:
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |']
    return '\n'.join(lines + ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows])


def f(value: float, d: int = 2) -> str:
    return num(value * 100, d) + '%'


def main() -> None:
    df = load()
    train, test = df[df['opened'] < TRAIN_END], df[df['opened'] >= TRAIN_END]
    y_train, y_test = label_teams(train, train), label_teams(test, train)

    settings, grid = select_settings(train)
    pipeline = build_pipeline(calibrate=True, **settings).fit(train['text'], y_train)
    scores = evaluate(pipeline, test['text'], y_test)

    majority = y_train.value_counts().index[0]
    baseline_top1 = float((y_test == majority).mean())

    confident = scores['confidence'] >= MANUAL_REVIEW_THRESHOLD
    correct = scores['predicted'] == y_test.to_numpy()
    acc_hi = correct[confident].mean() if confident.any() else float('nan')
    acc_lo = correct[~confident].mean() if (~confident).any() else float('nan')

    # Kalibrasi: rata-rata keyakinan vs akurasi per pita
    bands = [(0.0, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 0.9), (0.9, 1.01)]
    calibration = []
    ece = 0.0
    for lo, hi in bands:
        mask = (scores['confidence'] >= lo) & (scores['confidence'] < hi)
        if mask.any():
            gap = abs(scores['confidence'][mask].mean() - correct[mask].mean())
            ece += gap * mask.mean()
            calibration.append([f'{num(lo * 100)}–{num(min(hi, 1) * 100)}%', num(int(mask.sum())),
                                f(scores['confidence'][mask].mean(), 1), f(correct[mask].mean(), 1)])

    labels_sorted = y_test.value_counts().index.tolist() + [c for c in scores['classes'] if c not in set(y_test)]
    precision, recall, f1, support = precision_recall_fscore_support(
        y_test, scores['predicted'], labels=labels_sorted, zero_division=0)
    per_team = [[team, num(int(s)), f(p, 1), f(r, 1), f(v, 1)]
                for team, p, r, v, s in zip(labels_sorted, precision, recall, f1, support) if s > 0]

    confusions = Counter((t, p) for t, p in zip(y_test, scores['predicted']) if t != p).most_common(10)

    # Pergeseran data: tim asli di balik "Lainnya" pada data uji, dengan jumlahnya di data latih
    train_counts = train['assignment_group_name'].value_counts()
    other_test = test.loc[y_test == OTHER, 'assignment_group_name'].value_counts().head(5)
    drift = [[team, num(int(train_counts.get(team, 0))), num(int(n))] for team, n in other_test.items()]

    # Simpan model + indeks tiket mirip (data latih) untuk penjelasan di layanan
    similar = SimilarIndex.fit(train['text'].tolist(), train['ticket_number'].astype(str).tolist(),
                               y_train.tolist(), train['short_description'].fillna('').astype(str).tolist())
    metadata = {
        'versi_model': VERSION, 'dilatih': str(date.today()), 'data_latih': 'Jan–Jun 2026', 'data_uji': 'Jul–Ags 2026',
        'tiket_latih': int(len(train)), 'tiket_uji': int(len(test)), 'kelas': len(scores['classes']),
        'pengaturan': settings, 'top1': round(float(scores['top1']), 4), 'top3': round(float(scores['top3']), 4),
        'f1_macro': round(float(scores['f1_macro']), 4), 'ambang': MANUAL_REVIEW_THRESHOLD,
    }
    model = TriageModel(pipeline=pipeline, similar=similar, version=VERSION, metadata=metadata)
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_OUT, compress=3)

    report = '\n'.join([
        '# Model saran triase HaloSIS (routing ke tim)',
        '',
        f'Versi `{VERSION}` · dibuat oleh `ai/scripts/train_triage.py`. Hanya angka; model disimpan di '
        '`ai/models/triage.joblib` (di-ignore git).',
        '',
        '## Ringkasan',
        '',
        table(['Indikator', 'Nilai'], [
            ['Data latih / uji', f'{num(len(train))} tiket Jan–Jun / {num(len(test))} tiket Jul–Ags 2026'],
            ['Kelas (tim)', f'{len(scores["classes"])} (tim < {MIN_TEAM_TICKETS} tiket di data latih → "{OTHER}")'],
            ['**Akurasi top-1**', f'**{f(scores["top1"])}**'],
            ['**Akurasi top-3**', f'**{f(scores["top3"])}**'],
            ['F1 makro / tertimbang', f'{f(scores["f1_macro"])} / {f(scores["f1_weighted"])}'],
            ['Pembanding: selalu tim terbanyak', f'{f(baseline_top1)} ("{majority}")'],
            [f'Keyakinan ≥ {num(MANUAL_REVIEW_THRESHOLD * 100)}% (saran bisa langsung diterima)',
             f'akurasi {f(acc_hi)} · cakupan {f(confident.mean())} tiket'],
            [f'Keyakinan < {num(MANUAL_REVIEW_THRESHOLD * 100)}% ("Perlu penilaian manual")',
             f'akurasi {f(acc_lo)} · cakupan {f((~confident).mean())} tiket'],
            ['Galat kalibrasi (ECE)', f(ece)],
        ]),
        '',
        '## Input & metode',
        '',
        '- Input hanya informasi saat tiket dibuat: **judul + deskripsi + jenis (INC/REQ)**, sudah disamarkan.',
        '  Kolom `routing_*`, `reassignment_*`, `team_change_*`, `*sla*`, dan resolusi **tidak dipakai**.',
        '- Target: `assignment_group_name` akhir.',
        '- Fitur: TF-IDF kata (1–2 gram) + karakter (3–5 gram, tahan salah ketik). Model: Logistic Regression,',
        '  probabilitas dikalibrasi (sigmoid, 5-fold) → "keyakinan" = probabilitas tim teratas.',
        '- Split berdasarkan waktu: latih Jan–Jun, uji Jul–Ags (meniru pemakaian nyata: model dilatih dari masa lalu).',
        '- Populasi (DQR-05): `data/processed/tickets_clean.parquet` (ekspor history tiket 2026 hasil `prepare_data.py`,',
        '  teks disamarkan); **semua status** (terbuka maupun selesai) dan **kedua jenis** INC & REQ (jenis menjadi fitur);',
        '  hanya tiket dengan `assignment_group_name` terisi (tanpa tim tidak punya label). Latih: `opened` < 1 Jul 2026;',
        f'  uji: `opened` ≥ 1 Jul 2026. Tim dengan < {MIN_TEAM_TICKETS} tiket di data latih → "Lainnya" (juga di data uji).',
        '- Pemilihan pengaturan tanpa menyentuh data uji: latih Jan–Mei, validasi Juni.',
        '',
        table(['C', 'Bobot kelas', 'Validasi Juni: top-1', 'F1 makro'],
              [[num(r['c']), r['class_weight'] or 'tidak', f(r['top1']), f(r['f1_macro'])] for r in grid]),
        '',
        f'Terpilih: C = {num(settings["c"])}, bobot kelas = {settings["class_weight"] or "tidak"}.',
        '',
        '## Keyakinan vs akurasi (data uji)',
        '',
        'Bila terkalibrasi baik, "rata-rata keyakinan" ≈ "akurasi" di setiap pita.',
        '',
        table(['Pita keyakinan', 'Tiket', 'Rata-rata keyakinan', 'Akurasi'], calibration),
        '',
        '## Per tim (data uji)',
        '',
        table(['Tim', 'Tiket uji', 'Presisi', 'Recall', 'F1'], per_team),
        '',
        '## Tim yang paling sering tertukar (data uji)',
        '',
        table(['Tim sebenarnya', 'Disarankan model', 'Tiket'], [[t, p, n] for (t, p), n in confusions]),
        '',
        '## Pergeseran data: tim di balik "Lainnya" (data uji)',
        '',
        f'Tim yang kecil/baru di Jan–Jun tetapi muncul di Jul–Ags tidak bisa dipelajari model; tiketnya jatuh ke "{OTHER}"',
        'atau ke tim lama yang mirip. Latih ulang berkala (mis. bulanan) mengatasi ini.',
        '',
        table(['Tim asli', 'Tiket latih (Jan–Jun)', 'Tiket uji (Jul–Ags)'], drift),
        '',
        '## Catatan',
        '',
        '- Akurasi diukur terhadap tim akhir di data history; tim akhir itu sendiri kadang hasil koreksi routing',
        '  (≈5,8% tiket berindikasi salah routing), jadi sebagian "salah" model bisa berarti kasus ambigu.',
        '- Tiket "Operator Pusat" (ditangani langsung operator) ikut menjadi kelas sendiri.',
        '- Pembanding retrieval + LLM (opsional) tidak dijalankan: proyek berjalan tanpa API key LLM, sehingga tidak',
        '  ada data yang dikirim ke API eksternal. Triase sepenuhnya memakai model lokal ini.',
    ])
    # Laporan hanya boleh berisi angka & nama tim: pindai pola data pribadi sebelum menulis
    leaks = {name: len(pattern.findall(report)) for name, pattern in {
        'email': privacy._EMAIL, 'nip': privacy._NIP, 'nik': privacy._NIK, 'telepon': privacy._PHONE,
        'password': privacy._SECRET,
    }.items()}
    if any(leaks.values()):
        raise SystemExit(f'Laporan memuat pola data pribadi, tidak ditulis: {leaks}')
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(report + '\n', encoding='utf-8')

    print(f'Data latih/uji     : {len(train)} / {len(test)} | kelas {len(scores["classes"])}')
    print(f'Pengaturan terpilih: {settings}')
    print(f'Akurasi top-1/top-3: {f(scores["top1"])} / {f(scores["top3"])} | F1 makro {f(scores["f1_macro"])}')
    print(f'Pembanding (tim terbanyak): {f(baseline_top1)}')
    print(f'Keyakinan ≥70%     : akurasi {f(acc_hi)} pada {f(confident.mean())} tiket')
    print(f'Keyakinan <70%     : akurasi {f(acc_lo)} pada {f((~confident).mean())} tiket')
    print(f'ECE                : {f(ece)}')
    print(f'Disimpan           : {MODEL_OUT.relative_to(ROOT)}, {REPORT_OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
