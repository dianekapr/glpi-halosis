"""C.7: replikasi PoC (dokumen hal. 51–56) → reports/replikasi_poc.md + reports/penilaian_relevansi.xlsx.

READ-ONLY terhadap model & indeks aktif: tidak ada artefak di ai/models/ atau ai/index/ yang ditulis. Laporan hanya
berisi angka, nama grup, dan pertanyaan rekaan. Hanya penilaian_relevansi.xlsx yang memuat teks tiket, sudah tersamar.

Bagian (dijalankan terpisah; tiap bagian mengganti bloknya sendiri di laporan):
  triase     Split acak rs42 20%, tanpa stratifikasi. Fitur TF-IDF/MiniLM/e5 × metode k-NN kosinus/LR, cakupan 56 grup &
             39 grup terbesar, lalu pipeline HaloSIS dilatih ulang pada data referensi split yang sama (di memori).
  pola       DBSCAN eps 0,25 min_samples 5 MiniLM atas semua INC + sliding window 1 jam, kemiripan 0,70, minimal 3.
  retrieval  Kasus dari ai/scripts/kasus_retrieval_poc.json (isian tim), MiniLM & e5, korpus KB + layanan indeks aktif.
  chat       /chat nyata: ekstraktif vs Qwen grounded + unknown-answer. Butuh Ollama (LLM_BASE_URL, LLM_MODEL).
  relevansi  reports/penilaian_relevansi.xlsx: 20 kueri × 5 hasil, kolom nilai kosong untuk diisi tim.

Dokumen tidak menyebut metode pemilihan grup, teks masukan, metrik DBSCAN, atau asal 39 grup; keputusannya dicatat
di laporan sebagai tafsiran. 5.319 + 1.339 pada dokumen juga tidak cocok dengan 20% dari 6.659.

Pakai: .venv/bin/python ai/scripts/replikasi_poc.py --bagian triase|pola|retrieval|chat|relevansi|semua
Uji cepat: tambahkan --sampel 50 --keluar <folder sementara> (pelatihan dipersingkat, angkanya tidak bermakna).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from datetime import date
from functools import lru_cache
from pathlib import Path

os.environ.setdefault('HF_HUB_OFFLINE', '1')  # MiniLM & e5 sudah di-cache; jangan mengunduh saat replikasi

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.cluster import DBSCAN  # noqa: E402
from sklearn.feature_extraction.text import TfidfVectorizer  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import precision_recall_fscore_support  # noqa: E402
from sklearn.model_selection import train_test_split  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from eda import num  # noqa: E402
from halosis_ai import privacy, search  # noqa: E402
from halosis_ai.triage_model import build_pipeline, model_text  # noqa: E402
from train_triage import f, label_teams, replace_section, table  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data/processed/tickets_clean.parquet'
QA = ROOT / 'data/processed/qa_pairs.parquet'
ACTIVE_MODEL = ROOT / 'ai/models/triage.joblib'
CASES = Path(__file__).resolve().parent / 'kasus_retrieval_poc.json'
MINILM = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'

SEED, TEST_SIZE, TOP_GROUPS = 42, 0.20, 39
EPS, MIN_SAMPLES = 0.25, 5
WINDOW_MINUTES, WINDOW_SIMILARITY, WINDOW_MINIMUM = 60, 0.70, 3
QUERY_START = pd.Timestamp('2026-07-01')
RELEVANCE_QUERIES, RELEVANCE_RESULTS, EXCERPT = 20, 5, 300
OLLAMA_URL, OLLAMA_MODEL = 'http://localhost:11434/v1', 'qwen2.5:3b'
ANSWERABLE = ['Saya lupa password akun BPS, bagaimana cara mengatasinya?',  # pertanyaan uji dokumen hal. 55
              'Bagaimana cara mengajukan permintaan VPN?']
UNKNOWN = ['Bagaimana cara memasang printer jaringan Epson L9999?', 'Apa resep nasi goreng yang enak?',
           'Berapa harga tiket pesawat Jakarta ke Medan besok?']

POC_TRIAGE = {'TF-IDF': (0.6833, 0.9089, 0.7989), 'Embedding': (0.7043, 0.9029, 0.8092)}  # dokumen hal. 54
POC_PATTERN = {'klaster': 14, 'noise': 1073, 'terkluster': 1704, 'kandidat': 23, 'episode': 17}  # dokumen hal. 56
POC_SIZES = [851, 390, 289, 88, 30]

OUT = ROOT / 'reports'


def clean(value: object) -> str:
    return '' if pd.isna(value) else str(value).strip()


def poc_text(title: object, description: object) -> str:
    return str(privacy.mask_text(f'{clean(title)}. {clean(description)}')).strip()


@lru_cache(maxsize=1)
def minilm_encoder():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(MINILM)


def minilm(texts: list[str]) -> np.ndarray:
    """MiniLM tanpa awalan, vektor ternormalisasi (kosinus = perkalian titik)."""
    return minilm_encoder().encode(texts, batch_size=32, normalize_embeddings=True,
                                   show_progress_bar=len(texts) > 100).astype(np.float32)


def write_section(name: str, body: str) -> None:
    path = OUT / 'replikasi_poc.md'
    if not path.exists():
        path.write_text('# Replikasi PoC (C.7)\n\nDihasilkan `ai/scripts/replikasi_poc.py`. Model & indeks aktif tidak '
                        'berubah; laporan hanya berisi angka, nama grup, dan pertanyaan rekaan.\n', encoding='utf-8')
    replace_section(path, (f'<!-- {name}:mulai -->', f'<!-- {name}:selesai -->'), f'{body}\n\nDibuat {date.today():%d-%m-%Y}.')
    print(f'[{name}] → {path}')


# --- Triase ---------------------------------------------------------------------------------------------------------

def load_tickets(sample: int | None) -> pd.DataFrame:
    df = pd.read_parquet(SRC, columns=['ticket_number', 'ticket_type', 'short_description', 'description',
                                       'assignment_group_name', 'opened'])
    df = df[df['assignment_group_name'].notna()].sort_values('ticket_number', kind='stable').reset_index(drop=True)
    if sample:
        df = df.sample(min(sample, len(df)), random_state=SEED).reset_index(drop=True)
    df['grup'] = df['assignment_group_name'].astype(str)
    df['teks'] = [poc_text(t, d) for t, d in zip(df['short_description'], df['description'])]
    return df


def rank_metrics(scores: np.ndarray, classes: np.ndarray, y_true: np.ndarray) -> dict:
    """Top-1/Top-3/MRR dari urutan grup; label yang tidak dikenal metode dihitung salah (MRR 0)."""
    ranking = np.asarray(classes)[np.argsort(-scores, axis=1, kind='stable')]
    y_true = np.asarray(y_true)
    hit = ranking == y_true[:, None]
    rr = np.where(hit.any(axis=1), 1.0 / (hit.argmax(axis=1) + 1), 0.0)
    predicted = ranking[:, 0]
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, predicted, average='macro', zero_division=0)
    return {'top1': float(hit[:, 0].mean()), 'top3': float(hit[:, :3].any(axis=1).mean()), 'mrr': float(rr.mean()),
            'f1': float(f1), 'presisi': float(precision), 'recall': float(recall), 'pred': predicted, 'y': y_true}


def knn_scores(similarity: np.ndarray, reference_groups: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Skor grup = kemiripan tiket referensi termirip di grup itu (urutan grup = urutan kemunculan pertama)."""
    classes = np.unique(reference_groups)
    return np.stack([similarity[:, reference_groups == c].max(axis=1) for c in classes], axis=1), classes


