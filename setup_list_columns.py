"""Kolom default yang ringkas untuk daftar GLPI yang dipakai role HaloSIS (Display preferences, tanpa kode).

GLPI selalu menampilkan kolom ID & nama/judul; daftar di bawah adalah kolom TAMBAHANNYA, urut kiri → kanan.
Preferensi tampilan GLPI berlaku per itemtype (dan per pengguna), BUKAN per URL pencarian, sehingga:
- "Antrean validasi" & "Semua tiket" (Operator) memakai kolom Ticket global yang sama;
- "Tiket saya & tim" memakai kolom pribadi yang dipasang untuk setiap pengguna berprofil Tim Teknis;
- "Laporan saya" (Pegawai) memakai kolom Ticket antarmuka Helpdesk.
Urutan default antrean (waktu penyelesaian terdekat dulu) diatur di URL menu (plugin, src/RoleMenu.php).
Daftar aturan (Workflow & aturan) tidak memakai mesin pencarian GLPI, jadi kolomnya tetap bawaan dan tidak diatur di sini.

Aman dijalankan berulang: kolom tiap daftar ditulis ulang persis seperti di bawah. Pengguna tetap bisa
mengubah kolomnya sendiri (ikon "pilih kolom"); kolom pribadi Tim Teknis ditimpa saat skrip dijalankan lagi.

Pakai (setelah seed_halosis.py):  python setup_list_columns.py [http://localhost:8080]
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

# itemtype → (antarmuka, [ID opsi pencarian]); nama kolom di komentar (label GLPI id_ID)
GLOBAL = {
    # Operator: antrean validasi & semua tiket. Tanpa "Tanggal buka" (dobel dengan Terakhir diperbarui)
    # dan tanpa "Teknisi" (Operator menugaskan ke tim).
    ('Ticket', 'central'): [12, 3, 7, 4, 8, 18, 19],      # Status, Prioritas, Kategori, Pemohon, Grup teknisi, Waktu untuk menyelesaikan, Terakhir diperbarui
    # Pegawai (Helpdesk, "Laporan saya"): progres laporan + sisa waktu SLA (UC-07 langkah 2)
    ('Ticket', 'helpdesk'): [12, 7, 18, 19],              # Status, Kategori, Waktu untuk menyelesaikan, Terakhir diperbarui
    # Masalah / pola insiden: tanpa Deskripsi (panjang) & Waktu untuk menyelesaikan (kosong untuk pola)
    ('Problem', 'central'): [12, 3, 7, 141, 15],          # Status, Prioritas, Kategori, Jumlah tiket, Tanggal buka
    # Knowledge Base: tanpa Parent article / Unsur terkait (kosong)
    ('KnowbaseItem', 'central'): [87, 8, 70, 9, 19],      # Kategori, FAQ, Pengguna (penulis), Tampilan, Terakhir diperbarui
    # Pengguna: tanpa Telepon & Lokasi (kosong)
    ('User', 'central'): [9, 34, 5, 20, 13, 8, 14],       # Nama depan, Nama belakang, Email, Profil (Entitas), Grup, Aktif, Terakhir login
    ('Group', 'central'): [70, 150, 12],                  # Manager (ketua tim), Jumlah pengguna, Bisa ditugaskan
    ('ITILCategory', 'central'): [71, 77, 74, 75, 3],     # Grup, Jumlah tiket, Terlihat untuk insiden, permintaan, antarmuka sederhana
    ('SLM', 'central'): [4],                              # Kalender
    ('SLA', 'central'): [8, 7, 5],                        # SLM, Tipe, Waktu
}
# Tim Teknis ("Tiket saya & tim"): grup sudah tersaring (tim sendiri) → ganti dengan Teknisi
TIM_TEKNIS_TICKET = [12, 3, 7, 4, 5, 18, 19]              # Status, Prioritas, Kategori, Pemohon, Teknisi, Waktu untuk menyelesaikan, Terakhir diperbarui


ALL = None


def apply(itemtype, interface, columns, users_id=0):
    global ALL
    if ALL is None:
        ALL = s.get(f'{B}/DisplayPreference', params={'range': '0-10000'}).json()
    current = sorted((r for r in ALL if isinstance(r, dict) and r['itemtype'] == itemtype
                      and r['users_id'] == users_id and r['interface'] == interface), key=lambda r: r['rank'])
    if [r['num'] for r in current] == columns:
        return False
    if current:
        s.delete(f'{B}/DisplayPreference', data=json.dumps({'input': [{'id': r['id']} for r in current], 'force_purge': True}))
    for rank, num in enumerate(columns, start=1):
        res = s.post(f'{B}/DisplayPreference', data=json.dumps({'input': {
            'itemtype': itemtype, 'num': num, 'rank': rank, 'users_id': users_id, 'interface': interface}}))
        if res.status_code not in (200, 201):
            raise SystemExit(f'{itemtype} kolom {num} gagal: {res.status_code} {res.text[:200]}')
    return True


for (itemtype, interface), columns in GLOBAL.items():
    changed = apply(itemtype, interface, columns)
    print(f'{itemtype:13} {interface:8}: {columns} {"(diperbarui)" if changed else "(sudah sesuai)"}')

teknis = [pu['users_id'] for pu in s.get(f'{B}/Profile/{P["Tim Teknis"]}/Profile_User', params={'range': '0-500'}).json() or []
          if isinstance(pu, dict)]
users = {u['id']: u['name'] for u in s.get(f'{B}/User', params={'range': '0-1000'}).json() if isinstance(u, dict)}
for uid in sorted(set(teknis)):
    changed = apply('Ticket', 'central', TIM_TEKNIS_TICKET, users_id=uid)
    print(f'Ticket (pribadi {users.get(uid, uid)}): {TIM_TEKNIS_TICKET} {"(diperbarui)" if changed else "(sudah sesuai)"}')

# UC-07 langkah 5: survei kepuasan GLPI untuk setiap tiket yang ditutup (entitas induk, diwarisi sub-entitas).
# inquest_config 1 = survei internal GLPI; rate 100% tiket; dikirim tanpa jeda; batas isi 0 = tanpa batas.
INQUEST = {'inquest_config': 1, 'inquest_rate': 100, 'inquest_delay': 0, 'inquest_duration': 0}
entity = s.get(f'{B}/Entity/0').json()
if all(entity.get(k) == v for k, v in INQUEST.items()):
    print('Survei kepuasan saat tiket ditutup: sudah aktif')
else:
    s.put(f'{B}/Entity/0', data=json.dumps({'input': {'id': 0, **INQUEST}}))
    print('Survei kepuasan saat tiket ditutup: diaktifkan (100% tiket, tanpa jeda)')

s.get(B + '/killSession')
