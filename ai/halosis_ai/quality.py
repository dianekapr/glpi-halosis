"""Gerbang kualitas model (T32, pre-kondisi UC-04; syarat lulus reports/tata_kelola_ai.md §2 langkah 3).

Metrik dibaca dari artefak (dict `metrics`) atau berkas pendamping `<model>.metrics.json`; tidak ada yang dihitung
ulang saat layanan berjalan. Setiap syarat yang metriknya tidak tercatat dilaporkan "tidak tercatat" dan membuat model
TIDAK lolos, kecuali syarat banding versi sebelumnya (hanya berlaku bila versi sebelumnya tercatat).
"""
from __future__ import annotations

import json
import os
from pathlib import Path

# Syarat lulus (tata_kelola_ai.md §2): bisa diketatkan lewat environment layanan
MIN_TOP1 = float(os.environ.get('HALOSIS_GATE_MIN_TOP1', '0.68'))                 # baseline TF-IDF PoC (hal. 54)
MIN_ACC_CONFIDENT = float(os.environ.get('HALOSIS_GATE_MIN_ACC_CONFIDENT', '0.85'))  # akurasi pada keyakinan ≥ ambang
MIN_RECALL_BIG_TEAM = float(os.environ.get('HALOSIS_GATE_MIN_RECALL', '0.50'))     # tidak ada tim besar < 50%
MAX_DROP = float(os.environ.get('HALOSIS_GATE_MAX_DROP', '0.02'))                  # Top-1/Top-3 turun ≤ 2 poin


def load_metrics(model_path: Path, artifact) -> dict:
    """Metrik dari berkas pendamping (triase, urgensi) atau dari artefak (dict `metrics` / atribut `metadata`)."""
    side = model_path.with_suffix('.metrics.json')
    if side.exists():
        return json.loads(side.read_text(encoding='utf-8'))
    if isinstance(artifact, dict):
        return dict(artifact.get('metrics') or {})
    return dict(getattr(artifact, 'metadata', {}) or {})


def check(kind: str, metrics: dict) -> dict:
    """Status lolos per model. kind: triase (syarat tata kelola penuh) | jenis | urgensi (harus unggul pembanding
    kelas mayoritas dan, bila tercatat, F1 makro tidak turun > MAX_DROP dari versi aktif pada set uji yang sama)."""
    reasons, checks = [], {}

    def need(name: str, ok, detail: str):
        checks[name] = 'tidak tercatat' if ok is None else ('lolos' if ok else 'gagal')
        if ok is not True:
            reasons.append(detail if ok is False else f'{name} tidak tercatat')

    def get(key):
        value = metrics.get(key)
        return None if value is None else float(value)

    if kind == 'triase':
        top1, acc, recall = get('top1'), get('akurasi_yakin'), get('recall_tim_besar_min')
        need('top1', None if top1 is None else top1 >= MIN_TOP1, f'Top-1 {top1} < {MIN_TOP1}')
        need('akurasi_yakin', None if acc is None else acc >= MIN_ACC_CONFIDENT, f'akurasi pada ambang {acc} < {MIN_ACC_CONFIDENT}')
        need('recall_tim_besar', None if recall is None else recall >= MIN_RECALL_BIG_TEAM,
             f'recall tim besar terendah {recall} < {MIN_RECALL_BIG_TEAM}')
        previous = metrics.get('versi_sebelumnya') or {}
        for key in ('top1', 'top3'):
            if previous.get(key) is not None and get(key) is not None:
                need(f'{key}_vs_versi_sebelumnya', get(key) >= float(previous[key]) - MAX_DROP,
                     f'{key} turun > {MAX_DROP} dari versi sebelumnya')
    else:
        f1, base = get('f1_makro'), get('f1_makro_pembanding')
        need('f1_makro_vs_pembanding', None if f1 is None or base is None else f1 > base,
             f'F1 makro {f1} tidak mengungguli pembanding {base}')
        previous = metrics.get('versi_sebelumnya') or {}
        if previous.get('f1_makro') is not None and f1 is not None:
            need('f1_makro_vs_versi_sebelumnya', f1 >= float(previous['f1_makro']) - MAX_DROP,
                 f'F1 makro turun > {MAX_DROP} dari versi sebelumnya')
    return {'lolos': not reasons, 'alasan': reasons, 'syarat': checks, 'versi': metrics.get('versi'),
            'tanggal': metrics.get('tanggal')}
