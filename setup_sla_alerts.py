"""Peringatan risiko SLA sebelum terlampaui (BR-02, UC-08) — konfigurasi GLPI bawaan, tanpa kode.

- Aturan bisnis tiket "SLA <prioritas>": SLA waktu penyelesaian dipasang otomatis menurut prioritas, saat tiket
  dibuat maupun saat prioritas diubah (mis. operator menerima triase). Bisa diubah admin di menu Workflow.
- Tiap SLA "time to resolve" HaloSIS mendapat level eskalasi "Peringatan risiko SLA" yang berjalan SEBELUM batas
  waktu (execution_time negatif) dengan aksi "Automatic reminders of SLA" (recall).
- Notifikasi "Ticket Recall" dikirim ke teknisi & grup yang ditugaskan serta supervisor grup (atasan), lewat email
  dan notifikasi browser (mode ajax, terlihat tanpa server email).
- Pengguna contoh Manajemen (sri) dijadikan supervisor tiap tim teknis supaya peringatan "atasan" punya penerima.

Aman dijalankan berulang. Pakai (setelah seed_halosis.py):
    python setup_sla_alerts.py                      # default http://localhost:8080
Lalu aktifkan notifikasi (lihat README langkah 5b).
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

HOUR = 3600
# Waktu peringatan sebelum batas penyelesaian, ±25% dari target SLA
BEFORE = {'Kritis': HOUR, 'Tinggi': int(1.5 * HOUR), 'Sedang': 4 * HOUR, 'Rendah': 24 * HOUR}
LEVEL_NAME = 'Peringatan risiko SLA'

# Prioritas GLPI (1 sangat rendah … 6 mayor) → SLA HaloSIS; nilai prioritas mengikuti seed_halosis.py
PRIORITY_SLA = {'Kritis': (5, 6), 'Tinggi': (4,), 'Sedang': (3,), 'Rendah': (1, 2)}
RULE_ON_ADD_AND_UPDATE = 1 | 2   # RuleCommonITILObject::ONADD | ONUPDATE
PATTERN_IS = 0                   # Rule::PATTERN_IS
SUPERVISOR = 'sri'
TEAMS = ('Tim Aplikasi Statistik', 'Tim Jaringan', 'Tim Perangkat', 'Tim Identitas & Akses')

# Penerima "Ticket Recall": teknisi ditugaskan, grup ditugaskan, supervisor grup (Notification::*)
ASSIGN_TECH, ASSIGN_GROUP, SUPERVISOR_ASSIGN_GROUP, USER_TYPE = 2, 9, 10, 1


def get(itemtype, **criteria):
    rows = s.get(f'{B}/{itemtype}', params={'range': '0-500', **{f'searchText[{k}]': v for k, v in criteria.items()}}).json()
    return rows if isinstance(rows, list) else []


def add(itemtype, data):
    r = s.post(f'{B}/{itemtype}', data=json.dumps({'input': data}))
    j = r.json()
    if isinstance(j, dict) and 'id' in j:
        return j['id']
    raise SystemExit(f'{itemtype} gagal: {r.status_code} {r.text[:300]}')


for sla in get('SLA'):
    prio = sla['name'].split(' ')[0]
    if prio not in BEFORE or sla['type'] != 0:
        continue
    levels = [l for l in get('SlaLevel') if l['slas_id'] == sla['id'] and l['name'] == LEVEL_NAME]
    if levels:
        print(f'SLA "{sla["name"]}": level peringatan sudah ada')
        continue
    level = add('SlaLevel', {'name': LEVEL_NAME, 'slas_id': sla['id'], 'execution_time': -BEFORE[prio],
                             'is_active': 1, 'match': 'AND', 'entities_id': 0, 'is_recursive': 1})
    add('SlaLevelAction', {'slalevels_id': level, 'action_type': 'send', 'field': 'recall', 'value': 1})
    print(f'SLA "{sla["name"]}": peringatan {BEFORE[prio] // 60} menit sebelum batas waktu')

rules = {r['name'] for r in get('RuleTicket')}
for sla in get('SLA'):
    prio = sla['name'].split(' ')[0]
    if prio not in PRIORITY_SLA or sla['type'] != 0:
        continue
    name = f'SLA {prio}'
    if name in rules:
        print(f'Aturan "{name}" sudah ada')
        continue
    rule = add('RuleTicket', {'name': name, 'sub_type': 'RuleTicket', 'match': 'OR', 'is_active': 1,
                              'condition': RULE_ON_ADD_AND_UPDATE, 'entities_id': 0, 'is_recursive': 1,
                              'description': 'HaloSIS: SLA waktu penyelesaian menurut prioritas (BR-02)'})
    for value in PRIORITY_SLA[prio]:
        add('RuleCriteria', {'rules_id': rule, 'criteria': 'priority', 'condition': PATTERN_IS, 'pattern': value})
    add('RuleAction', {'rules_id': rule, 'action_type': 'assign', 'field': 'slas_id_ttr', 'value': sla['id']})
    print(f'Aturan "{name}": prioritas {PRIORITY_SLA[prio]} → SLA "{sla["name"]}"')

users = get('User', name=f'^{SUPERVISOR}$')
if users:
    for team in TEAMS:
        group = next((g for g in get('Group') if g['name'] == team), None)
        if group is None:
            continue
        links = [l for l in s.get(f'{B}/Group/{group["id"]}/Group_User').json() or [] if isinstance(l, dict)
                 and l.get('users_id') == users[0]['id']]
        if links and links[0].get('is_manager'):
            continue
        if links:
            s.put(f'{B}/Group_User/{links[0]["id"]}', data=json.dumps({'input': {'id': links[0]['id'], 'is_manager': 1}}))
        else:
            add('Group_User', {'groups_id': group['id'], 'users_id': users[0]['id'], 'is_manager': 1})
    print(f'Supervisor tim teknis: {SUPERVISOR}')

recall = next((n for n in get('Notification') if n['itemtype'] == 'Ticket' and n['event'] == 'recall'), None)
if recall is None:
    raise SystemExit('Notifikasi "Ticket Recall" tidak ditemukan')
targets = {(t['type'], t['items_id']) for t in s.get(f'{B}/Notification/{recall["id"]}/NotificationTarget').json() or []}
for items_id in (ASSIGN_TECH, ASSIGN_GROUP, SUPERVISOR_ASSIGN_GROUP):
    if (USER_TYPE, items_id) not in targets:
        add('NotificationTarget', {'notifications_id': recall['id'], 'type': USER_TYPE, 'items_id': items_id})
templates = s.get(f'{B}/Notification/{recall["id"]}/Notification_NotificationTemplate').json() or []
if templates and not any(t['mode'] == 'ajax' for t in templates):
    add('Notification_NotificationTemplate', {'notifications_id': recall['id'], 'mode': 'ajax',
                                              'notificationtemplates_id': templates[0]['notificationtemplates_id']})
if not recall['is_active']:
    s.put(f'{B}/Notification/{recall["id"]}', data=json.dumps({'input': {'id': recall['id'], 'is_active': 1}}))
print('Notifikasi "Ticket Recall": teknisi, grup, supervisor grup; email + browser')
