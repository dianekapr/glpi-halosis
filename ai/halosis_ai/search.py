"""Pencarian semantik HaloSIS (RAG): embedding lokal atas artikel KB GLPI yang terbit + qa_pairs.

Indeks disimpan di ai/index/ (di-ignore git): chunks.parquet (potongan + sumber) dan vectors.npy
(embedding ternormalisasi, float32). Pencarian = kosinus (perkalian titik). Semua teks disamarkan.

Artikel KB bisa diperbarui satu per satu (update_article, UC-09 langkah 7) tanpa membangun ulang indeks:
potongan artikel itu diganti/dihapus di memori, lalu indeks ditulis atomik (file sementara + rename) di bawah lock.
"""
from __future__ import annotations

import html
import json
import os
import urllib.request
import re
import threading
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from . import privacy

LOCAL_MODEL = 'intfloat/multilingual-e5-base'
MODEL_NAME = LOCAL_MODEL  # nama model lokal bawaan; konfigurasi aktif: model_name()
INDEX_DIR = Path(__file__).resolve().parents[1] / 'index'
MAX_WORDS = 220  # panjang potongan (kata); artikel KB panjang dipecah

_indexes: dict[Path, tuple[pd.DataFrame, np.ndarray]] = {}
_lock = threading.Lock()


