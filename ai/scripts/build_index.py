"""AI-4: bangun indeks pencarian dari artikel KB GLPI yang terbit + qa_pairs → ai/index/.

- KB  : diambil dari database GLPI (container `db`) — artikel yang punya target visibilitas
        (entitas/profil/grup/pengguna) dianggap terbit. Jika container mati, KB dilewati dengan peringatan.
- QA  : data/processed/qa_pairs.parquet (sudah disamarkan): "masalah" + "solusi" per tiket selesai.
Semua teks disamarkan ulang sebelum di-embed. Hanya angka yang dicetak.

Pakai (dari folder induk proyek):  .venv/bin/python ai/scripts/build_index.py
"""
from __future__ import annotations

import html
import io
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import privacy  # noqa: E402
from halosis_ai.search import INDEX_DIR, MODEL_NAME, embed  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / 'data/processed/qa_pairs.parquet'
MAX_WORDS = 220  # panjang potongan (kata); artikel KB panjang dipecah

KB_SQL = """
SELECT k.id, k.name, REPLACE(REPLACE(k.answer, '\\t', ' '), '\\n', ' ') AS answer
FROM glpi_knowbaseitems k
WHERE EXISTS (SELECT 1 FROM glpi_entities_knowbaseitems e WHERE e.knowbaseitems_id = k.id)
   OR EXISTS (SELECT 1 FROM glpi_knowbaseitems_profiles p WHERE p.knowbaseitems_id = k.id)
   OR EXISTS (SELECT 1 FROM glpi_groups_knowbaseitems g WHERE g.knowbaseitems_id = k.id)
   OR EXISTS (SELECT 1 FROM glpi_knowbaseitems_users u WHERE u.knowbaseitems_id = k.id)
"""


def strip_html(value: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', html.unescape(html.unescape(value or '')))
    return re.sub(r'\s+', ' ', text).strip()


def chunk(text: str) -> list[str]:
    words = text.split()
    return [' '.join(words[i:i + MAX_WORDS]) for i in range(0, max(len(words), 1), MAX_WORDS)]


def load_kb() -> pd.DataFrame:
    cmd = ['docker', 'compose', 'exec', '-T', 'db', 'sh', '-c',
           'mysql --default-character-set=utf8mb4 -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE" --batch -e "$0"',
           KB_SQL]
    try:
        out = subprocess.run(cmd, cwd=ROOT, capture_output=True, check=True, timeout=60).stdout\
            .decode('utf-8', errors='replace')
    except (subprocess.SubprocessError, FileNotFoundError):
        print('PERINGATAN: database GLPI tidak bisa dihubungi, artikel KB dilewati (jalankan docker compose up -d).')
        return pd.DataFrame(columns=['sumber', 'jenis_sumber', 'judul', 'teks'])
    kb = pd.read_csv(io.StringIO(out), sep='\t', quoting=3, dtype=str).fillna('')
    rows = []
    for _, r in kb.iterrows():
        title = str(privacy.mask_text(r['name']))
        for part in chunk(str(privacy.mask_text(strip_html(r['answer'])))):
            rows.append({'sumber': f'KB-{r["id"]}', 'jenis_sumber': 'kb', 'judul': title, 'teks': f'{title}. {part}'})
    return pd.DataFrame(rows)


def load_qa() -> pd.DataFrame:
    qa = pd.read_parquet(QA)
    qa = qa[qa['solusi'].fillna('').str.len() > 0]
    return pd.DataFrame({
        'sumber': qa['ticket_number'].astype(str),
        'jenis_sumber': 'tiket',
        'judul': [str(privacy.mask_text(str(m)))[:120] for m in qa['masalah']],
        'teks': [f'Masalah: {privacy.mask_text(str(m))} Solusi: {privacy.mask_text(str(s))}'
                 for m, s in zip(qa['masalah'], qa['solusi'])],
    })


def main() -> None:
    kb, qa = load_kb(), load_qa()
    chunks = pd.concat([kb, qa], ignore_index=True)
    leaks = sum(len(p.findall(' '.join(chunks['teks']))) for p in
                (privacy._EMAIL, privacy._NIP, privacy._NIK, privacy._PHONE))
    if leaks:
        raise SystemExit(f'Potongan memuat {leaks} pola data pribadi, indeks tidak ditulis.')

    vectors = embed(chunks['teks'].tolist(), 'passage')
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    chunks.to_parquet(INDEX_DIR / 'chunks.parquet', index=False)
    np.save(INDEX_DIR / 'vectors.npy', vectors)
    print(f'Model embedding : {MODEL_NAME} (dimensi {vectors.shape[1]})')
    print(f'Potongan KB     : {len(kb)} dari {kb["sumber"].nunique()} artikel')
    print(f'Potongan tiket  : {len(qa)}')
    print(f'Disimpan        : {INDEX_DIR.relative_to(ROOT)}/chunks.parquet, vectors.npy')


if __name__ == '__main__':
    main()
