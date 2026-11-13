"""Akun demo khusus untuk alur alternatif (lewat REST API, idempoten, tanpa ubah inti GLPI).

Tiap akun memakai profil turunan (salinan profil dasar dengan satu hak dicabut) sehingga akun demo lain tidak berubah:
  pegawai_tanpa_asisten  profil "Pegawai (tanpa asisten)"   Pegawai tanpa hak chatbot            -> UC-01 1b
  pegawai_tanpa_tiket    profil "Pegawai (tanpa buat tiket)" Pegawai tanpa hak membuat tiket     -> UC-03 5b
  operator_lihat         profil "Operator (lihat saja)"      Operator tanpa hak memutuskan saran  -> UC-05 3a
Kata sandi semua akun: halosis. Keycloak: akun ikut ke realm demo lewat keycloak/halosis-realm.json (impor ulang realm).

Pakai:  python setup_akun_demo_khusus.py [http://localhost:8080]
"""
import json, sys
import requests

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8080').rstrip('/')
B = BASE + '/apirest.php'
s = requests.Session()
r = s.get(B + '/initSession', auth=('glpi', 'glpi'))
if r.status_code != 200:
    raise SystemExit(f'Gagal login ke API ({r.status_code}): {r.text[:200]}')
s.headers.update({'Session-Token': r.json()['session_token'], 'Content-Type': 'application/json'})
P = {p['name']: p['id'] for p in s.get(B + '/Profile', params={'range': '0-100'}).json()}
s.post(B + '/changeActiveProfile', json={'profiles_id': P['Super-Admin']})

# (login, nama depan, nama belakang, profil dasar, nama profil turunan, {hak: nilai}, komentar)
AKUN = [
    ('pegawai_tanpa_asisten', 'Wahyu', 'Prasetyo', 'Pegawai', 'Pegawai (tanpa asisten)',
     {'plugin_halosis_chatbot': 0}, 'Demo UC-01 1b: tanpa hak asisten (chatbot)'),
    ('pegawai_tanpa_tiket', 'Tari', 'Lestari', 'Pegawai', 'Pegawai (tanpa buat tiket)',
     {'ticket': 1}, 'Demo UC-03 5b: bisa chat, tetapi tidak berhak membuat tiket (hanya baca)'),
    ('operator_lihat', 'Bima', 'Anggoro', 'Operator', 'Operator (lihat saja)',
     {'plugin_halosis_triase': 1}, 'Demo UC-05 3a: Operator tanpa hak memutuskan saran AI (hanya baca)'),
]
SALIN_ABAIKAN = {'id', 'name', 'comment', 'is_default', 'date_mod', 'date_creation', 'links', 'last_rights_update'}

def cari(item, nama_kolom, nilai):
    rows = s.get(f'{B}/{item}', params={'range': '0-999'}).json()
    return next((r['id'] for r in rows if r.get(nama_kolom) == nilai), None) if isinstance(rows, list) else None

def add(item, data):
    r = s.post(f'{B}/{item}', data=json.dumps({'input': data})).json()
    if isinstance(r, dict) and 'id' in r:
        return r['id']
    raise SystemExit(f'{item} gagal: {r}')

for login, fn, ln, dasar, nama_profil, hak, komentar in AKUN:
    # 1. Profil turunan: salin kolom profil dasar, lalu hak-hak (profilerights) dasar; terapkan pengecualian
    pid = P.get(nama_profil)
    base = s.get(f'{B}/Profile/{P[dasar]}').json()
    if pid is None:
        data = {k: base[k] for k in ('interface', 'helpdesk_hardware','use_mentions', 'show_map') if k in base}
        data.update({'name': nama_profil, 'comment': komentar, 'is_default': 0})
        pid = add('Profile', data)
        P[nama_profil] = pid
    target = {r['name']: r for r in s.get(f'{B}/Profile/{pid}/ProfileRight', params={'range': '0-300'}).json()}
    for r in s.get(f'{B}/Profile/{P[dasar]}/ProfileRight', params={'range': '0-300'}).json():
        nilai = hak.get(r['name'], r['rights'])
        if r['name'] in target and target[r['name']]['rights'] != nilai:
            s.put(f'{B}/ProfileRight/{target[r["name"]]["id"]}', data=json.dumps({'input': {'id': target[r['name']]['id'], 'rights': nilai}}))
    # 2. Akun: dibuat bila belum ada; satu profil saja
    uid = cari('User', 'name', login)
    if uid is None:
        uid = add('User', {'name': login, 'firstname': fn, 'realname': ln, 'password': 'halosis', 'password2': 'halosis',
                           'is_active': 1, 'language': 'id_ID', 'profiles_id': pid,
                           '_useremails': {'-1': f'{login}@contoh.go.id'}})
        add('Profile_User', {'users_id': uid, 'profiles_id': pid, 'entities_id': 0, 'is_recursive': 1})
    s.put(f'{B}/User/{uid}', data=json.dumps({'input': {'id': uid, 'language': 'id_ID', 'profiles_id': pid}}))
    ada = False
    for pu in s.get(f'{B}/User/{uid}/Profile_User').json() or []:
        if pu['profiles_id'] == pid and not ada:
            ada = True
        else:
            s.delete(f'{B}/Profile_User/{pu["id"]}')
    if not ada:
        add('Profile_User', {'users_id': uid, 'profiles_id': pid, 'entities_id': 0, 'is_recursive': 1})
    print(f'{login}: user #{uid}, profil "{nama_profil}" #{pid}')
