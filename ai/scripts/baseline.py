"""Baseline pembanding dashboard dari history versi baru → plugins/halosis/baseline.json + reports/eda.md.

- Kepatuhan SLA: `overall_sla_result_extended` MET ÷ (MET + OVERDUE); UNKNOWN / tanpa bukti SLA dikecualikan.
  Jumlah hasil yang memakai komponen imputasi (`overall_sla_result_basis` = IMPUTED, DQR-04 kolom `sla_imputasi`)
  dicatat, beserta kepatuhan bila hanya hasil asli (NATIVE) yang dihitung.
- Kepuasan: `rating_value` 1–5 (survei ESTIM); rata-rata dan % ≥ 4.
Hanya angka; dibaca Stats.php (kartu KPI dashboard). Bila berkas tidak ada, dashboard tanpa baseline.

Pakai: .venv/bin/python ai/scripts/baseline.py
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'ai/scripts'))
from prepare_data import RAW  # noqa: E402

SRC = ROOT / 'data/processed/tickets_clean.parquet'
OUT = ROOT / 'plugins/halosis/baseline.json'
REPORT = ROOT / 'reports/eda.md'
MARK_START, MARK_END = '<!-- baseline:mulai -->', '<!-- baseline:selesai -->'


def compute(df: pd.DataFrame) -> dict:
    result = df['overall_sla_result_extended'].astype('string')
    decided = result.isin(['MET', 'OVERDUE'])
    imputed = df['sla_imputasi'].fillna(False).astype(bool)
    native = decided & ~imputed
    met = result == 'MET'
    rating = pd.to_numeric(df['rating_value'], errors='coerce').dropna()
    rating = rating[rating.between(1, 5)]
    pct = lambda part, whole: round(float(part) * 100 / float(whole), 2) if whole else None  # noqa: E731
    return {
        'sumber': f'data/raw/{RAW.name}', 'dibuat': date.today().isoformat(), 'tiket': int(len(df)),
        'sla': {
            'met': int(met.sum()), 'overdue': int((result == 'OVERDUE').sum()), 'persen': pct(met.sum(), decided.sum()),
            'dikecualikan': int((~decided).sum()), 'imputasi': int((decided & imputed).sum()),
            'persen_tanpa_imputasi': pct((met & native).sum(), native.sum()), 'tanpa_imputasi': int(native.sum()),
        },
        'kepuasan': {
            'dinilai': int(len(rating)), 'rata_rata': round(float(rating.mean()), 2) if len(rating) else None,
            'persen_puas': pct((rating >= 4).sum(), len(rating)),
            'distribusi': {str(int(k)): int(v) for k, v in rating.value_counts().sort_index().items()},
        },
    }


def main() -> None:
    b = compute(pd.read_parquet(SRC))
    OUT.write_text(json.dumps(b, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    num = lambda v: f'{v:,}'.replace(',', '.')  # noqa: E731
    dec = lambda v: '–' if v is None else f'{v:.2f}'.replace('.', ',')  # noqa: E731
    s, k = b['sla'], b['kepuasan']
    section = '\n'.join([
        MARK_START, '## Baseline dashboard (history versi baru)', '',
        f'`ai/scripts/baseline.py` · {b["dibuat"]} · sumber `{b["sumber"]}` · dibaca dashboard dari '
        '`plugins/halosis/baseline.json`.', '',
        '| Indikator | Nilai | Rincian |', '| --- | ---: | --- |',
        f'| Kepatuhan SLA (`overall_sla_result_extended`) | **{dec(s["persen"])}%** | MET {num(s["met"])} ÷ (MET + OVERDUE '
        f'{num(s["overdue"])}); UNKNOWN / tanpa bukti SLA {num(s["dikecualikan"])} dikecualikan |',
        f'| … hasil berimputasi (DQR-04) | {num(s["imputasi"])} | komponen SLA diestimasi (jam kerja); ditandai '
        '`sla_imputasi` |',
        f'| … hanya hasil asli (tanpa imputasi) | {dec(s["persen_tanpa_imputasi"])}% | {num(s["tanpa_imputasi"])} tiket |',
        f'| Kepuasan (rating 1–5) | **{dec(k["persen_puas"])}% ≥ 4** | {num(k["dinilai"])} tiket dinilai '
        f'({dec(100 * k["dinilai"] / b["tiket"])}% dari {num(b["tiket"])}), rata-rata {dec(k["rata_rata"])}; '
        + ', '.join(f'{r}★ {num(n)}' for r, n in k['distribusi'].items()) + ' |', '',
        'Baseline lama 27,59% (`overall_sla_result` PASS ÷ PASS + BREACH, ekspor lama) diganti angka di atas. Kepuasan '
        'hanya dari tiket yang dinilai pemohon (bias responden: sebagian besar 5★).', MARK_END])
    text = REPORT.read_text(encoding='utf-8')
    if MARK_START in text:
        text = re.sub(re.escape(MARK_START) + '.*?' + re.escape(MARK_END), lambda _: section, text, flags=re.S)
    else:
        text = text.rstrip('\n') + '\n\n' + section + '\n'
    REPORT.write_text(text, encoding='utf-8')
    print(json.dumps(b, ensure_ascii=False))


if __name__ == '__main__':
    main()
