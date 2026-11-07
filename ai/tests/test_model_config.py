"""B.5/B.6: konfigurasi model lewat env, penolakan indeks lama, RAG grounded."""
import json

import numpy as np
import pandas as pd
import pytest

from halosis_ai import llm, search


def _index(tmp_path, dim=4, meta=None):
    pd.DataFrame({'sumber': ['KB-1'], 'jenis_sumber': ['kb'], 'judul': ['t'], 'teks': ['t']}).to_parquet(tmp_path / 'chunks.parquet')
    np.save(tmp_path / 'vectors.npy', np.ones((1, dim), dtype=np.float32))
    if meta:
        (tmp_path / 'meta.json').write_text(json.dumps(meta))


def test_legacy_index_ok_with_default(tmp_path, monkeypatch):
    monkeypatch.delenv('EMBEDDING_PROVIDER', raising=False)
    monkeypatch.delenv('EMBEDDING_MODEL', raising=False)
    _index(tmp_path)
    search.check_compatible(1, np.ones((1, 4)), tmp_path)


def test_index_rejected_when_model_changes(tmp_path, monkeypatch):
    _index(tmp_path, meta={'provider': 'local', 'model': search.LOCAL_MODEL, 'dim': 4})
    monkeypatch.setenv('EMBEDDING_PROVIDER', 'openai')
    monkeypatch.setenv('EMBEDDING_MODEL', 'bge-m3')
    with pytest.raises(search.IndexMismatch, match='bangun ulang indeks'):
        search.check_compatible(1, np.ones((1, 4)), tmp_path)


def test_index_rejected_when_dim_changes(tmp_path, monkeypatch):
    monkeypatch.delenv('EMBEDDING_PROVIDER', raising=False)
    _index(tmp_path, meta={'provider': 'local', 'model': search.LOCAL_MODEL, 'dim': 768})
    with pytest.raises(search.IndexMismatch, match='bangun ulang indeks'):
        search.check_compatible(1, np.ones((1, 4)), tmp_path)


def test_remote_embed_uses_prefix_and_normalizes(monkeypatch):
    seen = {}

    class Resp:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self, *a): return json.dumps({'data': [{'index': 0, 'embedding': [3.0, 4.0]}]}).encode()

    def fake_open(req, timeout):
        seen['body'] = json.loads(req.data)
        seen['url'] = req.full_url
        return Resp()

    monkeypatch.setenv('EMBEDDING_PROVIDER', 'openai')
    monkeypatch.setenv('EMBEDDING_BASE_URL', 'http://x/v1')
    monkeypatch.setenv('EMBEDDING_MODEL', 'm')
    monkeypatch.setattr(search.urllib.request, 'urlopen', fake_open)
    v = search.embed(['halo'], 'query')
    assert seen['url'] == 'http://x/v1/embeddings' and seen['body']['input'] == ['query: halo']
    assert np.allclose(v, [[0.6, 0.8]])


def test_llm_defaults_none(monkeypatch):
    for k in ('LLM_PROVIDER', 'ANTHROPIC_API_KEY'):
        monkeypatch.delenv(k, raising=False)
    assert llm.provider() == 'none' and llm.generate('q', [], [{'sumber': 'KB-1', 'potongan': 'x'}]) is None


def test_llm_empty_context_refused(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    assert llm.generate('q', [], []) is None


def test_llm_cites_sources_and_no_answer(monkeypatch):
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    hits = [{'sumber': 'KB-7', 'potongan': 'x'}]
    monkeypatch.setattr(llm, '_openai', lambda p: 'Lakukan A.')
    assert llm.generate('q', [], hits).endswith('Sumber: KB-7')
    monkeypatch.setattr(llm, '_openai', lambda p: 'TIDAK_ADA')
    assert llm.generate('q', [], hits) == llm.NO_ANSWER
