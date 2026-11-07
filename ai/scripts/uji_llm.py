"""Uji singkat RAG grounded (B.6): 3 pertanyaan lewat /chat nyata. Pakai: LLM_PROVIDER=openai LLM_BASE_URL=... LLM_MODEL=... .
Hanya jawaban dari artikel KB/layanan tersetujui; jawaban dipotong 300 karakter."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'ai'), str(ROOT / 'ai/service')]
from fastapi.testclient import TestClient  # noqa: E402
from service.app import app  # noqa: E402

QUESTIONS = sys.argv[1:] or ['Bagaimana cara mengajukan permintaan VPN?', 'Bagaimana cara memasang printer jaringan Epson L9999?',
                             'Apa resep nasi goreng yang enak?']
with TestClient(app) as c:
    print('health:', {k: v for k, v in c.get('/health').json().items() if k in ('generasi', 'model_llm', 'model_embedding', 'pencarian')})
    for q in QUESTIONS:
        r = c.post('/chat', json={'pertanyaan': q, 'riwayat': []}).json()
        print(f'\nQ: {q}\n  ditemukan={r["ditemukan"]} mode={r["mode"]} sumber={[s["sumber"] for s in r["sumber"]]}')
        print('  A:', r['jawaban'][:300].replace('\n', ' | '))