def lr_scores(train, y_train: np.ndarray, test) -> tuple[np.ndarray, np.ndarray]:
    model = LogisticRegression(max_iter=2000).fit(train, y_train)
    return model.predict_proba(test), model.classes_


def per_group_rows(scope: str, method: str, m: dict) -> tuple[list[dict], list[dict]]:
    groups = sorted(set(m['y']) | set(m['pred']))
    precision, recall, f1, support = precision_recall_fscore_support(m['y'], m['pred'], labels=groups, zero_division=0)
    per_group = [{'cakupan': scope, 'metode': method, 'grup': g, 'tiket_uji': int(n), 'presisi': round(float(p), 4),
                  'recall': round(float(r), 4), 'f1': round(float(v), 4)}
                 for g, p, r, v, n in zip(groups, precision, recall, f1, support)]
    pairs = pd.DataFrame({'aktual': m['y'], 'prediksi': m['pred']}).value_counts().reset_index(name='jumlah')
    confusion = [{'cakupan': scope, 'metode': method, **r} for r in pairs.to_dict('records')]
    return per_group, confusion


def run_triage(sample: int | None) -> None:
    df = load_tickets(sample)
    train_idx, test_idx = train_test_split(np.arange(len(df)), test_size=TEST_SIZE, random_state=SEED)
    train_idx, test_idx = np.sort(train_idx), np.sort(test_idx)
    groups = df['grup'].to_numpy()
    counts = df['grup'].value_counts()
    counts = counts.sort_index().sort_values(ascending=False, kind='stable')  # seri jumlah tiket: urut nama
    top = set(counts.index[:TOP_GROUPS])
    scopes = {f'{counts.size} grup': np.ones(len(df), dtype=bool), f'{min(TOP_GROUPS, counts.size)} grup terbesar': df['grup'].isin(top).to_numpy()}
    print(f'Tiket {len(df)}, grup {counts.size}, referensi {len(train_idx)}, uji {len(test_idx)}')

    texts = df['teks'].tolist()
    test_texts = [texts[i] for i in test_idx]
    timings = {}
    start = time.perf_counter()
    embedded_mini = minilm(texts)
    timings['MiniLM'] = time.perf_counter() - start
    start = time.perf_counter()
    e5_passage = search.embed(texts, 'passage')
    e5_query = search.embed(test_texts, 'query')
    timings['e5'] = time.perf_counter() - start
    e5_query_at = {int(i): n for n, i in enumerate(test_idx)}

    results, per_group, confusion = [], [], []

    def record(scope: str, method: str, scores: np.ndarray, classes: np.ndarray, y: np.ndarray) -> None:
        m = rank_metrics(scores, classes, y)
        results.append({'cakupan': scope, 'metode': method, 'tiket': len(y), **m})
        rows = per_group_rows(scope, method, m)
        per_group.extend(rows[0])
        confusion.extend(rows[1])

    for scope, mask in scopes.items():
        ref, tst = train_idx[mask[train_idx]], test_idx[mask[test_idx]]
        y_ref, y_tst = groups[ref], groups[tst]
        print(f'{scope}: referensi {len(ref)}, uji {len(tst)}, grup uji {len(set(y_tst))}')
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        x_ref = vectorizer.fit_transform([texts[i] for i in ref])
        x_tst = vectorizer.transform([texts[i] for i in tst])
        record(scope, 'TF-IDF k-NN', *knn_scores((x_tst @ x_ref.T).toarray(), y_ref), y_tst)
        record(scope, 'TF-IDF LR', *lr_scores(x_ref, y_ref, x_tst), y_tst)
        record(scope, 'MiniLM k-NN', *knn_scores(embedded_mini[tst] @ embedded_mini[ref].T, y_ref), y_tst)
        record(scope, 'MiniLM LR', *lr_scores(embedded_mini[ref], y_ref, embedded_mini[tst]), y_tst)
        queries = e5_query[[e5_query_at[int(i)] for i in tst]]
        record(scope, 'e5 k-NN', *knn_scores(queries @ e5_passage[ref].T, y_ref), y_tst)
        record(scope, 'e5 LR', *lr_scores(e5_passage[ref], y_ref, e5_passage[tst]), y_tst)

    # Model aktif dilatih Jan–Jun dan sebagian tiket uji acak ada di data latihnya, jadi pipeline dilatih ulang di memori
    settings = joblib.load(ACTIVE_MODEL).metadata.get('pengaturan') or {}
    settings = {'c': settings.get('c', 10.0), 'class_weight': settings.get('class_weight')}
    train_frame, test_frame = df.iloc[train_idx], df.iloc[test_idx]
    y_model = (label_teams(train_frame, train_frame) if not sample else train_frame['grup']).astype(str)
    model_texts = [model_text(t, d, k) for t, d, k in zip(df['short_description'], df['description'], df['ticket_type'])]
    start = time.perf_counter()
    pipeline = build_pipeline(calibrate=not sample, **settings).fit([model_texts[i] for i in train_idx], y_model)
    timings['HaloSIS'] = time.perf_counter() - start
    probabilities = pipeline.predict_proba([model_texts[i] for i in test_idx])
    classes = np.asarray(pipeline.classes_).astype(str)
    merged = (label_teams(test_frame, train_frame) if not sample else test_frame['grup']).astype(str).to_numpy()
    for scope, mask in scopes.items():
        keep = mask[test_idx]
        record(scope, 'HaloSIS (label gabungan)', probabilities[keep], classes, merged[keep])
        record(scope, 'HaloSIS (label asli)', probabilities[keep], classes, groups[test_idx][keep])

    pd.DataFrame(per_group).to_csv(OUT / 'replikasi_poc_per_grup.csv', index=False)
    pd.DataFrame(confusion).to_csv(OUT / 'replikasi_poc_confusion.csv', index=False)

    rows = [[r['cakupan'], r['metode'], num(r['tiket']), f(r['top1']), f(r['top3']), num(r['mrr'], 4), f(r['f1']),
             f(r['presisi']), f(r['recall'])] for r in results]
    best = max((r for r in results if not r['metode'].startswith('HaloSIS') and 'terbesar' in r['cakupan']),
               key=lambda r: r['top1'], default=results[0])
    mistakes = pd.DataFrame({'aktual': best['y'], 'prediksi': best['pred']})
    mistakes = mistakes[mistakes['aktual'] != mistakes['prediksi']].value_counts().head(10).reset_index(name='jumlah')
    write_section('triase', '\n'.join([
        '## Triase (BR-05)', '',
        f'Data: `tickets_clean.parquet`, {num(len(df))} tiket bergrup, {num(counts.size)} grup. Split acak '
        f'`random_state=42`, 20% uji, tanpa stratifikasi: referensi {num(len(train_idx))}, uji {num(len(test_idx))}.', '',
        table(['Acuan dokumen', 'Top-1', 'Top-3', 'MRR'],
              [[k, f(v[0]), f(v[1]), num(v[2], 4)] for k, v in POC_TRIAGE.items()]), '',
        table(['Cakupan', 'Metode', 'Tiket uji', 'Top-1', 'Top-3', 'MRR', 'F1 makro', 'Presisi makro', 'Recall makro'], rows), '',
        f'**Selisih dari PoC yang tidak bisa dihilangkan.** Dokumen menulis 6.659 tiket, 39 grup, referensi 5.319, uji '
        f'1.339; jumlah itu tidak saling cocok, dan data ini punya {num(counts.size)} grup. Tidak ada ambang jumlah tiket '
        'minimum yang menghasilkan tepat 39 grup, jadi cakupan 39 grup diambil dari grup terbanyak tiketnya, dengan '
        'tiket split yang sama. Hasil ini pembanding, bukan replikasi identik.', '',
        '**Tafsiran (tidak tertulis di dokumen).** Teks masukan = judul + deskripsi tersamar. k-NN: grup diurutkan menurut '
        'tiket referensi termirip (kosinus). LR: `LogisticRegression` bawaan sklearn. TF-IDF: unigram + bigram, `min_df=2`, '
        '`sublinear_tf`. e5 memakai awalan `query:` untuk kueri k-NN dan `passage:` selain itu.', '',
        f'**Model HaloSIS.** Pipeline `build_pipeline` (C = {num(settings["c"])}, bobot kelas = {settings["class_weight"] or "tidak"}, '
        'terkalibrasi) dilatih ulang di memori pada referensi split ini; artefak aktif tidak dipakai karena tiket uji acak '
        'bisa ada di data latihnya, dan tidak ditulis ulang. Tim < 30 tiket digabung "Lainnya". *Label gabungan* = cara '
        'produksi menilai; *label asli* = tiket tim kecil otomatis salah, sehingga sebanding dengan baris lain.', '',
        f'Waktu proses: embedding MiniLM {num(timings["MiniLM"], 1)} dtk, e5 {num(timings["e5"], 1)} dtk, latih HaloSIS '
        f'{num(timings["HaloSIS"], 1)} dtk.', '',
        f'Pasangan grup paling sering tertukar pada {best["metode"]}, {best["cakupan"]} (aktual → prediksi):', '',
        table(['Aktual', 'Prediksi', 'Tiket'], mistakes.values.tolist()), '',
        'Matriks kebingungan lengkap: `reports/replikasi_poc_confusion.csv`. Presisi/recall per grup: '
        '`reports/replikasi_poc_per_grup.csv`.',
    ]))


