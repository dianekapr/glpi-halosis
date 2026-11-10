"""Seed data demo dashboard HaloSIS — SEMUA data bertanda "[DEMO]". BELUM DIJALANKAN (menunggu persetujuan).

Pakai:  python scripts/seed_demo.py rencana            # hanya cetak jumlah per jenis, tanpa menulis apa pun
        python scripts/seed_demo.py buat               # buat data (idempoten: berhenti bila [DEMO] sudah ada)
        python scripts/seed_demo.py buat --ulang       # hapus dulu lalu buat ulang
        python scripts/seed_demo.py hapus              # hapus SEMUA data [DEMO] (tiket, Problem, saran, keputusan, chat, pola)
Syarat: API GLPI aktif, seed_halosis.py sudah jalan, layanan AI hidup (hook triase membuat saran saat tiket dibuat),
        container glpi berjalan (langkah plugin dijalankan lewat `docker compose exec`, memakai kelas plugin).
Pembagian jalur:
  - Tiket, penugasan (grup/akun peran), tindak lanjut, solusi, penutupan, survei, Problem  → REST API GLPI.
  - Saran AI → dibuat hook plugin saat tiket dibuat (bukan ditulis ttangan).
  - Keputusan (terima/ubah/tolak), chat + rating, deteksi pola → kelas plugin lewat scripts/seed_demo_plugin.php
    (tabel plugin tidak punya REST), dijalankan lewat plugins/halosis/tools/seed_demo_plugin.php. Mundurkan tanggal =
    UPDATE ber-WHERE ketat pada baris [DEMO] (flag --mundurkan-tanggal; disetujui). Alat demo, bukan layanan AI.
"""
import json, random, subprocess, sys
from datetime import datetime, timedelta
import requests

BASE, TAG, WEEKS, SEED = 'http://localhost:8080', '[DEMO]', 12, 42
JUMLAH = {'tiket': 135, 'selesai_ditutup': 66, 'l1': 13, 'survei_terisi': 33, 'saran_keputusan': 96,
          'pola': 2, 'tiket_pola': 15, 'chat': 40, 'rating_chat': 18}
random.seed(SEED)
mode = sys.argv[1] if len(sys.argv) > 1 else 'rencana'
if mode == 'rencana':
    print(json.dumps(JUMLAH, indent=1)); print('perkiraan durasi: 8-12 menit (hook AI ±2 dtk/tiket)'); sys.exit()

B = BASE + '/apirest.php'
s = requests.Session()
r = s.get(B + '/initSession', auth=('glpi', 'glpi')); r.raise_for_status()
s.headers.update({'Session-Token': r.json()['session_token'], 'Content-Type': 'application/json'})

P = {p['name']: p['id'] for p in s.get(B + '/Profile', params={'range': '0-100'}).json()}
s.post(B + '/changeActiveProfile', json={'profiles_id': P['Super-Admin']})

def api(method, path, **kw):
    r = s.request(method, f'{B}/{path}', **kw); r.raise_for_status(); return r.json()
def plugin(*args):
    return subprocess.run(['docker', 'compose', 'exec', '-T', 'glpi', 'php', '/var/www/glpi/plugins/halosis/tools/seed_demo_plugin.php', *args],
                          check=True, capture_output=True, text=True).stdout
def demo_ids():
    rows = api('GET', 'Ticket', params={'range': '0-999', 'is_deleted': 0, 'searchText[name]': TAG})
    return [t['id'] for t in rows if t['name'].startswith(TAG)]

def hapus():
    ids = demo_ids()
    print(plugin('hapus'))  # saran, keputusan, penugasan ulang, chat, pola + Problem [DEMO]
    if ids: api('DELETE', 'Ticket', data=json.dumps({'input': [{'id': i} for i in ids], 'force_purge': True}))
    print(f'dihapus: {len(ids)} tiket')

if mode == 'hapus': hapus(); sys.exit()
if demo_ids():
    if '--ulang' in sys.argv: hapus()
    else: sys.exit('Data [DEMO] sudah ada; pakai --ulang atau hapus dulu (idempoten).')

GRUP = {g['name']: g['id'] for g in api('GET', 'Group', params={'range': '0-99'})}
USER = {u['name']: u['id'] for u in api('GET', 'User', params={'range': '0-99'})}
TIM = ['Tim Aplikasi Statistik', 'Tim Jaringan', 'Tim Perangkat', 'Tim Identitas & Akses']
KAT = {c['completename']: c['id'] for c in api('GET', 'ITILCategory', params={'range': '0-99'})}
JUDUL = ['Tidak bisa login SSO', 'Printer lantai 3 tidak terdeteksi', 'Aplikasi SIMPEG lambat', 'VPN gagal tersambung',
         'Laptop tidak menyala', 'Email tidak terkirim', 'Minta akses folder bersama', 'Wi-Fi putus-putus']
sekarang = datetime.now()

