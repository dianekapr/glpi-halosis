"""Perapian form katalog "Laporkan Masalah" & "Ajukan Permintaan" lewat REST API GLPI (tanpa ubah inti).

1. Pertanyaan "Perangkat pengguna" dihapus dari kedua form.
2. "Pengamat" tetap opsional dan diberi keterangan.
3. (Opsional, --grup-bukan-pengamat) "Pengamat" hanya berisi pengguna. Tipe pertanyaan Pengamat GLPI selalu menawarkan
   pengguna + grup (src/Glpi/Form/QuestionType/QuestionTypeObserver.php: getAllowedActorTypes tidak bisa diatur), tetapi grup
   yang ditawarkan hanya yang berhak jadi pengamat (is_watcher=1). Opsi ini mengubah is_watcher grup tim menjadi 0
   (konfigurasi grup, berlaku global untuk tiket) → hanya dijalankan atas persetujuan.
Idempoten. Pakai:  python setup_form_laporan.py [http://localhost:8080] [--grup-bukan-pengamat]
"""
import json, sys
import requests

args = [a for a in sys.argv[1:] if not a.startswith('--')]
BASE = (args[0] if args else 'http://localhost:8080').rstrip('/')
B = BASE + '/apirest.php'
Q = B + '/Glpi%5CForm%5CQuestion'
KET = 'Opsional: orang yang ikut menerima pemberitahuan, mis. atasan.'
s = requests.Session()
r = s.get(B + '/initSession', auth=('glpi', 'glpi'))
if r.status_code != 200:
    raise SystemExit(f'Gagal login ke API ({r.status_code}).')
s.headers.update({'Session-Token': r.json()['session_token'], 'Content-Type': 'application/json'})
P = {p['name']: p['id'] for p in s.get(B + '/Profile', params={'range': '0-100'}).json()}
s.post(B + '/changeActiveProfile', json={'profiles_id': P['Super-Admin']})

forms = {f['id'] for f in s.get(B + '/Glpi%5CForm%5CForm', params={'range': '0-99'}).json() if f['name'] in ('Laporkan Masalah', 'Ajukan Permintaan')}
sections = {x['id'] for x in s.get(B + '/Glpi%5CForm%5CSection', params={'range': '0-99'}).json() if x['forms_forms_id'] in forms}
for q in s.get(Q, params={'range': '0-500'}).json():
    if q['forms_sections_id'] not in sections:
        continue
    if q['name'] == 'Perangkat pengguna':
        res = s.delete(f"{Q}/{q['id']}", params={'force_purge': 1})
        print(f"hapus pertanyaan #{q['id']} Perangkat pengguna: {res.status_code}")
    elif q['name'] == 'Pengamat' and (q['description'] or '') != KET:
        res = s.put(f"{Q}/{q['id']}", data=json.dumps({'input': {'id': q['id'], 'description': KET, 'is_mandatory': 0}}))
        print(f"keterangan Pengamat #{q['id']}: {res.status_code} {res.text[:120]}")
if '--grup-bukan-pengamat' in sys.argv:
    for g in s.get(B + '/Group', params={'range': '0-99'}).json():
        if g.get('is_watcher'):
            res = s.put(f"{B}/Group/{g['id']}", data=json.dumps({'input': {'id': g['id'], 'is_watcher': 0}}))
            print(f"grup {g['name']}: bukan pengamat ({res.status_code})")
s.get(B + '/killSession')