# --- Pola -----------------------------------------------------------------------------------------------------------

def sliding_windows(times: np.ndarray, vectors: np.ndarray, threshold: float, minutes: int, minimum: int,
                    pairwise: bool) -> dict:
    """Jendela berjangkar tiap insiden: anggota = insiden ≤ 1 jam setelah jangkar dengan kemiripan ≥ ambang ke jangkar.

    pairwise: anggota juga harus saling mirip ≥ ambang (diambil urut waktu). Tanpa union-find. Himpunan identik dibuang;
    `maksimal` juga membuang himpunan yang termuat di himpunan lain."""
    order = np.argsort(times, kind='stable')
    times, vectors = times[order], vectors[order]
    window = np.timedelta64(minutes, 'm')
    candidates = []
    for i in range(len(times)):
        end = int(np.searchsorted(times, times[i] + window, side='right'))
        scores = vectors[i + 1:end] @ vectors[i]
        members = [i] + [i + 1 + int(j) for j in np.flatnonzero(scores >= threshold)]
        if pairwise:
            kept = [i]
            for m in members[1:]:
                if np.all(vectors[kept] @ vectors[m] >= threshold):
                    kept.append(m)
            members = kept
        if len(members) >= minimum:
            candidates.append(frozenset(members))
    unique = set(candidates)
    return {'kandidat': len(candidates), 'unik': len(unique),
            'maksimal': sum(1 for s in unique if not any(s < other for other in unique))}


