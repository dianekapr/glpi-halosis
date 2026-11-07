"""Layanan AI HaloSIS (FastAPI): saran triase + jawaban chatbot dari indeks pencarian.

- POST /triage {judul, deskripsi, jenis, tim?} → {tim, top3, keyakinan, penjelasan, jenis_saran, urgensi_saran, versi_model}
- POST /chat   {pertanyaan, riwayat}     → {ditemukan, jawaban, sumber, mode, pilihan?}
- POST /reindex/layanan {layanan: [{id, nama, deskripsi}]} → katalog layanan masuk indeks (jenis_sumber 'layanan')
- POST /pola   {tiket[], ambang, min_anggota, jendela_menit} → {kelompok: [{ids, judul_wakil, skor_rata}]}
- POST /reindex/artikel {id, judul, isi, aksi} → perbarui potongan satu artikel KB di indeks (UC-09 langkah 7)
- POST /cari   {q, k}                    → artikel KB & tiket historis paling relevan (pencarian semantik agent, FR-03)
- GET  /metrics                          → metrik Prometheus (jumlah permintaan, durasi, ukuran indeks)
- GET  /health                           → status model & indeks

Setiap /chat & /triage mencatat durasi (ms) dan skor ke log JSON Lines terpisah (NFR-12, UC-02 langkah 8):
HALOSIS_LATENCY_LOG (default ai/logs/latency.jsonl). Isinya hanya angka, mode, dan versi model; tanpa teks.

Semua input pengguna disamarkan (privacy.mask_text) sebelum diproses. Jawaban chat dirangkum Claude HANYA
jika ANTHROPIC_API_KEY ada di environment; tanpa key → jawaban ekstraktif (potongan teratas apa adanya).
/chat hanya menjawab dari sumber tersetujui (CHAT_SOURCES: artikel KB terbit + katalog layanan); solusi tiket mentah
hanya untuk /cari (petugas) dan /kandidat.

Jalankan lokal (dari folder induk proyek):
    .venv/bin/uvicorn --app-dir ai service.app:app --port 8000
"""
from __future__ import annotations

import json
import logging
import os
import sys
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import candidates, llm, patterns, privacy, quality, search, triage_model  # noqa: E402

AI_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = Path(os.environ.get('HALOSIS_TRIAGE_MODEL', AI_DIR / 'models/triage.joblib'))
# Opsional (T4): klasifier jenis REQ/INC (ai/scripts/train_jenis.py); tidak ada → /triage tanpa saran jenis
JENIS_PATH = Path(os.environ.get('HALOSIS_JENIS_MODEL', AI_DIR / 'models/jenis.joblib'))
# Opsional: urgensi insiden Medium/Low (ai/scripts/train_urgensi.py); dipakai hanya bila lolos gerbang kualitas
URGENSI_PATH = Path(os.environ.get('HALOSIS_URGENSI_MODEL', AI_DIR / 'models/urgensi.joblib'))
# Skor kosinus E5 di bawah ambang ini → "belum menemukan jawaban" (lihat ai/README.md, AI-4)
CHAT_MIN_SCORE = float(os.environ.get('HALOSIS_CHAT_MIN_SCORE', '0.83'))
# Keyakinan sedang (TO-BE hal. 100): skor di antara ambang ini dan CHAT_MIN_SCORE → tidak menjawab, hanya
# menawarkan judul artikel KB sebagai pilihan "Maksud Anda…?" (mode 'pilihan')
CHAT_SUGGEST_MIN_SCORE = float(os.environ.get('HALOSIS_CHAT_SUGGEST_MIN_SCORE', '0.78'))
CHAT_TOP_K = 3
# Sumber tersetujui chatbot pegawai: solusi tiket mentah belum dikurasi, jadi tidak pernah dijawabkan ke pegawai
CHAT_SOURCES = ('kb', 'layanan')
# Artikel KB pilihan dicari di sekian hasil teratas: tiket historis jauh lebih banyak dan sering memenuhi 3 teratas
CHAT_CHOICE_POOL = 20
NOT_FOUND = ('Maaf, saya belum menemukan jawaban untuk pertanyaan ini. Coba kata lain, atau buat laporan '
             'agar petugas membantu Anda.')

LATENCY_LOG = Path(os.environ.get('HALOSIS_LATENCY_LOG', AI_DIR / 'logs/latency.jsonl'))

log = logging.getLogger('halosis-ai')
state: dict = {}


def ms_since(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 1)


