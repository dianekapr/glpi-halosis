"""Urgensi tiket dari pemohon pejabat naik satu tingkat (wawancara PM 09:11–13:30, operator 20:33) — konfigurasi GLPI
bawaan, tanpa kode inti.

- Grup GLPI "Pejabat" (pemohon saja: bukan grup penugasan). Keanggotaan diisi plugin saat login SSO dari atribut
  jabatan Keycloak yang diawali salah satu kata di Pengaturan AI › Jabatan pejabat (bawaan: Kepala, Direktur, Deputi,
  Sekretaris Utama); lihat KeycloakAuth::prepareExternalLogin dan Config::matchOfficialTitle.
- Aturan bisnis "Pejabat: urgensi N → N+1" (N = 1..4): grup pemohon = Pejabat DAN urgensi = N → urgensi N+1, saat
  tiket dibuat. Ditempatkan paling awal (ranking terkecil) supaya aturan "SLA BPS …" memakai prioritas yang sudah naik.
- Saran triase AI menaikkan urgensi dengan aturan yang sama dan menulis alasannya di panel ("pemohon pejabat").

Aman dijalankan berulang. Pakai (setelah seed_halosis.py):
    python setup_pejabat_rules.py                   # default http://localhost:8080
"""
import json, sys
import requests

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8080').rstrip('/')
B = BASE + '/apirest.php'
s = requests.Session()
r = s.get(B + '/initSession', auth=('glpi', 'glpi'))
if r.status_code != 200:
    raise SystemExit(f'Gagal login ke API ({r.status_code}). Ganti kredensial glpi di skrip bila password sudah diubah.')
s.headers.update({'Session-Token': r.json()['session_token'], 'Content-Type': 'application/json'})
P = {p['name']: p['id'] for p in s.get(B + '/Profile', params={'range': '0-100'}).json()}
s.post(B + '/changeActiveProfile', json={'profiles_id': P['Super-Admin']})

GROUP = 'Pejabat'               # = Config::OFFICIAL_GROUP di plugin
RULE_ON_ADD = 1                 # RuleCommonITILObject::ONADD
PATTERN_IS = 0                  # Rule::PATTERN_IS


def get(itemtype):
    rows = s.get(f'{B}/{itemtype}', params={'range': '0-1000'}).json()
    return rows if isinstance(rows, list) else []


def add(itemtype, data):
    r = s.post(f'{B}/{itemtype}', data=json.dumps({'input': data}))
    j = r.json()
    if isinstance(j, dict) and 'id' in j:
        return j['id']
    raise SystemExit(f'{itemtype} gagal: {r.status_code} {r.text[:300]}')


group = next((g for g in get('Group') if g.get('name') == GROUP), None)
if group is None:
    group_id = add('Group', {'name': GROUP, 'entities_id': 0, 'is_recursive': 1, 'is_requester': 1, 'is_watcher': 0,
                             'is_assign': 0, 'is_notify': 0, 'is_itemgroup': 0, 'is_usergroup': 1, 'is_manager': 0,
                             'comment': 'HaloSIS: pemohon pejabat (anggota dari jabatan SSO); dipakai aturan urgensi'})
    print(f'Grup "{GROUP}" dibuat')
else:
    group_id = group['id']
    print(f'Grup "{GROUP}" sudah ada')

rules = {r['name']: r for r in get('RuleTicket')}
first = min((int(r.get('ranking') or 0) for r in rules.values()), default=1)
for level in (1, 2, 3, 4):
    name = f'Pejabat: urgensi {level} → {level + 1}'
    if name in rules:
        print(f'Aturan "{name}" sudah ada')
        continue
    rule = add('RuleTicket', {'name': name, 'sub_type': 'RuleTicket', 'match': 'AND', 'is_active': 1,
                              'condition': RULE_ON_ADD, 'entities_id': 0, 'is_recursive': 1,
                              'description': 'HaloSIS: urgensi naik satu tingkat untuk pemohon pejabat'})
    add('RuleCriteria', {'rules_id': rule, 'criteria': '_groups_id_of_requester', 'condition': PATTERN_IS,
                         'pattern': group_id})
    add('RuleCriteria', {'rules_id': rule, 'criteria': 'urgency', 'condition': PATTERN_IS, 'pattern': level})
    add('RuleAction', {'rules_id': rule, 'action_type': 'assign', 'field': 'urgency', 'value': level + 1})
    # Paling awal dan menurun (4→5 dievaluasi dulu, lalu 3→4, …) supaya satu tiket hanya naik satu tingkat, tidak berantai
    s.put(f'{B}/RuleTicket/{rule}', data=json.dumps({'input': {'id': rule, 'ranking': first - level}}))
    print(f'Aturan "{name}"')
s.get(B + '/killSession')
