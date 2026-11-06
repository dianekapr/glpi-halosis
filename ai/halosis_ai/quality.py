"""Gerbang kualitas model (T32, pre-kondisi UC-04; syarat lulus reports/tata_kelola_ai.md §2 langkah 3).

Metrik dibaca dari artefak (dict `metrics`) atau berkas pendamping `<model>.metrics.json`; tidak ada yang dihitung
ulang saat layanan berjalan. Setiap syarat yang metriknya tidak tercatat dilaporkan "tidak tercatat" dan membuat model
TIDAK lolos, kecuali syarat banding versi sebelumnya (hanya berlaku bila versi sebelumnya tercatat).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
from datetime import datetime
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
MAX_THRESHOLD_SPREAD = float(os.environ.get('HALOSIS_GATE_MAX_THRESHOLD_SPREAD', '0.10'))  # antarlipatan luar; lebih = "tidak stabil"
# Pola insiden (peringatan saja, tidak memblokir), diuji pada 666 INC Jul–Ags seperti reports/banding_pola.md
MIN_PATTERN_PURITY = float(os.environ.get('HALOSIS_GATE_MIN_PATTERN_PURITY', '0.85'))
MIN_PATTERN_GROUPS = int(os.environ.get('HALOSIS_GATE_MIN_PATTERN_GROUPS', '5'))
# Titik ambang triase dengan bukti di bawah ini tidak boleh dianggap lolos
MIN_POINT_COVERAGE = float(os.environ.get('HALOSIS_GATE_MIN_POINT_COVERAGE', '0.10'))
MIN_POINT_TICKETS = int(os.environ.get('HALOSIS_GATE_MIN_POINT_TICKETS', '100'))
NOT_ENOUGH_DATA = 'data tidak cukup'


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


def backup_artifacts(models_dir: Path, backup_root: Path) -> Path:
    """Salin semua artefak aktif ke backup/model-<waktu>/ dan catat sha256 tiap salinan di MANIFEST.txt."""
    folder = backup_root / f'model-{datetime.now():%Y%m%d-%H%M%S}'
    folder.mkdir(parents=True)
    lines = []
    for path in sorted(p for p in models_dir.iterdir() if p.is_file()):
        copy = Path(shutil.copy2(path, folder / path.name))
        lines.append(f'{hashlib.sha256(copy.read_bytes()).hexdigest()}  {path.name}')
    (folder / 'MANIFEST.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return folder


def threshold_curve(confidence, correct) -> dict:
    """Akurasi & cakupan per 1 poin ambang pada set uji triase → `kurva_ambang` (dibaca triage_point)."""
    curve = {}
    for percent in range(101):
        chosen = confidence >= percent / 100
        tickets = int(chosen.sum())
        curve[str(percent)] = {'akurasi': round(float(correct[chosen].mean()), 4) if tickets else None,
                               'cakupan': round(float(chosen.mean()), 4), 'tiket': tickets}
    return curve


def threshold_spread(per_fold: list[dict]) -> dict:
    """Stabilitas ambang urgensi antarlipatan luar (skema B). per_fold: [{'Low': t, 'Medium': t}, …]. Rentang >
    MAX_THRESHOLD_SPREAD → kelas masuk `tidak_stabil`; hanya penanda, tidak mengubah status lolos."""
    spread = {k: round(max(f[k] for f in per_fold) - min(f[k] for f in per_fold), 4) for k in URGENCY_CLASSES}
    return {'rentang_ambang': spread, 'tidak_stabil': [k for k, v in spread.items() if v > MAX_THRESHOLD_SPREAD]}


def triage_point(metrics: dict, threshold: float) -> tuple[bool | str | None, str]:
    """Syarat akurasi pada ambang triase aktif (0–1) dari `kurva_ambang` {'70': {akurasi, cakupan, tiket}, …}.
    Cakupan < MIN_POINT_COVERAGE atau < MIN_POINT_TICKETS tiket → NOT_ENOUGH_DATA (bukan lolos). None = tidak tercatat."""
    point = (metrics.get('kurva_ambang') or {}).get(str(round(threshold * 100)))
    if not point:
        return None, ''
    accuracy, coverage, tickets = point.get('akurasi'), point['cakupan'], point['tiket']
    if coverage < MIN_POINT_COVERAGE or tickets < MIN_POINT_TICKETS or accuracy is None:
        return NOT_ENOUGH_DATA, (f'ambang {threshold}: {NOT_ENOUGH_DATA} (cakupan {coverage}, {tickets} tiket; minimal '
                                 f'{MIN_POINT_COVERAGE} dan {MIN_POINT_TICKETS} tiket)')
    return accuracy >= MIN_ACC_CONFIDENT, f'akurasi pada ambang {threshold} = {accuracy} < {MIN_ACC_CONFIDENT}'


def load_metrics(model_path: Path, artifact) -> dict:
    """Metrik dari berkas pendamping (triase, urgensi) atau dari artefak (dict `metrics` / atribut `metadata`)."""
    side = model_path.with_suffix('.metrics.json')
    if side.exists():
        return json.loads(side.read_text(encoding='utf-8'))
    if isinstance(artifact, dict):
        return dict(artifact.get('metrics') or {})
    return dict(getattr(artifact, 'metadata', {}) or {})


def check(kind: str, metrics: dict, threshold: float | None = None) -> dict:
    """Status lolos per model. kind: triase (syarat tata kelola penuh; threshold = ambang aktif 0–1, None = ambang
    tercatat di metrik) | pola (peringatan saja, `memblokir` selalu False) | jenis (F1 makro harus unggul pembanding
    kelas mayoritas dan, bila tercatat, tidak turun > MAX_DROP dari versi aktif) | urgensi (per kelas Low/Medium,
    urgency_class_check; model lolos bila ≥ 1 kelas lolos, hanya kelas di `kelas_lolos` yang boleh disarankan)."""
    reasons, checks = [], {}

    def need(name: str, ok, detail: str):
        checks[name] = ok if ok == NOT_ENOUGH_DATA else (
            'tidak tercatat' if ok is None else ('lolos' if ok else 'gagal'))
        if ok is not True:
            reasons.append(f'{name} tidak tercatat' if ok is None else detail)

    def get(key):
        value = metrics.get(key)
        return None if value is None else float(value)

    if kind == 'triase':
        top1, acc, recall = get('top1'), get('akurasi_yakin'), get('recall_tim_besar_min')
        need('top1', None if top1 is None else top1 >= MIN_TOP1, f'Top-1 {top1} < {MIN_TOP1}')
        if threshold is None:
            need('akurasi_yakin', None if acc is None else acc >= MIN_ACC_CONFIDENT,
                 f'akurasi pada ambang {acc} < {MIN_ACC_CONFIDENT}')
        else:
            need('akurasi_yakin', *triage_point(metrics, threshold))
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
                'skema': metrics.get('skema'), 'tidak_stabil': metrics.get('tidak_stabil') or [],
                'versi': metrics.get('versi'), 'tanggal': metrics.get('tanggal')}
    elif kind == 'pola':
        purity, groups = get('kemurnian_tim'), get('kelompok')
        need('kemurnian_tim', None if purity is None else purity >= MIN_PATTERN_PURITY,
             f'kemurnian tim {purity} < {MIN_PATTERN_PURITY}')
        need('kelompok', None if groups is None else groups >= MIN_PATTERN_GROUPS,
             f'kelompok {groups} < {MIN_PATTERN_GROUPS}')
        return {'lolos': not reasons, 'memblokir': False, 'alasan': reasons, 'syarat': checks,
                'tiket_terkelompok': metrics.get('tiket_terkelompok'), 'parameter': metrics.get('parameter'),
                'tanggal': metrics.get('tanggal')}
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