def strip_html(value: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', html.unescape(html.unescape(value or '')))
    return re.sub(r'\s+', ' ', text).strip()


def chunk(text: str) -> list[str]:
    words = text.split()
    return [' '.join(words[i:i + MAX_WORDS]) for i in range(0, max(len(words), 1), MAX_WORDS)]


def article_chunks(kb_id: int, title: str, answer_html: str) -> pd.DataFrame:
    """Potongan satu artikel KB (tersamar), format sama dengan build_index.py."""
    title = str(privacy.mask_text(title))
    rows = [{'sumber': f'KB-{kb_id}', 'jenis_sumber': 'kb', 'judul': title, 'teks': f'{title}. {part}'}
            for part in chunk(str(privacy.mask_text(strip_html(answer_html))))]
    return pd.DataFrame(rows, columns=['sumber', 'jenis_sumber', 'judul', 'teks'])


def _solution_key(text: str) -> str:
    return re.sub(r'\W+', ' ', text.lower()).strip()


def ticket_chunks(qa: pd.DataFrame, dedup: bool = True) -> pd.DataFrame:
    """Potongan tiket historis dari qa_pairs (masalah, solusi, ticket_number, tanggal), teks disamarkan ulang.

    dedup: tiket dengan teks solusi identik (abaikan huruf besar & tanda baca) → satu potongan; masalah diambil dari
    tiket terbaru, `jumlah_tiket` = banyak tiket, `tiket` = semua nomornya (terbaru dulu). Solusi > MAX_WORDS kata
    dipecah; setiap potongan memuat teks masalah utuh (kueri pengguna berupa masalah; potongan lanjutan yang hanya
    berawalan judul menurunkan Top-3, reports/banding_solusi.md). Kolom `masalah`/`solusi` menyimpan teks utuh.
    """
    qa = qa[qa['solusi'].fillna('').str.strip().str.len() > 0].copy()
    qa['masalah'] = [str(privacy.mask_text(str(m))) for m in qa['masalah']]
    qa['solusi'] = [str(privacy.mask_text(str(v))) for v in qa['solusi']]
    qa['ticket_number'] = qa['ticket_number'].astype(str)
    qa = qa.sort_values('tanggal', ascending=False, kind='stable') if 'tanggal' in qa else qa
    key = qa['solusi'].map(_solution_key) if dedup else pd.Series(range(len(qa)), index=qa.index)
    groups = qa.groupby(key, sort=False)
    head = groups.head(1).set_index(key[groups.head(1).index])
    members = groups['ticket_number'].agg(','.join)
    rows = []
    for k, r in head.iterrows():
        title = r['masalah'][:120]
        tickets = members[k].split(',')
        for part in chunk(r['solusi']):
            rows.append({'sumber': r['ticket_number'], 'jenis_sumber': 'tiket', 'judul': title,
                         'teks': f'Masalah: {r["masalah"]} Solusi: {part}', 'masalah': r['masalah'], 'solusi': r['solusi'],
                         'jumlah_tiket': len(tickets), 'tiket': ','.join(tickets)})
    return pd.DataFrame(rows, columns=['sumber', 'jenis_sumber', 'judul', 'teks', 'masalah', 'solusi', 'jumlah_tiket',
                                       'tiket'])


class IndexMismatch(RuntimeError):
    """Indeks dibangun dengan model/dimensi lain dari konfigurasi aktif."""


def provider() -> str:
    """EMBEDDING_PROVIDER = local (bawaan) | openai (endpoint /v1/embeddings)."""
    return 'openai' if os.environ.get('EMBEDDING_PROVIDER', '').strip().lower() == 'openai' else 'local'


def model_name() -> str:
    return os.environ.get('EMBEDDING_MODEL') or LOCAL_MODEL


def signature() -> dict:
    return {'provider': provider(), 'model': model_name()}


def check_compatible(chunks_len: int, vectors: np.ndarray, index_dir: Path) -> None:
    """Tolak indeks lama bila model/penyedia/dimensi berbeda dari konfigurasi aktif."""
    meta_path = index_dir / 'meta.json'
    # Indeks tanpa meta.json = dibangun sebelum fitur ini, dengan e5 lokal bawaan
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {'provider': 'local', 'model': LOCAL_MODEL}
    if (meta['provider'], meta['model']) != (signature()['provider'], signature()['model']):
        raise IndexMismatch(f'Indeks dibangun dengan {meta["provider"]}:{meta["model"]} tetapi konfigurasi aktif '
                            f'{provider()}:{model_name()}: bangun ulang indeks (ai/scripts/build_index.py).')
    if meta.get('dim') and vectors.shape[1] != meta['dim']:
        raise IndexMismatch(f'Dimensi indeks {vectors.shape[1]} != {meta["dim"]}: bangun ulang indeks.')
    if len(vectors) != chunks_len:
        raise IndexMismatch('Jumlah vektor tidak cocok dengan potongan: bangun ulang indeks.')


def write_meta(index_dir: Path, dim: int) -> None:
    (index_dir / 'meta.json').write_text(json.dumps({**signature(), 'dim': int(dim)}))


@lru_cache(maxsize=1)
def encoder():
    from sentence_transformers import SentenceTransformer  # impor berat, hanya saat dipakai
    return SentenceTransformer(LOCAL_MODEL)


def _remote_embed(prefixed: list[str]) -> np.ndarray:
    base = os.environ.get('EMBEDDING_BASE_URL', '').rstrip('/')
    if not base or not os.environ.get('EMBEDDING_MODEL'):
        raise RuntimeError('EMBEDDING_BASE_URL dan EMBEDDING_MODEL wajib untuk EMBEDDING_PROVIDER=openai')
    headers = {'Content-Type': 'application/json'}
    if os.environ.get('EMBEDDING_API_KEY'):
        headers['Authorization'] = f'Bearer {os.environ["EMBEDDING_API_KEY"]}'
    out = []
    for i in range(0, len(prefixed), 32):
        body = json.dumps({'model': model_name(), 'input': prefixed[i:i + 32]}).encode()
        req = urllib.request.Request(f'{base}/embeddings', data=body, headers=headers)
        with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 (URL dari konfigurasi admin)
            data = sorted(json.load(r)['data'], key=lambda d: d['index'])
        out.extend(d['embedding'] for d in data)
    vectors = np.asarray(out, dtype=np.float32)
    return vectors / np.maximum(np.linalg.norm(vectors, axis=1, keepdims=True), 1e-12)


def embed(texts: list[str], kind: str) -> np.ndarray:
    """E5 memakai awalan 'query: ' untuk pertanyaan dan 'passage: ' untuk dokumen (lokal maupun remote)."""
    prefixed = [f'{kind}: {t}' for t in texts]
    if provider() == 'openai':
        return _remote_embed(prefixed)
    return encoder().encode(prefixed, batch_size=32, normalize_embeddings=True, show_progress_bar=len(texts) > 100)\
        .astype(np.float32)


def load_index(index_dir: Path | None = None) -> tuple[pd.DataFrame, np.ndarray]:
    index_dir = index_dir or INDEX_DIR  # dibaca saat dipanggil (tes bisa memakai folder sementara)
    if index_dir not in _indexes:
        with _lock:
            if index_dir not in _indexes:
                chunks, vectors = pd.read_parquet(index_dir / 'chunks.parquet'), np.load(index_dir / 'vectors.npy')
                check_compatible(len(chunks), vectors, index_dir)
                _indexes[index_dir] = (chunks, vectors)
    return _indexes[index_dir]


def _read_checked(index_dir: Path) -> tuple[pd.DataFrame, np.ndarray]:
    chunks, vectors = pd.read_parquet(index_dir / 'chunks.parquet'), np.load(index_dir / 'vectors.npy')
    check_compatible(len(chunks), vectors, index_dir)
    return chunks, vectors


def update_article(kb_id: int, title: str, answer_html: str, remove: bool = False,
                   index_dir: Path | None = None) -> int:
    """Ganti (atau hapus bila remove) potongan artikel KB-<kb_id>; potongan tiket historis tidak disentuh.

    Kembalikan jumlah potongan artikel di indeks setelah pembaruan.
    """
    index_dir = index_dir or INDEX_DIR
    new = None if remove else article_chunks(kb_id, title, answer_html)
    new_vectors = embed(new['teks'].tolist(), 'passage') if new is not None and len(new) else None
    with _lock:
        chunks, vectors = _indexes.get(index_dir) or _read_checked(index_dir)
        keep = (chunks['sumber'] != f'KB-{kb_id}').to_numpy()
        chunks, vectors = chunks[keep].reset_index(drop=True), vectors[keep]
        if new_vectors is not None:
            chunks = pd.concat([chunks, new], ignore_index=True)
            vectors = np.vstack([vectors, new_vectors]).astype(np.float32)
        _write_atomic(index_dir, chunks, vectors)
        _indexes[index_dir] = (chunks, vectors)
    return 0 if new_vectors is None else len(new)


def replace_services(items: list[dict], index_dir: Path | None = None) -> int:
    """Ganti seluruh potongan katalog layanan (jenis_sumber 'layanan', sumber LAYANAN-<id>) dengan `items`
    [{id, nama, deskripsi}]; artikel KB & tiket historis tidak disentuh. Kembalikan jumlah potongan layanan."""
    index_dir = index_dir or INDEX_DIR
    new = pd.DataFrame([{
        'sumber': f'LAYANAN-{item["id"]}', 'jenis_sumber': 'layanan', 'judul': str(privacy.mask_text(item['nama'])),
        'teks': f'Layanan {privacy.mask_text(item["nama"])}. {privacy.mask_text(strip_html(item.get("deskripsi") or ""))}'.strip(),
    } for item in items], columns=['sumber', 'jenis_sumber', 'judul', 'teks'])
    new_vectors = embed(new['teks'].tolist(), 'passage') if len(new) else None
    with _lock:
        chunks, vectors = _indexes.get(index_dir) or _read_checked(index_dir)
        keep = (chunks['jenis_sumber'] != 'layanan').to_numpy()
        chunks, vectors = chunks[keep].reset_index(drop=True), vectors[keep]
        if new_vectors is not None:
            chunks = pd.concat([chunks, new], ignore_index=True)
            vectors = np.vstack([vectors, new_vectors]).astype(np.float32)
        _write_atomic(index_dir, chunks, vectors)
        _indexes[index_dir] = (chunks, vectors)
    return len(new)


def _write_atomic(index_dir: Path, chunks: pd.DataFrame, vectors: np.ndarray) -> None:
    tmp_chunks, tmp_vectors = index_dir / '.chunks.parquet.tmp', index_dir / '.vectors.npy.tmp'
    chunks.to_parquet(tmp_chunks, index=False)
    with open(tmp_vectors, 'wb') as f:
        np.save(f, vectors)
    os.replace(tmp_chunks, index_dir / 'chunks.parquet')
    os.replace(tmp_vectors, index_dir / 'vectors.npy')
    write_meta(index_dir, vectors.shape[1])


def cari(query: str, k: int = 5, index_dir: Path | None = None, jenis: tuple[str, ...] | None = None) -> list[dict]:
    """Cari k sumber paling mirip → [{potongan, skor, sumber, jenis_sumber, judul, solusi?}].

    jenis: batasi ke jenis_sumber tertentu (/chat: hanya sumber tersetujui); None = semua (/cari petugas).

    Satu hasil per sumber (potongan terbaik); artikel/tiket yang dipecah tidak memenuhi daftar dengan dirinya sendiri.
    `solusi` = solusi tiket utuh bila potongannya hasil pemecahan (kolom ada di indeks baru).
    """
    chunks, vectors = load_index(index_dir)
    q = embed([str(privacy.mask_text(query))], 'query')[0]
    scores = vectors @ q
    if jenis is not None:
        scores = np.where(chunks['jenis_sumber'].isin(jenis).to_numpy(), scores, -np.inf)
    has_solution = 'solusi' in chunks
    results, seen = [], set()
    for i in np.argsort(scores)[::-1]:
        if scores[i] == -np.inf:
            break  # sisanya di luar jenis yang diminta
        source = chunks.at[i, 'sumber']
        if source in seen:
            continue
        seen.add(source)
        hit = {'potongan': chunks.at[i, 'teks'], 'skor': round(float(scores[i]), 4), 'sumber': source,
               'jenis_sumber': chunks.at[i, 'jenis_sumber'], 'judul': chunks.at[i, 'judul']}
        if has_solution and isinstance(chunks.at[i, 'solusi'], str):
            hit['solusi'] = chunks.at[i, 'solusi']
        results.append(hit)
        if len(results) >= k:
            break
    return results