def run_pattern(sample: int | None) -> None:
    df = pd.read_parquet(SRC, columns=['ticket_type', 'short_description', 'description', 'opened'])
    df = df[df['ticket_type'].astype(str).str.upper().str.startswith('INC')].copy()
    df['opened'] = pd.to_datetime(df['opened'], errors='coerce')
    df = df.sort_values('opened', kind='stable').reset_index(drop=True)
    missing = int(df['opened'].isna().sum())
    if sample:
        df = df.head(sample).reset_index(drop=True)
    vectors = minilm([poc_text(t, d) for t, d in zip(df['short_description'], df['description'])])
    labels = DBSCAN(eps=EPS, min_samples=MIN_SAMPLES, metric='cosine').fit_predict(vectors)
    sizes = pd.Series(labels[labels >= 0]).value_counts().tolist()
    noise = int((labels == -1).sum())
    dated = df['opened'].notna().to_numpy()
    times = df.loc[dated, 'opened'].to_numpy()
    anchor = sliding_windows(times, vectors[dated], WINDOW_SIMILARITY, WINDOW_MINUTES, WINDOW_MINIMUM, False)
    strict = sliding_windows(times, vectors[dated], WINDOW_SIMILARITY, WINDOW_MINUTES, WINDOW_MINIMUM, True)
    rows = [['Klaster', num(POC_PATTERN['klaster']), num(len(sizes))],
            ['Noise', num(POC_PATTERN['noise']), num(noise)],
            ['Tiket terkluster', num(POC_PATTERN['terkluster']), num(len(df) - noise)],
            ['5 klaster terbesar', ' / '.join(num(v) for v in POC_SIZES), ' / '.join(num(v) for v in sizes[:5])]]
    window_rows = [[name, f'{num(POC_PATTERN["kandidat"])} → {num(POC_PATTERN["episode"])}',
                    f'{num(r["kandidat"])} → {num(r["unik"])}', num(r['maksimal'])]
                   for name, r in (('Mirip ke jangkar', anchor), ('Saling mirip semua anggota', strict))]
    write_section('pola', '\n'.join([
        '## Pola insiden (BR-07)', '',
        f'{num(len(df))} INC, MiniLM tanpa pemusatan, teks judul + deskripsi tersamar. DBSCAN eps 0,25, min_samples 5, '
        'jarak kosinus (metrik dan teks masukan tidak tertulis di dokumen).', '',
        table(['DBSCAN', 'PoC', 'Replikasi'], rows), '',
        'Sliding window: 1 jam, kemiripan 0,70, minimal 3 insiden, tanpa union-find, himpunan tiket ganda dibuang.', '',
        table(['Tafsiran "strict"', 'PoC kandidat → episode', 'Replikasi kandidat → unik', 'Tanpa himpunan bagian'], window_rows), '',
        f'Definisi jangkar jendela tidak tertulis di dokumen, jadi dua tafsiran dilaporkan. {num(missing)} INC tanpa '
        'tanggal dibuka dilewati pada sliding window. Ini metode PoC, bukan metode `/pola` produksi '
        '(`reports/banding_pola.md`).',
    ]))


