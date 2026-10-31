"""Banding ekstraksi solusi untuk indeks pencarian → reports/banding_solusi.md (angka saja).

Set uji sama dengan reports/banding_embedding.md: korpus = potongan tiket selesai yang dibuka Jan–Jun 2026,
kueri = teks masalah tiket selesai Jul–Ags 2026, relevan = potongan dari tiket yang ditangani tim yang sama
(potongan gabungan dedup relevan bila salah satu tiketnya dari tim itu). Metrik: Top-1, Top-3, MRR@10, dihitung
per sumber (potongan lanjutan dari tiket yang sama tidak dihitung dua kali). Model embedding e5-base (search.embed).

Varian (semua pada ekspor baru, kueri sama):
- sebelum        : aturan lama — pesan substantif terakhir di seluruh percakapan, petugas diutamakan, lalu
                   resolution → close_notes; satu potongan per tiket tanpa pemecahan
- sesudah        : aturan baru (conversations.extract_solution: ≤ resolved + 5 mnt, bukan pemohon) lalu
                   close_notes → resolution; solusi > 220 kata dipecah, masalah diulang di tiap potongan
- sesudah+dedup  : sesudah + solusi identik digabung (seperti build_index.py)
Ditambah baris acuan: ekspor lama + aturan lama (qa_pairs cadangan, bila disebut lewat --qa-lama).

Pakai: .venv/bin/python ai/scripts/banding_solusi.py [--qa-lama backup/<folder>/qa_pairs.parquet]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai.conversations import Message, _is_solution_candidate, meaningful_note, substantive_text  # noqa: E402
from halosis_ai.search import MODEL_NAME, embed, ticket_chunks  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TICKETS = ROOT / 'data/processed/tickets_clean.parquet'
QA = ROOT / 'data/processed/qa_pairs.parquet'
REPORT = ROOT / 'reports/banding_solusi.md'
SPLIT = pd.Timestamp('2026-07-01')
SOLVED = {'Closed', 'Resolved', 'Completed'}
K = 10
TOL_POINT, TOL_MRR = 0.01, 0.01  # "tidak lebih buruk": di bawah galat baku Top-1 (±1,4 poin untuk ±1.000 kueri)


def legacy_solution(row: pd.Series) -> str | None:
    """Aturan sebelum perubahan (dipertahankan di sini hanya untuk pembanding)."""
    messages = [Message(m['waktu'], m['teks']) for m in json.loads(row['messages'])]
    candidates = [(staff, m) for m in messages for ok, staff in [_is_solution_candidate(m.text)] if ok]
    if candidates:
        staff = [m for s, m in candidates if s]
        return substantive_text((staff or [m for _, m in candidates])[-1].text)
    return meaningful_note(row['resolution']) or meaningful_note(row['close_notes'])


def passes(result: dict, base: dict) -> bool:
    return (result['top1'] >= base['top1'] - TOL_POINT and result['top3'] >= base['top3'] - TOL_POINT
            and result['mrr'] >= base['mrr'] - TOL_MRR)


def unsplit(qa: pd.DataFrame) -> pd.DataFrame:
    """Format indeks lama: satu potongan utuh per tiket (tanpa dedup & pemecahan)."""
    c = ticket_chunks(qa, dedup=False).drop_duplicates('sumber').copy()
    c['teks'] = 'Masalah: ' + c['masalah'] + ' Solusi: ' + c['solusi']
    return c


def problem(df: pd.DataFrame) -> pd.Series:
    return (df['short_description'].fillna('').astype(str).str.strip() + '\n'
            + df['description'].fillna('').astype(str).str.strip()).str.strip()


def evaluate(corpus: pd.DataFrame, teams: dict[str, str], queries: pd.DataFrame, query_vectors: np.ndarray) -> dict:
    """corpus: keluaran ticket_chunks; teams: nomor tiket → tim; queries: kolom tim."""
    start = time.perf_counter()
    vectors = embed(corpus['teks'].tolist(), 'passage')
    seconds = time.perf_counter() - start
    member_teams = [{teams.get(t) for t in str(ts).split(',')} for ts in corpus['tiket']]
    sources = corpus['sumber'].to_numpy()
    scores = query_vectors @ vectors.T
    top1 = top3 = rr = 0.0
    for qi, team in enumerate(queries['tim']):
        seen, rank = set(), 0
        for ci in np.argsort(-scores[qi]):
            if sources[ci] in seen:
                continue
            seen.add(sources[ci])
            rank += 1
            if team in member_teams[ci]:
                top1 += rank == 1
                top3 += rank <= 3
                rr += 1 / rank
                break
            if rank >= K:
                break
    n = len(queries)
    words = corpus['teks'].str.split().str.len()
    return {'top1': top1 / n, 'top3': top3 / n, 'mrr': rr / n, 'potongan': len(corpus),
            'tiket': int(corpus.drop_duplicates('sumber')['jumlah_tiket'].sum()), 'kata_rata': float(words.mean()),
            'detik_indeks': seconds}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--qa-lama', type=Path, help='qa_pairs.parquet dari ekspor lama (baris acuan)')
    args = parser.parse_args()

    t = pd.read_parquet(TICKETS)
    t = t[t['state_name'].isin(SOLVED) & t['assignment_group_name'].notna()].copy()
    t['opened'] = pd.to_datetime(t['opened'], errors='coerce')
    t['masalah'] = problem(t)
    t = t[t['masalah'].str.len() > 0]
    teams = dict(zip(t['ticket_number'].astype(str), t['assignment_group_name']))
    queries = t[t['opened'] >= SPLIT].rename(columns={'assignment_group_name': 'tim'})
    query_vectors = embed(queries['masalah'].tolist(), 'query')
    train = t[t['opened'] < SPLIT]

    legacy = train.assign(solusi=[legacy_solution(r) for _, r in train.iterrows()], tanggal=train['opened'])
    qa = pd.read_parquet(QA)
    qa = qa[pd.to_datetime(qa['tanggal']) < SPLIT]
    variants = {
        'sebelum (aturan lama)': unsplit(legacy[['ticket_number', 'masalah', 'solusi', 'tanggal']]),
        'sesudah (aturan baru)': ticket_chunks(qa, dedup=False),
        'sesudah + dedup': ticket_chunks(qa, dedup=True),
    }
    results = {name: evaluate(corpus, teams, queries, query_vectors) for name, corpus in variants.items()}

    reference = None
    if args.qa_lama:
        old = pd.read_parquet(args.qa_lama)
        old['tanggal'] = pd.to_datetime(old['tanggal'])
        old_teams = dict(zip(old['ticket_number'].astype(str), old['tim']))
        old_queries = old[old['tanggal'] >= SPLIT]
        reference = evaluate(unsplit(old[old['tanggal'] < SPLIT]),
                             old_teams, old_queries, embed(old_queries['masalah'].tolist(), 'query'))
        reference['kueri'] = len(old_queries)

    pct = lambda v: f'{v * 100:.2f}%'.replace('.', ',')  # noqa: E731
    num = lambda v: f'{v:,}'.replace(',', '.')  # noqa: E731
    dec = lambda v: f'{v:.4f}'.replace('.', ',')  # noqa: E731

    def row(name: str, r: dict) -> str:
        return (f'| {name} | {num(r["potongan"])} | {num(r["tiket"])} | {r["kata_rata"]:.0f} | {pct(r["top1"])} | '
                f'{pct(r["top3"])} | {dec(r["mrr"])} |')

    base = results['sebelum (aturan lama)']
    gates = {name: passes(r, base) for name, r in results.items() if r is not base}
    lines = [
        '# Banding ekstraksi solusi untuk indeks pencarian (/chat, /cari, /kandidat)', '',
        f'Tanggal: {date.today():%d %b %Y}. `ai/scripts/banding_solusi.py`. Hanya angka; teks tiket tidak ditampilkan.', '',
        '## Set uji (sama dengan `reports/banding_embedding.md`)', '',
        f'- Korpus: potongan tiket selesai yang dibuka **Jan–Jun 2026**; kueri: teks masalah **{num(len(queries))}** tiket '
        'selesai **Jul–Ags 2026** (sama untuk semua varian, tidak bergantung pada ada/tidaknya solusi).',
        '- Relevan = potongan dari tiket yang ditangani **tim yang sama** (potongan dedup: salah satu tiketnya).',
        f'- Metrik: Top-1, Top-3, MRR@{K}, per sumber (potongan lanjutan tiket yang sama tidak dihitung ulang). '
        f'Model `{MODEL_NAME}`.', '',
        '## Hasil', '',
        '| Varian | Potongan | Tiket terwakili | Kata/potongan | Top-1 | Top-3 | MRR@10 |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |',
        *[row(name, r) for name, r in results.items()],
    ]
    if reference:
        lines.append(row(f'acuan: ekspor lama + aturan lama ({num(reference["kueri"])} kueri, set banding_embedding)',
                         reference))
    lines += [
        '', '## Aturan', '',
        '- **Sebelum**: pesan substantif terakhir di seluruh percakapan (termasuk sesudah tiket diselesaikan), pesan '
        'bercirikan petugas diutamakan; cadangan `resolution` → `close_notes`; satu potongan utuh per tiket.',
        '- **Sesudah**: pesan terakhir yang dikirim ≤ `resolved` + 5 menit, bukan dari pemohon (pesan terakhir dicek '
        'dengan `last_conversation_user_id`), lolos `substantive_text`, ≥ 5 kata; cadangan `close_notes` → `resolution` '
        'bila bukan template. Toleransi 5 menit (bukan 1): petugas sering menulis solusi 1–3 menit sesudah menekan '
        '"selesai" (median 1,6 menit, 91% ≤ 5 menit); dengan 1 menit 209 solusi asli hilang. Solusi > 220 kata '
        'dipecah, teks masalah diulang di setiap potongan (varian "potongan lanjutan berawalan judul" saja: Top-3 '
        'turun ±1,6 poin pada uji pendahuluan).',
        '- **Dedup**: solusi identik (abaikan huruf besar & tanda baca) → satu potongan, masalah dari tiket terbaru, '
        '`jumlah_tiket` & semua nomor tiket disimpan (dipakai `/kandidat`).',
        '', '## Keputusan', '',
        f'Syarat "tidak lebih buruk" dari *sebelum*: Top-1 & Top-3 turun ≤ {TOL_POINT * 100:.0f} poin dan MRR turun ≤ '
        f'{TOL_MRR:.2f}'.replace('.', ',') + f'. Dengan {num(len(queries))} kueri, galat baku Top-1 ±1,4 poin, jadi '
        'selisih di bawah 1 poin dianggap derau.', '',
        *[f'- {name}: **{"lolos" if ok else "tidak lolos"}** (Top-1 {(r["top1"] - base["top1"]) * 100:+.2f} poin, '
          f'Top-3 {(r["top3"] - base["top3"]) * 100:+.2f} poin, MRR {r["mrr"] - base["mrr"]:+.4f})'.replace('.', ',')
          for (name, ok), r in zip(gates.items(), [results[n] for n in gates])],
        '',
        f'- Indeks memakai **{"sesudah + dedup" if gates.get("sesudah + dedup") else ("sesudah" if gates.get("sesudah (aturan baru)") else "sebelum")}**'
        ' (`ai/scripts/build_index.py`, konstanta `DEDUP`).',
        '- Keterbatasan: relevansi berdasarkan kesamaan tim, bukan penilaian manusia atas solusi. Dedup memperkecil '
        'korpus sehingga satu potongan mewakili banyak tiket; proksi tim menghukum hal ini (tiga hasil teratas tidak '
        'lagi berisi salinan solusi yang sama). Mutu solusi aturan baru dinilai terpisah pada sampel manual.',
    ]
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    for name, r in results.items():
        print(name, {k: round(v, 4) if isinstance(v, float) else v for k, v in r.items()})
    if reference:
        print('acuan', {k: round(v, 4) if isinstance(v, float) else v for k, v in reference.items()})
    print('gerbang', gates)


if __name__ == '__main__':
    main()