def tanggal(minggu_lalu):  # tersebar 12 minggu; lebih padat di minggu terbaru
    return (sekarang - timedelta(weeks=minggu_lalu, days=random.randint(0, 6), hours=random.randint(0, 8))).strftime('%Y-%m-%d %H:%M:%S')

PEMOHON = ['budi'] * 35 + ['siti'] * 35 + ['maya'] * 30  # budi 35% (≤ 40%)
OPERATOR = 'Operator Service Desk'

def buat_tiket(judul, minggu, kategori=None, tim=None, tipe=1, isi=None, tgl=None, pemohon=None, l1=False):
    # l1=True: ditangani langsung Operator (grup Operator + rina, tanpa tim teknis) → KPI L1
    tim = OPERATOR if l1 else (tim or random.choice(TIM))
    tid = api('POST', 'Ticket', data=json.dumps({'input': {
        'name': f'{TAG} {judul}', 'content': f'{TAG} {isi or "Data fiktif untuk demo dashboard."}', 'type': tipe,
        **({'date': tgl or tanggal(minggu)} if (minggu is not None or tgl) else {}),
        'urgency': random.choice([2, 3, 3, 4]), 'impact': random.choice([2, 3, 3]),
        '_users_id_requester': USER[pemohon or random.choice(PEMOHON)], **({'itilcategories_id': kategori} if kategori else {})}}))['id']  # hook AI → saran
    api('POST', 'Ticket_User', data=json.dumps({'input': {'tickets_id': tid, 'users_id': USER['rina' if l1 else random.choice(['andi', 'andi', 'hendra'])], 'type': 2}}))
    api('POST', 'Group_Ticket', data=json.dumps({'input': {'tickets_id': tid, 'groups_id': GRUP[tim], 'type': 2}}))
    return tid

# 2 pola, 15 tiket (tidak ikut diselesaikan: detektor hanya membaca tiket belum Selesai). DIBUAT PERTAMA: detektor membaca
# tiket belum selesai dalam jendela 60 menit terakhir, jadi tiket lain belum boleh ada. Pola 2 (Presensi) dibuat dan dideteksi
# dulu, lalu tanggal tiketnya digeser 6 minggu ke belakang (langkah geser_pola, [DEMO] saja), baru pola 1 (Wi-Fi, terbaru ->
# banner aktif untuk operator). Dijalankan terpisah agar tidak tergabung.
def buat_pola(judul, n, tim, isi): [buat_tiket(judul, None, tim=tim, isi=isi, pemohon=['budi', 'siti', 'maya'][i % 3]) for i in range(n)]  # banyak pemohon
buat_pola('Presensi online error 500', 7, 'Tim Aplikasi Statistik', 'Halaman presensi online menampilkan galat 500 saat absen masuk.')
print(plugin('pola')); print(plugin('geser_pola'))
buat_pola('Wi-Fi gedung B putus', 8, 'Tim Jaringan', 'Koneksi Wi-Fi di gedung B terputus berulang, situs tidak bisa dibuka.')
print(plugin('pola'))

semua, l1_ids = [], []
bobot = [17, 15, 13, 12, 11, 10, 9, 8, 7, 7, 6, 5]  # minggu 0 (terbaru) … 11 → 120 tiket
l1_idx = set(random.sample(range(sum(bobot)), 13))  # 13 tiket diselesaikan langsung Operator (L1 ≈ 17–20% dari tiket selesai)
for minggu, n in enumerate(bobot):
    for _ in range(n):
        l1 = len(semua) in l1_idx
        tid = buat_tiket(random.choice(JUDUL), minggu, l1=l1)
        semua.append(tid); l1 and l1_ids.append(tid)
lain = [t for t in semua if t not in l1_ids]; random.shuffle(lain)
selesai = l1_ids + lain[:JUMLAH['selesai_ditutup'] - len(l1_ids)]
for i, tid in enumerate(selesai):  # tindak lanjut + solusi; separuhnya ditutup (+ survei)
    api('POST', 'ITILFollowup', data=json.dumps({'input': {'items_id': tid, 'itemtype': 'Ticket', 'content': f'{TAG} Sudah dicek.'}}))
    api('POST', 'ITILSolution', data=json.dumps({'input': {'items_id': tid, 'itemtype': 'Ticket', 'content': f'{TAG} Solusi demo.'}}))
    if i % 2 == 0: api('PUT', f'Ticket/{tid}', data=json.dumps({'input': {'status': 6}}))

print(plugin('survei', str(JUMLAH['survei_terisi'])))  # survei diisi lewat DB layer GLPI, terbatas tiket [DEMO] Ditutup
print(plugin('keputusan'))  # Triage::decide (terima 70 / ubah 15 / tolak 15 %), sebagai rina
print(plugin('chat', str(JUMLAH['chat']), str(JUMLAH['rating_chat'])))  # status/rating bervariasi + article_uses
if '--mundurkan-tanggal' in sys.argv: print(plugin('mundurkan'))  # satu UPDATE terbatas pada baris [DEMO]
print('selesai (target):', JUMLAH)
