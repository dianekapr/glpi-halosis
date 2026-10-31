"""Klasifier urgensi INSIDEN (Medium vs Low) → ai/models/urgensi.joblib + urgensi.metrics.json (BR-05, 2.1.4).

Label = kolom `urgency` ekspor history versi baru. Dampak (`impact`) sama dengan urgensi pada 99,7% insiden dan
`priority` = matriks keduanya, jadi satu model urgensi cukup; dampak & prioritas diturunkan aturan (lihat Triage.php:
dampak = urgensi, naik satu tingkat bila banyak tiket serupa atau layanan kritis). High/Critical (± 21 tiket) dan
permintaan (REQ, hampir semuanya Medium) tidak dimodelkan: tetap aturan + sinyal.

Fitur: teks judul + deskripsi tersamar (TF-IDF kata + karakter) + nama tim (one-hot; saat dipakai = tim saran triase).
Model: Logistic Regression class_weight=balanced → P(Low). Evaluasi: validasi silang 5 lipatan bertingkat
(StratifiedKFold, seed tetap) pada seluruh insiden berlabel; model akhir dilatih pada semua data.
Ambang per kelas dipilih otomatis dari P(Low) validasi silang (triage_model.pick_urgency_thresholds): Low bila
P(Low) ≥ ambang Low (presisi ≥ 75%, terendah = recall terbesar), Medium bila P(Low) ≤ ambang Medium (akurasi >
pembanding + 3 poin, tertinggi = cakupan terbesar), di antaranya aturan kata kunci. Gerbang per kelas
(quality.check 'urgensi'); kelas yang tidak lolos tidak pernah disarankan. Laporan (angka saja) → reports/triase.md
(penanda "urgensi").

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
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import quality  # noqa: E402
from halosis_ai.triage_model import build_urgency_pipeline, jenis_text, pick_urgency_thresholds  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data/processed/tickets_clean.parquet'
OUT = ROOT / 'ai/models/urgensi.joblib'
REPORT = ROOT / 'reports/triase.md'
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
    # LR seimbang (C=3, sama dengan model jenis; tidak di-tuning); kolom P(Low) = kelas 'Low' (urutan sklearn)
    probs = cross_val_predict(build_urgency_pipeline(), x, y, cv=folds, method='predict_proba')
    p_low = probs[:, list(np.array(sorted(LABELS))).index('Low')]
    pred = np.where(p_low >= 0.5, 'Low', 'Medium')  # keputusan tanpa ambang per kelas (informasi saja)
    kelas = pick_urgency_thresholds(p_low, y)
    majority = pd.Series(y).value_counts().index[0]
    version = f'urgensi-tfidf-tim-lr-{date.today():%Y%m%d}'
    metrics = {
        'versi': version, 'tanggal': date.today().isoformat(), 'evaluasi': f'validasi silang {FOLDS} lipatan bertingkat',
        'insiden_berlabel': int(len(df)), 'distribusi': {k: int(v) for k, v in pd.Series(y).value_counts().items()},
        'tidak_dimodelkan': {k: int(v) for k, v in all_inc['label'].fillna('(kosong)').value_counts().items()
                             if k not in LABELS},
        'dampak_sama_urgensi': round(float((all_inc['impact'] == all_inc['urgency'])[
            all_inc['impact'].notna() & all_inc['urgency'].notna()].mean()), 4),
        'kelas': kelas,
        'syarat': {'presisi_low_min': quality.MIN_PRECISION_LOW, 'tambahan_akurasi_medium': quality.MIN_GAIN_MEDIUM,
                   'tiket_min': quality.MIN_SUPPORT},
        # Tanpa ambang per kelas (argmax 0,5), untuk banding dengan versi 31 Okt
        'akurasi_argmax': round(float(accuracy_score(y, pred)), 4),
        'f1_makro_argmax': round(float(f1_score(y, pred, average='macro')), 4),
        'pembanding_kelas': majority,
        'pembanding_akurasi': round(float((y == majority).mean()), 4),
    }
    gate = quality.check('urgensi', metrics)
    metrics['lolos_gerbang'], metrics['kelas_lolos'] = gate['lolos'], gate['kelas_lolos']

    OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'pipeline': build_urgency_pipeline().fit(x, y), 'version': version,
                 'ambang': {k: v['ambang'] for k, v in kelas.items()}, 'metrics': metrics,
                 'urgensi_glpi': URGENCY_GLPI}, OUT, compress=3)
    OUT.with_suffix('.metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    pct = lambda v: '–' if v is None else f'{v * 100:.2f}%'.replace('.', ',')  # noqa: E731
    num = lambda v: f'{v:,}'.replace(',', '.')  # noqa: E731
    dec = lambda v: f'{v:.2f}'.replace('.', ',')  # noqa: E731
    status = lambda k: '**lolos**' if k in gate['kelas_lolos'] else '**tidak lolos** (tidak disarankan)'  # noqa: E731
    low, med = kelas['Low'], kelas['Medium']
    ci = low['wilson_95'] or [None, None]
    section = '\n'.join([
        MARK_START, '## Saran urgensi insiden (BR-05, 2.1.4 Urgency/Impact/Priority)', '',
        f'Versi `{version}` · `ai/scripts/train_urgensi.py` · artefak `ai/models/urgensi.joblib` + `urgensi.metrics.json` '
        '(di-ignore git). Label = kolom `urgency` history versi baru (insiden Medium vs Low). Dampak = urgensi pada '
        f'{pct(metrics["dampak_sama_urgensi"])} insiden dan prioritas = matriks keduanya, jadi satu model; '
        'model prioritas lama (proksi tier SLA) dihapus.', '',
        f'Insiden berlabel Medium / Low: {num(metrics["distribusi"].get("Medium", 0))} / '
        f'{num(metrics["distribusi"].get("Low", 0))}; {metrics["evaluasi"]} (seed {SEED}); LR berbobot kelas seimbang '
        '→ P(Low). **Ambang per kelas** dipilih otomatis dari P(Low) validasi silang (bukan satu ambang keyakinan):',
        '',
        '| Kelas | Aturan | Hasil validasi silang | Pembanding | Gerbang |', '| --- | --- | --- | --- | --- |',
        f'| Low (Rendah) | P(Low) ≥ {dec(low["ambang"])} | presisi **{pct(low["presisi"])}** (Wilson 95% '
        f'{pct(ci[0])}–{pct(ci[1])}), recall {pct(low["recall"])}, {num(low["tiket"])} tiket | proporsi Low '
        f'{pct(low["pembanding"])} | {status("Low")} |',
        f'| Medium (Sedang) | P(Low) ≤ {dec(med["ambang"])} | akurasi **{pct(med["akurasi"])}**, cakupan '
        f'{pct(med["cakupan"])} insiden ({num(med["tiket"])}) | proporsi Medium {pct(med["pembanding"])} | '
        f'{status("Medium")} |',
        f'| Di antaranya | – | {pct(1 - low["cakupan"] - med["cakupan"])} insiden | – | aturan kata kunci |', '',
        f'Syarat (quality.urgency_class_check): Low presisi ≥ {pct(quality.MIN_PRECISION_LOW)}, batas bawah Wilson > '
        f'pembanding, ≥ {quality.MIN_SUPPORT} tiket (ambang terendah yang lolos = recall terbesar); Medium akurasi > '
        f'pembanding + {int(quality.MIN_GAIN_MEDIUM * 100)} poin, ≥ {quality.MIN_SUPPORT} tiket (ambang tertinggi yang '
        'lolos = cakupan terbesar). Kisi ambang 0,05.', '',
        f'**Keterbatasan cakupan Low:** hanya {pct(low["recall"])} insiden Low dikenali model; sisanya tetap dari '
        f'aturan kata kunci. Tanpa ambang per kelas (argmax 0,5): akurasi {pct(metrics["akurasi_argmax"])}, F1 makro '
        f'{pct(metrics["f1_makro_argmax"])} vs pembanding selalu {majority} {pct(metrics["pembanding_akurasi"])}.', '',
        'Tidak dimodelkan (tetap aturan + sinyal): '
        + ', '.join(f'{k} {num(v)}' for k, v in metrics['tidak_dimodelkan'].items()) + ' insiden; permintaan (REQ).',
        f'Catatan label: {pct(metrics["pembanding_akurasi"])} insiden berlabel Medium; sebagian besar kemungkinan nilai '
        'bawaan formulir, bukan penilaian petugas, sehingga batas atas akurasi model terbatas.', '',
        'Panel Saran AI menampilkan "Urgensi disarankan: Rendah/Sedang (keyakinan)" hanya bila kelas itu lolos gerbang '
        'dan P(Low) melewati ambangnya (keyakinan = P(Low) untuk Rendah, 1 − P(Low) untuk Sedang); selain itu urgensi '
        'dari aturan kata kunci. Dampak = urgensi, naik satu tingkat bila ≥ 3 tiket serupa dalam 60 menit atau layanan '
        'kritis (konfigurasi). Operator tetap memutuskan.', MARK_END])
    text = REPORT.read_text(encoding='utf-8')
    text = re.sub(re.escape(OLD_MARKS[0]) + '.*?' + re.escape(OLD_MARKS[1]) + r'\n?', '', text, flags=re.S)
    if MARK_START in text:
        text = re.sub(re.escape(MARK_START) + '.*?' + re.escape(MARK_END), lambda _: section, text, flags=re.S)
    else:
        text = text.rstrip('\n') + '\n\n' + section + '\n'
    REPORT.write_text(text, encoding='utf-8')
    print({k: {m: v[m] for m in ('ambang', 'tiket', 'presisi', 'wilson_95', 'recall', 'akurasi', 'cakupan', 'lolos')
               if m in v} for k, v in kelas.items()}, 'kelas lolos:', gate['kelas_lolos'])


if __name__ == '__main__':
    main()