# --- Retrieval ------------------------------------------------------------------------------------------------------

def load_cases(chunks: pd.DataFrame) -> list[dict]:
    cases = json.loads(CASES.read_text(encoding='utf-8')).get('kasus', [])
    known = set(chunks['judul']) | set(chunks['sumber'])  # sumber_benar boleh judul artikel atau kode sumber
    for n, case in enumerate(cases, 1):
        if not str(case.get('pertanyaan') or '').strip() or not case.get('sumber_benar'):
            raise SystemExit(f'Kasus {n}: "pertanyaan" dan "sumber_benar" wajib diisi ({CASES.name})')
        if isinstance(case['sumber_benar'], str):
            case['sumber_benar'] = [case['sumber_benar']]
        absent = set(case['sumber_benar']) - known
        if absent:
            raise SystemExit(f'Kasus {n}: sumber tidak ada di korpus: {sorted(absent)}')
    return cases


def source_ranks(scores: np.ndarray, sources: np.ndarray, wanted: list[str]) -> int | None:
    best = pd.Series(scores).groupby(sources).max().sort_values(ascending=False, kind='stable')
    hits = np.flatnonzero(best.index.isin(wanted))
    return int(hits[0]) + 1 if len(hits) else None


def run_retrieval(sample: int | None) -> None:
    chunks, vectors = search.load_index()
    approved = chunks['jenis_sumber'].isin(['kb', 'layanan']).to_numpy()
    corpus = chunks[approved].reset_index(drop=True)
    cases = load_cases(corpus)
    if not cases:
        write_section('retrieval', f'## Retrieval terkendali (BR-04)\n\n**Menunggu kasus.** Dokumen hal. 53 hanya memberi '
                      f'hasil, bukan teks 8 kasusnya. Tim mengisi `ai/scripts/{CASES.name}` lalu menjalankan ulang bagian ini.')
        return
    title_to_source = dict(zip(corpus['judul'], corpus['sumber']))
    for c in cases:
        c['sumber_benar'] = [title_to_source.get(w, w) for w in c['sumber_benar']]
    sources = corpus['sumber'].to_numpy()
    questions = [str(privacy.mask_text(c['pertanyaan'])) for c in cases]
    models = {'MiniLM': (minilm(questions) @ minilm(corpus['teks'].tolist()).T),
              'e5': (search.embed(questions, 'query') @ vectors[approved].T)}
    rows, details = [], []
    for name, scores in models.items():
        ranks = [source_ranks(scores[i], sources, c['sumber_benar']) for i, c in enumerate(cases)]
        rr = [1 / r if r else 0.0 for r in ranks]
        rows.append([name, f(np.mean([r == 1 for r in ranks])), f(np.mean([bool(r) and r <= 3 for r in ranks])), num(float(np.mean(rr)), 4)])
        details.append([name] + [str(r or '–') for r in ranks])
    note = '' if len(cases) == 8 else f' **Berkas berisi {len(cases)} kasus, bukan 8.**'
    write_section('retrieval', '\n'.join([
        '## Retrieval terkendali (BR-04)', '',
        f'{len(cases)} kasus real dari KB HaloSIS existing, pertanyaan disusun tim (bukan kasus PoC asli), dari `ai/scripts/{CASES.name}`.{note} Korpus: {num(corpus["sumber"].nunique())} sumber KB terbit + '
        'katalog layanan pada indeks aktif, bukan korpus Zammad PoC. Acuan dokumen: Top-1 100%, Top-3 100%, MRR 1,0000, '
        'dan dokumen menegaskan angka itu hanya berlaku pada PoC terkendali.', '',
        table(['Model', 'Top-1', 'Top-3', 'MRR'], rows), '',
        'Peringkat sumber benar per kasus:', '',
        table(['Model'] + [f'K{i}' for i in range(1, len(cases) + 1)], details),
    ]))


