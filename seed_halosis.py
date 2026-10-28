"""Isi GLPI dengan data contoh HaloSIS (tim, kategori, pengguna, SLA, tiket, knowledge base, masalah).

Pakai:  pip install requests
        python seed_halosis.py                      # default http://localhost:8080
        python seed_halosis.py http://localhost:8080
Syarat: API sudah aktif dan role HaloSIS sudah diterapkan (README langkah 3-4):
        php bin/console plugins:halosis:setup-roles

Aman dijalankan berulang: tim, kategori, pengguna (beserta tim & status ketua tim), dan SLA dicari dulu menurut
nama lalu dibuat bila belum ada. Tiket, tindak lanjut, artikel KB, dan masalah contoh hanya dibuat pada run
pertama (penanda: tiket contoh pertama sudah ada).
"""
import json, sys
import requests

BASE = (sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8080').rstrip('/')
B = BASE + '/apirest.php'
s = requests.Session()
r = s.get(B + '/initSession', auth=('glpi', 'glpi'))
if r.status_code != 200:
    raise SystemExit(f'Gagal login ke API ({r.status_code}): {r.text[:200]}\nCek: API aktif & login lewat kredensial diizinkan.')
tok = r.json()['session_token']
s.headers.update({'Session-Token': tok, 'Content-Type': 'application/json'})

# Profil GLPI per role HaloSIS (nama diatur oleh perintah plugins:halosis:setup-roles)
P = {p['name']: p['id'] for p in s.get(B + '/Profile', params={'range': '0-100'}).json()}
ROLES = ['Pegawai', 'Operator', 'Tim Teknis', 'Manajemen', 'Knowledge Manager', 'Administrator', 'Super-Admin']
if missing := [n for n in ROLES if n not in P]:
    raise SystemExit(f'Profil belum ada: {", ".join(missing)}.\n'
                     'Jalankan dulu: docker compose exec glpi php bin/console plugins:halosis:setup-roles --allow-superuser')
s.post(B + '/changeActiveProfile', json={'profiles_id': P['Super-Admin']})

def add(it, data):
    r = s.post(f'{B}/{it}', data=json.dumps({'input': data}))
    j = r.json()
    if isinstance(j, dict) and 'id' in j: return j['id']
    if isinstance(j, list) and j and isinstance(j[0], dict) and 'id' in j[0]: return j[0]['id']
    raise SystemExit(f'{it} gagal: {r.status_code} {r.text[:300]}')

_found = {}
def existing(it):
    """Nama → ID objek yang sudah ada (dibaca sekali per tipe)."""
    if it not in _found:
        rows = s.get(f'{B}/{it}', params={'range': '0-999'}).json()
        _found[it] = {r['name']: r['id'] for r in rows} if isinstance(rows, list) else {}
    return _found[it]

created = []
def ensure(it, data):
    """ID objek bernama data['name']; dibuat bila belum ada."""
    known = existing(it)
    if data['name'] not in known:
        known[data['name']] = add(it, data)
        created.append(it)
    return known[data['name']]

# Entitas: nama root
s.put(f'{B}/Entity/0', data=json.dumps({'input': {'id': 0, 'name': 'BPS'}}))

# Grup = Tim Teknis
G = {}
for n in ['Tim Aplikasi Statistik', 'Tim Jaringan', 'Tim Perangkat', 'Tim Identitas & Akses', 'Operator Service Desk']:
    G[n] = ensure('Group', {'name': n, 'is_assign': 1, 'is_requester': 0, 'is_notify': 1, 'is_recursive': 1})

# Kategori ITIL (service catalog)
C = {}
for parent, kids in {'Akun & Akses': ['SSO / Login', 'TTE', 'Hak akses folder'], 'Aplikasi Statistik': ['FASIH', 'SiPecut', 'SIMDASI', 'Email Dinas', 'Zoom / Konferensi'], 'Jaringan & Perangkat': ['Jaringan & VPN', 'Laptop / Perangkat', 'Printer']}.items():
    pid = ensure('ITILCategory', {'name': parent, 'is_recursive': 1})
    C[parent] = pid
    for k in kids:
        grp = {'Akun & Akses': 'Tim Identitas & Akses', 'Aplikasi Statistik': 'Tim Aplikasi Statistik'}.get(parent, 'Tim Jaringan' if k == 'Jaringan & VPN' else 'Tim Perangkat')
        C[k] = ensure('ITILCategory', {'name': k, 'itilcategories_id': pid, 'groups_id': G[grp], 'is_recursive': 1, 'is_helpdeskvisible': 1, 'is_incident': 1, 'is_request': 1})

# Pengguna & role (profile)
U = {}
USERS = [
    ('budi', 'Budi', 'Santoso', 'Pegawai', None), ('siti', 'Siti', 'Rahma', 'Pegawai', None), ('maya', 'Maya', 'Putri', 'Pegawai', None),
    ('rina', 'Rina', 'Wulandari', 'Operator', 'Operator Service Desk'), ('andi', 'Andi', 'Pratama', 'Tim Teknis', 'Tim Aplikasi Statistik'),
    ('yoga', 'Yoga', 'Saputra', 'Tim Teknis', 'Tim Aplikasi Statistik'), ('fajar', 'Fajar', 'Nugroho', 'Tim Teknis', 'Tim Identitas & Akses'),
    ('dedi', 'Dedi', 'Kurniawan', 'Tim Teknis', 'Tim Jaringan'), ('sri', 'Sri', 'Handayani', 'Manajemen', None),
    ('lina', 'Lina', 'Marlina', 'Knowledge Manager', None),
    ('dimas', 'Dimas', 'Aditya', 'Administrator', None),  # UC-10 Mengonfigurasi Platform ITSM
    # Ketua tim: Tim Teknis yang juga supervisor grup → penerima "atasan" peringatan risiko SLA (BR-02)
    ('hendra', 'Hendra', 'Wijaya', 'Tim Teknis', 'Tim Aplikasi Statistik'), ('agus', 'Agus', 'Setiawan', 'Tim Teknis', 'Tim Jaringan'),
    ('rudi', 'Rudi', 'Hermawan', 'Tim Teknis', 'Tim Perangkat'), ('wati', 'Wati', 'Susanti', 'Tim Teknis', 'Tim Identitas & Akses'),
]
TEAM_LEADERS = {'hendra', 'agus', 'rudi', 'wati'}
for login, fn, ln, role, grp in USERS:
    prof = P[role]
    is_new = login not in existing('User')
    uid = ensure('User', {'name': login, 'firstname': fn, 'realname': ln, 'password': 'halosis', 'password2': 'halosis', 'is_active': 1, 'profiles_id': prof, '_useremails': {'-1': f'{login}@bps.go.id'}})
    U[login] = uid
    if is_new:
        add('Profile_User', {'users_id': uid, 'profiles_id': prof, 'entities_id': 0, 'is_recursive': 1})
        # GLPI otomatis menambahkan profil default (Pegawai) ke pengguna baru; satu pengguna = satu role HaloSIS
        kept = False
        for pu in s.get(f'{B}/User/{uid}/Profile_User').json():
            if pu['profiles_id'] == prof and not kept:
                kept = True
            else:
                s.delete(f'{B}/Profile_User/{pu["id"]}')
    if grp:
        manager = int(login in TEAM_LEADERS)
        link = next((l for l in s.get(f'{B}/User/{uid}/Group_User').json() or []
                     if isinstance(l, dict) and l.get('groups_id') == G[grp]), None)
        if link is None:
            add('Group_User', {'users_id': uid, 'groups_id': G[grp], 'is_manager': manager})
        elif int(link.get('is_manager') or 0) != manager:
            s.put(f'{B}/Group_User/{link["id"]}', data=json.dumps({'input': {'id': link['id'], 'is_manager': manager}}))

# SLA per prioritas (time to resolve)
slm = ensure('SLM', {'name': 'SLA HaloSIS', 'calendars_id': 1})
SLA = {}
for nama, n, unit in [('Kritis · 4 jam', 4, 'hour'), ('Tinggi · 6 jam', 6, 'hour'), ('Sedang · 1 hari', 1, 'day'), ('Rendah · 3 hari', 3, 'day')]:
    SLA[nama.split(' ')[0]] = ensure('SLA', {'name': nama, 'slms_id': slm, 'type': 0, 'number_time': n, 'definition_time': unit, 'calendars_id': 1})

# Data transaksi contoh (tiket, KB, masalah): hanya pada run pertama
FIRST_TICKET = 'FASIH tidak bisa sinkron data, error 502'
seeded = FIRST_TICKET in existing('Ticket')
if not seeded:
    # Tiket (status: 1 Baru, 2 Diproses-ditugaskan, 3 Diproses-direncanakan, 4 Pending, 5 Selesai/Solved, 6 Ditutup)
    PRIO = {'Kritis': 5, 'Tinggi': 4, 'Sedang': 3, 'Rendah': 2}
    TICKETS = [
        ('FASIH tidak bisa sinkron data, error 502', 'Sejak Minggu, 25 Okt, FASIH di tablet saya gagal sinkron dengan pesan "Sinkronisasi gagal (502)". Tiga rekan satu tim mengalami hal sama.', 1, 'FASIH', 'Tinggi', 'budi', 'Tim Aplikasi Statistik', 'andi', 5),
        ('Tidak bisa login SSO sejak pagi', 'Login SSO gagal dengan pesan "invalid token". Sudah ganti browser dan hapus cache.', 1, 'SSO / Login', 'Kritis', 'siti', None, None, 1),
        ('Minta akses folder bersama Subdit Neraca', 'Butuh akses baca-tulis ke folder bersama Subdit Neraca untuk penyusunan publikasi.', 2, 'Hak akses folder', 'Sedang', 'budi', None, None, 1),
        ('Laptop mati total setelah update', 'Laptop tidak menyala sejak update Windows semalam.', 1, 'Laptop / Perangkat', 'Tinggi', 'maya', None, None, 1),
        ('Zoom tidak bisa share screen', 'Share screen di Zoom dinas hanya menampilkan layar hitam.', 1, 'Zoom / Konferensi', 'Sedang', 'maya', 'Tim Aplikasi Statistik', 'andi', 2),
        ('VPN putus setiap 10 menit', 'VPN kantor terputus berulang setiap ±10 menit saat bekerja dari rumah.', 1, 'Jaringan & VPN', 'Tinggi', 'budi', 'Tim Jaringan', 'dedi', 4),
        ('Gagal login SSO', 'Tidak bisa masuk SSO, pesan "invalid token".', 1, 'SSO / Login', 'Kritis', 'siti', 'Tim Identitas & Akses', 'fajar', 2),
        ('SiPecut error saat ajukan cuti tahunan', 'Tombol "Ajukan" tidak merespons, muncul error 500.', 1, 'SiPecut', 'Sedang', 'budi', 'Tim Aplikasi Statistik', None, 2),
        ('Dashboard SIMDASI tidak memuat grafik', 'Halaman dashboard hanya menampilkan tabel, grafik tidak muncul.', 1, 'SIMDASI', 'Rendah', 'maya', 'Tim Aplikasi Statistik', 'yoga', 3),
        ('Permintaan laptop pengganti', 'Laptop lama rusak permanen, perlu unit pengganti untuk kegiatan Sensus.', 2, 'Laptop / Perangkat', 'Sedang', 'budi', 'Tim Perangkat', None, 2),
        ('Email dinas tidak bisa kirim lampiran besar', 'Lampiran 15 MB selalu gagal terkirim dari email dinas.', 2, 'Email Dinas', 'Sedang', 'budi', 'Tim Aplikasi Statistik', 'andi', 2),
        ('Lupa password SSO', 'Tidak bisa masuk karena lupa kata sandi.', 1, 'SSO / Login', 'Rendah', 'budi', 'Tim Identitas & Akses', 'fajar', 6),
    ]
    T = {}
    for judul, isi, typ, cat, prio, req, grp, tech, status in TICKETS:
        data = {'name': judul, 'content': f'<p>{isi}</p>', 'type': typ, 'itilcategories_id': C[cat], 'priority': PRIO[prio], 'urgency': PRIO[prio], 'impact': 3,
                'slas_id_ttr': SLA[prio], '_users_id_requester': U[req]}
        if grp: data['_groups_id_assign'] = G[grp]
        if tech: data['_users_id_assign'] = U[tech]
        tid = add('Ticket', data)
        T[judul] = tid
        if status != 1 and status != 2:
            s.put(f'{B}/Ticket/{tid}', data=json.dumps({'input': {'id': tid, 'status': status if status != 5 else 2}}))

    def fu(tid, user_login, teks, private=0):
        add('ITILFollowup', {'itemtype': 'Ticket', 'items_id': tid, 'content': f'<p>{teks}</p>', 'is_private': private, 'users_id': U[user_login]})

    t = T['FASIH tidak bisa sinkron data, error 502']
    fu(t, 'andi', 'Terima kasih laporannya, Pak Budi. Kami sedang cek server sinkronisasi wilayah Anda.')
    fu(t, 'andi', 'Node sinkronisasi Semarang mengembalikan 502 sejak Minggu 21.00. Cek log load balancer.', 1)
    fu(t, 'budi', 'Baik, ditunggu. Pencacahan Susenas harus terkirim hari ini.')
    add('TicketTask', {'tickets_id': t, 'content': '<p>Restart layanan fasih-sync di node regional DIY dan verifikasi antrean data tertunda.</p>', 'state': 2, 'actiontime': 1800, 'users_id_tech': U['andi']})
    add('ITILSolution', {'itemtype': 'Ticket', 'items_id': t, 'content': '<p>Server sinkronisasi FASIH wilayah Jawa Tengah–DIY sudah dipulihkan pukul 10.32. Silakan buka FASIH lalu tekan <b>Coba sinkron ulang</b>.</p>', 'solutiontypes_id': 0})

    t = T['VPN putus setiap 10 menit']
    fu(t, 'dedi', 'Boleh kirim versi aplikasi VPN yang terpasang dan tangkapan layar saat koneksi putus?')
    fu(t, 'budi', 'Versi aplikasi VPN saya 4.2.1, tangkapan layar terlampir.')

    # Knowledge base
    KC = {}
    for n in ['Akun & SSO', 'FASIH & aplikasi survei', 'Jaringan & VPN', 'Laptop & perangkat', 'Email Dinas']:
        KC[n] = add('Glpi%5CForm%5CCategory', {'name': n})  # GLPI 11+: kategori artikel = kategori form
    KB = [
        ('Reset password SSO BPS', 'Akun & SSO', 1, '<p>Buka portal akun BPS, pilih <b>Lupa password</b>, masukkan NIP, lalu ikuti tautan yang dikirim ke email dinas.</p>'),
        ('FASIH: sinkronisasi gagal', 'FASIH & aplikasi survei', 1, '<p>Gunakan panduan ini jika FASIH menampilkan pesan "Sinkronisasi gagal".</p><ol><li>Pastikan tablet terhubung ke internet.</li><li>Tutup FASIH sepenuhnya, lalu buka lagi.</li><li>Pengaturan › Sinkronisasi › Coba sinkron ulang.</li><li>Perbarui FASIH ke versi terbaru.</li></ol><p><b>Jangan hapus aplikasi FASIH</b>, data yang belum tersinkron bisa hilang.</p>'),
        ('Mengatasi VPN sering terputus', 'Jaringan & VPN', 1, '<p>Perbarui klien VPN ke versi 4.3, matikan mode hemat daya Wi-Fi, lalu sambung ulang.</p>'),
        ('Restart layanan sinkronisasi FASIH (internal)', 'FASIH & aplikasi survei', 0, '<ol><li>Masuk ke konsol node sinkronisasi wilayah.</li><li>Cek status layanan <code>fasih-sync</code>.</li><li>Restart layanan, tunggu status healthy.</li><li>Verifikasi antrean data tertunda berkurang.</li></ol>'),
        ('Lampiran email lebih dari 10 MB', 'Email Dinas', 1, '<p>Lampiran di atas 10 MB ditolak server. Unggah ke Drive BPS lalu bagikan tautannya.</p>'),
    ]
    for judul, kat, faq, isi in KB:
        kid = add('KnowbaseItem', {'name': judul, 'answer': isi, 'is_faq': faq, 'users_id': U['lina'], 'forms_categories_id': KC[kat], 'is_recursive': 1})
        add('Entity_KnowbaseItem', {'knowbaseitems_id': kid, 'entities_id': 0, 'is_recursive': 1})

    # Problem = pola insiden
    pid = add('Problem', {'name': 'Pola insiden: Gagal login SSO (DIY–Jateng)', 'content': '<p>15 tiket serupa dalam 1 jam dari 6 satker. Kemiripan 0,91. Terdeteksi AI 08.05.</p>', 'priority': 5, 'urgency': 5, 'impact': 4, 'itilcategories_id': C['SSO / Login'], '_groups_id_assign': G['Tim Identitas & Akses']})
    for j in ['Tidak bisa login SSO sejak pagi', 'Gagal login SSO']:
        add('Problem_Ticket', {'problems_id': pid, 'tickets_id': T[j]})

if seeded:
    print(f'Data contoh sudah ada; tiket/KB/masalah tidak dibuat ulang. Objek baru: {len(created)}. Buka {BASE}')
else:
    print(f'Selesai: {len(T)} tiket, {len(KB)} artikel, {len(USERS)} pengguna. Buka {BASE}')
s.get(B + '/killSession')
