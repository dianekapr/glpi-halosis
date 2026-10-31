"""AI-4: bangun indeks pencarian dari artikel KB GLPI yang terbit + qa_pairs → ai/index/.

- KB  : diambil dari database GLPI (container `db`) — artikel yang punya target visibilitas
        (entitas/profil/grup/pengguna) dianggap terbit. Jika container mati, KB dilewati dengan peringatan.
- QA  : data/processed/qa_pairs.parquet (sudah disamarkan): "masalah" + "solusi" per tiket selesai; solusi > 220 kata
        dipecah, masalah diulang di tiap potongan (search.ticket_chunks). Penggabungan solusi identik (DEDUP) tersedia
        tetapi mati: Top-1 turun 1,6–2 poin di set uji reports/banding_solusi.md.
- Layanan: potongan katalog layanan (POST /reindex/layanan) di indeks lama dibawa ulang, agar tidak hilang sampai
        GLPI mengirim ulang katalog.
Semua teks disamarkan ulang sebelum di-embed. Hanya angka yang dicetak.

Pakai (dari folder induk proyek):  .venv/bin/python ai/scripts/build_index.py
"""
from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import privacy  # noqa: E402
from halosis_ai.search import INDEX_DIR, MODEL_NAME, chunk, embed, strip_html, ticket_chunks  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / 'data/processed/qa_pairs.parquet'
DEDUP = False  # gerbang reports/banding_solusi.md: dedup lebih buruk dari satu potongan per tiket

KB_SQL = """
SELECT k.id, k.name, REPLACE(REPLACE(k.answer, '\\t', ' '), '\\n', ' ') AS answer
FROM glpi_knowbaseitems k
WHERE EXISTS (SELECT 1 FROM glpi_entities_knowbaseitems e WHERE e.knowbaseitems_id = k.id)
   OR EXISTS (SELECT 1 FROM glpi_knowbaseitems_profiles p WHERE p.knowbaseitems_id = k.id)
   OR EXISTS (SELECT 1 FROM glpi_groups_knowbaseitems g WHERE g.knowbaseitems_id = k.id)
   OR EXISTS (SELECT 1 FROM glpi_knowbaseitems_users u WHERE u.knowbaseitems_id = k.id)
"""


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
    return ticket_chunks(pd.read_parquet(QA), dedup=DEDUP)


def load_services() -> pd.DataFrame:
    """Potongan katalog layanan dari indeks yang sedang dipakai (jenis_sumber 'layanan'), bila ada."""
    try:
        old = pd.read_parquet(INDEX_DIR / 'chunks.parquet')
    except (OSError, ValueError):
        return pd.DataFrame(columns=['sumber', 'jenis_sumber', 'judul', 'teks'])
    return old.loc[old['jenis_sumber'] == 'layanan', ['sumber', 'jenis_sumber', 'judul', 'teks']].reset_index(drop=True)


def main() -> None:
    kb, qa, services = load_kb(), load_qa(), load_services()
    chunks = pd.concat([kb, qa, services], ignore_index=True)
    leaks = sum(len(p.findall(' '.join(chunks['teks']))) for p in
                (privacy._EMAIL, privacy._NIP, privacy._NIP_OLD, privacy._NIK, privacy._PHONE))
    if leaks:
        raise SystemExit(f'Potongan memuat {leaks} pola data pribadi, indeks tidak ditulis.')

    vectors = embed(chunks['teks'].tolist(), 'passage')
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    chunks.to_parquet(INDEX_DIR / 'chunks.parquet', index=False)
    np.save(INDEX_DIR / 'vectors.npy', vectors)
    print(f'Model embedding : {MODEL_NAME} (dimensi {vectors.shape[1]})')
    print(f'Potongan KB     : {len(kb)} dari {kb["sumber"].nunique()} artikel')
    print(f'Potongan tiket  : {len(qa)} dari {int(qa.drop_duplicates("sumber")["jumlah_tiket"].sum())} tiket '
          f'({qa["sumber"].nunique()} sumber, {int((qa.groupby("sumber").size() > 1).sum())} dipecah > 220 kata)')
    print(f'Potongan layanan: {len(services)} (dibawa dari indeks sebelumnya)')
    print(f'Disimpan        : {INDEX_DIR.relative_to(ROOT)}/chunks.parquet, vectors.npy')


if __name__ == '__main__':
    main()