# --- Chat -----------------------------------------------------------------------------------------------------------

def reachable(base: str) -> bool:
    try:
        with urllib.request.urlopen(f'{base.rstrip("/")}/models', timeout=5):  # noqa: S310 (URL dari konfigurasi admin)
            return True
    except OSError:
        return False


def support_ratio(answer: str, sources: list[str], chunks: pd.DataFrame) -> float | None:
    """Porsi kata jawaban (≥ 4 huruf) yang ada di sumber yang dikutip; indikator kasar, bukan penilaian grounding."""
    words = set(re.findall(r'[a-z0-9]{4,}', answer.split('\n\nSumber:')[0].lower()))
    context = set(re.findall(r'[a-z0-9]{4,}', ' '.join(chunks.loc[chunks['sumber'].isin(sources), 'teks']).lower()))
    return len(words & context) / len(words) if words else None


def run_chat(sample: int | None) -> None:
    sys.path[:0] = [str(ROOT / 'ai'), str(ROOT / 'ai/service')]
    from fastapi.testclient import TestClient
    import service.app as service  # impor memuat dependensi layanan, jadi hanya saat bagian ini dipakai
    service.record_latency = lambda *_, **__: None  # uji ini tidak boleh masuk ke ai/logs/latency.jsonl

    base = os.environ.get('LLM_BASE_URL') or OLLAMA_URL
    model = os.environ.get('LLM_MODEL') or OLLAMA_MODEL
    if not reachable(base):
        raise SystemExit(f'LLM tidak terjangkau di {base}: jalankan Ollama lalu ulangi (--bagian chat).')
    questions = [(q, True) for q in ANSWERABLE] + [(q, False) for q in UNKNOWN]
    if sample:
        questions = [questions[0], questions[-1]]
    chunks = search.load_index()[0]
    rows, excerpts, failed = [], [], 0
    with TestClient(service.app) as client:
        for label, provider in (('Ekstraktif', 'none'), (f'Qwen grounded ({model})', 'openai')):
            os.environ.update({'LLM_PROVIDER': provider, 'LLM_BASE_URL': base, 'LLM_MODEL': model})
            for n, (question, answerable) in enumerate(questions, 1):
                start = time.perf_counter()
                response = client.post('/chat', json={'pertanyaan': question, 'riwayat': []}).json()
                seconds = time.perf_counter() - start
                sources = [s['sumber'] for s in response['sumber']]
                correct = response['ditemukan'] == answerable
                if provider == 'openai' and response['mode'] == 'ekstraktif':
                    correct = False  # LLM gagal lalu jatuh ke ekstraktif: bukan hasil Qwen
                cited = bool(sources) if response['ditemukan'] else None
                failed += not correct
                ratio = support_ratio(response['jawaban'], sources, chunks) if response['ditemukan'] else None
                rows.append([label, f'P{n}', 'jawab' if answerable else 'tolak', response['mode'],
                             'ya' if correct else '**tidak**', num(response['sumber'][0]['skor'], 4) if sources else '–',
                             {True: 'ya', False: 'tidak', None: '–'}[cited], f(ratio, 0) if ratio is not None else '–',
                             num(seconds, 1)])
                if response['ditemukan']:
                    text = str(privacy.mask_text(response['jawaban'].split('\n\nSumber:')[0]))
                    excerpts.append(f'- {label}, P{n}: {" ".join(text.split())[:200]}')
    write_section('chat', '\n'.join([
        '## Ekstraktif vs Qwen grounded (BR-06)', '',
        'Lewat `/chat` nyata, sumber hanya KB terbit + katalog layanan. Pertanyaan rekaan; P1 dari dokumen hal. 55.', '',
        '\n'.join(f'- P{n}: {q}' for n, (q, _) in enumerate(questions, 1)), '',
        table(['Mode uji', 'No', 'Harapan', 'Mode /chat', 'Sesuai', 'Skor', 'Ada sumber', 'Kata dari sumber', 'Detik'], rows), '',
        f'Tidak sesuai harapan: {failed} dari {len(rows)}. Kolom *Kata dari sumber* indikator kasar; menilai halusinasi '
        'tetap perlu pembacaan manusia atas cuplikan berikut. Similarity PoC 0,8592 (MiniLM) tidak sebanding dengan skor e5.', '',
        'Cuplikan jawaban (dari sumber tersetujui, tersamar, maks. 200 karakter):', '', '\n'.join(excerpts) or '-',
    ]))


