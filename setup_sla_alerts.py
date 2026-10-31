"""Peringatan risiko SLA sebelum terlampaui (BR-02, UC-08) — konfigurasi GLPI bawaan, tanpa kode.

- SLA resmi BPS dari history ESTIM (config/sla_layanan.json, T1/T22): respons 15 menit semua tiket; penyelesaian
  insiden menurut tier prioritas (Crit 2 hari, Medium 8 hari, Low 15 hari); pemenuhan permintaan 7 hari, 14 hari untuk
  layanan tim yang di history dominan 14 hari. Dihitung dengan kalender jam kerja GLPI.
- Aturan bisnis "SLA BPS …" (jenis × prioritas, dan kategori 14 hari) memasang SLA saat tiket dibuat maupun diubah.
  Aturan lama ("SLA <prioritas>", "SLA layanan: …") dinonaktifkan, tidak dihapus (riwayat tiket tetap merujuknya).
- Tiap SLA penyelesaian/pemenuhan mendapat level "Peringatan risiko SLA" ±20% sebelum batas dan "Eskalasi SLA
  terlewati" tepat di batas, keduanya dengan aksi "Automatic reminders of SLA" (recall).
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
import json, os, sys
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
LEVEL_NAME = 'Peringatan risiko SLA'
ESCALATION_NAME = 'Eskalasi SLA terlewati'
OPERATOR_GROUP = 'Operator Service Desk'

SLM_NAME = 'SLA HaloSIS'
SLA_TTR, SLA_TTO = 0, 1          # SLM::TTR | SLM::TTO
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


# --- SLA resmi BPS (config/sla_layanan.json) ---------------------------------------------------------------------
CFG = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config/sla_layanan.json'), encoding='utf-8'))
UNITS = {'m': ('minute', 'menit', 60), 'h': ('hour', 'jam', HOUR), 'd': ('day', 'hari', None)}
INCIDENT, REQUEST = 1, 2          # Ticket::INCIDENT_TYPE, Ticket::DEMAND_TYPE
LEGACY_RULES = ('SLA Kritis', 'SLA Tinggi', 'SLA Sedang', 'SLA Rendah')

slm = next((m for m in get('SLM') if m['name'] == SLM_NAME), None)
if slm is None:
    raise SystemExit(f'SLM "{SLM_NAME}" tidak ditemukan; jalankan seed_halosis.py dulu')
calendar = slm.get('calendars_id') or 1
# Jam kerja per hari dari kalender GLPI (segmen hari Senin), untuk menghitung peringatan ±20% dalam waktu kerja
segment = next(iter(s.get(f'{B}/Calendar/{calendar}/CalendarSegment').json() or []), None)
WORKDAY = (int(segment['end'][:2]) - int(segment['begin'][:2])) * HOUR if segment else 8 * HOUR
WARN = float(CFG.get('peringatan_sebelum_batas', 0.2))
slas = {x['name']: x for x in get('SLA')}


def official_sla(label, target, sla_type):
    """SLA "BPS · <label>" (dibuat sekali) + level peringatan ±20% & eskalasi untuk SLA penyelesaian."""
    n, (unit, word, seconds) = int(target[:-1]), UNITS[target[-1]]
    name = f'BPS · {label} {n} {word}'
    if name in slas:
        return slas[name]['id']
    sla_id = add('SLA', {'name': name, 'slms_id': slm['id'], 'type': sla_type, 'number_time': n,
                         'definition_time': unit, 'calendars_id': calendar, 'end_of_working_day': 0,
                         'comment': f'Sumber: {CFG["sumber"]}'})
    slas[name] = {'id': sla_id}
    if sla_type == SLA_TTR:
        total = n * (seconds or WORKDAY)
        before = int(round(total * WARN / HOUR)) * HOUR or 900
        for level_name, when in ((LEVEL_NAME, -before), (ESCALATION_NAME, 0)):
            level = add('SlaLevel', {'name': level_name, 'slas_id': sla_id, 'execution_time': when, 'is_active': 1,
                                     'match': 'AND', 'entities_id': 0, 'is_recursive': 1})
            add('SlaLevelAction', {'slalevels_id': level, 'action_type': 'send', 'field': 'recall', 'value': 1})
        print(f'SLA "{name}": peringatan {before // HOUR} jam kerja sebelum batas, eskalasi di batas')
    else:
        print(f'SLA "{name}"')
    return sla_id


tto = official_sla('respons', CFG['respons']['target'], SLA_TTO)
rules = {r['name']: r for r in get('RuleTicket')}
actions = [a for a in get('RuleAction') if isinstance(a, dict)]


def ensure_rule(name, criteria, ttr):
    """Aturan "SLA BPS …": semua kriteria (AND) → SLA respons 15 menit + SLA penyelesaian/pemenuhan."""
    if name in rules:
        return
    rule = add('RuleTicket', {'name': name, 'sub_type': 'RuleTicket', 'match': 'AND', 'is_active': 1,
                              'condition': RULE_ON_ADD_AND_UPDATE, 'entities_id': 0, 'is_recursive': 1,
                              'description': f'HaloSIS: SLA resmi BPS ({CFG["sumber"]})'})
    for field, value in criteria:
        add('RuleCriteria', {'rules_id': rule, 'criteria': field, 'condition': PATTERN_IS, 'pattern': value})
    add('RuleAction', {'rules_id': rule, 'action_type': 'assign', 'field': 'slas_id_tto', 'value': tto})
    add('RuleAction', {'rules_id': rule, 'action_type': 'assign', 'field': 'slas_id_ttr', 'value': ttr})
    print(f'Aturan "{name}"')


# Insiden: tier resolution_sla_name history → prioritas GLPI (satu aturan per nilai prioritas)
for tier, spec in CFG['insiden'].items():
    if tier.startswith('_'):
        continue
    ttr = official_sla(f'insiden {tier}', spec['target'], SLA_TTR)
    for priority in spec['prioritas_glpi']:
        ensure_rule(f'SLA BPS insiden {tier} · prioritas {priority}', [('type', INCIDENT), ('priority', priority)], ttr)

# Permintaan: 7 hari; kategori layanan tim yang dominan 14 hari (aturan dipasang belakangan → menimpa)
ensure_rule('SLA BPS permintaan', [('type', REQUEST)], official_sla('permintaan', CFG['permintaan']['bawaan']['target'], SLA_TTR))
long = CFG['permintaan']['14_hari']
ttr14 = official_sla('permintaan', long['target'], SLA_TTR)
categories = {}
for c in get('ITILCategory'):
    categories.setdefault(c['name'], c['id'])
    categories.setdefault(c['completename'], c['id'])
for category in long['kategori_glpi']:
    if category not in categories:
        print(f'Info: kategori "{category}" belum ada di katalog GLPI; SLA 14 hari dipasang saat kategori dibuat (jalankan ulang)')
        continue
    ensure_rule(f'SLA BPS permintaan 14 hari · {category}', [('type', REQUEST), ('itilcategories_id', categories[category])], ttr14)

# Aturan versi sebelumnya (angka asumsi) dinonaktifkan, tidak dihapus
for name, rule in rules.items():
    if (name in LEGACY_RULES or name.startswith('SLA layanan: ')) and rule.get('is_active'):
        s.put(f'{B}/RuleTicket/{rule["id"]}', data=json.dumps({'input': {'id': rule['id'], 'is_active': 0}}))
        print(f'Aturan lama "{name}" dinonaktifkan')

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

# T23 (5.1, akar masalah "notifikasi hanya sekali"): balasan/tindak lanjut pemohon sampai ke teknisi & grup yang
# ditugaskan (bawaan GLPI "New followup"), email + browser
ensure_notification('Ticket', 'add_followup', [(USER_TYPE, ASSIGN_TECH), (USER_TYPE, ASSIGN_GROUP)])
print('Notifikasi "New followup": + teknisi & grup yang ditugaskan; email + browser')

# T9: pola insiden baru = Problem baru yang ditugaskan ke grup Operator (plugin PatternDetector) → peringatan dini
ensure_notification('Problem', 'new', [(USER_TYPE, ASSIGN_GROUP)] + operator_target)
print(f'Notifikasi "New problem" (pola insiden): grup yang ditugaskan & grup {OPERATOR_GROUP}; email + browser')
