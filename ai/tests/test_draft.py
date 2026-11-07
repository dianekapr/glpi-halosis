"""Tes draf artikel KB dari kandidat: LLM dimock + fallback ke templat (None)."""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import llm  # noqa: E402
from service import app as service  # noqa: E402

OUT = 'JUDUL: Akun SSO terkunci\nGEJALA:\n- Tidak bisa masuk (istilah awam: "kena blokir")\nLANGKAH:\n1. Reset akun.\n2. Login ulang.'


def test_draf_dari_llm_dengan_sitasi_dan_label(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setattr(llm, '_openai', lambda prompt, system=llm.SYSTEM: OUT)
    d = llm.draft_article('SSO', 'tidak bisa login', 'akun direset', ['T1', 'T2'])
    assert d['judul'] == 'Akun SSO terkunci' and 'kena blokir' in d['gejala'] and d['langkah'].startswith('1.')
    assert d['sumber'] == ['T1', 'T2'] and d['label'] == 'Disusun AI, wajib ditinjau Knowledge Manager'


def test_fallback_provider_none_gagal_atau_format_salah(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'none')
    assert llm.draft_article('a', 'b', 'c', []) is None
    monkeypatch.setenv('LLM_PROVIDER', 'openai')

    def boom(prompt, system=llm.SYSTEM):
        raise TimeoutError
    monkeypatch.setattr(llm, '_openai', boom)
    assert llm.draft_article('a', 'b', 'c', []) is None
    monkeypatch.setattr(llm, '_openai', lambda prompt, system=llm.SYSTEM: 'bebas tanpa format')
    assert llm.draft_article('a', 'b', 'c', []) is None


def test_endpoint_draf_null_saat_llm_none(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'none')
    r = TestClient(service.app).post('/kandidat/draf', json={'judul': 'x', 'masalah': 'm', 'solusi': 's', 'sumber': ['T1']})
    assert r.status_code == 200 and r.json() == {'draf': None}
