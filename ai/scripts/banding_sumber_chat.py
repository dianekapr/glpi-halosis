"""Dampak pembatasan sumber /chat (A.1) → bagian berpenanda di reports/banding_solusi.md (angka + contoh rekaan).

Kebijakan /chat disimulasikan pada indeks aktif: "sebelum" = semua sumber, "sesudah" = hanya KB terbit + katalog layanan
(app.CHAT_SOURCES). Kueri = teks masalah tiket selesai Jul–Ags 2026; potongan tiket yang dibuka sejak Juli dibuang dari
korpus agar kueri tidak menemukan dirinya sendiri. Contoh memakai pertanyaan rekaan, bukan teks tiket; sumber tiket
tidak ditampilkan judulnya.

Pakai: .venv/bin/python ai/scripts/banding_sumber_chat.py
"""
from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from banding_solusi import QA, SOLVED, SPLIT, TICKETS, problem  # noqa: E402
from halosis_ai import privacy, search  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'reports/banding_solusi.md'
MARK_START, MARK_END = '<!-- sumber-chat:mulai -->', '<!-- sumber-chat:selesai -->'
MIN_SCORE, SUGGEST_SCORE, POOL = 0.83, 0.78, 20  # bawaan app.py: CHAT_MIN_SCORE, CHAT_SUGGEST_MIN_SCORE, CHAT_CHOICE_POOL
APPROVED = {'kb', 'layanan'}
EXAMPLES = ['Lupa kata sandi akun SSO', 'Printer di ruangan tidak bisa mencetak', 'Bagaimana cara mengajukan akun Zoom',
            'Kuota email saya penuh', 'Aplikasi presensi error saat dibuka', 'Bagaimana resep nasi goreng']


def decide(scores: np.ndarray, chunks: pd.DataFrame, allowed: np.ndarray) -> dict:
    """Satu kueri → keputusan /chat: mode, jenis sumber teratas, skor teratas, sumber teratas."""
    scores = np.where(allowed, scores, -np.inf)
    order = np.argsort(-scores)[:POOL * 8]
    seen, found = set(), []
    for i in order:
        source = chunks['sumber'].iat[i]
        if scores[i] != -np.inf and source not in seen:
            seen.add(source)
            found.append(i)
        if len(found) == POOL:
            break
    top = found[0]
    kinds = chunks['jenis_sumber'].to_numpy()
    if scores[top] >= MIN_SCORE:
        mode = 'jawab'
    elif any(kinds[i] == 'kb' and scores[i] >= SUGGEST_SCORE for i in found):
        mode = 'pilihan'
    else:
        mode = 'tidak-ditemukan'
    return {'mode': mode, 'jenis': kinds[top], 'skor': float(scores[top]), 'sumber': chunks['sumber'].iat[top],
            'judul': chunks['judul'].iat[top]}


