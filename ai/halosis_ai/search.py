"""Pencarian semantik HaloSIS (RAG): embedding lokal atas artikel KB GLPI yang terbit + qa_pairs.

Indeks disimpan di ai/index/ (di-ignore git): chunks.parquet (potongan + sumber) dan vectors.npy
(embedding ternormalisasi, float32). Pencarian = kosinus (perkalian titik). Semua teks disamarkan.

Artikel KB bisa diperbarui satu per satu (update_article, UC-09 langkah 7) tanpa membangun ulang indeks:
potongan artikel itu diganti/dihapus di memori, lalu indeks ditulis atomik (file sementara + rename) di bawah lock.
"""
from __future__ import annotations

import html
import os
import re
import threading
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from . import privacy

MODEL_NAME = 'intfloat/multilingual-e5-base'
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


@lru_cache(maxsize=1)
def encoder():
    from sentence_transformers import SentenceTransformer  # impor berat, hanya saat dipakai
    return SentenceTransformer(MODEL_NAME)


def embed(texts: list[str], kind: str) -> np.ndarray:
    """E5 memakai awalan 'query: ' untuk pertanyaan dan 'passage: ' untuk dokumen."""
    prefixed = [f'{kind}: {t}' for t in texts]
    return encoder().encode(prefixed, batch_size=32, normalize_embeddings=True, show_progress_bar=len(texts) > 100)\
        .astype(np.float32)


def load_index(index_dir: Path | None = None) -> tuple[pd.DataFrame, np.ndarray]:
    index_dir = index_dir or INDEX_DIR  # dibaca saat dipanggil (tes bisa memakai folder sementara)
    if index_dir not in _indexes:
        with _lock:
            if index_dir not in _indexes:
                _indexes[index_dir] = (pd.read_parquet(index_dir / 'chunks.parquet'), np.load(index_dir / 'vectors.npy'))
    return _indexes[index_dir]


def update_article(kb_id: int, title: str, answer_html: str, remove: bool = False,
                   index_dir: Path | None = None) -> int:
    """Ganti (atau hapus bila remove) potongan artikel KB-<kb_id>; potongan tiket historis tidak disentuh.

    Kembalikan jumlah potongan artikel di indeks setelah pembaruan.
    """
    index_dir = index_dir or INDEX_DIR
    new = None if remove else article_chunks(kb_id, title, answer_html)
    new_vectors = embed(new['teks'].tolist(), 'passage') if new is not None and len(new) else None
    with _lock:
        chunks, vectors = _indexes.get(index_dir) or (pd.read_parquet(index_dir / 'chunks.parquet'),
                                                      np.load(index_dir / 'vectors.npy'))
        keep = (chunks['sumber'] != f'KB-{kb_id}').to_numpy()
        chunks, vectors = chunks[keep].reset_index(drop=True), vectors[keep]
        if new_vectors is not None:
            chunks = pd.concat([chunks, new], ignore_index=True)
            vectors = np.vstack([vectors, new_vectors]).astype(np.float32)
        _write_atomic(index_dir, chunks, vectors)
        _indexes[index_dir] = (chunks, vectors)
    return 0 if new_vectors is None else len(new)


def _write_atomic(index_dir: Path, chunks: pd.DataFrame, vectors: np.ndarray) -> None:
    tmp_chunks, tmp_vectors = index_dir / '.chunks.parquet.tmp', index_dir / '.vectors.npy.tmp'
    chunks.to_parquet(tmp_chunks, index=False)
    with open(tmp_vectors, 'wb') as f:
        np.save(f, vectors)
    os.replace(tmp_chunks, index_dir / 'chunks.parquet')
    os.replace(tmp_vectors, index_dir / 'vectors.npy')


def cari(query: str, k: int = 5, index_dir: Path | None = None) -> list[dict]:
    """Cari k potongan paling mirip → [{potongan, skor, sumber, jenis_sumber, judul}]."""
    chunks, vectors = load_index(index_dir)
    q = embed([str(privacy.mask_text(query))], 'query')[0]
    scores = vectors @ q
    top = np.argsort(scores)[::-1][:k]
    return [
        {'potongan': chunks.at[i, 'teks'], 'skor': round(float(scores[i]), 4), 'sumber': chunks.at[i, 'sumber'],
         'jenis_sumber': chunks.at[i, 'jenis_sumber'], 'judul': chunks.at[i, 'judul']}
        for i in top
    ]
