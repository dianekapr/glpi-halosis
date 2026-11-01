"""Baseline pembanding dashboard dari history versi baru → plugins/halosis/baseline.json + reports/eda.md.

- Kepatuhan SLA: `overall_sla_result_extended` MET ÷ (MET + OVERDUE); UNKNOWN / tanpa bukti SLA dikecualikan.
  Jumlah hasil yang memakai komponen imputasi (`overall_sla_result_basis` = IMPUTED, DQR-04 kolom `sla_imputasi`)
  dicatat, beserta kepatuhan bila hanya hasil asli (NATIVE) yang dihitung.
- Kepatuhan SLA respons: `response_sla_final_result` MET ÷ (MET + OVERDUE) (hasil akhir, termasuk imputasi
  `response_sla_result_basis` = IMPUTED); UNKNOWN / NA dikecualikan.
- Baseline dokumen (§5.2.1.5: overall 27,59%, respons 42,62%) disimpan apa adanya sebagai pembanding utama; beda
  metode dengan angka history versi baru dijelaskan di `metode` (ditulis ke baseline.json).
- Kepuasan: `rating_value` 1–5 (survei ESTIM); rata-rata, % ≥ 4, dan cakupan rating (dinilai ÷ semua tiket).
  Rating tidak wajib (dokumen §5.2.1: cakupan ± 15–16%), jadi kepuasan tinggi berisiko terlalu optimistis.
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
# Baseline resmi dokumen perancangan (§5.2.1.5 AS-IS SLA Management, data Jan–Ags 2026, ekspor lama)
DOCUMENT = {'overall': 27.59, 'respons': 42.62, 'sumber': 'dokumen §5.2.1.5 (validasi Jan–Ags 2026)'}
METHOD = {
    'dokumen': 'overall_sla_result / response_sla_result PASS ÷ (PASS + BREACH) pada ekspor lama (137 kolom; '
               '1.621 ÷ 5.876 dan 2.549 ÷ 5.981), tanpa imputasi; IN PROGRESS dikecualikan',
    'history_versi_baru': 'overall_sla_result_extended MET ÷ (MET + OVERDUE) pada ekspor 220 kolom; komponen SLA yang '
                          'tidak tercatat diestimasi (jam kerja, overall_sla_result_basis = IMPUTED) sehingga lebih '
                          'banyak tiket punya hasil; UNKNOWN / tanpa bukti SLA dikecualikan',
    'respons': 'response_sla_final_result MET ÷ (MET + OVERDUE), termasuk hasil berimputasi; UNKNOWN / NA dikecualikan',
    'kepuasan': 'rating_value 1–5, hanya tiket yang dinilai; rating tidak wajib (dokumen §5.2.1: cakupan ± 15–16%), '
                'klaim kepuasan tinggi berisiko terlalu optimistis',
}


def compute(df: pd.DataFrame) -> dict:
    result = df['overall_sla_result_extended'].astype('string')
    decided = result.isin(['MET', 'OVERDUE'])
    imputed = df['sla_imputasi'].fillna(False).astype(bool)
    native = decided & ~imputed
    met = result == 'MET'
    response = df['response_sla_final_result'].astype('string')
    response_decided = response.isin(['MET', 'OVERDUE'])
    response_imputed = df['response_sla_result_basis'].astype('string') == 'IMPUTED'
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
        'sla_respons': {
            'met': int((response == 'MET').sum()), 'overdue': int((response == 'OVERDUE').sum()),
            'persen': pct((response == 'MET').sum(), response_decided.sum()),
            'dikecualikan': int((~response_decided).sum()),
            'imputasi': int((response_decided & response_imputed).sum()),
        },
        'dokumen': DOCUMENT, 'metode': METHOD,
        'kepuasan': {
            'dinilai': int(len(rating)), 'cakupan_persen': pct(len(rating), len(df)),
            'rata_rata': round(float(rating.mean()), 2) if len(rating) else None,
            'persen_puas': pct((rating >= 4).sum(), len(rating)),
            'distribusi': {str(int(k)): int(v) for k, v in rating.value_counts().sort_index().items()},
        },
    }


def main() -> None:
    b = compute(pd.read_parquet(SRC))
    OUT.write_text(json.dumps(b, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    num = lambda v: f'{v:,}'.replace(',', '.')  # noqa: E731
    dec = lambda v: '–' if v is None else f'{v:.2f}'.replace('.', ',')  # noqa: E731
    s, r, k, d = b['sla'], b['sla_respons'], b['kepuasan'], b['dokumen']
    section = '\n'.join([
        MARK_START, '## Baseline dashboard (history versi baru)', '',
        f'`ai/scripts/baseline.py` · {b["dibuat"]} · sumber `{b["sumber"]}` · dibaca dashboard dari '
        '`plugins/halosis/baseline.json`.', '',
        '| Indikator | Nilai | Rincian |', '| --- | ---: | --- |',
        f'| Baseline dokumen: kepatuhan SLA overall / respons | **{dec(d["overall"])}% / {dec(d["respons"])}%** | '
        f'{d["sumber"]}; {b["metode"]["dokumen"]} |',
        f'| Kepatuhan SLA (`overall_sla_result_extended`) | **{dec(s["persen"])}%** | MET {num(s["met"])} ÷ (MET + OVERDUE '
        f'{num(s["overdue"])}); UNKNOWN / tanpa bukti SLA {num(s["dikecualikan"])} dikecualikan |',
        f'| … hasil berimputasi (DQR-04) | {num(s["imputasi"])} | komponen SLA diestimasi (jam kerja); ditandai '
        '`sla_imputasi` |',
        f'| … hanya hasil asli (tanpa imputasi) | {dec(s["persen_tanpa_imputasi"])}% | {num(s["tanpa_imputasi"])} tiket |',
        f'| Kepatuhan SLA respons (`response_sla_final_result`) | **{dec(r["persen"])}%** | MET {num(r["met"])} ÷ '
        f'(MET + OVERDUE {num(r["overdue"])}); {num(r["imputasi"])} berimputasi; UNKNOWN / NA {num(r["dikecualikan"])} '
        'dikecualikan |',
        f'| Kepuasan (rating 1–5) | **{dec(k["persen_puas"])}% ≥ 4** | {num(k["dinilai"])} tiket dinilai '
        f'(cakupan {dec(k["cakupan_persen"])}% dari {num(b["tiket"])}), rata-rata {dec(k["rata_rata"])}; '
        + ', '.join(f'{r}★ {num(n)}' for r, n in k['distribusi'].items()) + ' |', '',
        'Dashboard menampilkan dua baris pembanding: **dokumen** (resmi, dipakai di bab analisis) dan **history versi '
        'baru** (metode extended). Selisih overall 27,59% vs '
        f'{dec(s["persen"])}% berasal dari metode, bukan perubahan kinerja: ekspor baru mengestimasi komponen SLA yang '
        f'tidak tercatat ({num(s["imputasi"])} hasil berimputasi) sehingga penyebutnya lebih besar. Respons '
        f'{dec(r["persen"])}% vs dokumen 42,62% juga berbeda karena hasil akhir memuat imputasi.', '',
        f'Kepuasan hanya dari tiket yang dinilai pemohon ({dec(k["cakupan_persen"])}% tiket; dokumen §5.2.1: rating '
        'tidak wajib, cakupan ± 15–16%) dan bias responden (sebagian besar 5★): klaim kepuasan tinggi berisiko terlalu '
        'optimistis.', MARK_END])
    text = REPORT.read_text(encoding='utf-8')
    if MARK_START in text:
        text = re.sub(re.escape(MARK_START) + '.*?' + re.escape(MARK_END), lambda _: section, text, flags=re.S)
    else:
        text = text.rstrip('\n') + '\n\n' + section + '\n'
    REPORT.write_text(text, encoding='utf-8')
    print(json.dumps(b, ensure_ascii=False))


if __name__ == '__main__':
    main()
