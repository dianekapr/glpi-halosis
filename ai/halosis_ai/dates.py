"""Tanggal ekspor history tiket.

Ekspor lama menyimpan tanggal sebagai datetime Excel; ekspor baru (220 kolom) sebagai angka serial Excel
(hari sejak 1899-12-30, pecahan = jam). Satu fungsi untuk keduanya, dipakai prepare_data, reconcile, dan skrip latih.
"""
from __future__ import annotations

import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

EXCEL_EPOCH = pd.Timestamp('1899-12-30')

# Kolom waktu yang dipakai pipeline (yang tidak ada di ekspor dilewati)
DATE_COLUMNS = (
    'opened', 'created', 'updated', 'resolved', 'closed', 'first_conversation_time', 'last_conversation_time',
    'first_operator_response_time', 'first_activity_time', 'last_activity_time', 'resolution_timestamp',
    'first_team_change_time', 'rating_complete_date',
)


def to_datetime(values) -> pd.Series:
    """Serial Excel (angka) / teks / datetime → datetime64, dibulatkan ke detik; tidak terbaca → NaT."""
    s = pd.Series(values)
    if is_datetime64_any_dtype(s):
        return s
    serial = pd.to_numeric(s, errors='coerce')
    text = pd.to_datetime(s.where(serial.isna()), errors='coerce')
    excel = (EXCEL_EPOCH + pd.to_timedelta(serial, unit='D')).dt.round('s')
    return text.where(serial.isna(), excel)


def convert_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Salinan df dengan semua DATE_COLUMNS yang ada diubah ke datetime."""
    out = df.copy()
    for col in DATE_COLUMNS:
        if col in out:
            out[col] = to_datetime(out[col]).values
    return out
