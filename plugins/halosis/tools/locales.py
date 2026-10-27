"""Periksa & kompilasi terjemahan plugin HaloSIS.

Mencari semua string ber-domain 'halosis' di kode PHP/Twig, melaporkan yang belum ada
di locales/*.po, lalu mengompilasi setiap .po menjadi .mo dengan msgfmt.

Pakai (dari folder plugin):  python3 tools/locales.py
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
# __('teks', 'halosis'), __s(...), _x('konteks', 'teks', 'halosis')
CALL = re.compile(r"""\b(?:__s?|_x)\(\s*(?:'[^']*'\s*,\s*)?'((?:[^'\\]|\\.)*)'\s*,\s*'halosis'""")
MSGID = re.compile(r'^msgid "(.*)"$', re.M)

used = set()
for path in list(ROOT.rglob('*.php')) + list(ROOT.rglob('*.twig')):
    for m in CALL.finditer(path.read_text(encoding='utf-8')):
        used.add(m.group(1).replace("\\'", "'"))

ok = True
for po in sorted((ROOT / 'locales').glob('*.po')):
    known = {m.replace('\\"', '"') for m in MSGID.findall(po.read_text(encoding='utf-8'))}
    missing = sorted(used - known)
    if missing:
        ok = False
        print(f'{po.name}: {len(missing)} string belum diterjemahkan')
        for s in missing:
            print(f'  msgid "{s}"')
    subprocess.run(['msgfmt', '--check', '-o', str(po.with_suffix('.mo')), str(po)], check=True)
    print(f'{po.name} → {po.with_suffix(".mo").name}')

sys.exit(0 if ok else 1)
