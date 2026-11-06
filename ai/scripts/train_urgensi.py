"""Klasifier urgensi INSIDEN (Medium vs Low) skema B → ai/models/urgensi.joblib + urgensi.metrics.json (BR-05, 2.1.4).

Label = kolom `urgency` ekspor history versi baru. Dampak (`impact`) sama dengan urgensi pada 99,7% insiden dan
`priority` = matriks keduanya, jadi satu model urgensi cukup. High/Critical dan permintaan (REQ) tidak dimodelkan.

Fitur: teks judul + deskripsi tersamar (TF-IDF kata + karakter) + nama tim; LR class_weight=balanced → P(Low).
Saat dipakai, tim = saran triase, jadi evaluasi dengan tim aktual terlalu optimistis. Dua skema, lipatan sama:
- A (pembanding): tim aktual.
- B (gerbang): validasi silang bertingkat 5 lipatan luar. Data latih luar memakai tim prediksi out-of-fold (5 lipatan
  dalam); data uji luar memakai prediksi model tim dari seluruh data latih luar.
Ambang per kelas dipilih HANYA dari P(Low) lipatan dalam (triage_model.pick_urgency_thresholds), lalu diterapkan ke data
uji luar; metrik = gabungan prediksi lipatan luar. Ambang artefak = median lima lipatan; rentang > 0,10 → "tidak stabil".
Model tim tanpa kalibrasi (kalibrasi tidak diperlukan untuk memilih tim teratas dan melipatgandakan waktu latih) dan
dilatih juga dengan semua REQ, seperti model triase.

Gerbang: quality.check('urgensi'). Lolos → cadangkan ai/models ke backup/model-<waktu>/ (+ MANIFEST.txt sha256), baru
tulis artefak. Tidak lolos → setelah cadangan, HANYA urgensi.metrics.json diganti hasil skema B: artefak lama tersimpan
untuk rollback, tetapi tidak dipakai (quality.check → tidak ada kelas lolos); exit code 2. Rollback = pulihkan metrik dari
cadangan. Laporan (angka saja) → reports/triase.md.

Pakai: .venv/bin/python ai/scripts/train_urgensi.py
Uji jalur kode tanpa menulis apa pun: .venv/bin/python ai/scripts/train_urgensi.py --kering 400
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
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
from halosis_ai.triage_model import (MIN_TEAM_TICKETS, OTHER, build_pipeline, build_urgency_pipeline,  # noqa: E402
                                     jenis_text, model_text, pick_urgency_thresholds, urgency_class_metrics)

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data/processed/tickets_clean.parquet'
OUT = ROOT / 'ai/models/urgensi.joblib'
BACKUP = ROOT / 'backup'
REPORT = ROOT / 'reports/triase.md'
LABELS = ('Medium', 'Low')
URGENCY_GLPI = {'Medium': 3, 'Low': 2}  # skala GLPI: 3 sedang, 2 rendah
FOLDS, SEED = 5, 42
MARK_START, MARK_END = '<!-- urgensi:mulai -->', '<!-- urgensi:selesai -->'


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    """→ (semua insiden, permintaan bertim). Permintaan hanya menambah data latih model tim."""
    df = pd.read_parquet(SRC, columns=['ticket_type', 'short_description', 'description', 'assignment_group_name',
                                       'urgency', 'impact'])
    df['tim'] = df['assignment_group_name'].astype('string').fillna('').str.strip()
    df['teks_tim'] = [model_text(t, d, k) for t, d, k in zip(df['short_description'], df['description'], df['ticket_type'])]
    is_inc = df['ticket_type'].astype(str).str.upper().str.startswith('INC')
    incidents = df[is_inc].copy()
    incidents['label'] = incidents['urgency'].astype('string')
    incidents['teks'] = [jenis_text(t, d) for t, d in zip(incidents['short_description'], incidents['description'])]
    return incidents, df[~is_inc & (df['tim'] != '')][['teks_tim', 'tim']]


def team_model():
    """Pengaturan sama dengan model triase aktif (C=3, tanpa bobot kelas); tanpa kalibrasi, lihat docstring modul."""
    return build_pipeline(c=3.0, class_weight=None, calibrate=False)


def fit_team(train: pd.DataFrame, requests: pd.DataFrame):
    """Model tim dari insiden latih + semua permintaan; tim < MIN_TEAM_TICKETS digabung 'Lainnya' seperti triase."""
    pool = pd.concat([train[['teks_tim', 'tim']], requests], ignore_index=True)
    pool = pool[pool['tim'] != '']
    counts = pool['tim'].value_counts()
    keep = set(counts[counts >= MIN_TEAM_TICKETS].index)
    return team_model().fit(pool['teks_tim'], pool['tim'].where(pool['tim'].isin(keep), OTHER))


def out_of_fold_teams(df: pd.DataFrame, requests: pd.DataFrame, folds: StratifiedKFold) -> np.ndarray:
    teams = np.empty(len(df), dtype=object)
    for fit, held in folds.split(df, df['label']):
        teams[held] = fit_team(df.iloc[fit], requests).predict(df['teks_tim'].iloc[held])
    return teams


def frame(df: pd.DataFrame, teams) -> pd.DataFrame:
    return pd.DataFrame({'teks': df['teks'].to_numpy(), 'tim': np.asarray(teams, dtype=object)})


def evaluate_scheme(df: pd.DataFrame, requests: pd.DataFrame, scheme: str) -> dict:
    """Validasi silang bertingkat. Ambang tiap lipatan luar dipilih dari lipatan dalam, lalu dipakai pada data uji luar."""
    outer = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    inner = StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED + 1)
    y = df['label'].to_numpy()
    low = sorted(LABELS).index('Low')  # kolom P(Low): urutan kelas sklearn
    p_low = np.zeros(len(df))
    per_row = {k: np.zeros(len(df)) for k in quality.URGENCY_CLASSES}
    per_fold = []
    for number, (fit, test) in enumerate(outer.split(df, y), 1):
        train, held = df.iloc[fit], df.iloc[test]
        if scheme == 'B':
            x_fit = frame(train, out_of_fold_teams(train, requests, inner))
            x_test = frame(held, fit_team(train, requests).predict(held['teks_tim']))
        else:
            x_fit, x_test = frame(train, train['tim']), frame(held, held['tim'])
        inner_p = cross_val_predict(build_urgency_pipeline(), x_fit, y[fit], cv=inner, method='predict_proba')[:, low]
        chosen = pick_urgency_thresholds(inner_p, y[fit])
        p_low[test] = build_urgency_pipeline().fit(x_fit, y[fit]).predict_proba(x_test)[:, low]
        for k in quality.URGENCY_CLASSES:
            per_row[k][test] = chosen[k]['ambang']
        per_fold.append({'lipatan': number, **{k: chosen[k]['ambang'] for k in quality.URGENCY_CLASSES},
                         'lolos_dalam': [k for k in quality.URGENCY_CLASSES if chosen[k]['lolos']]})
        print(f'skema {scheme} lipatan {number}/{FOLDS} selesai', flush=True)
    kelas = {}
    for k in quality.URGENCY_CLASSES:
        m = urgency_class_metrics(k, p_low, y, per_row[k])
        kelas[k] = {**m, 'ambang': float(np.median([f[k] for f in per_fold])),
                    'ambang_per_lipatan': [f[k] for f in per_fold]}
    return {'kelas': kelas, 'per_lipatan': per_fold, 'p_low': p_low, **quality.threshold_spread(per_fold)}


def record_rejected(metrics: dict) -> Path:
    """Gerbang gagal: cadangkan lalu ganti metrik saja; artefak tetap ada untuk rollback tetapi tidak dipakai."""
    folder = quality.backup_artifacts(OUT.parent, BACKUP)
    side, tmp = OUT.with_suffix('.metrics.json'), OUT.with_suffix('.metrics.tmp')
    tmp.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, side)
    return folder


def publish(artifact: dict, metrics: dict) -> Path:
    """Cadangkan, lalu tulis artefak & metrik; gagal di tengah → kembalikan keduanya dari cadangan."""
    folder = quality.backup_artifacts(OUT.parent, BACKUP)
    side = OUT.with_suffix('.metrics.json')
    tmp_model, tmp_side = OUT.with_suffix('.joblib.tmp'), side.with_suffix('.json.tmp')
    try:
        joblib.dump(artifact, tmp_model, compress=3)
        tmp_side.write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(tmp_model, OUT)
        os.replace(tmp_side, side)
    except Exception:
        for path in (OUT, side):
            if (folder / path.name).exists():
                shutil.copy2(folder / path.name, path)
        raise
    finally:
        tmp_model.unlink(missing_ok=True)
        tmp_side.unlink(missing_ok=True)
    return folder


def build_section(metrics: dict, gate: dict, scheme_a: dict, status: str) -> str:
    pct = lambda v: '–' if v is None else f'{v * 100:.2f}%'.replace('.', ',')  # noqa: E731
    num = lambda v: f'{v:,}'.replace(',', '.')  # noqa: E731
    dec = lambda v: f'{v:.2f}'.replace('.', ',')  # noqa: E731
    kelas = metrics['kelas']
    mark = lambda k: '**lolos**' if k in gate['kelas_lolos'] else '**tidak lolos** (tidak disarankan)'  # noqa: E731

    def row(name: str, values: dict, label: str) -> str:
        low, med = values['Low'], values['Medium']
        ci = low['wilson_95'] or [None, None]
        return (f'| {name} | {pct(low["presisi"])} (Wilson {pct(ci[0])}–{pct(ci[1])}) | {pct(low["recall"])} | '
                f'{num(low["tiket"])} | {pct(med["akurasi"])} | {pct(med["cakupan"])} | {num(med["tiket"])} | {label} |')

    unstable = metrics['tidak_stabil']
    return '\n'.join([
        MARK_START, '## Saran urgensi insiden (BR-05, 2.1.4 Urgency/Impact/Priority)', '',
        f'{status} · `ai/scripts/train_urgensi.py` · label = kolom `urgency` history (insiden Medium vs Low). '
        f'Insiden berlabel Medium / Low: {num(metrics["distribusi"].get("Medium", 0))} / '
        f'{num(metrics["distribusi"].get("Low", 0))}; {metrics["evaluasi"]} (seed {SEED}).', '',
        '### Skema A vs B', '',
        'Saat dipakai, tim berasal dari saran triase, jadi **skema B adalah gerbang** dan skema A hanya pembanding. Ambang '
        'dipilih di lipatan dalam dan metrik dari data uji luar yang tidak ikut memilih ambang.', '',
        '| Skema | Presisi Low | Recall Low | Tiket Low | Akurasi Medium | Cakupan Medium | Tiket Medium | Peran |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |',
        row('A: tim aktual', scheme_a['kelas'], 'pembanding'), row('B: tim prediksi OOF', kelas, 'gerbang'), '',
        f'Pembanding proporsi: Low {pct(kelas["Low"]["pembanding"])}, Medium {pct(kelas["Medium"]["pembanding"])}. '
        f'Gerbang B: Low {mark("Low")}, Medium {mark("Medium")}.', '',
        '### Ambang per lipatan luar (skema B)', '',
        '| Lipatan | Ambang Low | Ambang Medium | Lolos di lipatan dalam |', '| ---: | ---: | ---: | --- |',
        *[f'| {f["lipatan"]} | {dec(f["Low"])} | {dec(f["Medium"])} | {", ".join(f["lolos_dalam"]) or "–"} |'
          for f in metrics['per_lipatan']],
        f'| **Median** | **{dec(kelas["Low"]["ambang"])}** | **{dec(kelas["Medium"]["ambang"])}** | |', '',
        f'Rentang antarlipatan: Low {dec(metrics["rentang_ambang"]["Low"])}, Medium '
        f'{dec(metrics["rentang_ambang"]["Medium"])} (batas {dec(quality.MAX_THRESHOLD_SPREAD)}). Stabilitas: **'
        + (f'tidak stabil ({", ".join(unstable)})' if unstable else 'stabil') + '**.', '',
        f'Syarat: Low presisi ≥ {pct(quality.MIN_PRECISION_LOW)}, batas bawah Wilson > pembanding, ≥ '
        f'{quality.MIN_SUPPORT} tiket; Medium akurasi > pembanding + {int(quality.MIN_GAIN_MEDIUM * 100)} poin, ≥ '
        f'{quality.MIN_SUPPORT} tiket. Tanpa ambang per kelas (argmax 0,5, skema B): akurasi '
        f'{pct(metrics["akurasi_argmax"])}, F1 makro {pct(metrics["f1_makro_argmax"])} vs selalu '
        f'{metrics["pembanding_kelas"]} {pct(metrics["pembanding_akurasi"])}.', '',
        'Model tim skema B tanpa kalibrasi (C=3, tanpa bobot kelas, seperti model triase aktif; disetujui 6 Nov 2026): '
        'hanya tim teratas yang dipakai dan kalibrasi melipatgandakan waktu latih, sehingga pilihan tim bisa sedikit '
        'berbeda dari model triase terkalibrasi.', '',
        'Tidak dimodelkan (tetap aturan + sinyal): '
        + ', '.join(f'{k} {num(v)}' for k, v in metrics['tidak_dimodelkan'].items()) + ' insiden; permintaan (REQ). '
        f'{pct(metrics["pembanding_akurasi"])} insiden berlabel Medium; sebagian besar kemungkinan nilai bawaan formulir.',
        '', 'Panel Saran AI menampilkan urgensi hanya bila kelasnya lolos gerbang dan P(Low) melewati ambangnya; selain '
        'itu urgensi dari aturan kata kunci. Operator tetap memutuskan.', MARK_END])


def write_section(section: str) -> None:
    text = REPORT.read_text(encoding='utf-8')
    if MARK_START in text:
        text = re.sub(re.escape(MARK_START) + '.*?' + re.escape(MARK_END), lambda _: section, text, flags=re.S)
    else:
        text = text.rstrip('\n') + '\n\n' + section + '\n'
    REPORT.write_text(text, encoding='utf-8')


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--kering', type=int, metavar='N', help='contoh N insiden, tanpa menulis artefak/laporan')
    args = parser.parse_args(argv)

    all_inc, requests = load()
    df = all_inc[all_inc['label'].isin(LABELS)].reset_index(drop=True)
    if args.kering:
        df = df.sample(min(args.kering, len(df)), random_state=SEED).reset_index(drop=True)
        requests = requests.sample(min(args.kering, len(requests)), random_state=SEED)
    y = df['label'].to_numpy()

    scheme_a = evaluate_scheme(df, requests, 'A')
    scheme_b = evaluate_scheme(df, requests, 'B')
    pred = np.where(scheme_b['p_low'] >= 0.5, 'Low', 'Medium')  # tanpa ambang per kelas (informasi saja)
    majority = pd.Series(y).value_counts().index[0]
    version = f'urgensi-tfidf-timpred-lr-{date.today():%Y%m%d}'
    known = all_inc['impact'].notna() & all_inc['urgency'].notna()
    metrics = {
        'versi': version, 'tanggal': date.today().isoformat(), 'skema': 'B',
        'evaluasi': f'validasi silang bertingkat {FOLDS} lipatan luar × {FOLDS} lipatan dalam, tim prediksi out-of-fold',
        'insiden_berlabel': int(len(df)), 'distribusi': {k: int(v) for k, v in pd.Series(y).value_counts().items()},
        'tidak_dimodelkan': {k: int(v) for k, v in all_inc['label'].fillna('(kosong)').value_counts().items()
                             if k not in LABELS},
        'dampak_sama_urgensi': round(float((all_inc['impact'] == all_inc['urgency'])[known].mean()), 4),
        'kelas': scheme_b['kelas'], 'per_lipatan': scheme_b['per_lipatan'],
        'rentang_ambang': scheme_b['rentang_ambang'], 'tidak_stabil': scheme_b['tidak_stabil'],
        'skema_a': {'kelas': scheme_a['kelas'], 'rentang_ambang': scheme_a['rentang_ambang']},
        'syarat': {'presisi_low_min': quality.MIN_PRECISION_LOW, 'tambahan_akurasi_medium': quality.MIN_GAIN_MEDIUM,
                   'tiket_min': quality.MIN_SUPPORT, 'rentang_ambang_maks': quality.MAX_THRESHOLD_SPREAD},
        'akurasi_argmax': round(float(accuracy_score(y, pred)), 4),
        'f1_makro_argmax': round(float(f1_score(y, pred, average='macro')), 4),
        'pembanding_kelas': majority, 'pembanding_akurasi': round(float((y == majority).mean()), 4),
    }
    gate = quality.check('urgensi', metrics)
    for k in quality.URGENCY_CLASSES:
        metrics['kelas'][k]['lolos'] = k in gate['kelas_lolos']
    metrics['lolos_gerbang'], metrics['kelas_lolos'] = gate['lolos'], gate['kelas_lolos']
    summary = {k: {m: v.get(m) for m in ('ambang', 'tiket', 'presisi', 'recall', 'akurasi', 'cakupan', 'lolos')}
               for k, v in metrics['kelas'].items()}
    print('skema B:', summary, '| rentang', metrics['rentang_ambang'], '| tidak stabil:', metrics['tidak_stabil'])

    if args.kering:
        print('KERING: tidak ada artefak/laporan yang ditulis.')
        return

    side = OUT.with_suffix('.metrics.json')
    recorded = json.loads(side.read_text(encoding='utf-8')) if side.exists() else {}
    active = recorded.get('artefak_versi') or recorded.get('versi')
    if gate['lolos']:
        final_teams = out_of_fold_teams(df, requests, StratifiedKFold(n_splits=FOLDS, shuffle=True, random_state=SEED))
        pipeline = build_urgency_pipeline().fit(frame(df, final_teams), y)
        folder = publish({'pipeline': pipeline, 'version': version, 'metrics': metrics, 'urgensi_glpi': URGENCY_GLPI,
                          'ambang': {k: v['ambang'] for k, v in metrics['kelas'].items()}}, metrics)
        status = f'Versi aktif `{version}` (menggantikan `{active}`)'
        print(f'GERBANG LOLOS {gate["kelas_lolos"]}. Artefak ditulis; cadangan: {folder.relative_to(BACKUP.parent)}')
    else:
        metrics['artefak_versi'] = active
        status = (f'**Tidak lolos dalam kondisi nyata (tim prediksi): model urgensi tidak dipakai.** Kandidat `{version}` '
                  f'gagal gerbang; artefak `{active}` disimpan hanya untuk rollback, dan urgensi kembali ke aturan kata '
                  f'kunci + validasi Operator (cadangan: `{record_rejected(metrics).relative_to(BACKUP.parent)}`)')
    write_section(build_section(metrics, gate, scheme_a, status))
    if not gate['lolos']:
        print('GERBANG GAGAL: saran urgensi dimatikan lewat metrik, artefak tidak disentuh.', gate['alasan'])
        raise SystemExit(2)


if __name__ == '__main__':
    main()
