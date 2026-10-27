"""Pencarian semantik HaloSIS (RAG): embedding lokal atas artikel KB GLPI yang terbit + qa_pairs.

Indeks disimpan di ai/index/ (di-ignore git): chunks.parquet (potongan + sumber) dan vectors.npy
(embedding ternormalisasi, float32). Pencarian = kosinus (perkalian titik). Semua teks disamarkan.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from . import privacy

MODEL_NAME = 'intfloat/multilingual-e5-base'
INDEX_DIR = Path(__file__).resolve().parents[1] / 'index'


@lru_cache(maxsize=1)
def encoder():
    from sentence_transformers import SentenceTransformer  # impor berat, hanya saat dipakai
    return SentenceTransformer(MODEL_NAME)


def embed(texts: list[str], kind: str) -> np.ndarray:
    """E5 memakai awalan 'query: ' untuk pertanyaan dan 'passage: ' untuk dokumen."""
    prefixed = [f'{kind}: {t}' for t in texts]
    return encoder().encode(prefixed, batch_size=32, normalize_embeddings=True, show_progress_bar=len(texts) > 100)\
        .astype(np.float32)


@lru_cache(maxsize=1)
def load_index(index_dir: Path = INDEX_DIR) -> tuple[pd.DataFrame, np.ndarray]:
    return pd.read_parquet(index_dir / 'chunks.parquet'), np.load(index_dir / 'vectors.npy')


def cari(query: str, k: int = 5, index_dir: Path = INDEX_DIR) -> list[dict]:
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