def main() -> None:
    chunks, vectors = search.load_index()
    t = pd.read_parquet(TICKETS)
    t = t[t['state_name'].isin(SOLVED)].copy()
    t['masalah'] = problem(t)
    t = t[t['masalah'].str.len() > 0]
    queries = t[pd.to_datetime(t['opened'], errors='coerce') >= SPLIT]
    qa = pd.read_parquet(QA, columns=['ticket_number', 'tanggal'])
    later = set(qa.loc[pd.to_datetime(qa['tanggal']) >= SPLIT, 'ticket_number'].astype(str))
    keep = ~(chunks['jenis_sumber'].eq('tiket') & chunks['sumber'].astype(str).isin(later)).to_numpy()
    chunks, vectors = chunks[keep].reset_index(drop=True), vectors[keep]

    masked = [str(privacy.mask_text(q)) for q in queries['masalah']]
    scores = search.embed(masked, 'query') @ vectors.T
    example_scores = search.embed([str(privacy.mask_text(q)) for q in EXAMPLES], 'query') @ vectors.T
    policies = {'sebelum (semua sumber)': np.ones(len(chunks), bool),
                'sesudah (KB + layanan)': chunks['jenis_sumber'].isin(APPROVED).to_numpy()}
    results = {name: pd.DataFrame([decide(row, chunks, allowed) for row in scores]) for name, allowed in policies.items()}

    pct = lambda v: f'{v * 100:.2f}%'.replace('.', ',')  # noqa: E731
    dec = lambda v: f'{v:.3f}'.replace('.', ',')  # noqa: E731
    counts = chunks.groupby('jenis_sumber')['sumber'].nunique()
    n = len(queries)

    def row(name: str, r: pd.DataFrame) -> str:
        answered = r[r['mode'] == 'jawab']
        by_kind = answered['jenis'].value_counts(normalize=True)
        return (f'| {name} | {pct((r["mode"] == "jawab").mean())} | {pct((r["mode"] == "pilihan").mean())} | '
                f'{pct((r["mode"] == "tidak-ditemukan").mean())} | {pct(by_kind.get("tiket", 0))} | '
                f'{pct(by_kind.get("kb", 0))} | {pct(by_kind.get("layanan", 0))} | {dec(r["skor"].median())} |')

    def example(question: str, s: np.ndarray) -> str:
        cells = []
        for allowed in policies.values():
            d = decide(s, chunks, allowed)
            label = 'tiket (disembunyikan)' if d['jenis'] == 'tiket' else f'{d["sumber"]} "{d["judul"][:50]}"'
            cells.append(f'{d["mode"]} · {label} · {dec(d["skor"])}')
        return f'| {question} | {cells[0]} | {cells[1]} |'

    section = '\n'.join([
        MARK_START, '## Dampak pembatasan sumber /chat (A.1)', '',
        f'Tanggal: {date.today():%d %b %Y}. `ai/scripts/banding_sumber_chat.py` (jalankan ulang setelah '
        '`banding_solusi.py`, yang menulis ulang berkas ini). `/chat` hanya menjawab dari artikel KB terbit + katalog '
        'layanan; solusi tiket tetap untuk Cari pengetahuan dan Kandidat Knowledge.', '',
        f'Simulasi keputusan `/chat` pada indeks aktif ({counts.get("kb", 0)} artikel KB, {counts.get("layanan", 0)} '
        f'layanan, {counts.get("tiket", 0)} tiket Jan–Jun), ambang {MIN_SCORE}/{SUGGEST_SCORE}, {n} kueri (masalah tiket '
        'selesai Jul–Ags 2026). Tiket sejak Juli dibuang dari korpus agar kueri tidak menemukan dirinya sendiri.', '',
        '| Kebijakan | Dijawab | Pilihan "Maksud Anda" | Tidak ditemukan | Jawaban dari tiket | dari KB | dari layanan | Median skor teratas |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |',
        *[row(name, r) for name, r in results.items()], '',
        '### Contoh (pertanyaan rekaan, bukan teks tiket)', '',
        '| Pertanyaan | Sebelum (mode · sumber · skor) | Sesudah (mode · sumber · skor) |', '| --- | --- | --- |',
        *[example(q, s) for q, s in zip(EXAMPLES, example_scores)], '',
        'Keterbatasan: **"dijawab" bukan berarti benar**, hanya skor teratas ≥ ambang. Korpus sesudah sangat kecil, dan '
        'skor e5 teratas tetap tinggi walau topiknya meleset (lihat contoh presensi → layanan umum), jadi tingkat jawab '
        'sesudah kemungkinan melebihi jawaban yang benar-benar relevan; ketepatan belum diukur dan ambang belum '
        'dikalibrasi ulang untuk korpus ini (bagian C.9). Kueri berupa teks tiket, bukan pertanyaan chat.', MARK_END])
    text = REPORT.read_text(encoding='utf-8')
    if MARK_START in text:
        text = re.sub(re.escape(MARK_START) + '.*?' + re.escape(MARK_END), lambda _: section, text, flags=re.S)
    else:
        text = text.rstrip('\n') + '\n\n' + section + '\n'
    REPORT.write_text(text, encoding='utf-8')
    for name, r in results.items():
        print(name, r['mode'].value_counts(normalize=True).round(4).to_dict())


if __name__ == '__main__':
    main()
