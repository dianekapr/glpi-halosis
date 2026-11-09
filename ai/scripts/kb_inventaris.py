"""Inventaris artikel KB lewat REST API GLPI (hanya baca): id, judul, kategori, is_faq, target, terlihat oleh budi di FAQ,
masuk indeks /chat, masuk indeks /cari. Hanya metadata artikel dicetak (bukan isi). Tanpa koneksi DB.

  .venv/bin/python ai/scripts/kb_inventaris.py logs/kb_inventaris_sebelum.md
Environment: GLPI_API_URL (bawaan http://localhost:8080), GLPI_API_USER/GLPI_API_PASSWORD (bawaan glpi/glpi),
PEGAWAI_USER/PEGAWAI_PASSWORD (bawaan budi/halosis).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_index as bi  # noqa: E402

BASE = (os.environ.get('GLPI_API_URL') or 'http://localhost:8080').rstrip('/') + '/apirest.php'


def login(user: str, password: str) -> requests.Session:
    s = requests.Session()
    r = bi._check(s.get(f'{BASE}/initSession', auth=(user, password), timeout=bi.TIMEOUT), f'login {user}')
    s.headers['Session-Token'] = r.json()['session_token']
    return s


def budi_visible() -> dict:
    """Hasil scripts/budi_faq.js (Playwright, UI sebagai budi): id artikel di pohon Tanya Jawab & id yang bisa dibuka."""
    import json
    import subprocess
    out = subprocess.run(['node', str(Path(__file__).resolve().parents[2] / 'tests/e2e/budi_faq.js')], capture_output=True, env={**os.environ, 'KB_IDS': ','.join(map(str, range(1, 80)))},
                         text=True, check=True).stdout
    data = json.loads(out)
    return {'faq': set(data['faq']), 'buka': set(data['buka'])}


def rows(chat_rule) -> list[dict]:
    admin = login(os.environ.get('GLPI_API_USER') or 'glpi', os.environ.get('GLPI_API_PASSWORD') or 'glpi')
    visible = budi_visible()
    out = []
    for a in bi.fetch_articles(admin, BASE):
        n_targets = {t: len(admin.get(f'{BASE}/KnowbaseItem/{a["id"]}/{t}', timeout=30).json()) for t in bi.KB_TARGETS}
        detail = admin.get(f'{BASE}/KnowbaseItem/{a["id"]}', timeout=30).json()
        cat = f'induk KB-{",".join(map(str, detail.get("_parents") or [])) or "-"}; kat.layanan {detail.get("forms_categories_id", 0)}'
        total = sum(n_targets.values())
        faq = bool(a.get('is_faq'))
        budi_open = int(a['id']) in visible['buka']
        published = faq or total > 0
        out.append({'id': a['id'], 'judul': a['name'], 'kategori': cat or '-', 'is_faq': int(faq),
                    'target': ','.join(f'{k.split("_")[0][:3]}={v}' for k, v in n_targets.items() if v) or '-',
                    'budi_faq': 'ya' if int(a['id']) in visible['faq'] else 'tidak', 'budi_buka': 'ya' if budi_open else 'tidak',
                    'chat': 'ya' if chat_rule(faq, total) else 'tidak', 'cari': 'ya' if published else 'tidak'})
    return out


def main() -> None:
    path = Path(sys.argv[1])
    rule = (lambda faq, total: faq and total > 0) if '--aturan-baru' in sys.argv else (lambda faq, total: faq or total > 0)
    data = rows(rule)
    head = '| id | judul | kategori | is_faq | target | budi lihat di FAQ | budi bisa buka | indeks /chat | indeks /cari |'
    lines = [f'# Inventaris KB ({"sesudah" if "--aturan-baru" in sys.argv else "sebelum"} perbaikan)', '',
             f'Artikel: {len(data)}; sumber /chat: {sum(r["chat"] == "ya" for r in data)}; '
             f'sumber /cari (artikel): {sum(r["cari"] == "ya" for r in data)}', '', head, '|' + '---|' * 9]
    lines += [f'| KB-{r["id"]} | {r["judul"]} | {r["kategori"]} | {r["is_faq"]} | {r["target"]} | {r["budi_faq"]} | '
              f'{r["budi_buka"]} | {r["chat"]} | {r["cari"]} |' for r in sorted(data, key=lambda r: r['id'])]
    path.write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines[:3]))


if __name__ == '__main__':
    main()
