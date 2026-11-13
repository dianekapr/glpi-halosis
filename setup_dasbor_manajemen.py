"""Dasbor bawaan GLPI untuk SEMUA profil staf (Operator, Tim Teknis, Knowledge Manager, Manajemen, Administrator): hanya "Assistance", dan itu dasbor awalnya (lewat REST API, tanpa ubah inti).

GLPI: dasbor tanpa baris berbagi (glpi_dashboards_rights) terlihat oleh semua profil berhak "Dasbor"; begitu ada baris,
hanya penerima yang melihatnya. Maka "Central" & "Assets" dibagikan HANYA ke profil non-staf (Pegawai, Super-Admin, Supervisor,
Read-Only); baris berbagi profil staf dihapus. "Assistance" dibiarkan tanpa batas. Dasbor awal semua pengguna profil staf = assistance,
dan mode data demonstrasi GLPI (is_demo_dashboards, angka "114.7K") dimatikan.
Laporan aset ("berdasarkan perangkat keras") TIDAK disentuh di sini: lihat catatan di laporan sesi.
Idempoten. Pakai:  python setup_dasbor_manajemen.py [http://localhost:8080]
"""
import json, sys
import requests

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8080').rstrip('/')
B = BASE + '/apirest.php'
D = B + '/Glpi%5CDashboard%5CDashboard'
R = B + '/Glpi%5CDashboard%5CRight'
s = requests.Session()
r = s.get(B + '/initSession', auth=('glpi', 'glpi'))
if r.status_code != 200:
    raise SystemExit(f'Gagal login ke API ({r.status_code}).')
s.headers.update({'Session-Token': r.json()['session_token'], 'Content-Type': 'application/json'})
P = {p['name']: p['id'] for p in s.get(B + '/Profile', params={'range': '0-100'}).json()}
s.post(B + '/changeActiveProfile', json={'profiles_id': P['Super-Admin']})

STAF = ('Operator', 'Tim Teknis', 'Knowledge Manager', 'Manajemen', 'Administrator')

# Mode data demonstrasi dasbor GLPI (angka palsu) dimatikan.
res = s.put(B + '/Config/1', data=json.dumps({'input': {'id': 1, 'is_demo_dashboards': 0}}))
print(f'is_demo_dashboards=0: {res.status_code}')

dasbor = {d['key']: d['id'] for d in s.get(D, params={'range': '0-60'}).json()}
baris = s.get(R, params={'range': '0-500'}).json()
ada = {(x['dashboards_dashboards_id'], x['itemtype'], x['items_id']): x['id'] for x in baris}
for kunci in ('central', 'assets'):
    for nama, pid in P.items():
        kunci_baris = (dasbor[kunci], 'Profile', pid)
        if nama in STAF:
            if kunci_baris in ada:
                res = s.delete(f'{R}/{ada[kunci_baris]}')
                print(f'cabut {kunci} <- {nama}: {res.status_code}')
        elif kunci_baris not in ada:
            res = s.post(R, data=json.dumps({'input': {'dashboards_dashboards_id': dasbor[kunci], 'itemtype': 'Profile', 'items_id': pid}}))
            print(f'bagikan {kunci} -> {nama}: {res.status_code}')

users = {u['id']: u['name'] for u in s.get(B + '/User', params={'range': '0-500'}).json() if isinstance(u, dict)}
for nama in STAF:
    for pu in s.get(f"{B}/Profile/{P[nama]}/Profile_User", params={'range': '0-500'}).json() or []:
        if not isinstance(pu, dict):
            continue
        uid = pu['users_id']
        if s.get(f'{B}/User/{uid}').json().get('default_dashboard_central') != 'assistance':
            res = s.put(f'{B}/User/{uid}', data=json.dumps({'input': {'id': uid, 'default_dashboard_central': 'assistance'}}))
            print(f'dasbor awal {users.get(uid, uid)} = assistance: {res.status_code}')
s.get(B + '/killSession')
