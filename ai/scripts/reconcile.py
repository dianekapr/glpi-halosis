"""FR-10: laporan rekonsiliasi migrasi data history tiket → reports/rekonsiliasi.md.

Menjalankan pembersihan & penyamaran yang sama dengan prepare_data.py (AI-1), lalu menghitung:
- baris sumber, berhasil diproses, gagal (per kategori alasan);
- ditandai tidak lengkap (tanpa deskripsi / tim / solusi, urutan tanggal tidak valid) dan duplikat;
- jumlah nilai yang disamarkan per jenis (email, NIP, NIK, telepon, rahasia, nama);
- rincian per bulan (tanggal dibuka) dan per tim;
- banding ekspor lama vs baru (baris, tiket hilang/baru, perubahan status & kolom teks, hasil SLA berimputasi).

Laporan HANYA berisi angka, bulan, dan nama tim. Tidak ada isi tiket, nama orang, atau nilai yang disamarkan.
Tidak menulis ulang data/processed/ (itu tugas prepare_data.py).

Pakai (dari folder induk proyek):  .venv/bin/python ai/scripts/reconcile.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from halosis_ai import privacy  # noqa: E402
from prepare_data import (  # noqa: E402
    INCOMPLETE_REASONS, RAW, RAW_OLD, ROOT, USER_COLUMNS, clean, common_words, incomplete_flags, load, text_columns,
)

REPORT = ROOT / 'reports/rekonsiliasi.md'
NO_TEAM = '(tanpa tim)'
UNKNOWN_STATES = {'UNKNOWN / STATE NOT FOUND'}
# Kolom pengenal, bukan teks bebas; kolom turunan (messages, solusi) tidak dihitung agar tidak ganda
NOT_FREE_TEXT = {'ticket_type', 'ticket_number', 'assignment_group_name', 'state_name', 'messages', 'solusi', 'solusi_sumber'}

PLACEHOLDERS = {
    'Email': privacy.EMAIL,
    'NIP': privacy.NIP,
    'NIK': privacy.NIK,
    'Telepon': privacy.PHONE,
    'Rahasia (password/PIN/OTP)': privacy.SECRET,
    'Nama': privacy.NAME,
}

FAIL_REASONS = {
    'no_number': 'Tanpa nomor tiket',
    'bad_date': 'Tanggal dibuka tidak valid',
    'unknown_state': 'Status tidak dikenal (tidak bisa dipetakan ke status GLPI)',
    'residual_pii': 'Masih memuat pola data pribadi setelah penyamaran',
}
DUPLICATE_REASONS = {
    'dup_number': 'Nomor tiket ganda',
    'dup_content': 'Isi identik dari pemohon yang sama (judul + deskripsi)',
}


def blank(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype('string').str.strip().fillna('') == '')


def residual_rows(cleaned: pd.DataFrame, raw: pd.DataFrame) -> pd.Series:
    """Baris yang teksnya MASIH memuat pola data pribadi setelah penyamaran (seharusnya 0)."""
    names = pd.concat([raw[c] for c in USER_COLUMNS]).dropna().astype(str)
    patterns = [privacy._EMAIL, privacy._NIP, privacy._NIP_OLD, privacy._NIK, privacy._PHONE,
                privacy.build_name_pattern(names), privacy.build_name_token_pattern(names, common_words(raw))]
    patterns = [p for p in patterns if p is not None]

    def leaks(text: object) -> bool:
        if not isinstance(text, str):
            return False
        if any(p.search(text) for p in patterns):
            return True
        return any(not m.group('value').startswith(privacy.SECRET) and any(ch.isalnum() for ch in m.group('value'))
                   for m in privacy._SECRET.finditer(text))

    cols = [c for c in text_columns(cleaned) if c not in NOT_FREE_TEXT]
    return cleaned[cols].map(leaks).any(axis=1)


def placeholder_counts(frame: pd.DataFrame) -> dict[str, int]:
    cols = [c for c in text_columns(frame) if c not in NOT_FREE_TEXT]
    texts = pd.concat([frame[c].dropna().astype(str) for c in cols], ignore_index=True)
    return {label: int(texts.str.count(token.replace('[', r'\[').replace(']', r'\]')).sum())
            for label, token in PLACEHOLDERS.items()}


def flags(raw: pd.DataFrame, cleaned: pd.DataFrame) -> pd.DataFrame:
    f = pd.DataFrame(index=raw.index)
    f['no_number'] = blank(raw['ticket_number'])
    f['bad_date'] = pd.to_datetime(raw['opened'], errors='coerce').isna()
    f['unknown_state'] = raw['state_name'].isin(UNKNOWN_STATES)
    f['residual_pii'] = residual_rows(cleaned, raw)
    f['failed'] = f[list(FAIL_REASONS)].any(axis=1)

    # Aturan kelengkapan sama dengan kolom `tidak_lengkap` di tickets_clean.parquet (prepare_data.py)
    f = f.join(incomplete_flags(cleaned))
    f['incomplete'] = ~f['failed'] & f[list(INCOMPLETE_REASONS)].any(axis=1)

    numbered = ~f['no_number']
    f['dup_number'] = numbered & raw['ticket_number'].duplicated(keep='first')
    content = (cleaned['requester_pid'].astype('string').fillna('') + '\x1f'
               + cleaned['short_description'].astype('string').str.strip().str.lower().fillna('') + '\x1f'
               + cleaned['description'].astype('string').str.strip().str.lower().fillna(''))
    f['dup_content'] = ~f['dup_number'] & cleaned['requester_pid'].notna() & content.duplicated(keep='first')
    f['duplicate'] = ~f['failed'] & f[list(DUPLICATE_REASONS)].any(axis=1)
    f['processed'] = ~f['failed']
    return f


def breakdown(f: pd.DataFrame, key: pd.Series) -> pd.DataFrame:
    table = f.assign(_key=key.values).groupby('_key').agg(
        sumber=('failed', 'size'), berhasil=('processed', 'sum'), gagal=('failed', 'sum'),
        tidak_lengkap=('incomplete', 'sum'), duplikat=('duplicate', 'sum'))
    return table.astype(int)


def md_table(table: pd.DataFrame, first: str) -> list[str]:
    head = [first, 'Sumber', 'Berhasil', 'Gagal', 'Tidak lengkap', 'Duplikat']
    lines = ['| ' + ' | '.join(head) + ' |', '| --- |' + ' ---: |' * (len(head) - 1)]
    for key, row in table.iterrows():
        lines.append(f'| {key} | ' + ' | '.join(f'{v:,}'.replace(',', '.') for v in row) + ' |')
    total = table.sum()
    lines.append('| **Total** | ' + ' | '.join(f'**{v:,}**'.replace(',', '.') for v in total) + ' |')
    return lines


def num(n: int) -> str:
    return f'{n:,}'.replace(',', '.')


def pct(part: int, whole: int) -> str:
    return f'{part / max(whole, 1) * 100:.2f}%'.replace('.', ',')


COMPARED_TEXT = ['short_description', 'description', 'assignment_group_name', 'all_conversations', 'close_notes',
                 'resolution']


def compare_exports(old: pd.DataFrame, new: pd.DataFrame) -> dict:
    """Banding ekspor lama vs baru per nomor tiket: hanya hitungan, nama status, dan jenis tiket."""
    kind = lambda df: df['ticket_type'].astype('string').str.upper().str[:3].fillna('?')  # noqa: E731
    old_keys, new_keys = set(old['ticket_number'].dropna()), set(new['ticket_number'].dropna())
    only_old = old[old['ticket_number'].isna() | old['ticket_number'].isin(old_keys - new_keys)]
    only_new = new[new['ticket_number'].isna() | new['ticket_number'].isin(new_keys - old_keys)]
    both = old.merge(new, on='ticket_number', suffixes=('_lama', '_baru'))
    changed = both['state_name_lama'].astype('string') != both['state_name_baru'].astype('string')
    transitions = both[changed].groupby(['state_name_lama', 'state_name_baru']).size().sort_values(ascending=False)
    text = {c: int((both[f'{c}_lama'].astype('string').fillna('') != both[f'{c}_baru'].astype('string').fillna('')).sum())
            for c in COMPARED_TEXT if f'{c}_lama' in both}
    return {
        'lama': len(old), 'baru': len(new), 'kolom_lama': old.shape[1], 'kolom_baru': new.shape[1],
        'hanya_lama': only_old.assign(_k=kind(only_old), _tanpa_nomor=only_old['ticket_number'].isna())
                              .groupby(['_k', '_tanpa_nomor']).size().to_dict(),
        'hanya_baru': kind(only_new).value_counts().to_dict(), 'sama': len(both),
        'status_berubah': int(changed.sum()), 'transisi': transitions.head(10).to_dict(), 'teks_berubah': text,
        'kolom_tambahan': [c for c in new.columns if c not in old.columns],
    }


def comparison_lines(c: dict, new: pd.DataFrame) -> list[str]:
    lost = '; '.join(f'{num(n)} {k}{" tanpa nomor tiket" if no_number else ""}'
                     for (k, no_number), n in c['hanya_lama'].items()) or '0'
    added = '; '.join(f'{num(n)} {k}' for k, n in c['hanya_baru'].items()) or '0'
    imputed = int((new.get('overall_sla_result_basis') == 'IMPUTED').sum()) if 'overall_sla_result_basis' in new else 0
    sla = new['overall_sla_result_extended'].value_counts() if 'overall_sla_result_extended' in new else pd.Series(dtype=int)
    return [
        '## Banding ekspor lama vs baru',
        '',
        f'Lama `data/raw/{RAW_OLD.name}` ({c["kolom_lama"]} kolom) vs baru `data/raw/{RAW.name}` ({c["kolom_baru"]} '
        'kolom). Pipeline memakai ekspor baru; dicocokkan per nomor tiket.',
        '',
        '| Ukuran | Jumlah |',
        '| --- | ---: |',
        f'| Baris lama / baru | {num(c["lama"])} / {num(c["baru"])} |',
        f'| Hanya di ekspor lama | {lost} |',
        f'| Hanya di ekspor baru | {added} |',
        f'| Nomor tiket di keduanya | {num(c["sama"])} |',
        f'| Status berubah | {num(c["status_berubah"])} ({pct(c["status_berubah"], c["sama"])}) |',
        *[f'| Kolom `{k}` berubah | {num(v)} |' for k, v in c['teks_berubah'].items()],
        f'| Hasil SLA keseluruhan berimputasi (DQR-04, kolom `sla_imputasi`) | {num(imputed)} |',
        '',
        'Perubahan status terbanyak (lama → baru); umumnya tiket yang masih berjalan saat ekspor lama lalu ditutup:',
        '',
        '| Lama | Baru | Tiket |',
        '| --- | --- | ---: |',
        *[f'| {a} | {b} | {num(n)} |' for (a, b), n in c['transisi'].items()],
        '',
        f'Hasil SLA keseluruhan versi diperluas (`overall_sla_result_extended`): '
        + ', '.join(f'{k} {num(int(v))}' for k, v in sla.items()) + '.',
        '',
        f'Kolom tambahan ekspor baru: {len(c["kolom_tambahan"])} (antara lain impact, urgency, priority, rating_*, '
        'SLA *_native/_final/_imputation_*).',
        '',
    ]


def write_report(raw: pd.DataFrame, f: pd.DataFrame, masked: dict[str, int], comparison: list[str] | None = None) -> None:
    months = pd.to_datetime(raw['opened'], errors='coerce').dt.strftime('%Y-%m').fillna('(tanggal tidak valid)')
    teams = raw['assignment_group_name'].astype('string').str.strip().replace('', pd.NA).fillna(NO_TEAM)
    by_team = breakdown(f, teams).sort_values('sumber', ascending=False)

    total, ok, failed = len(f), int(f['processed'].sum()), int(f['failed'].sum())
    lines = [
        '# Rekonsiliasi migrasi data history tiket (FR-10)',
        '',
        f'Dibuat `ai/scripts/reconcile.py` · {datetime.now():%Y-%m-%d %H:%M} · sumber `data/raw/{RAW.name}`',
        '',
        'Laporan ini hanya berisi angka, bulan, dan nama tim. Isi tiket, nama orang, dan nilai yang disamarkan '
        'tidak pernah ditampilkan.',
        '',
        '## Ringkasan',
        '',
        '| Ukuran | Jumlah |',
        '| --- | ---: |',
        f'| Baris sumber | {num(total)} |',
        f'| Berhasil diproses | {num(ok)} |',
        f'| Gagal | {num(failed)} |',
        f'| Ditandai tidak lengkap (dari yang berhasil) | {num(int(f["incomplete"].sum()))} |',
        f'| Duplikat (dari yang berhasil) | {num(int(f["duplicate"].sum()))} |',
        f'| Cek: sumber = berhasil + gagal | {"✓" if total == ok + failed else "✗"} |',
        '',
        '## Gagal per alasan',
        '',
        'Satu baris bisa punya lebih dari satu alasan. Baris gagal tetap ada di `tickets_clean.parquet` untuk '
        'analisis AS-IS, tetapi tidak layak dimigrasikan ke GLPI.',
        '',
        '| Alasan | Baris |',
        '| --- | ---: |',
        *[f'| {label} | {num(int(f[key].sum()))} |' for key, label in FAIL_REASONS.items()],
        '',
        '## Ditandai tidak lengkap',
        '',
        'Tetap diproses, tetapi perlu dilengkapi atau diperlakukan khusus (mis. tidak dipakai melatih model routing '
        'bila tanpa tim, tidak masuk pasangan masalah → solusi bila tanpa solusi).',
        '',
        '| Penanda | Baris |',
        '| --- | ---: |',
        *[f'| {label} | {num(int((f[key] & ~f["failed"]).sum()))} |' for key, label in INCOMPLETE_REASONS.items()],
        '',
        '## Duplikat',
        '',
        'Baris pertama dianggap asli; yang dihitung adalah salinan berikutnya.',
        '',
        '| Jenis | Baris |',
        '| --- | ---: |',
        *[f'| {label} | {num(int((f[key] & ~f["failed"]).sum()))} |' for key, label in DUPLICATE_REASONS.items()],
        '',
        '## Nilai yang disamarkan per jenis',
        '',
        'Jumlah kemunculan yang diganti penanda (mis. `[EMAIL]`) di kolom teks bebas, selisih keluaran terhadap sumber.',
        '',
        '| Jenis | Nilai disamarkan |',
        '| --- | ---: |',
        *[f'| {label} | {num(n)} |' for label, n in masked.items()],
        f'| **Total** | **{num(sum(masked.values()))}** |',
        '',
        f'Kolom nama pengguna ({", ".join(USER_COLUMNS)}) dihapus dan diganti ID samaran `*_pid`.',
        '',
        *(comparison or []),
        '## Per bulan (tanggal dibuka)',
        '',
        *md_table(breakdown(f, months).sort_index(), 'Bulan'),
        '',
        '## Per tim',
        '',
        *md_table(by_team, 'Tim'),
        '',
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text('\n'.join(lines), encoding='utf-8')


def main() -> None:
    raw = load()
    cleaned = clean(raw)
    f = flags(raw, cleaned)
    if int(f['residual_pii'].sum()):
        print('PERINGATAN: ada baris yang masih memuat pola data pribadi (lihat laporan, isi tidak ditampilkan).')

    before = placeholder_counts(raw[[c for c in cleaned.columns if c in raw.columns]])
    after = placeholder_counts(cleaned)
    masked = {k: after[k] - before[k] for k in PLACEHOLDERS}
    comparison = None
    if RAW_OLD.exists() and RAW_OLD != RAW:
        c = compare_exports(load(RAW_OLD), raw)
        comparison = comparison_lines(c, raw)
        print(f'Lama vs baru        : {c["lama"]} vs {c["baru"]}, hanya lama {c["hanya_lama"]}, '
              f'status berubah {c["status_berubah"]}')
    write_report(raw, f, masked, comparison)

    print(f'Baris sumber        : {len(f)}')
    print(f'Berhasil diproses   : {int(f["processed"].sum())}')
    print(f'Gagal               : {int(f["failed"].sum())} ' + str({k: int(f[k].sum()) for k in FAIL_REASONS}))
    print(f'Tidak lengkap       : {int(f["incomplete"].sum())} '
          + str({k: int((f[k] & ~f["failed"]).sum()) for k in INCOMPLETE_REASONS}))
    print(f'Duplikat            : {int(f["duplicate"].sum())} '
          + str({k: int((f[k] & ~f["failed"]).sum()) for k in DUPLICATE_REASONS}))
    print(f'Nilai disamarkan    : {masked}')
    print(f'Laporan             : {REPORT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
