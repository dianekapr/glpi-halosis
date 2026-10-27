"""Penyamaran data pribadi pada teks tiket HaloSIS.

Dipakai sebelum data disimpan ke data/processed/ dan sebelum teks apa pun dikirim ke API eksternal.
Urutan penting: password lebih dulu (nilainya bisa berupa angka/email), lalu email, NIP, NIK, HP, nama.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

EMAIL = '[EMAIL]'
NIP = '[NIP]'
NIK = '[NIK]'
PHONE = '[TELEPON]'
SECRET = '[RAHASIA]'
NAME = '[NAMA]'

# Nilai setelah kata kunci kata sandi: "password: x", "pasw : x", "pwd=x", "kata sandi baru: x", "PIN: 1234".
_SECRET = re.compile(
    r'(?P<key>\b(?:pass(?:word|wd|wod|sword)?|pasw(?:ord)?|pswd|pwd|kata\s*sandi|sandi|pin|otp)'
    r'(?:\s+(?:baru|lama|awal|sementara|default|nya|saya|akun|email|sso|login))*)'
    r'(?P<sep>\s*(?:[:=]|adalah|yaitu|nya\s*:?)\s*)'
    r'(?P<value>[^\s,;|]+)',
    re.IGNORECASE,
)
_EMAIL = re.compile(r'[\w.+-]+@[\w-]+(?:\.[\w-]+)+')
# NIP 18 digit, ditulis rapat atau berkelompok "19870101 201001 1 001"
_NIP = re.compile(r'(?<!\d)(?:\d{18}|\d{8}[\s.-]?\d{6}[\s.-]?\d[\s.-]?\d{3})(?!\d)')
_NIK = re.compile(r'(?<!\d)\d{16}(?!\d)')
# Nomor HP Indonesia: 08xx / +628xx / 628xx, boleh berpemisah spasi/titik/strip
_PHONE = re.compile(r'(?<![\w+])(?:\+?62|0)\s?8\d(?:[\s.-]?\d){6,11}(?!\d)')
# Sapaan + nama: "Ysh. Bpk. Budi Santoso", "Yth Ibu Siti", "Pak Andi", "Bu Rina", "Mas Yoga"
_SALUTATION_NAME = re.compile(
    r'(?P<salut>\b(?:Ysh|Yth)\.?\s*(?:(?:Bpk|Bapak|Ibu|Bu|Sdr|Sdri|Saudara|Saudari)\.?\s*(?:/\s*(?:Ibu|Bu)\.?\s*)?)?'
    r'|\b(?:Bapak|Bpk\.?|Ibu|Pak|Bu|Mas|Mbak|Sdr\.?|Sdri\.?)\s+)'
    r'(?P<name>[A-Z][A-Za-z\'.-]+(?:\s+[A-Z][A-Za-z\'.-]+){0,3})'
)


def mask_text(text: object, names: Iterable[str] | None = None) -> object:
    """Samarkan satu teks. Nilai bukan string (NaN, angka, tanggal) dikembalikan apa adanya."""
    if not isinstance(text, str) or not text:
        return text
    out = _SECRET.sub(lambda m: f"{m.group('key')}{m.group('sep')}{SECRET}", text)
    out = _EMAIL.sub(EMAIL, out)
    out = _NIP.sub(NIP, out)
    out = _NIK.sub(NIK, out)
    out = _PHONE.sub(PHONE, out)
    out = _SALUTATION_NAME.sub(lambda m: f"{m.group('salut').rstrip()} {NAME}", out)
    if names is not None:
        out = mask_names(out, names)
    return out


def build_name_pattern(names: Iterable[str]) -> re.Pattern[str] | None:
    """Pola untuk nama lengkap pengguna (dari kolom *_name), terpanjang lebih dulu."""
    clean = sorted({n.strip() for n in names if isinstance(n, str) and len(n.strip()) >= 4}, key=len, reverse=True)
    if not clean:
        return None
    return re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(n) for n in clean) + r')(?!\w)', re.IGNORECASE)


def build_name_token_pattern(names: Iterable[str], common_words: set[str]) -> re.Pattern[str] | None:
    """Pola bagian nama (depan/tengah/belakang) berhuruf kapital, mis. "atas nama Budi", "user SANTOSO".

    Bagian nama yang juga kata umum di korpus (sering muncul berhuruf kecil, mis. "bintang") dikecualikan
    supaya kata biasa tidak ikut tersamar.
    """
    tokens = set()
    for name in names:
        if not isinstance(name, str):
            continue
        for part in re.split(r"[\s,.'-]+", name):
            if len(part) >= 3 and part.isalpha() and part.lower() not in common_words:
                tokens.add(part.capitalize())
                tokens.add(part.upper())
    if not tokens:
        return None
    return re.compile(r'(?<![\w\[])(?:' + '|'.join(re.escape(t) for t in sorted(tokens, key=len, reverse=True)) + r')(?![\w\]])')


def mask_names(text: str, names: Iterable[str] | re.Pattern[str] | list[re.Pattern[str] | None]) -> str:
    """Samarkan nama: daftar nama lengkap, satu pola, atau beberapa pola (dijalankan berurutan)."""
    if isinstance(names, list) and all(p is None or isinstance(p, re.Pattern) for p in names):
        patterns = names
    elif isinstance(names, re.Pattern):
        patterns = [names]
    else:
        patterns = [build_name_pattern(names)]
    for pattern in patterns:
        if pattern is not None:
            text = pattern.sub(NAME, text)
    return text


def contains_secret_value(text: object) -> bool:
    """Apakah teks memuat pola kata sandi berisi nilai (untuk menghitung, tanpa menampilkan nilainya)."""
    return isinstance(text, str) and _SECRET.search(text) is not None
