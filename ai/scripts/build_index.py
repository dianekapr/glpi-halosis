"""AI-4: bangun indeks pencarian dari artikel KB GLPI yang terbit + qa_pairs → ai/index/.

- KB  : diambil lewat REST API GLPI (bukan koneksi DB) — artikel FAQ atau yang punya target visibilitas
        (entitas/profil/grup/pengguna) dianggap terbit, sama dengan KnowledgeIndex::isPublished. API tidak bisa
        dipakai → berhenti dengan pesan jelas & exit code 1, indeks lama tidak disentuh (tidak ada fallback).
- QA  : data/processed/qa_pairs.parquet (sudah disamarkan): "masalah" + "solusi" per tiket selesai; solusi > 220 kata
        dipecah, masalah diulang di tiap potongan (search.ticket_chunks). Penggabungan solusi identik (DEDUP) tersedia
        tetapi mati: Top-1 turun 1,6–2 poin di set uji reports/banding_solusi.md.
- Layanan: potongan katalog layanan (POST /reindex/layanan) di indeks lama dibawa ulang, agar tidak hilang sampai
        GLPI mengirim ulang katalog.
Semua teks disamarkan ulang sebelum di-embed. Hanya angka yang dicetak.

Pakai (dari folder induk proyek):  .venv/bin/python ai/scripts/build_index.py
Cek API saja (tanpa embedding, indeks tidak ditulis):  .venv/bin/python ai/scripts/build_index.py --cek-kb
Environment: GLPI_API_URL (bawaan http://localhost:8080), GLPI_API_USER & GLPI_API_PASSWORD (bawaan akun lokal glpi)
atau GLPI_API_USER_TOKEN, GLPI_API_APP_TOKEN (bila diwajibkan GLPI).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import privacy  # noqa: E402
from halosis_ai.search import INDEX_DIR, MODEL_NAME, article_chunks, embed, ticket_chunks  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / 'data/processed/qa_pairs.parquet'
DEDUP = False  # gerbang reports/banding_solusi.md: dedup lebih buruk dari satu potongan per tiket

KB_TARGETS = ('Entity_KnowbaseItem', 'KnowbaseItem_Profile', 'Group_KnowbaseItem', 'KnowbaseItem_User')
PAGE = 200
TIMEOUT = 30


class ApiError(Exception):
    """REST API GLPI tidak bisa dipakai; pesannya aman dicetak (tanpa isi artikel/kredensial)."""


def _check(response: requests.Response, what: str) -> requests.Response:
    if response.status_code >= 400:
        raise ApiError(f'{what}: HTTP {response.status_code}')
    return response


def api_session(base: str) -> requests.Session:
    session = requests.Session()
    if os.environ.get('GLPI_API_APP_TOKEN'):
        session.headers['App-Token'] = os.environ['GLPI_API_APP_TOKEN']
    user_token = os.environ.get('GLPI_API_USER_TOKEN')
    login = {'headers': {'Authorization': f'user_token {user_token}'}} if user_token else {
        'auth': (os.environ.get('GLPI_API_USER') or 'glpi', os.environ.get('GLPI_API_PASSWORD') or 'glpi')}
    token = _check(session.get(f'{base}/initSession', timeout=TIMEOUT, **login), 'login API').json()['session_token']
    session.headers['Session-Token'] = token
    return session


def fetch_articles(session: requests.Session, base: str) -> list[dict]:
    """Semua artikel, per halaman. GLPI menjawab 400 ERROR_RANGE_EXCEEDS_TOTAL bila rentang melewati total."""
    articles, start = [], 0
    while True:
        response = session.get(f'{base}/KnowbaseItem', params={'range': f'{start}-{start + PAGE - 1}'}, timeout=TIMEOUT)
        if response.status_code == 400 and 'ERROR_RANGE_EXCEEDS_TOTAL' in response.text:
            return articles
        page = _check(response, 'daftar artikel').json()
        articles += page
        if len(page) < PAGE:
            return articles
        start += PAGE


def is_published(session: requests.Session, base: str, article: dict) -> bool:
    if article.get('is_faq'):
        return True
    return any(_check(session.get(f'{base}/KnowbaseItem/{article["id"]}/{target}', timeout=TIMEOUT),
                      f'target visibilitas {target}').json() for target in KB_TARGETS)


def load_kb() -> pd.DataFrame:
    base = (os.environ.get('GLPI_API_URL') or 'http://localhost:8080').rstrip('/') + '/apirest.php'
    try:
        session = api_session(base)
        try:
            published = [a for a in fetch_articles(session, base) if is_published(session, base, a)]
        finally:
            session.get(f'{base}/killSession', timeout=TIMEOUT)
    except (requests.RequestException, ApiError, KeyError, ValueError) as e:
        detail = str(e) if isinstance(e, ApiError) else type(e).__name__
        raise SystemExit(f'GAGAL: artikel KB tidak bisa diambil dari REST API GLPI ({base}): {detail}. Indeks tidak '
                         'ditulis. Pastikan GLPI berjalan, API aktif, dan kredensial GLPI_API_* benar.') from e
    chunks = [article_chunks(int(a['id']), str(a['name']), str(a['answer'])) for a in published]
    if not chunks:
        return pd.DataFrame(columns=['sumber', 'jenis_sumber', 'judul', 'teks'])
    return pd.concat(chunks, ignore_index=True)


def load_qa() -> pd.DataFrame:
    return ticket_chunks(pd.read_parquet(QA), dedup=DEDUP)


def load_services() -> pd.DataFrame:
    """Potongan katalog layanan dari indeks yang sedang dipakai (jenis_sumber 'layanan'), bila ada."""
    try:
        old = pd.read_parquet(INDEX_DIR / 'chunks.parquet')
    except (OSError, ValueError):
        return pd.DataFrame(columns=['sumber', 'jenis_sumber', 'judul', 'teks'])
    return old.loc[old['jenis_sumber'] == 'layanan', ['sumber', 'jenis_sumber', 'judul', 'teks']].reset_index(drop=True)


def main() -> None:
    kb = load_kb()  # lebih dulu: API mati → berhenti sebelum embedding
    if '--cek-kb' in sys.argv:
        print(f'REST API OK. Potongan KB: {len(kb)} dari {kb["sumber"].nunique()} artikel terbit. Indeks tidak ditulis.')
        return
    qa, services = load_qa(), load_services()
    chunks = pd.concat([kb, qa, services], ignore_index=True)
    leaks = sum(len(p.findall(' '.join(chunks['teks']))) for p in
                (privacy._EMAIL, privacy._NIP, privacy._NIP_OLD, privacy._NIK, privacy._PHONE))
    if leaks:
        raise SystemExit(f'Potongan memuat {leaks} pola data pribadi, indeks tidak ditulis.')

    vectors = embed(chunks['teks'].tolist(), 'passage')
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    chunks.to_parquet(INDEX_DIR / 'chunks.parquet', index=False)
    np.save(INDEX_DIR / 'vectors.npy', vectors)
    print(f'Model embedding : {MODEL_NAME} (dimensi {vectors.shape[1]})')
    print(f'Potongan KB     : {len(kb)} dari {kb["sumber"].nunique()} artikel')
    print(f'Potongan tiket  : {len(qa)} dari {int(qa.drop_duplicates("sumber")["jumlah_tiket"].sum())} tiket '
          f'({qa["sumber"].nunique()} sumber, {int((qa.groupby("sumber").size() > 1).sum())} dipecah > 220 kata)')
    print(f'Potongan layanan: {len(services)} (dibawa dari indeks sebelumnya)')
    print(f'Disimpan        : {INDEX_DIR.relative_to(ROOT)}/chunks.parquet, vectors.npy')


if __name__ == '__main__':
    main()
