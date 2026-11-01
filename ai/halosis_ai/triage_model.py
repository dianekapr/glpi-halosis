"""Model saran triase (routing ke tim) HaloSIS.

Input HANYA informasi saat tiket dibuat: judul + deskripsi + jenis (INC/REQ). Teks selalu disamarkan
(privacy.mask_text) sebelum diubah menjadi fitur, baik saat latih maupun saat dipakai layanan.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import OneHotEncoder

from . import privacy, quality

OTHER = 'Lainnya'
MIN_TEAM_TICKETS = 30
MANUAL_REVIEW_THRESHOLD = 0.70


def model_text(title: object, description: object, ticket_type: object) -> str:
    """Teks fitur: jenis sebagai token, judul diulang (lebih informatif), lalu deskripsi; sudah disamarkan."""
    title = str(privacy.mask_text(str(title or '')))
    description = str(privacy.mask_text(str(description or '')))
    kind = f'jenis_{str(ticket_type or "").strip().lower() or "x"}'
    text = f'{kind} {title} {title} {description}'.lower()
    text = re.sub(r'\d+', '0', text)
    return re.sub(r'\s+', ' ', text).strip()


def jenis_text(title: object, description: object) -> str:
    """Teks fitur klasifier jenis REQ/INC (T4): sama dengan model_text tetapi tanpa token jenis yang diprediksi."""
    return model_text(title, description, None).removeprefix('jenis_x ')


def build_pipeline(c: float = 10.0, class_weight: str | None = 'balanced', calibrate: bool = True) -> Pipeline:
    features = FeatureUnion([
        ('kata', TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.5, sublinear_tf=True,
                                 token_pattern=r'(?u)\b\w\w+\b|\[[a-z]+\]')),
        ('karakter', TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=3, sublinear_tf=True,
                                     max_features=150_000)),
    ])
    classifier = LogisticRegression(C=c, class_weight=class_weight, max_iter=3000)
    if calibrate:
        classifier = CalibratedClassifierCV(classifier, method='sigmoid', cv=5)
    return Pipeline([('fitur', features), ('model', classifier)])


def urgency_frame(title: object, description: object, team: object) -> pd.DataFrame:
    """Masukan model urgensi: teks fitur (sama dengan jenis_text) + nama tim (tim tiket atau saran triase)."""
    return pd.DataFrame({'teks': [jenis_text(title, description)], 'tim': [str(team or '').strip() or OTHER]})


def build_urgency_pipeline(c: float = 3.0) -> Pipeline:
    """Urgensi insiden Medium/Low: TF-IDF teks tersamar + one-hot nama tim, LR berbobot kelas seimbang.

    Keputusan dari P(Low) dengan ambang per kelas (pick_urgency_thresholds): Low bila P(Low) ≥ ambang Low, Medium bila
    P(Low) ≤ ambang Medium, di antaranya tidak disarankan (aturan kata kunci).
    """
    features = ColumnTransformer([
        ('kata', TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.5, sublinear_tf=True,
                                 token_pattern=r'(?u)\b\w\w+\b|\[[a-z]+\]'), 'teks'),
        ('karakter', TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=3, sublinear_tf=True,
                                     max_features=100_000), 'teks'),
        ('tim', OneHotEncoder(handle_unknown='ignore', min_frequency=5), ['tim']),
    ])
    return Pipeline([('fitur', features), ('model', LogisticRegression(C=c, class_weight='balanced', max_iter=3000))])


URGENCY_GRID_LOW = tuple(round(0.50 + 0.05 * i, 2) for i in range(10))     # 0,50 … 0,95
URGENCY_GRID_MEDIUM = tuple(round(0.50 - 0.05 * i, 2) for i in range(10))  # 0,50 … 0,05


def urgency_class_metrics(kelas: str, p_low: np.ndarray, y: np.ndarray, threshold: float) -> dict:
    """Metrik satu kelas pada ambangnya dari P(Low) validasi silang. Low: presisi (+ Wilson 95%), recall; Medium:
    akurasi & cakupan. pembanding = proporsi kelas itu (tebakan tanpa model)."""
    is_low = np.asarray(y) == 'Low'
    chosen = p_low >= threshold if kelas == 'Low' else p_low <= threshold
    target = is_low if kelas == 'Low' else ~is_low
    hits, n = int((chosen & target).sum()), int(chosen.sum())
    r = lambda v: round(float(v), 4)  # noqa: E731
    m = {'ambang': threshold, 'tiket': n, 'cakupan': r(chosen.mean()), 'pembanding': r(target.mean())}
    if kelas == 'Low':
        ci = quality.wilson(hits, n)
        m.update({'presisi': r(hits / n) if n else None, 'wilson_95': [r(ci[0]), r(ci[1])] if ci else None,
                  'recall': r(hits / max(int(target.sum()), 1))})
    else:
        m['akurasi'] = r(hits / n) if n else None
    return m


def pick_urgency_thresholds(p_low: np.ndarray, y: np.ndarray) -> dict:
    """Ambang per kelas otomatis: Low = ambang terendah yang lolos (recall maksimum); Medium = ambang tertinggi yang
    lolos (cakupan maksimum); syarat = quality.urgency_class_check. Tidak ada yang lolos → ambang terketat dicatat
    dengan `lolos` False (kelas itu tidak disarankan)."""
    p_low = np.asarray(p_low, dtype=float)
    out = {}
    for kelas, grid in (('Low', URGENCY_GRID_LOW), ('Medium', URGENCY_GRID_MEDIUM)):
        candidates = [urgency_class_metrics(kelas, p_low, y, t) for t in grid]
        passing = [m for m in candidates if quality.urgency_class_check(kelas, m)[0]]
        out[kelas] = {**(passing[0] if passing else candidates[-1]), 'lolos': bool(passing)}
    return out


@dataclass
class SimilarIndex:
    """Tiket latih yang mirip (TF-IDF kata, kosinus) sebagai penjelasan saran."""
    vectorizer: TfidfVectorizer
    neighbors: NearestNeighbors
    ticket_numbers: list[str]
    teams: list[str]
    titles: list[str]  # judul tersamarkan

    @classmethod
    def fit(cls, texts: list[str], ticket_numbers: list[str], teams: list[str], titles: list[str]) -> 'SimilarIndex':
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        matrix = vectorizer.fit_transform(texts)
        neighbors = NearestNeighbors(metric='cosine').fit(matrix)
        return cls(vectorizer, neighbors, list(ticket_numbers), list(teams), list(titles))

    def search(self, text: str, k: int = 3) -> list[dict]:
        distances, indexes = self.neighbors.kneighbors(self.vectorizer.transform([text]), n_neighbors=k)
        return [
            {'ticket_number': self.ticket_numbers[i], 'tim': self.teams[i], 'judul': self.titles[i],
             'kemiripan': round(float(1 - d), 3)}
            for d, i in zip(distances[0], indexes[0])
        ]


@dataclass
class TriageModel:
    pipeline: Pipeline
    similar: SimilarIndex
    version: str
    threshold: float = MANUAL_REVIEW_THRESHOLD
    metadata: dict = field(default_factory=dict)

    @property
    def classes(self) -> list[str]:
        return list(self.pipeline.classes_)

    def predict(self, title: object, description: object, ticket_type: object, k: int = 3) -> dict:
        text = model_text(title, description, ticket_type)
        probs = self.pipeline.predict_proba([text])[0]
        order = np.argsort(probs)[::-1][:3]
        top = [{'tim': self.classes[i], 'keyakinan': round(float(probs[i]), 4)} for i in order]
        return {
            'tim': top[0]['tim'],
            'keyakinan': top[0]['keyakinan'],
            # Kelas gabungan "Lainnya" (tim kecil) bukan tim tujuan: selalu penilaian manual (tata_kelola_ai.md §2)
            'perlu_penilaian_manual': top[0]['keyakinan'] < self.threshold or top[0]['tim'] == OTHER,
            'top3': top,
            'tiket_mirip': self.similar.search(text, k=k),
            'versi_model': self.version,
        }
