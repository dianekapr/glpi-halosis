"""Dasbor bawaan GLPI untuk profil Manajemen: hanya "Assistance", dan itu dasbor awalnya (lewat REST API, tanpa ubah inti).

GLPI: dasbor tanpa baris berbagi (glpi_dashboards_rights) terlihat oleh semua profil berhak "Dasbor"; begitu ada baris,
hanya penerima yang melihatnya. Maka dasbor "Central" & "Assets" dibagikan ke SEMUA profil kecuali Manajemen, sedangkan
"Assistance" dibiarkan tanpa batas. Dasbor awal (default_dashboard_central) pengguna berprofil Manajemen = assistance.
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

dasbor = {d['key']: d['id'] for d in s.get(D, params={'range': '0-60'}).json()}
ada = {(x['dashboards_dashboards_id'], x['itemtype'], x['items_id']) for x in s.get(R, params={'range': '0-500'}).json()}
for kunci in ('central', 'assets'):
    for nama, pid in P.items():
        if nama == 'Manajemen' or (dasbor[kunci], 'Profile', pid) in ada:
            continue
        res = s.post(R, data=json.dumps({'input': {'dashboards_dashboards_id': dasbor[kunci], 'itemtype': 'Profile', 'items_id': pid}}))
        print(f'bagikan {kunci} -> {nama}: {res.status_code}')

users = {u['id']: u['name'] for u in s.get(B + '/User', params={'range': '0-500'}).json() if isinstance(u, dict)}
for pu in s.get(f"{B}/Profile/{P['Manajemen']}/Profile_User", params={'range': '0-500'}).json() or []:
    if not isinstance(pu, dict):
        continue
    uid = pu['users_id']
    if s.get(f'{B}/User/{uid}').json().get('default_dashboard_central') != 'assistance':
        res = s.put(f'{B}/User/{uid}', data=json.dumps({'input': {'id': uid, 'default_dashboard_central': 'assistance'}}))
        print(f'dasbor awal {users.get(uid, uid)} = assistance: {res.status_code}')
s.get(B + '/killSession')
