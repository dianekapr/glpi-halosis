"""Gerbang kualitas model (T32, pre-kondisi UC-04; syarat lulus reports/tata_kelola_ai.md §2 langkah 3).

Metrik dibaca dari artefak (dict `metrics`) atau berkas pendamping `<model>.metrics.json`; tidak ada yang dihitung
ulang saat layanan berjalan. Setiap syarat yang metriknya tidak tercatat dilaporkan "tidak tercatat" dan membuat model
TIDAK lolos, kecuali syarat banding versi sebelumnya (hanya berlaku bila versi sebelumnya tercatat).
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

# Syarat lulus (tata_kelola_ai.md §2): bisa diketatkan lewat environment layanan
MIN_TOP1 = float(os.environ.get('HALOSIS_GATE_MIN_TOP1', '0.68'))                 # baseline TF-IDF PoC (hal. 54)
MIN_ACC_CONFIDENT = float(os.environ.get('HALOSIS_GATE_MIN_ACC_CONFIDENT', '0.85'))  # akurasi pada keyakinan ≥ ambang
MIN_RECALL_BIG_TEAM = float(os.environ.get('HALOSIS_GATE_MIN_RECALL', '0.50'))     # tidak ada tim besar < 50%
MAX_DROP = float(os.environ.get('HALOSIS_GATE_MAX_DROP', '0.02'))                  # Top-1/Top-3 turun ≤ 2 poin
# Urgensi insiden, per kelas pada ambangnya (validasi silang): Low = presisi, Medium = akurasi di atas pembanding
MIN_PRECISION_LOW = float(os.environ.get('HALOSIS_GATE_MIN_PRECISION_LOW', '0.75'))
MIN_GAIN_MEDIUM = float(os.environ.get('HALOSIS_GATE_MIN_GAIN_MEDIUM', '0.03'))     # akurasi > pembanding + 3 poin
MIN_SUPPORT = int(os.environ.get('HALOSIS_GATE_MIN_SUPPORT', '30'))                # tiket di atas ambang
URGENCY_CLASSES = ('Low', 'Medium')


def wilson(successes: int, n: int, z: float = 1.96) -> tuple[float, float] | None:
    """Interval kepercayaan Wilson 95% untuk proporsi (mis. presisi Low); None bila n = 0."""
    if n <= 0:
        return None
    p = successes / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, center - half), min(1.0, center + half)


def urgency_class_check(kelas: str, m: dict) -> tuple[bool | None, str]:
    """Syarat lulus satu kelas urgensi dari metriknya pada ambang terpilih (dipakai juga train_urgensi.py saat memilih
    ambang). Low: presisi ≥ MIN_PRECISION_LOW, batas bawah Wilson > pembanding (proporsi Low), ≥ MIN_SUPPORT tiket.
    Medium: akurasi > pembanding (proporsi Medium) + MIN_GAIN_MEDIUM, ≥ MIN_SUPPORT tiket. None = tidak tercatat."""
    n, base = m.get('tiket'), m.get('pembanding')
    if kelas == 'Low':
        precision, ci = m.get('presisi'), m.get('wilson_95')
        if None in (n, base, precision) or not ci:
            return None, 'Low: metrik tidak tercatat'
        ok = precision >= MIN_PRECISION_LOW and ci[0] > base and n >= MIN_SUPPORT
        return ok, (f'Low: presisi {precision} (Wilson bawah {ci[0]}, {n} tiket) belum memenuhi ≥ {MIN_PRECISION_LOW}, '
                    f'> pembanding {base}, ≥ {MIN_SUPPORT} tiket')
    accuracy = m.get('akurasi')
    if None in (n, base, accuracy):
        return None, 'Medium: metrik tidak tercatat'
    ok = accuracy > base + MIN_GAIN_MEDIUM and n >= MIN_SUPPORT
    return ok, f'Medium: akurasi {accuracy} ({n} tiket) tidak > pembanding {base} + {MIN_GAIN_MEDIUM}'


def load_metrics(model_path: Path, artifact) -> dict:
    """Metrik dari berkas pendamping (triase, urgensi) atau dari artefak (dict `metrics` / atribut `metadata`)."""
    side = model_path.with_suffix('.metrics.json')
    if side.exists():
        return json.loads(side.read_text(encoding='utf-8'))
    if isinstance(artifact, dict):
        return dict(artifact.get('metrics') or {})
    return dict(getattr(artifact, 'metadata', {}) or {})


def check(kind: str, metrics: dict) -> dict:
    """Status lolos per model. kind: triase (syarat tata kelola penuh) | jenis (F1 makro harus unggul pembanding
    kelas mayoritas dan, bila tercatat, tidak turun > MAX_DROP dari versi aktif) | urgensi (per kelas Low/Medium,
    urgency_class_check; model lolos bila ≥ 1 kelas lolos, hanya kelas di `kelas_lolos` yang boleh disarankan)."""
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
    elif kind == 'urgensi':
        per_class = metrics.get('kelas') or {}
        passed = []
        for name in URGENCY_CLASSES:
            ok, detail = urgency_class_check(name, per_class.get(name) or {})
            checks[name] = 'tidak tercatat' if ok is None else ('lolos' if ok else 'gagal')
            if ok:
                passed.append(name)
            else:
                reasons.append(detail)
        return {'lolos': bool(passed), 'kelas_lolos': passed, 'alasan': reasons, 'syarat': checks,
                'versi': metrics.get('versi'), 'tanggal': metrics.get('tanggal')}
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
