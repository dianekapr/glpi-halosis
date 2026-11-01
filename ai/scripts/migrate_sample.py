"""FR-10/NFR-13: migrasi SAMPEL tiket history (tersamar) ke GLPI lewat REST API, di entitas terpisah "Arsip ESTIM".

- Sumber: data/processed/tickets_clean.parquet (hasil prepare_data.py, teks & pengguna sudah disamarkan).
- Sampel deterministik: N tiket pertama menurut nomor tiket (bawaan 200).
- Idempoten: nomor tiket history disimpan di field `externalid`; tiket yang sudah ada di entitas arsip dilewati.
- Status history → status GLPI (STATE_MAP); status tak dikenal, tanpa nomor, atau tanggal tidak valid → GAGAL.
- Notifikasi: `_disablenotif` tidak dihormati lewat REST API, jadi antrean notifikasi tiket arsip dihapus setelah
  migrasi (tidak ada email ke pegawai); tiket selesai tidak memicu triase AI (plugin melewati tiket selesai).
- Rekonsiliasi (sumber = berhasil + dilewati + gagal) ditulis ke reports/rekonsiliasi.md, bagian "Migrasi sampel".
  Hanya angka; isi tiket tidak dicetak.

Pakai (dari root repo, GLPI jalan di :8080, akun lokal glpi):
    .venv/bin/python ai/scripts/migrate_sample.py [--jumlah 200] [--url http://localhost:8080]
    .venv/bin/python ai/scripts/migrate_sample.py --hapus     # hapus SEMUA tiket arsip + entitasnya
Kredensial: GLPI_API_USER / GLPI_API_PASSWORD (bawaan glpi/glpi, sama dengan skrip setup lain).
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data/processed/tickets_clean.parquet'
REPORT = ROOT / 'reports/rekonsiliasi.md'
ENTITY = 'Arsip ESTIM'
MARK_START, MARK_END = '<!-- migrasi-sampel:mulai -->', '<!-- migrasi-sampel:selesai -->'

# Status history → status GLPI (1 Baru, 2 Diproses-ditugaskan, 4 Menunggu, 5 Selesai, 6 Ditutup)
STATE_MAP = {
    'New': 1, 'Assigned': 2, 'In Progress': 2, 'On-Hold': 4, 'Resolved': 5,
    'Closed': 6, 'Completed': 6, 'Canceled': 6, 'Cancel': 6, 'Close Cancelled': 6, 'Close Incomplete': 6,
}
TYPE_MAP = {'INC': 1, 'REQ': 2}


class Api:
    def __init__(self, base: str):
        self.base = base.rstrip('/') + '/apirest.php'
        self.s = requests.Session()
        r = self.s.get(f'{self.base}/initSession', auth=(os.environ.get('GLPI_API_USER', 'glpi'),
                                                         os.environ.get('GLPI_API_PASSWORD', 'glpi')))
        r.raise_for_status()
        self.s.headers.update({'Session-Token': r.json()['session_token'], 'Content-Type': 'application/json'})
        profiles = {p['name']: p['id'] for p in self.s.get(f'{self.base}/Profile', params={'range': '0-100'}).json()}
        self.s.post(f'{self.base}/changeActiveProfile', json={'profiles_id': profiles['Super-Admin']})
        self.s.post(f'{self.base}/changeActiveEntities', json={'entities_id': 0, 'is_recursive': True})

    def list(self, itemtype: str, **params) -> list[dict]:
        rows = self.s.get(f'{self.base}/{itemtype}', params={'range': '0-5000', **params}).json()
        return rows if isinstance(rows, list) else []

    def add(self, itemtype: str, data: dict) -> int | None:
        r = self.s.post(f'{self.base}/{itemtype}', data=json.dumps({'input': data}))
        body = r.json() if r.content else {}
        return body.get('id') if isinstance(body, dict) else None

    def close(self):
        self.s.get(f'{self.base}/killSession')


def entity_id(api: Api, create: bool) -> int | None:
    found = next((e['id'] for e in api.list('Entity') if e['name'] == ENTITY), None)
    if found is None and create:
        found = api.add('Entity', {'name': ENTITY, 'entities_id': 0,
                                   'comment': 'Sampel migrasi history ESTIM (FR-10); terpisah dari data demo'})
        # Entitas baru belum termasuk entitas aktif sesi: segarkan agar tiket boleh dibuat di sana
        api.s.post(f'{api.base}/changeActiveEntities', json={'entities_id': 0, 'is_recursive': True})
    return found


def ticket_input(row: pd.Series, ent: int) -> dict:
    opened = pd.to_datetime(row['opened'], errors='coerce')
    done = pd.to_datetime(row['closed'] if pd.notna(row['closed']) else row['resolved'], errors='coerce')
    status = STATE_MAP[row['state_name']]
    content = [f'<p>{html(row["description"]) or "(tanpa deskripsi)"}</p>',
               f'<p><em>Migrasi history ESTIM · tim asal: {html(row["assignment_group_name"]) or "-"}'
               f' · status asal: {html(row["state_name"])}</em></p>']
    if pd.notna(row.get('solusi')):
        content.append(f'<p><strong>Solusi (history):</strong> {html(row["solusi"])}</p>')
    data = {
        'name': (str(row['short_description'] or '').strip() or '(tanpa judul)')[:250],
        'content': ''.join(content),
        'entities_id': ent,
        'externalid': str(row['ticket_number']),
        'type': TYPE_MAP.get(str(row['ticket_type']).upper()[:3], 1),
        'status': status,
        'date': opened.strftime('%Y-%m-%d %H:%M:%S'),
        '_disablenotif': True,
    }
    if status >= 5 and pd.notna(done):
        data['solvedate'] = data['closedate'] = done.strftime('%Y-%m-%d %H:%M:%S')
    return data


def html(value) -> str:
    text = '' if value is None or (isinstance(value, float) and pd.isna(value)) else str(value)
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')[:4000]


def migrate(api: Api, count: int) -> dict:
    df = pd.read_parquet(SRC).sort_values('ticket_number', na_position='first').head(count)
    ent = entity_id(api, create=True)
    existing = {t['externalid'] for t in api.list('Ticket', is_deleted=0) if t.get('entities_id') == ent}
    stats = {'sumber': len(df), 'berhasil': 0, 'dilewati': 0, 'gagal': 0, 'alasan_gagal': {}, 'per_status': {}}

    def fail(reason: str):
        stats['gagal'] += 1
        stats['alasan_gagal'][reason] = stats['alasan_gagal'].get(reason, 0) + 1

    for _, row in df.iterrows():
        if pd.isna(row['ticket_number']) or not str(row['ticket_number']).strip():
            fail('Tanpa nomor tiket'); continue
        if row['state_name'] not in STATE_MAP:
            fail('Status tidak bisa dipetakan ke GLPI'); continue
        if pd.isna(pd.to_datetime(row['opened'], errors='coerce')):
            fail('Tanggal dibuka tidak valid'); continue
        if str(row['ticket_number']) in existing:
            stats['dilewati'] += 1; continue
        if api.add('Ticket', ticket_input(row, ent)):
            stats['berhasil'] += 1
            label = str(row['state_name'])
            stats['per_status'][label] = stats['per_status'].get(label, 0) + 1
        else:
            fail('Ditolak API GLPI')
    assert stats['sumber'] == stats['berhasil'] + stats['dilewati'] + stats['gagal']
    archived = {t['id'] for t in api.list('Ticket', is_deleted=0) if t.get('entities_id') == ent}
    stats['di_glpi'] = len(archived)
    stats['notifikasi_dihapus'] = drop_notifications(api, archived)
    return stats


def drop_notifications(api: Api, ticket_ids: set[int]) -> int:
    """Hapus notifikasi antre (belum terkirim) milik tiket arsip."""
    queued = [q['id'] for q in api.list('QueuedNotification')
              if q.get('itemtype') == 'Ticket' and q.get('items_id') in ticket_ids]
    for start in range(0, len(queued), 100):
        api.s.delete(f'{api.base}/QueuedNotification',
                     data=json.dumps({'input': [{'id': i} for i in queued[start:start + 100]], 'force_purge': True}))
    return len(queued)


def remove(api: Api) -> dict:
    ent = entity_id(api, create=False)
    if ent is None:
        return {'dihapus': 0}
    ids = [t['id'] for t in api.list('Ticket') if t.get('entities_id') == ent]
    drop_notifications(api, set(ids))
    for start in range(0, len(ids), 100):
        api.s.delete(f'{api.base}/Ticket', data=json.dumps({'input': [{'id': i} for i in ids[start:start + 100]],
                                                            'force_purge': True}))
    api.s.delete(f'{api.base}/Entity/{ent}', params={'force_purge': True})
    return {'dihapus': len(ids), 'entitas_dihapus': ENTITY}


def write_report(stats: dict) -> None:
    rows = [f'| {k} | {v} |' for k, v in sorted(stats['alasan_gagal'].items())] or ['| – | 0 |']
    per_status = ', '.join(f'{k} {v}' for k, v in sorted(stats['per_status'].items())) or '–'
    section = '\n'.join([
        MARK_START, '## Migrasi sampel ke GLPI (FR-10/NFR-13)', '',
        f'Dibuat `ai/scripts/migrate_sample.py` · {datetime.now():%Y-%m-%d %H:%M} · entitas GLPI terpisah **{ENTITY}**'
        f' (bukan data demo) · {stats["sumber"]} tiket pertama menurut nomor tiket.', '',
        '| Ukuran | Jumlah |', '| --- | ---: |',
        f'| Sumber (sampel) | {stats["sumber"]} |', f'| Berhasil dibuat | {stats["berhasil"]} |',
        f'| Dilewati (sudah ada, idempoten) | {stats["dilewati"]} |', f'| Gagal | {stats["gagal"]} |',
        f'| **Cek: sumber = berhasil + dilewati + gagal** | {"✅" if stats["sumber"] == stats["berhasil"] + stats["dilewati"] + stats["gagal"] else "❌"} |',
        f'| Tiket di entitas {ENTITY} setelah migrasi | {stats["di_glpi"]} |', '',
        f'Berhasil per status asal: {per_status}.', '', '| Alasan gagal | Jumlah |', '| --- | ---: |', *rows, '',
        'Hapus seluruh sampel: `.venv/bin/python ai/scripts/migrate_sample.py --hapus` (tiket di entitas arsip '
        'di-purge, lalu entitasnya).', MARK_END])
    text = REPORT.read_text(encoding='utf-8') if REPORT.exists() else ''
    if MARK_START in text:
        text = re.sub(re.escape(MARK_START) + '.*?' + re.escape(MARK_END), section, text, flags=re.S)
    else:
        text = text.rstrip('\n') + '\n\n' + section + '\n'
    REPORT.write_text(text, encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--jumlah', type=int, default=200)
    parser.add_argument('--url', default='http://localhost:8080')
    parser.add_argument('--hapus', action='store_true')
    args = parser.parse_args()
    api = Api(args.url)
    try:
        if args.hapus:
            print(json.dumps(remove(api), ensure_ascii=False))
            return
        stats = migrate(api, args.jumlah)
        write_report(stats)
        print(json.dumps({k: v for k, v in stats.items()}, ensure_ascii=False))
    finally:
        api.close()


if __name__ == '__main__':
    main()
