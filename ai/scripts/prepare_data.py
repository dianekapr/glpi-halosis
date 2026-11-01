"""AI-1: pembersihan & penyamaran data history tiket.

Masukan : data/raw/data_ticketing_202601_202608.xlsx — ekspor history versi baru (220 kolom: + impact/urgency/
          priority, rating, SLA diperluas); berisi data pribadi, tidak pernah di-commit. Tanggal serial Excel →
          datetime (halosis_ai.dates).
Keluaran: data/processed/tickets_clean.parquet  — kolom terpilih, teks tersamarkan, nama pengguna → ID samaran
          data/processed/qa_pairs.parquet       — masalah → solusi untuk tiket Closed/Resolved/Completed

Hanya angka ringkasan yang dicetak; isi teks (apalagi password) tidak pernah ditampilkan.

Pakai (dari folder induk proyek):  .venv/bin/python ai/scripts/prepare_data.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
from pandas.api.types import is_object_dtype, is_string_dtype

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from halosis_ai import dates, privacy  # noqa: E402
from halosis_ai.conversations import extract_solution, meaningful_note, split_conversation  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / 'data/raw'
# Ekspor versi baru (nama baku, lalu nama asli unduhan); versi lama hanya untuk rekonsiliasi (reconcile.py)
RAW_CANDIDATES = ('data_ticketing_202601_202608.xlsx', 'data ticketing (202601_202608).xlsx')
RAW = next((RAW_DIR / n for n in RAW_CANDIDATES if (RAW_DIR / n).exists()), RAW_DIR / RAW_CANDIDATES[0])
RAW_OLD = RAW_DIR / 'ticketing_history_202601_202608.xlsx'
OUT = ROOT / 'data/processed'

KEEP_PREFIXES = ('reassignment_', 'response_sla_')
KEEP = [
    'ticket_type', 'ticket_number', 'short_description', 'description', 'assignment_group_name', 'state_name',
    'opened', 'resolved', 'closed', 'all_conversations', 'close_notes', 'resolution', 'potential_wrong_routing',
    'routing_result', 'overall_sla_result', 'resolution_sla_name', 'resolution_sla_result', 'fulfillment_sla_result',
    # Versi baru: urgensi/dampak/prioritas (label model urgensi), kepuasan, SLA diperluas (baseline dashboard)
    'impact', 'urgency', 'priority', 'rating_value', 'overall_sla_result_extended', 'overall_sla_result_basis',
]
# Kolom pengguna: nama dihapus, ID diganti ID samaran
USER_COLUMNS = {
    'requester_name': 'requester_id',
    'assigned_to_name': 'assigned_to_id',
    'resolved_by_name': 'resolved_by',
    'closed_by_name': 'closed_by',
}
SOLVED_STATES = {'Closed', 'Resolved', 'Completed'}

# Data historis kurang lengkap (DQR-04) & urutan tanggal tidak valid (DQR-02): tetap diproses, tetapi ditandai
# di kolom `tidak_lengkap` + `alasan_tidak_lengkap` (dipakai juga oleh reconcile.py)
INCOMPLETE_REASONS = {
    'no_description': 'Tanpa deskripsi',
    'no_team': 'Tanpa tim (assignment group)',
    'no_solution': 'Selesai tanpa solusi yang bisa diambil',
    'bad_order': 'Urutan tanggal tidak valid (selesai/ditutup sebelum dibuka)',
}


def text_columns(df: pd.DataFrame) -> list[str]:
    """Kolom teks (pandas 3 memakai dtype 'str', versi lama 'object')."""
    return [c for c in df.columns if is_string_dtype(df[c]) or is_object_dtype(df[c])]


FREE_TEXT = ['short_description', 'description', 'all_conversations', 'resolution', 'close_notes']
COMMON_WORD_MIN = 5


def common_words(df: pd.DataFrame) -> set[str]:
    """Kata yang muncul berhuruf kecil ≥ COMMON_WORD_MIN kali di teks bebas: dianggap kata umum, bukan nama.

    Dihitung setelah email/HP/NIP disamarkan, dan kata yang menempel ke titik/garis bawah/@ (gaya username,
    mis. "budi.santoso") tidak dihitung, supaya nama yang sering muncul di username tidak dikira kata umum.
    """
    counts: dict[str, int] = {}
    word = re.compile(r'(?<![\w.@])[a-z]+(?![\w.@])')
    for col in FREE_TEXT:
        for text in df[col].dropna().astype(str):
            for w in word.findall(str(privacy.mask_text(text))):
                counts[w] = counts.get(w, 0) + 1
    return {w for w, n in counts.items() if n >= COMMON_WORD_MIN}


def name_patterns(df: pd.DataFrame, names: pd.Series) -> list:
    return [privacy.build_name_pattern(names), privacy.build_name_token_pattern(names, common_words(df))]


def load(path: Path = RAW) -> pd.DataFrame:
    return dates.convert_columns(pd.read_excel(path))


def pseudonymize(df: pd.DataFrame) -> pd.DataFrame:
    """ID pengguna asli → U00001 dst. (urutan ID terurut; pemetaan tidak disimpan)."""
    ids = pd.concat([df[c] for c in USER_COLUMNS.values()]).dropna().astype(str)
    mapping = {value: f'U{i:05d}' for i, value in enumerate(sorted(ids.unique()), start=1)}
    out = pd.DataFrame(index=df.index)
    for name_col, id_col in USER_COLUMNS.items():
        out[name_col.replace('_name', '_pid')] = df[id_col].astype('string').map(mapping)
    return out


def clean(df: pd.DataFrame) -> pd.DataFrame:
    keep = KEEP + [c for c in df.columns if c.startswith(KEEP_PREFIXES)]
    result = df[[c for c in dict.fromkeys(keep) if c in df.columns]].copy()

    # Nama pengguna dari kolom *_name ikut disamarkan di semua teks: nama lengkap, lalu bagian nama
    names = pd.concat([df[c] for c in USER_COLUMNS]).dropna().astype(str)
    name_pattern = name_patterns(df, names)

    text_cols = [c for c in text_columns(result) if c not in ('ticket_type', 'ticket_number', 'assignment_group_name', 'state_name')]
    if 'description' not in text_cols or 'all_conversations' not in text_cols:
        raise RuntimeError('Kolom teks tidak terdeteksi; penyamaran dibatalkan agar data mentah tidak tersimpan.')
    for col in text_cols:
        result[col] = result[col].map(lambda v: privacy.mask_text(v, name_pattern))

    result = pd.concat([result, pseudonymize(df)], axis=1)
    # Pengirim pesan terakhir = pemohon (ID asli dibandingkan di sini; ID tidak ikut disimpan)
    if 'last_conversation_user_id' in df:
        result['pesan_terakhir_pemohon'] = (df['last_conversation_user_id'].astype('string')
                                            == df['requester_id'].astype('string')).fillna(False).astype(bool)
    else:
        result['pesan_terakhir_pemohon'] = False

    # Percakapan → daftar pesan (JSON) + solusi
    messages = result['all_conversations'].map(split_conversation)
    result['messages'] = messages.map(lambda ms: json.dumps([{'waktu': m.time, 'teks': m.text} for m in ms], ensure_ascii=False))
    result['message_count'] = messages.map(len)
    resolved = dates.to_datetime(result['resolved']) if 'resolved' in result else pd.Series(pd.NaT, index=result.index)
    conv_solution = pd.Series([extract_solution(ms, None if pd.isna(r) else r, bool(last))
                               for ms, r, last in zip(messages, resolved, result['pesan_terakhir_pemohon'])],
                              index=result.index, dtype='object')
    close_note = result['close_notes'].map(meaningful_note)
    res_note = result['resolution'].map(meaningful_note)
    result['solusi'] = conv_solution.fillna(close_note).fillna(res_note)
    result['solusi_sumber'] = 'percakapan'
    result.loc[conv_solution.isna() & close_note.notna(), 'solusi_sumber'] = 'close_notes'
    result.loc[conv_solution.isna() & close_note.isna() & res_note.notna(), 'solusi_sumber'] = 'resolution'
    result.loc[result['solusi'].isna(), 'solusi_sumber'] = None
    # DQR-04: hasil SLA yang memakai komponen imputasi (bukan catatan asli ESTIM) ditandai, bukan dibuang
    result['sla_imputasi'] = result.get('overall_sla_result_basis', pd.Series(index=result.index, dtype='object')) == 'IMPUTED'

    flags = incomplete_flags(result)
    result['tidak_lengkap'] = flags.any(axis=1)
    result['alasan_tidak_lengkap'] = flags.apply(
        lambda row: '; '.join(INCOMPLETE_REASONS[k] for k, v in row.items() if v) or None, axis=1)
    return result


def _blank(series: pd.Series) -> pd.Series:
    return series.isna() | (series.astype('string').str.strip().fillna('') == '')


def incomplete_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Satu kolom boolean per alasan INCOMPLETE_REASONS untuk tiket yang sudah dibersihkan (kolom `solusi` ada)."""
    def date(col: str) -> pd.Series:
        return pd.to_datetime(df[col], errors='coerce') if col in df else pd.Series(pd.NaT, index=df.index)

    opened = date('opened')
    f = pd.DataFrame(index=df.index)
    f['no_description'] = _blank(df['description'])
    f['no_team'] = _blank(df['assignment_group_name'])
    f['no_solution'] = df['state_name'].isin(SOLVED_STATES) & df['solusi'].isna()
    f['bad_order'] = (date('resolved') < opened) | (date('closed') < opened)
    return f