# --- Lembar penilaian relevansi -------------------------------------------------------------------------------------

def excerpt(value: object) -> str:
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', ' ', str(privacy.mask_text(clean(value))))
    text = re.sub(r'\d{9,}', '[ANGKA]', text)  # NIP lama/nomor HP tanpa kata kunci lolos dari mask_text
    return ' '.join(text.split())[:EXCERPT]


def pick_queries(count: int) -> pd.DataFrame:
    """Satu tiket selesai Jul–Ags dari tiap tim terbesar (acak rs42), agar kueri tidak menumpuk di satu tim."""
    qa = pd.read_parquet(QA, columns=['ticket_number', 'tim', 'tanggal', 'masalah'])
    qa = qa[(pd.to_datetime(qa['tanggal'], errors='coerce') >= QUERY_START) & (qa['masalah'].fillna('').str.len() >= 20)]
    shuffled = qa.sample(frac=1, random_state=SEED)
    shuffled['urut'] = shuffled.groupby('tim', sort=False).cumcount()
    shuffled['besar'] = shuffled.groupby('tim', sort=False)['tim'].transform('size')
    return shuffled.sort_values(['urut', 'besar'], ascending=[True, False], kind='stable').head(count)


def run_relevance(sample: int | None) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.worksheet.datavalidation import DataValidation

    chunks = search.load_index()[0]
    members = {}
    if 'tiket' in chunks:
        known = chunks[chunks['tiket'].notna()].drop_duplicates('sumber')
        members = {s: set(str(t).split(',')) for s, t in zip(known['sumber'], known['tiket'])}
    queries = pick_queries(max(sample // 10, 2) if sample else RELEVANCE_QUERIES)
    book = Workbook()
    sheet = book.active
    sheet.title = 'Penilaian'
    headers = ['kueri', 'teks_kueri', 'peringkat', 'sumber', 'jenis_sumber', 'skor', 'hasil', 'nilai_0_2', 'catatan']
    sheet.append(headers)
    for n, row in enumerate(queries.itertuples(), 1):
        text = excerpt(row.masalah)
        hits = search.cari(text, k=RELEVANCE_RESULTS + 15)
        own = str(row.ticket_number)
        hits = [h for h in hits if h['sumber'] != own and own not in members.get(h['sumber'], ())][:RELEVANCE_RESULTS]
        for rank, hit in enumerate(hits, 1):
            sheet.append([f'Q{n:02d}', text if rank == 1 else None, rank, hit['sumber'], hit['jenis_sumber'], hit['skor'],
                          excerpt(hit['potongan']), None, None])
    for line in sheet.iter_rows(min_row=2):
        for cell in line:
            if isinstance(cell.value, str):
                cell.data_type = 's'  # teks berawalan "=" tetap teks, bukan rumus
                cell.alignment = Alignment(wrap_text=True, vertical='top')
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    for column, width in zip('ABCDEFGHI', (7, 50, 9, 14, 12, 8, 70, 10, 24)):
        sheet.column_dimensions[column].width = width
    sheet.freeze_panes = 'A2'
    rule = DataValidation(type='whole', operator='between', formula1='0', formula2='2', allow_blank=True,
                          showErrorMessage=True, error='Isi 0, 1, atau 2')
    sheet.add_data_validation(rule)
    rule.add(f'H2:H{max(sheet.max_row, 2)}')
    guide = book.create_sheet('Petunjuk')
    for line in (('Nilai', 'Arti'), (0, 'Tidak relevan: tidak membantu menyelesaikan masalah kueri'),
                 (1, 'Sebagian relevan: topik sama, tetapi solusi tidak langsung menjawab'),
                 (2, 'Relevan: solusi dapat dipakai langsung untuk masalah kueri'),
                 ('Catatan', 'Teks sudah disamarkan otomatis. Bila masih terlihat data pribadi, tandai di kolom catatan.')):
        guide.append(line)
    guide.column_dimensions['B'].width = 80
    target = OUT / 'penilaian_relevansi.xlsx'
    book.save(target)
    print(f'[relevansi] {len(queries)} kueri, {sheet.max_row - 1} baris → {target}')


def main() -> None:
    global OUT
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--bagian', default='semua', choices=['triase', 'pola', 'retrieval', 'chat', 'relevansi', 'semua'])
    parser.add_argument('--sampel', type=int, help='uji cepat pada N baris; wajib bersama --keluar')
    parser.add_argument('--keluar', type=Path, help='folder keluaran (bawaan reports/)')
    args = parser.parse_args()
    if args.sampel and not args.keluar:
        parser.error('--sampel wajib bersama --keluar agar laporan asli tidak tertimpa angka sampel')
    OUT = args.keluar or OUT
    OUT.mkdir(parents=True, exist_ok=True)
    parts = {'triase': run_triage, 'pola': run_pattern, 'retrieval': run_retrieval, 'relevansi': run_relevance, 'chat': run_chat}
    for name, run in parts.items():
        if args.bagian in (name, 'semua'):
            start = time.perf_counter()
            run(args.sampel)
            print(f'[{name}] selesai {time.perf_counter() - start:.1f} dtk')


if __name__ == '__main__':
    main()
