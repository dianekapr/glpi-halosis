"""build_index.py mengambil KB lewat REST API GLPI; API tidak bisa dipakai → gagal jelas, tanpa fallback (A.2)."""
import importlib.util
import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('build_index', ROOT / 'scripts/build_index.py')
build_index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_index)


class Reply:
    def __init__(self, data=None, status=200, text=''):
        self.data, self.status_code, self.text = data, status, text

    def json(self):
        return self.data


class FakeSession:
    """#1 FAQ tanpa target (terbit, tapi tidak terlihat pegawai); #2 bertarget bukan FAQ (internal); #3 belum terbit;
    #4 FAQ + bertarget = satu-satunya sumber /chat."""
    articles = [{'id': 1, 'name': 'A', 'answer': '&lt;p&gt;satu&lt;/p&gt;', 'is_faq': 1},
                {'id': 2, 'name': 'B', 'answer': 'dua', 'is_faq': 0},
                {'id': 3, 'name': 'C', 'answer': 'tiga', 'is_faq': 0},
                {'id': 4, 'name': 'D', 'answer': 'empat', 'is_faq': 1}]

    def __init__(self):
        self.headers = {}

    def get(self, url, params=None, timeout=None, **_):
        if url.endswith('/initSession'):
            return Reply({'session_token': 't'})
        if url.endswith('/killSession'):
            return Reply({})
        if url.endswith('/KnowbaseItem'):
            return Reply(self.articles)
        return Reply([{'id': 9}] if ('/2/Entity_KnowbaseItem' in url or '/4/Entity_KnowbaseItem' in url) else [])


def test_kb_terbit_dari_api(monkeypatch):
    monkeypatch.setattr(build_index.requests, 'Session', FakeSession)
    kb = build_index.load_kb()
    assert sorted(kb['sumber'].unique()) == ['KB-1', 'KB-2', 'KB-4']
    # sumber /chat = FAQ DAN bertarget; terbit lainnya hanya untuk /cari
    assert dict(kb.drop_duplicates('sumber').set_index('sumber')['jenis_sumber']) == {
        'KB-1': 'kb_internal', 'KB-2': 'kb_internal', 'KB-4': 'kb'}
    assert '<p>' not in kb['teks'].iloc[0]


def test_api_mati_gagal_jelas(monkeypatch):
    def down(*a, **k):
        raise requests.ConnectionError('tolak')
    monkeypatch.setattr(build_index.requests.Session, 'get', down)
    with pytest.raises(SystemExit) as e:
        build_index.load_kb()
    assert 'REST API GLPI' in str(e.value) and e.value.code not in (0, None)


def test_login_ditolak_gagal_jelas(monkeypatch):
    monkeypatch.setattr(build_index.requests.Session, 'get', lambda *a, **k: Reply({}, 401))
    with pytest.raises(SystemExit) as e:
        build_index.load_kb()
    assert 'HTTP 401' in str(e.value)