def qa_pairs(clean_df: pd.DataFrame) -> pd.DataFrame:
    solved = clean_df[clean_df['state_name'].isin(SOLVED_STATES) & clean_df['solusi'].notna()]
    problem = (solved['short_description'].fillna('').astype(str).str.strip() + '\n'
               + solved['description'].fillna('').astype(str).str.strip()).str.strip()
    return pd.DataFrame({
        'ticket_number': solved['ticket_number'],
        'jenis': solved['ticket_type'],
        'tim': solved['assignment_group_name'],
        'tanggal': solved['opened'],
        'masalah': problem,
        'solusi': solved['solusi'],
        'solusi_sumber': solved['solusi_sumber'],
    }).reset_index(drop=True)


def residual_pii(df: pd.DataFrame, names: pd.Series, raw: pd.DataFrame) -> dict[str, int]:
    """Pindai ulang hasil: jumlah teks yang MASIH memuat pola data pribadi (harus 0).

    Kolom pengenal (nomor tiket, nama tim, status) bukan teks bebas dan tidak dipindai; kolom messages
    (JSON) dipindai per pesan agar tanda baca JSON tidak dikira nilai kata sandi.
    """
    skip = {'ticket_type', 'ticket_number', 'assignment_group_name', 'state_name'}
    texts = [df[c].dropna().astype(str) for c in text_columns(df) if c not in skip | {'messages'}]
    texts.append(pd.Series([m['teks'] for raw in df['messages'] for m in json.loads(raw)], dtype='object'))
    texts = [t for t in texts if len(t)]
    if not texts:
        raise RuntimeError('Tidak ada teks untuk dipindai.')
    cells = pd.concat(texts, ignore_index=True)
    name_pattern = privacy.build_name_pattern(names)
    token_pattern = privacy.build_name_token_pattern(names, common_words(raw))

    def unmasked_secret(text: str) -> bool:
        for match in privacy._SECRET.finditer(text):
            value = match.group('value')
            if value.startswith(privacy.SECRET):
                continue
            if any(ch.isalnum() for ch in value):
                return True
        return False

    return {
        'email': int(cells.str.contains(privacy._EMAIL).sum()),
        'nip': int(cells.str.contains(privacy._NIP).sum()),
        'nip_lama': int(cells.str.contains(privacy._NIP_OLD).sum()),
        'nik': int(cells.str.contains(privacy._NIK).sum()),
        'telepon': int(cells.str.contains(privacy._PHONE).sum()),
        'password_belum_tersamar': int(cells.map(unmasked_secret).sum()),
        'nama_pengguna': int(cells.map(lambda t: bool(name_pattern.search(t))).sum()) if name_pattern else 0,
        'bagian_nama_pengguna': int(cells.map(lambda t: bool(token_pattern.search(t))).sum()) if token_pattern else 0,
    }