def record_latency(endpoint: str, **fields) -> None:
    """Satu baris JSON per permintaan: angka & label saja (tanpa pertanyaan, jawaban, atau judul)."""
    entry = {'waktu': datetime.now(timezone.utc).isoformat(timespec='seconds'), 'endpoint': endpoint, **fields}
    try:
        LATENCY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with LATENCY_LOG.open('a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
    except OSError as e:  # pencatatan tidak boleh menggagalkan permintaan
        log.warning('Log latensi gagal ditulis: %s', type(e).__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Muat sekali saat start; kegagalan dicatat & dilaporkan /health (layanan tetap hidup)
    try:
        state['triage'] = joblib.load(MODEL_PATH)
    except Exception as e:  # noqa: BLE001
        log.error('Model triase gagal dimuat: %s', e)
    for key, path in (('jenis', JENIS_PATH), ('urgensi', URGENSI_PATH)):
        if path.exists():
            try:
                state[key] = joblib.load(path)
            except Exception as e:  # noqa: BLE001
                log.error('Model %s gagal dimuat (saran dilewati): %s', key, e)
    # Metrik gerbang kualitas per model: berkas pendamping *.metrics.json atau metrik di artefak (T32)
    state['metrics'] = {key: quality.load_metrics(path, state[name]) for key, name, path in (
        ('triase', 'triage', MODEL_PATH), ('jenis', 'jenis', JENIS_PATH), ('urgensi', 'urgensi', URGENSI_PATH),
    ) if state.get(name) is not None}
    try:
        _, vectors = search.load_index()
        if search.provider() == 'local':
            search.encoder()
        state['corpus_mean'] = vectors.mean(axis=0)  # pemusatan vektor untuk deteksi pola
        state['search'] = True
    except Exception as e:  # noqa: BLE001
        log.error('Indeks pencarian gagal dimuat: %s', e)
    yield


app = FastAPI(title='HaloSIS AI', version='1.0.0', lifespan=lifespan)

# Metrik Prometheus (NFR-09). Label hanya pola rute & kode status, tidak pernah teks pengguna.
REQUESTS = Counter('halosis_ai_requests_total', 'Jumlah permintaan per endpoint & status', ['endpoint', 'status'])
DURATION = Histogram('halosis_ai_request_duration_seconds', 'Durasi permintaan per endpoint', ['endpoint'],
                     buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10))
INDEX_CHUNKS = Gauge('halosis_ai_index_chunks', 'Jumlah potongan di indeks pencarian')
TIMED = {'/chat', '/triage', '/pola', '/reindex/artikel', '/cari'}

# T26 (2.1.5): batas permintaan sederhana per klien (IP) per menit, jendela geser di memori satu proses.
# 0 = mati. Bawaan 1200/menit (20/dtk) di atas puncak uji Stress (±12/dtk dari satu klien GLPI).
RATE_LIMIT = int(os.environ.get('HALOSIS_RATE_LIMIT_PER_MIN', '1200'))
RATE_EXEMPT = {'/health', '/metrics'}
_hits: dict[str, deque] = defaultdict(deque)
_hits_lock = threading.Lock()


def rate_limited(client: str, now: float) -> int:
    """Detik tunggu bila klien melewati batas dalam 60 detik terakhir; 0 bila boleh lanjut."""
    with _hits_lock:
        hits = _hits[client]
        while hits and now - hits[0] >= 60:
            hits.popleft()
        if len(hits) >= RATE_LIMIT:
            return max(1, int(60 - (now - hits[0])) + 1)
        hits.append(now)
        return 0


@app.middleware('http')
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        if RATE_LIMIT > 0 and request.url.path not in RATE_EXEMPT:
            wait = rate_limited(request.client.host if request.client else '-', time.monotonic())
            if wait:
                status = 429
                return Response('{"detail":"Terlalu banyak permintaan"}', status_code=429,
                                media_type='application/json', headers={'Retry-After': str(wait)})
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = request.scope.get('route')
        endpoint = getattr(route, 'path', 'lainnya')  # pola rute terdaftar; URL tak dikenal → "lainnya"
        if endpoint != '/metrics':
            REQUESTS.labels(endpoint, str(status)).inc()
            if endpoint in TIMED:
                DURATION.labels(endpoint).observe(time.perf_counter() - start)


@app.get('/metrics')
def metrics() -> Response:
    if state.get('search'):
        try:
            INDEX_CHUNKS.set(len(search.load_index()[0]))
        except (OSError, ValueError):  # indeks tak terbaca: metrik lain tetap dilaporkan
            pass
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class TriageRequest(BaseModel):
    judul: str = Field(max_length=500)
    deskripsi: str = Field(default='', max_length=20000)
    jenis: str = Field(default='INC', description='INC (insiden) atau REQ (permintaan)')
    tim: str = Field(default='', max_length=255, description='Tim tiket bila sudah ada; kosong → tim saran triase')
    ambang: float | None = Field(default=None, ge=0, le=1, description='Ambang triase aktif Pengaturan AI (gerbang)')


class GateRequest(BaseModel):
    """Nilai aktif Pengaturan AI yang dinilai gerbang."""
    ambang_triase: float = Field(ge=0, le=1)
    ambang: float = Field(default=patterns.DEFAULT_THRESHOLD, ge=0, le=1)
    min_anggota: int = Field(default=patterns.DEFAULT_MIN_MEMBERS, ge=2)
    jendela_menit: int = Field(default=patterns.DEFAULT_WINDOW_MINUTES, ge=1)
    metode: Literal['rata', 'dbscan'] = 'rata'
    eps: float = Field(default=patterns.DEFAULT_EPS, gt=0, le=2)
    min_sampel: int | None = Field(default=None, ge=2)


class ChatTurn(BaseModel):
    peran: str = Field(description='pengguna atau asisten')
    teks: str = Field(max_length=4000)


class PatternTicket(BaseModel):
    id: int
    judul: str = Field(max_length=500)
    deskripsi: str = Field(default='', max_length=20000)
    waktu: str = Field(default='', description='Waktu tiket dibuat (ISO / "Y-m-d H:i:s")')


class PatternRequest(BaseModel):
    tiket: list[PatternTicket] = Field(max_length=2000)
    ambang: float = Field(default=patterns.DEFAULT_THRESHOLD, ge=0, le=1)
    min_anggota: int = Field(default=patterns.DEFAULT_MIN_MEMBERS, ge=2)
    jendela_menit: int = Field(default=patterns.DEFAULT_WINDOW_MINUTES, ge=1)
    metode: Literal['rata', 'dbscan'] = Field(default='rata', description='rata = rakus rata-rata kemiripan (bawaan)')
    eps: float = Field(default=patterns.DEFAULT_EPS, gt=0, le=2, description='DBSCAN: jarak kosinus maksimal')
    min_sampel: int | None = Field(default=None, ge=2, description='DBSCAN: min_samples (bawaan = min_anggota)')


class ServiceItem(BaseModel):
    id: str = Field(pattern=r'^[CF]\d{1,9}$', description='C<id> kategori layanan atau F<id> form katalog GLPI')
    nama: str = Field(max_length=255)
    deskripsi: str = Field(default='', max_length=5000)


class ServiceCatalogReindexRequest(BaseModel):
    layanan: list[ServiceItem] = Field(max_length=500)


class ArticleReindexRequest(BaseModel):
    id: int = Field(gt=0)
    judul: str = Field(default='', max_length=500)
    isi: str = Field(default='', max_length=200000, description='Isi artikel (HTML GLPI)')
    aksi: Literal['simpan', 'hapus']


class SearchRequest(BaseModel):
    q: str = Field(min_length=1, max_length=2000)
    k: int = Field(default=10, ge=1, le=50)


class ChatRequest(BaseModel):
    pertanyaan: str = Field(min_length=1, max_length=2000)
    riwayat: list[ChatTurn] = Field(default_factory=list, max_length=20)


def normalize_type(jenis: str) -> str:
    value = jenis.strip().lower()
    return 'REQ' if value.startswith(('req', 'perm', 'dem')) or value == '2' else 'INC'


def quality_gate(kind: str, threshold: float | None = None) -> dict:
    """Status gerbang kualitas satu model (syarat tata_kelola_ai.md); model tidak dimuat → tidak lolos.
    threshold: ambang triase aktif Pengaturan AI (0–1)."""
    artifact = state.get('triage' if kind == 'triase' else kind)
    if artifact is None:
        return {'lolos': False, 'alasan': [f'model {kind} tidak tersedia'], 'syarat': {}}
    metrics = state.get('metrics', {}).get(kind) or quality.load_metrics(Path('/nonexistent'), artifact)
    return quality.check(kind, metrics, threshold) if kind == 'triase' else quality.check(kind, metrics)


def pattern_gate(req: GateRequest) -> dict:
    """Gerbang pola pada parameter aktif (peringatan saja); set uji dari ai/scripts/gerbang_pola.py."""
    path = search.INDEX_DIR / 'pola_uji.npz'
    if not path.exists():
        return {'lolos': False, 'memblokir': False, 'syarat': {}, 'alasan': ['set uji pola belum dibangun (gerbang_pola.py)']}
    if 'pola_uji' not in state:
        with np.load(path) as data:
            state['pola_uji'] = (data['vektor'], data['waktu'].tolist(), data['tim'])
    vectors, times, teams = state['pola_uji']
    parameter = {'metode': req.metode, 'ambang': req.ambang, 'eps': req.eps, 'min_sampel': req.min_sampel,
                 'min_anggota': req.min_anggota, 'jendela_menit': req.jendela_menit}
    result = patterns.replay(times, patterns.center(vectors, state.get('corpus_mean')), teams, req.metode, req.ambang,
                             req.eps, req.min_sampel, req.min_anggota, req.jendela_menit)
    return quality.check('pola', {**result, 'parameter': parameter})


@app.get('/health')
def health() -> dict:
    model = state.get('triage')
    return {
        'status': 'ok' if model and state.get('search') else 'sebagian',
        'triase': bool(model), 'versi_model': model.version if model else None,
        'kualitas_model': {kind: quality_gate(kind) for kind in ('triase', 'jenis', 'urgensi')
                           if kind == 'triase' or state.get(kind) is not None},
        'pencarian': bool(state.get('search')), 'model_embedding': search.model_name(), 'penyedia_embedding': search.provider(),
        'generasi': llm.provider() if llm.provider() != 'none' else 'ekstraktif', 'model_llm': llm.model_name(),
    }


def suggest_type(title: str, description: str) -> dict | None:
    """Saran jenis REQ/INC + keyakinan (T4); None bila model jenis tidak tersedia."""
    artifact = state.get('jenis')
    if not artifact or not quality_gate('jenis')['lolos']:
        return None
    probs = artifact['pipeline'].predict_proba([triage_model.jenis_text(title, description)])[0]
    best = int(np.argmax(probs))
    return {'jenis': str(artifact['pipeline'].classes_[best]), 'keyakinan': round(float(probs[best]), 4),
            'versi_model': artifact['version']}


def suggest_urgency(title: str, description: str, kind: str, team: str) -> dict | None:
    """Saran urgensi insiden (Medium/Low → skala GLPI) dengan ambang per kelas dari P(Low) (train_urgensi.py).

    Low bila kelas Low lolos gerbang & P(Low) ≥ ambang Low; Medium bila kelas Medium lolos & P(Low) ≤ ambang Medium;
    selain itu None → aturan di plugin. team = tim tiket atau saran triase. High/Critical & REQ tidak dimodelkan.
    """
    artifact = state.get('urgensi')
    passed = (quality_gate('urgensi').get('kelas_lolos') or []) if artifact else []
    if kind != 'INC' or not passed:
        return None  # tidak ada kelas lolos gerbang (skema B): urgensi kembali ke aturan + validasi Operator
    pipeline, thresholds = artifact['pipeline'], artifact.get('ambang') or {}
    probs = pipeline.predict_proba(triage_model.urgency_frame(title, description, team))[0]
    p_low = float(probs[list(pipeline.classes_).index('Low')])
    if 'Low' in passed and p_low >= float(thresholds.get('Low', 2)):
        label, confidence = 'Low', p_low
    elif 'Medium' in passed and p_low <= float(thresholds.get('Medium', -1)):
        label, confidence = 'Medium', 1 - p_low
    else:
        return None
    return {'urgensi': label, 'nilai_glpi': artifact['urgensi_glpi'][label], 'keyakinan': round(confidence, 4),
            'versi_model': artifact['version']}


@app.post('/triage')
def triage(req: TriageRequest) -> dict:
    model = state.get('triage')
    if model is None:
        raise HTTPException(503, 'Model triase belum tersedia')
    start = time.perf_counter()
    result = model.predict(req.judul, req.deskripsi, normalize_type(req.jenis))
    # Inferensi model + pencarian tiket mirip (satu langkah di TriageModel.predict); tanpa generation
    record_latency('triage', inferensi_ms=ms_since(start), generation_ms=None, total_ms=ms_since(start),
                   skor_teratas=round(float(result['keyakinan']), 4), versi_model=result['versi_model'])
    gate = quality_gate('triase', req.ambang)
    return {
        'lolos_uji_kualitas': gate['lolos'],
        'alasan_kualitas': gate['alasan'],
        'jenis_saran': suggest_type(req.judul, req.deskripsi),
        'urgensi_saran': suggest_urgency(req.judul, req.deskripsi, normalize_type(req.jenis), req.tim or result['tim']),
        'tim': result['tim'],
        'top3': result['top3'],
        'keyakinan': result['keyakinan'],
        'perlu_penilaian_manual': result['perlu_penilaian_manual'],
        'penjelasan': {
            'ringkas': f'Model memilih tim ini dengan keyakinan {round(result["keyakinan"] * 100)}% '
                       'berdasarkan judul, deskripsi, dan jenis tiket.',
            'tiket_mirip': result['tiket_mirip'],
        },
        'versi_model': result['versi_model'],
    }


def extractive(hit: dict) -> str:
    text = hit['potongan']
    title = hit['judul'].strip().split('\n', 1)[0][:80].rstrip()
    if hit['jenis_sumber'] == 'layanan':
        return f'Permintaan ini bisa diajukan lewat layanan "{title}" di katalog layanan.\n{text}'
    return f'Berdasarkan artikel "{title}":\n{text}'


@app.post('/chat')
def chat(req: ChatRequest) -> dict:
    if not state.get('search'):
        raise HTTPException(503, 'Indeks pencarian belum tersedia')
    start = time.perf_counter()
    question = str(privacy.mask_text(req.pertanyaan))
    found = search.cari(question, k=CHAT_CHOICE_POOL, jenis=CHAT_SOURCES)
    retrieval_ms = ms_since(start)
    top_score = round(float(found[0]['skor']), 4) if found else None
    hits = [h for h in found[:CHAT_TOP_K] if h['skor'] >= CHAT_MIN_SCORE]
    if not hits:
        choices = list({h['sumber']: {'sumber': h['sumber'], 'judul': h['judul'], 'skor': h['skor']}
                        for h in found if h['jenis_sumber'] == 'kb' and h['skor'] >= CHAT_SUGGEST_MIN_SCORE}.values())
        mode = 'pilihan' if choices else 'tidak-ditemukan'
        record_latency('chat', retrieval_ms=retrieval_ms, generation_ms=None, total_ms=ms_since(start),
                       skor_teratas=top_score, mode=mode)
        return {'ditemukan': False, 'jawaban': NOT_FOUND, 'sumber': [], 'mode': mode, 'pilihan': choices[:3]}

    generation_start = time.perf_counter()
    answer = llm.generate(question, req.riwayat, hits)
    if answer == llm.NO_ANSWER:  # LLM menilai konteks tidak memuat jawaban → tolak, jangan mengarang
        record_latency('chat', retrieval_ms=retrieval_ms, generation_ms=ms_since(generation_start), total_ms=ms_since(start),
                       skor_teratas=top_score, mode='tidak-ditemukan')
        return {'ditemukan': False, 'jawaban': NOT_FOUND, 'sumber': [], 'mode': 'tidak-ditemukan', 'pilihan': []}
    mode = llm.provider() if answer else 'ekstraktif'
    if answer is None:
        hits = hits[:1]  # ekstraktif: hanya solusi teratas
        answer = extractive(hits[0])
    record_latency('chat', retrieval_ms=retrieval_ms, generation_ms=ms_since(generation_start) if mode != 'ekstraktif' else None,
                   total_ms=ms_since(start), skor_teratas=top_score, mode=mode)
    sources = [{'sumber': h['sumber'], 'jenis_sumber': h['jenis_sumber'], 'judul': h['judul'], 'skor': h['skor']}
               for h in hits]
    return {'ditemukan': True, 'jawaban': answer, 'sumber': sources, 'mode': mode}


@app.post('/pola')
def pola(req: PatternRequest) -> dict:
    """Kelompokkan tiket baru yang maknanya mirip dalam jendela waktu (deteksi pola insiden semantik)."""
    if not state.get('search'):
        raise HTTPException(503, 'Model embedding belum tersedia')
    if len(req.tiket) < req.min_anggota:
        return {'kelompok': [], 'metode': 'semantik'}
    start = time.perf_counter()
    # Judul + awal deskripsi, disamarkan dulu (data minimization)
    texts = [str(privacy.mask_text(f'{t.judul}. {t.deskripsi[:300]}')) for t in req.tiket]
    vectors = patterns.center(search.embed(texts, 'query'), state.get('corpus_mean'))
    tickets = [{'id': t.id, 'judul': str(privacy.mask_text(t.judul)), 'waktu': t.waktu} for t in req.tiket]
    if req.metode == 'dbscan':
        groups = patterns.group_dbscan(tickets, vectors, req.eps, req.min_sampel or req.min_anggota, req.min_anggota,
                                       req.jendela_menit)
    else:
        groups = patterns.group(tickets, vectors, req.ambang, req.min_anggota, req.jendela_menit)
    record_latency('pola', total_ms=ms_since(start), tiket=len(tickets), kelompok=len(groups), metode=req.metode)
    return {'kelompok': groups, 'metode': 'semantik' if req.metode == 'rata' else 'dbscan'}


@app.post('/gerbang')
def gates(req: GateRequest) -> dict:
    """Status gerbang pada nilai aktif Pengaturan AI; pola = peringatan saja (tata_kelola_ai.md §2)."""
    if not state.get('search'):
        raise HTTPException(503, 'Layanan AI belum siap')
    return {'triase': quality_gate('triase', req.ambang_triase), 'pola': pattern_gate(req),
            'urgensi': quality_gate('urgensi')}


@app.post('/reindex/artikel')
def reindex_article(req: ArticleReindexRequest) -> dict:
    """Artikel KB terbit → ganti potongannya; dihapus/tidak terbit → hapus potongannya. Tiket historis tetap."""
    if not state.get('search'):
        raise HTTPException(503, 'Indeks pencarian belum tersedia')
    start = time.perf_counter()
    try:
        count = search.update_article(req.id, req.judul, req.isi, remove=req.aksi == 'hapus')
    except OSError as e:
        log.error('Indeks gagal ditulis: %s', type(e).__name__)
        raise HTTPException(500, 'Indeks gagal ditulis; indeks lama tetap dipakai') from e
    _, vectors = search.load_index()
    state['corpus_mean'] = vectors.mean(axis=0)
    record_latency('reindex', total_ms=ms_since(start), aksi=req.aksi, potongan=count)
    return {'ok': True, 'aksi': req.aksi, 'potongan': count}


@app.post('/reindex/layanan')
def reindex_services(req: ServiceCatalogReindexRequest) -> dict:
    """Katalog layanan (kategori & form GLPI) → potongan 'layanan', agar chatbot bisa mengarahkan ke layanan (BR-03)."""
    if not state.get('search'):
        raise HTTPException(503, 'Indeks pencarian belum tersedia')
    start = time.perf_counter()
    try:
        count = search.replace_services([item.model_dump() for item in req.layanan])
    except OSError as e:
        log.error('Indeks gagal ditulis: %s', type(e).__name__)
        raise HTTPException(500, 'Indeks gagal ditulis; indeks lama tetap dipakai') from e
    _, vectors = search.load_index()
    state['corpus_mean'] = vectors.mean(axis=0)
    record_latency('reindex', total_ms=ms_since(start), aksi='layanan', potongan=count)
    return {'ok': True, 'potongan': count}


@app.post('/cari')
def cari(req: SearchRequest) -> dict:
    """Pencarian semantik untuk Operator & Tim Teknis: tanpa ambang, petugas menilai sendiri relevansinya."""
    if not state.get('search'):
        raise HTTPException(503, 'Indeks pencarian belum tersedia')
    start = time.perf_counter()
    hits = search.cari(str(privacy.mask_text(req.q)), k=req.k)
    record_latency('cari', retrieval_ms=ms_since(start), total_ms=ms_since(start),
                   skor_teratas=round(float(hits[0]['skor']), 4) if hits else None, hasil=len(hits))
    return {'hasil': [{'judul': h['judul'], 'potongan': h['potongan'], 'skor': h['skor'], 'sumber': h['sumber'],
                       'jenis_sumber': h['jenis_sumber']} for h in hits]}


@app.get('/kandidat')
def kandidat(min: int = 5, limit: int = 20) -> dict:
    """Solusi yang sering berulang di history tiket, untuk dikurasi Knowledge Manager (UC-09)."""
    if not state.get('search'):
        raise HTTPException(503, 'Indeks pencarian belum tersedia')
    key = (max(2, min), max(1, limit))
    if key not in state.setdefault('kandidat', {}):
        chunks, _ = search.load_index()
        state['kandidat'][key] = candidates.recurring_solutions(chunks, min_size=key[0], limit=key[1])
    return {'kandidat': state['kandidat'][key]}
