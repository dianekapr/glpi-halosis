"""Hitung metrik gerbang kualitas untuk model triase YANG SUDAH ADA (tanpa melatih ulang) →
ai/models/triage.metrics.json (berkas pendamping; dibaca halosis-ai, T32). Set uji = train_triage.py (Jul–Ags 2026).

Pakai: .venv/bin/python ai/scripts/model_metrics.py
Hanya tambah kurva ambang ke metrik tercatat (nilai lain tetap, cadangan dulu): ... model_metrics.py --kurva
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import f1_score, recall_score

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parent)]
from halosis_ai import quality  # noqa: E402
import train_triage as tt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT / 'ai/models/triage.joblib'
BIG_TEAM_SHARE = 0.05  # "tim besar" = ≥ 5% tiket uji


def compute(model, df) -> dict:
    """Metrik gerbang satu model triase pada set uji df (Jul–Ags), label tim dari data latih df."""
    train, test = df[df['opened'] < tt.TRAIN_END], df[df['opened'] >= tt.TRAIN_END]
    labels = tt.label_teams(test, train)
    s = tt.evaluate(model.pipeline, test['text'], labels)
    confident = s['confidence'] >= model.threshold
    correct = s['predicted'] == np.asarray(labels)
    big = labels.value_counts(normalize=True)
    # Kelas gabungan "Lainnya" (tim kecil) bukan tim; recall-nya dicatat terpisah, tidak ikut syarat tim besar
    big = [t for t, share in big.items() if share >= BIG_TEAM_SHARE and t != tt.OTHER]
    recalls = recall_score(labels, s['predicted'], labels=big, average=None, zero_division=0)
    other = float(recall_score(labels, s['predicted'], labels=[tt.OTHER], average=None, zero_division=0)[0])
    return {
        'versi': model.version, 'tanggal': date.today().isoformat(),
        'tiket_uji': int(len(test)), 'top1': round(float(s['top1']), 4), 'top3': round(float(s['top3']), 4),
        'mrr': round(float(s['mrr']), 4), 'f1_makro': round(float(f1_score(labels, s['predicted'], average='macro', zero_division=0)), 4),
        'ambang': float(model.threshold), 'akurasi_yakin': round(float(correct[confident].mean()), 4),
        'cakupan_yakin': round(float(confident.mean()), 4),
        'tim_besar': len(big), 'recall_tim_besar_min': round(float(recalls.min()), 4),
        'recall_lainnya': round(other, 4), 'kurva_ambang': quality.threshold_curve(s['confidence'], correct),
    }


def write(metrics: dict) -> None:
    MODEL.with_suffix('.metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> None:
    computed = compute(joblib.load(MODEL), tt.load())
    if '--kurva' in sys.argv:
        recorded = json.loads(MODEL.with_suffix('.metrics.json').read_text(encoding='utf-8'))
        folder = quality.backup_artifacts(MODEL.parent, ROOT / 'backup')
        write({**recorded, 'kurva_ambang': computed['kurva_ambang']})
        print(f'Cadangan: {folder.relative_to(ROOT)}. Tercatat akurasi_yakin {recorded["akurasi_yakin"]}, cakupan '
              f'{recorded["cakupan_yakin"]}; hitung ulang {computed["akurasi_yakin"]}, {computed["cakupan_yakin"]}')
        for percent in (40, 50, 60, 65, 70, 75, 80, 90, 95, 99):
            print(percent, computed['kurva_ambang'][str(percent)])
        return
    metrics = {**computed, 'dihitung_ulang_tanpa_latih': True}
    write(metrics)
    print(json.dumps({k: v for k, v in metrics.items() if k != 'kurva_ambang'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