def main() -> None:
    raw = load()
    OUT.mkdir(parents=True, exist_ok=True)
    tickets = clean(raw)
    pairs = qa_pairs(tickets)

    # Pindai ulang SEBELUM menulis: keluaran hanya disimpan bila tidak ada pola data pribadi tersisa
    names = pd.concat([raw[c] for c in USER_COLUMNS]).dropna().astype(str)
    residual = residual_pii(tickets, names, raw)
    if any(residual.values()):
        raise SystemExit(f'Penyamaran belum bersih, keluaran TIDAK disimpan: {residual}')
    tickets.to_parquet(OUT / 'tickets_clean.parquet', index=False)
    pairs.to_parquet(OUT / 'qa_pairs.parquet', index=False)

    text_cols = ['short_description', 'description', 'all_conversations', 'resolution', 'close_notes']
    raw_secret_tickets = int(raw[text_cols].map(privacy.contains_secret_value).any(axis=1).sum())

    print(f'Tiket dibaca            : {len(raw)} ({raw.shape[1]} kolom)')
    print(f'tickets_clean.parquet   : {len(tickets)} baris, {tickets.shape[1]} kolom')
    print(f'Kolom nama pengguna dihapus: {", ".join(USER_COLUMNS)} → *_pid')
    print(f'Tiket mentah berisi pola kata sandi bernilai: {raw_secret_tickets} (nilai tidak ditampilkan)')
    print(f'Total pesan percakapan  : {int(tickets["message_count"].sum())}')
    print(f'Tiket dengan solusi     : {int(tickets["solusi"].notna().sum())} '
          f'(sumber: {tickets["solusi_sumber"].value_counts().to_dict()})')
    print(f'Hasil SLA berimputasi   : {int(tickets["sla_imputasi"].sum())} (DQR-04, kolom sla_imputasi)')
    print(f'Ditandai tidak lengkap  : {int(tickets["tidak_lengkap"].sum())} '
          + str({k: int(v) for k, v in incomplete_flags(tickets).sum().items()}))
    print(f'qa_pairs.parquet        : {len(pairs)} pasangan (status {sorted(SOLVED_STATES)})')
    print(f'  per jenis             : {pairs["jenis"].value_counts().to_dict()}')
    print(f'  panjang solusi (kata) : median {int(pairs["solusi"].str.split().str.len().median())}')
    print(f'Sisa pola data pribadi di keluaran (harus 0): {residual}')


if __name__ == '__main__':
    main()
