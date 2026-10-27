"""AI-2: analisis awal (angka AS-IS) → reports/eda.md.

Membaca data/processed/tickets_clean.parquet (sudah disamarkan). Laporan hanya berisi angka agregat dan
label topik; sebelum ditulis, isinya dipindai ulang untuk memastikan tidak ada pola data pribadi.

Pakai (dari folder induk proyek):  .venv/bin/python ai/scripts/eda.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import privacy  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'data/processed/tickets_clean.parquet'
OUT = ROOT / 'reports/eda.md'

MONTHS = {1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Mei', 6: 'Jun', 7: 'Jul', 8: 'Agu', 9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Des'}
TOPICS = 40          # jumlah kelompok topik K-Means (yang dilaporkan: 20 terbesar)
SEED = 42

# Kata umum & penanda samaran yang tidak informatif untuk label topik
STOPWORDS = {
    'yang', 'dan', 'di', 'ke', 'dari', 'untuk', 'dengan', 'pada', 'ini', 'itu', 'ada', 'tidak', 'bisa', 'sudah',
    'belum', 'akan', 'saya', 'kami', 'mohon', 'bantuan', 'bantu', 'tolong', 'terima', 'kasih', 'terimakasih', 'pak',
    'bu', 'bapak', 'ibu', 'yth', 'ysh', 'selamat', 'pagi', 'siang', 'sore', 'malam', 'atas', 'nama', 'dalam', 'juga',
    'karena', 'agar', 'apakah', 'bagaimana', 'sebagai', 'oleh', 'atau', 'kepada', 'telah', 'hal', 'tersebut', 'kak',
    'email', 'nip', 'nik', 'telepon', 'rahasia', 'the', 'and', 'for', 'to', 'of', 'in', 'is', 'mas', 'mbak', 'min',
    'admin', 'halo', 'hai', 'izin', 'ijin', 'request', 'permintaan', 'permohonan', 'masalah', 'kendala',
    # Terlalu umum di semua tiket BPS / nama wilayah: membentuk kelompok campuran bila dipakai
    'bps', 'dapat', 'data', 'kabupaten', 'kota', 'provinsi', 'kab', 'prov', 'pusat', 'badan', 'pusat', 'statistik',
    'mohon', 'segera', 'sudah', 'masih', 'hari', 'tanggal', 'tahun', 'bulan', 'https', 'http', 'www', 'id', 'go',
}
MIXED_TEAM_SHARE = 0.25   # kelompok yang tim terbanyaknya < 25% dianggap campuran (bukan satu masalah)


def num(value: float, decimals: int = 0) -> str:
    """Format angka gaya Indonesia: 6.682 · 27,59"""
    text = f'{value:,.{decimals}f}'
    return text.replace(',', '_').replace('.', ',').replace('_', '.')


def pct(part: float, whole: float) -> str:
    return f'{num(part / whole * 100, 2)}%' if whole else '–'


def fmt_hours(hours: float) -> str:
    if pd.isna(hours):
        return '–'
    return f'{num(hours, 1)} jam' if hours < 48 else f'{num(hours / 24, 1)} hari'


def fmt_date(value: pd.Timestamp) -> str:
    return f'{value.day} {MONTHS[value.month]} {value.year}'


def table(headers: list[str], rows: list[list[object]]) -> str:
    lines = ['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join('---' for _ in headers) + ' |']
    lines += ['| ' + ' | '.join(str(c) for c in row) + ' |' for row in rows]
    return '\n'.join(lines)


def sla_rate(series: pd.Series) -> tuple[int, int, int, str]:
    passed = int((series == 'PASS').sum())
    breach = int((series == 'BREACH').sum())
    in_progress = int((series == 'IN PROGRESS').sum())
    return passed, breach, in_progress, pct(passed, passed + breach)


def normalize_title(text: object) -> str:
    text = re.sub(r'\[[A-Z]+\]', ' ', str(text or '').lower())
    text = re.sub(r'\d+', '#', text)
    return re.sub(r'[^\w#]+', ' ', text).strip()


def topics(df: pd.DataFrame) -> list[dict]:
    """Kelompok topik masalah (TF-IDF judul+deskripsi → K-Means), label = kata kunci dominan."""
    text = (df['short_description'].fillna('') + ' ' + df['short_description'].fillna('') + ' '
            + df['description'].fillna('')).map(normalize_title)
    vectorizer = TfidfVectorizer(
        token_pattern=r'(?u)\b[a-z][a-z]{2,}\b', stop_words=sorted(STOPWORDS), ngram_range=(1, 2),
        min_df=5, max_df=0.4, sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(text)
    model = KMeans(n_clusters=TOPICS, n_init=10, random_state=SEED).fit(matrix)
    terms = np.array(vectorizer.get_feature_names_out())

    result = []
    for cluster in range(TOPICS):
        members = df[model.labels_ == cluster]
        centroid = model.cluster_centers_[cluster]
        top_terms = [t for t in terms[centroid.argsort()[::-1]] if ' ' not in t][:4]
        team_share = members['assignment_group_name'].value_counts(normalize=True)
        result.append({
            'label': ', '.join(top_terms),
            'count': len(members),
            'inc': int((members['ticket_type'] == 'INC').sum()),
            'req': int((members['ticket_type'] == 'REQ').sum()),
            'team': team_share.index[0] if len(team_share) else '–',
            'team_share': team_share.iloc[0] if len(team_share) else 0.0,
        })
    return merge_similar(sorted(result, key=lambda r: r['count'], reverse=True))


def merge_similar(items: list[dict]) -> list[dict]:
    """Gabungkan topik yang ≥ 3 dari 4 kata kuncinya sama (mis. dua kelompok 'reset password akun')."""
    merged: list[dict] = []
    for item in items:
        terms = set(item['label'].split(', '))
        for target in merged:
            if len(terms & set(target['label'].split(', '))) >= 3:
                total = target['count'] + item['count']
                target['team_share'] = (target['team_share'] * target['count'] + item['team_share'] * item['count']) / total \
                    if target['team'] == item['team'] else max(target['team_share'], item['team_share'])
                target['count'], target['inc'], target['req'] = total, target['inc'] + item['inc'], target['req'] + item['req']
                break
        else:
            merged.append(dict(item))
    return sorted(merged, key=lambda r: r['count'], reverse=True)


def build(df: pd.DataFrame) -> tuple[str, dict]:
    n = len(df)
    df = df.assign(month=df['opened'].dt.month)
    solved = df[df['resolved'].notna()].copy()
    solved['hours'] = (solved['resolved'] - solved['opened']).dt.total_seconds() / 3600

    overall = sla_rate(df['overall_sla_result'])
    response = sla_rate(df['response_sla_result'])
    resolution = sla_rate(df['resolution_sla_result'])
    fulfillment = sla_rate(df['fulfillment_sla_result'])
    wrong = int((df['potential_wrong_routing'].fillna('NO') != 'NO').sum())

    sections = [
        '# Analisis awal history tiket HaloSIS (AS-IS)',
        '',
        f'Sumber: {num(n)} tiket dibuka {fmt_date(df["opened"].min())} – {fmt_date(df["opened"].max())} '
        '(`data/processed/tickets_clean.parquet`, sudah disamarkan). Dibuat oleh `ai/scripts/eda.py`; '
        'hanya angka agregat dan label topik, tanpa isi tiket.',
        '',
        '## Ringkasan',
        '',
        table(['Indikator', 'Nilai', 'Keterangan'], [
            ['Total tiket', num(n), f'REQ {num((df["ticket_type"] == "REQ").sum())} · INC {num((df["ticket_type"] == "INC").sum())}'],
            ['**Kepatuhan SLA keseluruhan**', f'**{overall[3]}**', f'PASS {num(overall[0])} ÷ (PASS + BREACH {num(overall[1])}); IN PROGRESS & tanpa bukti SLA dikecualikan'],
            ['Response SLA lolos', response[3], f'PASS {num(response[0])} ÷ {num(response[0] + response[1])}'],
            ['Resolution SLA lolos (INC)', resolution[3], f'PASS {num(resolution[0])} ÷ {num(resolution[0] + resolution[1])}'],
            ['Fulfillment SLA lolos (REQ)', fulfillment[3], f'PASS {num(fulfillment[0])} ÷ {num(fulfillment[0] + fulfillment[1])}'],
            ['Indikasi salah routing', pct(wrong, n), f'{num(wrong)} tiket dengan `potential_wrong_routing` ≠ NO'],
            ['Waktu selesai (median)', fmt_hours(solved['hours'].median()), f'{num(len(solved))} tiket ber-tanggal resolved; rata-rata {fmt_hours(solved["hours"].mean())}'],
        ]),
        '',
        f'Bila tiket IN PROGRESS dan tanpa bukti SLA ikut dihitung sebagai penyebut, kepatuhan SLA keseluruhan '
        f'menjadi {pct(overall[0], n)} ({num(overall[0])} ÷ {num(n)}).',
        '',
        '## Jumlah tiket per bulan',
        '',
        table(['Bulan', 'INC', 'REQ', 'Total'], [
            [f'{MONTHS[m]} 2026', int(((df.month == m) & (df.ticket_type == 'INC')).sum()),
             int(((df.month == m) & (df.ticket_type == 'REQ')).sum()), int((df.month == m).sum())]
            for m in sorted(df['month'].unique())
        ]),
        '',
        '## Status tiket',
        '',
        table(['Status', 'Jumlah', '%'], [[s, c, pct(c, n)] for s, c in df['state_name'].value_counts().items()]),
        '',
        '## SLA per jenis',
        '',
        table(['SLA', 'PASS', 'BREACH', 'IN PROGRESS', 'Lolos (PASS ÷ PASS+BREACH)'], [
            ['Keseluruhan', *overall],
            ['Response', *response],
            ['Resolution', *resolution],
            ['Fulfillment', *fulfillment],
        ]),
        '',
        '## Routing',
        '',
        table(['`potential_wrong_routing`', 'Jumlah', '%'],
              [[s, c, pct(c, n)] for s, c in df['potential_wrong_routing'].fillna('(kosong)').value_counts().items()]),
        '',
        table(['`routing_result`', 'Jumlah', '%'],
              [[s, c, pct(c, n)] for s, c in df['routing_result'].fillna('(kosong)').value_counts().items()]),
        '',
    ]

    # Per tim: volume, SLA, salah routing, waktu selesai
    team_rows = []
    for team, group in df.groupby('assignment_group_name'):
        o = sla_rate(group['overall_sla_result'])
        hours = solved.loc[solved['assignment_group_name'] == team, 'hours']
        team_rows.append([
            team, len(group), int((group['ticket_type'] == 'INC').sum()), int((group['ticket_type'] == 'REQ').sum()),
            o[3], pct(int((group['potential_wrong_routing'].fillna('NO') != 'NO').sum()), len(group)),
            fmt_hours(hours.mean()), fmt_hours(hours.median()),
        ])
    team_rows.sort(key=lambda r: r[1], reverse=True)
    sections += [
        f'## Per tim ({len(team_rows)} tim)',
        '',
        'Waktu selesai = `resolved − opened` (waktu kalender, bukan jam kerja), hanya tiket yang punya tanggal resolved.',
        '',
        table(['Tim', 'Tiket', 'INC', 'REQ', 'SLA lolos', 'Indikasi salah routing', 'Rata-rata selesai', 'Median selesai'], team_rows),
        '',
    ]

    all_topics = topics(df)
    mixed = [t for t in all_topics if t['team_share'] < MIXED_TEAM_SHARE]
    topic_rows = [t for t in all_topics if t['team_share'] >= MIXED_TEAM_SHARE][:20]
    sections += [
        '## 20 masalah paling sering (topik)',
        '',
        f'Judul tiket hampir selalu ditulis bebas ({num(df["short_description"].nunique())} judul berbeda dari {num(n)} tiket), '
        f'jadi tiket dikelompokkan berdasarkan kemiripan teks (TF-IDF judul+deskripsi, K-Means {TOPICS} kelompok). '
        'Label = kata kunci paling dominan di kelompok; kelompok dengan ≥ 3 kata kunci sama digabung. '
        f'Kelompok "campuran" (tim terbanyak < {MIXED_TEAM_SHARE:.0%}, isinya beragam) tidak diperingkat: '
        f'{len(mixed)} kelompok, {num(sum(t["count"] for t in mixed))} tiket.',
        '',
        table(['#', 'Topik (kata kunci)', 'Tiket', '%', 'INC', 'REQ', 'Tim terbanyak'], [
            [i, t['label'], t['count'], pct(t['count'], n), t['inc'], t['req'], f'{t["team"]} ({num(t["team_share"] * 100)}%)']
            for i, t in enumerate(topic_rows, start=1)
        ]),
        '',
    ]

    titles = df['short_description'].map(normalize_title)
    top_titles = titles[titles != ''].value_counts().head(20)
    sections += [
        '## Judul identik paling sering (pembanding)',
        '',
        'Setelah huruf kecil, angka → `#`, dan penanda samaran dihapus.',
        '',
        table(['Judul', 'Tiket'], [[t, c] for t, c in top_titles.items()]),
        '',
    ]

    summary = {
        'tiket': n, 'sla_keseluruhan': overall[3], 'response_sla': response[3], 'resolution_sla': resolution[3],
        'fulfillment_sla': fulfillment[3], 'salah_routing': pct(wrong, n), 'tim': len(team_rows),
    }
    return '\n'.join(sections), summary


def main() -> None:
    df = pd.read_parquet(SRC)
    report, summary = build(df)

    # Laporan hanya boleh berisi angka & label agregat: pindai pola data pribadi sebelum menulis
    leaks = {name: len(pattern.findall(report)) for name, pattern in {
        'email': privacy._EMAIL, 'nip': privacy._NIP, 'nik': privacy._NIK, 'telepon': privacy._PHONE,
        'password': privacy._SECRET,
    }.items()}
    if any(leaks.values()):
        raise SystemExit(f'Laporan memuat pola data pribadi, tidak ditulis: {leaks}')

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(report + '\n', encoding='utf-8')
    print(f'Ditulis: {OUT.relative_to(ROOT)}')
    for key, value in summary.items():
        print(f'  {key:18}: {value}')


if __name__ == '__main__':
    main()
