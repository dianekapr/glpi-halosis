"""Model saran triase (routing ke tim) HaloSIS.

Input HANYA informasi saat tiket dibuat: judul + deskripsi + jenis (INC/REQ). Teks selalu disamarkan
(privacy.mask_text) sebelum diubah menjadi fitur, baik saat latih maupun saat dipakai layanan.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import NearestNeighbors
from sklearn.pipeline import FeatureUnion, Pipeline

from . import privacy

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
            'perlu_penilaian_manual': top[0]['keyakinan'] < self.threshold,
            'top3': top,
            'tiket_mirip': self.similar.search(text, k=k),
            'versi_model': self.version,
        }
