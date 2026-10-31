"""Peringatan risiko SLA sebelum terlampaui (BR-02, UC-08) — konfigurasi GLPI bawaan, tanpa kode.

- SLA respons "time to own" (T1, KebijakanSLA.targetRespons) per prioritas dibuat di SLM "SLA HaloSIS": batas
  tiket diambil/ditugaskan, dihitung GLPI dari tanggal "diambil alih" (takeintoaccountdate).
- Aturan bisnis tiket "SLA <prioritas>": SLA waktu respons & penyelesaian dipasang otomatis menurut prioritas, saat
  tiket dibuat maupun saat prioritas diubah (mis. operator menerima triase). Bisa diubah admin di menu Workflow.
- Tiap SLA "time to resolve" HaloSIS mendapat level eskalasi "Peringatan risiko SLA" yang berjalan SEBELUM batas
  waktu (execution_time negatif) dengan aksi "Automatic reminders of SLA" (recall).
- Notifikasi "Ticket Recall" dikirim ke teknisi & grup yang ditugaskan serta supervisor grup (atasan), lewat email
  dan notifikasi browser (mode ajax, terlihat tanpa server email).
- Notifikasi "New problem" dikirim ke grup yang ditugaskan & grup Operator: pola insiden baru dari plugin
  (PatternDetector) menjadi peringatan dini bagi Operator (T9).
- Penerima "atasan" = supervisor grup, yaitu ketua tim yang dibuat seed_halosis.py (hendra, agus, rudi, wati).
  Skrip ini hanya memeriksa dan memperingatkan bila ada tim tanpa supervisor.

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
ESCALATION_NAME = 'Eskalasi SLA terlewati'
OPERATOR_GROUP = 'Operator Service Desk'

# Target respons (time to own) per prioritas; dokumen tidak memberi angka, nilai ini asumsi prototipe
TTO = {'Kritis': (15, 'minute'), 'Tinggi': (30, 'minute'), 'Sedang': (2, 'hour'), 'Rendah': (4, 'hour')}
SLM_NAME = 'SLA HaloSIS'
SLA_TTR, SLA_TTO = 0, 1          # SLM::TTR | SLM::TTO
# Prioritas GLPI (1 sangat rendah … 6 mayor) → SLA HaloSIS; nilai prioritas mengikuti seed_halosis.py
PRIORITY_SLA = {'Kritis': (5, 6), 'Tinggi': (4,), 'Sedang': (3,), 'Rendah': (1, 2)}
RULE_ON_ADD_AND_UPDATE = 1 | 2   # RuleCommonITILObject::ONADD | ONUPDATE
PATTERN_IS = 0                   # Rule::PATTERN_IS
TEAMS = ('Tim Aplikasi Statistik', 'Tim Jaringan', 'Tim Perangkat', 'Tim Identitas & Akses')

# Penerima "Ticket Recall": teknisi ditugaskan, grup ditugaskan, supervisor grup (Notification::*), grup Operator
ASSIGN_TECH, ASSIGN_GROUP, SUPERVISOR_ASSIGN_GROUP, USER_TYPE, GROUP_TYPE = 2, 9, 10, 1, 3


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

# FR-09: eskalasi saat batas waktu terlewati (execution_time 0 = tepat di batas) → Ticket Recall ke ketua tim
# & operator, dan prioritas dinaikkan ke "Sangat tinggi" agar tiket naik di antrean
for sla in get('SLA'):
    prio = sla['name'].split(' ')[0]
    if prio not in BEFORE or sla['type'] != 0:
        continue
    if any(l['slas_id'] == sla['id'] and l['name'] == ESCALATION_NAME for l in get('SlaLevel')):
        print(f'SLA "{sla["name"]}": level eskalasi sudah ada')
        continue
    level = add('SlaLevel', {'name': ESCALATION_NAME, 'slas_id': sla['id'], 'execution_time': 0,
                             'is_active': 1, 'match': 'AND', 'entities_id': 0, 'is_recursive': 1})
    add('SlaLevelAction', {'slalevels_id': level, 'action_type': 'send', 'field': 'recall', 'value': 1})
    if prio != 'Kritis':
        add('SlaLevelAction', {'slalevels_id': level, 'action_type': 'assign', 'field': 'priority', 'value': 5})
    print(f'SLA "{sla["name"]}": eskalasi saat batas waktu terlewati')

# SLA respons (time to own) per prioritas, di SLM yang sama dengan SLA penyelesaian dari seed_halosis.py
slm = next((m for m in get('SLM') if m['name'] == SLM_NAME), None)
if slm is None:
    raise SystemExit(f'SLM "{SLM_NAME}" tidak ditemukan; jalankan seed_halosis.py dulu')
for prio, (n, unit) in TTO.items():
    if any(x['slms_id'] == slm['id'] and x['type'] == SLA_TTO and x['name'].split(' ')[0] == prio for x in get('SLA')):
        print(f'SLA respons {prio}: sudah ada')
        continue
    label = f'{n} menit' if unit == 'minute' else f'{n} jam'
    add('SLA', {'name': f'{prio} · respons {label}', 'slms_id': slm['id'], 'type': SLA_TTO, 'number_time': n,
                'definition_time': unit, 'calendars_id': slm.get('calendars_id', 1)})
    print(f'SLA respons {prio}: {label}')

rules = {r['name']: r['id'] for r in get('RuleTicket')}
actions = [a for a in get('RuleAction') if isinstance(a, dict)]
for prio, values in PRIORITY_SLA.items():
    name = f'SLA {prio}'
    rule = rules.get(name)
    if rule is None:
        rule = add('RuleTicket', {'name': name, 'sub_type': 'RuleTicket', 'match': 'OR', 'is_active': 1,
                                  'condition': RULE_ON_ADD_AND_UPDATE, 'entities_id': 0, 'is_recursive': 1,
                                  'description': 'HaloSIS: SLA respons & penyelesaian menurut prioritas (BR-02)'})
        for value in values:
            add('RuleCriteria', {'rules_id': rule, 'criteria': 'priority', 'condition': PATTERN_IS, 'pattern': value})
        print(f'Aturan "{name}": prioritas {values}')
    # Satu aksi per jenis SLA (TTR & TTO); aturan lama dari versi sebelumnya mendapat aksi TTO saja
    for sla in get('SLA'):
        if sla['name'].split(' ')[0] != prio or sla['type'] not in (SLA_TTR, SLA_TTO):
            continue
        field = 'slas_id_ttr' if sla['type'] == SLA_TTR else 'slas_id_tto'
        if any(a['rules_id'] == rule and a['field'] == field for a in actions):
            continue
        add('RuleAction', {'rules_id': rule, 'action_type': 'assign', 'field': field, 'value': sla['id']})
        print(f'Aturan "{name}": {field} → SLA "{sla["name"]}"')

for team in TEAMS:
    group = next((g for g in get('Group') if g['name'] == team), None)
    links = s.get(f'{B}/Group/{group["id"]}/Group_User').json() if group else []
    if not any(isinstance(l, dict) and l.get('is_manager') for l in links or []):
        print(f'PERINGATAN: "{team}" belum punya supervisor (ketua tim); peringatan "atasan" tanpa penerima. '
              'Jalankan seed_halosis.py atau tandai ketua tim di Administrasi › Grup › Pengguna.')


def ensure_notification(itemtype, event, targets):
    """Pastikan notifikasi GLPI aktif, punya penerima `targets` [(type, items_id)], dan dikirim lewat browser."""
    notif = next((n for n in get('Notification') if n['itemtype'] == itemtype and n['event'] == event), None)
    if notif is None:
        raise SystemExit(f'Notifikasi {itemtype} "{event}" tidak ditemukan')
    existing = {(t['type'], t['items_id']) for t in s.get(f'{B}/Notification/{notif["id"]}/NotificationTarget').json() or []}
    for target in targets:
        if target not in existing:
            add('NotificationTarget', {'notifications_id': notif['id'], 'type': target[0], 'items_id': target[1]})
    templates = s.get(f'{B}/Notification/{notif["id"]}/Notification_NotificationTemplate').json() or []
    if templates and not any(t['mode'] == 'ajax' for t in templates):
        add('Notification_NotificationTemplate', {'notifications_id': notif['id'], 'mode': 'ajax',
                                                  'notificationtemplates_id': templates[0]['notificationtemplates_id']})
    if not notif['is_active']:
        s.put(f'{B}/Notification/{notif["id"]}', data=json.dumps({'input': {'id': notif['id'], 'is_active': 1}}))


operator = next((g for g in get('Group') if g['name'] == OPERATOR_GROUP), None)
operator_target = [(GROUP_TYPE, operator['id'])] if operator else []
ensure_notification('Ticket', 'recall', [(USER_TYPE, ASSIGN_TECH), (USER_TYPE, ASSIGN_GROUP),
                                         (USER_TYPE, SUPERVISOR_ASSIGN_GROUP)] + operator_target)
print(f'Notifikasi "Ticket Recall": teknisi, grup, supervisor grup (ketua tim), grup {OPERATOR_GROUP}; email + browser')

# T9: pola insiden baru = Problem baru yang ditugaskan ke grup Operator (plugin PatternDetector) → peringatan dini
ensure_notification('Problem', 'new', [(USER_TYPE, ASSIGN_GROUP)] + operator_target)
print(f'Notifikasi "New problem" (pola insiden): grup yang ditugaskan & grup {OPERATOR_GROUP}; email + browser')
