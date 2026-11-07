"""Impor artikel KB HaloSIS existing (data/kb_existing.xlsx) ke GLPI lewat REST API sebagai artikel terbit (is_faq=1).

Judul = Permasalahan, isi = Solusi (baris baru → HTML). Judul yang sudah ada dilewati. Hanya angka/judul pendek dicetak.
Pakai:  .venv/bin/python ai/scripts/impor_kb_existing.py [--dry]
Env: GLPI_API_URL (bawaan http://localhost:8080), GLPI_API_USER/GLPI_API_PASSWORD (bawaan glpi/glpi).
"""
from __future__ import annotations

import html
import os
import re
import sys
from pathlib import Path

import openpyxl
import requests

ROOT = Path(__file__).resolve().parents[2]
BASE = (os.environ.get('GLPI_API_URL') or 'http://localhost:8080').rstrip('/') + '/apirest.php'
# id kategori (Glpi\Form\Category): 1 Akun & SSO, 3 Jaringan & VPN, 4 Laptop & perangkat, 5 Email Dinas
CATEGORY_RULES = [(r'email', 5), (r'community', 1), (r'wi-?fi|wan|jaringan|wireless|internet', 3), (r'laptop|monitor|pc', 4)]


def category(title: str) -> int:
    low = title.lower()
    return next((cid for pattern, cid in CATEGORY_RULES if re.search(pattern, low)), 0)


def to_html(text: str) -> str:
    text = html.escape(text.replace('\xa0', ' ').strip())
    paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
    return ''.join('<p>' + p.replace('\n', '<br>') + '</p>' for p in paragraphs)


def main() -> int:
    dry = '--dry' in sys.argv
    rows = [r for r in openpyxl.load_workbook(ROOT / 'data/kb_existing.xlsx').active.iter_rows(min_row=2, values_only=True) if r[0]]
    try:
        s = requests.Session()
        auth = (os.environ.get('GLPI_API_USER') or 'glpi', os.environ.get('GLPI_API_PASSWORD') or 'glpi')
        s.headers['Session-Token'] = s.get(f'{BASE}/initSession', auth=auth, timeout=30).json()['session_token']
        existing = set()
        start = 0
        while True:
            r = s.get(f'{BASE}/KnowbaseItem', params={'range': f'{start}-{start + 199}'}, timeout=30)
            if r.status_code >= 400:
                break
            existing |= {a['name'].strip() for a in r.json()}
            if len(r.json()) < 200:
                break
            start += 200
    except (requests.RequestException, KeyError, ValueError) as exc:
        print(f'GAGAL: REST API GLPI tidak bisa dipakai ({type(exc).__name__})')
        return 1
    made = skipped = 0
    for title, solution in rows:
        title = str(title).strip()
        if title in existing:
            skipped += 1
            print(f'lewati (sudah ada): {title[:50]}')
            continue
        payload = {'input': {'name': title, 'answer': to_html(str(solution or '')), 'is_faq': 1,
                             'forms_categories_id': category(title), 'entities_id': 0, 'is_recursive': 1}}
        if dry:
            print(f'[dry] kategori {payload["input"]["forms_categories_id"]}: {title[:50]}')
            continue
        r = s.post(f'{BASE}/KnowbaseItem', json=payload, timeout=30)
        if r.status_code >= 400:
            print(f'GAGAL buat "{title[:40]}": HTTP {r.status_code}')
            return 1
        made += 1
        print(f'dibuat id={r.json().get("id")} kategori={payload["input"]["forms_categories_id"]}: {title[:50]}')
    print(f'ringkas: dibuat={made} dilewati={skipped} total={len(rows)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
