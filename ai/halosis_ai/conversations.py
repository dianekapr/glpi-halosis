"""Pecah kolom all_conversations dan ambil pesan solusi substantif.

Format: "YYYY-MM-DD HH:MM:SS | teks || YYYY-MM-DD HH:MM:SS | teks || ...". Tidak ada kolom pengirim,
jadi asal pesan disimpulkan dari isinya: template operator & salam dibuang per kalimat, permintaan
informasi dan ucapan singkat pegawai tidak dianggap solusi, pesan bercirikan petugas diutamakan.
Fungsi di sini bekerja pada teks yang SUDAH disamarkan.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_MESSAGE = re.compile(r'^\s*(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*\|\s*(.*)$', re.DOTALL)

# Kalimat template operator (tidak membawa solusi)
_TEMPLATE = re.compile(
    r'telah menghubungi halosis|terima ?kasih telah menghubungi|teruskan kepada tim|diteruskan (?:ke|kepada) tim'
    r'|bintang ?(?:5|lima)|keterlambatan respon|telah disampaikan (?:pada|kepada|ke) tim|akan (?:di ?)?eskalasi'
    r'|tiket (?:ini )?akan|sedang (?:kami )?(?:proses|tindaklanjuti|cek)|mohon (?:di)?tunggu|harap menunggu'
    r'|mohon kesediaan|isi(?:kan)? survei|survey|ketidaknyamanan|gangguan yang dialami'
    # Penutup baku (bukan isi solusi)
    r'|masih ada kendala|infokan kembali|hubungi kembali|perhatian dan kerja ?sama|maka tiket|tiket (?:akan )?(?:kami )?tutup'
    r'|tiket (?:ini )?(?:kami )?(?:close|tutup)|(?:sudah|telah) (?:di)?selesaikan oleh tim|semoga membantu',
    re.IGNORECASE,
)
# Salam & penutup murni
_GREETING = re.compile(
    r'^(?:(?:selamat (?:pagi|siang|sore|malam))|(?:kepada )?(?:yth|ysh)\b.*|(?:bapak|ibu|bpk)\b.*\[NAMA\].*'
    r'|terima ?kasih.*|salam.*|hormat kami.*|wassalam.*|ok(?:e|ay)?|baik(?: pak| bu)?|siap)$',
    re.IGNORECASE,
)
# Permintaan informasi ke pegawai (bukan solusi)
_REQUEST = re.compile(
    r'^(?:mohon|tolong|harap|silakan|silahkan) (?:infokan|informasikan|kirim|lampirkan|dilampirkan|segera kirim'
    r'|konfirmasi|dikonfirmasi|berikan|sertakan|cantumkan|sebutkan)|\?$|^apakah\b',
    re.IGNORECASE,
)
# Ciri pesan petugas
_STAFF = re.compile(
    r'\b(?:kami|silakan|silahkan|telah (?:di|kami)|sudah (?:di|kami)|bapak/ibu|yth|ysh|mohon ikuti|dapat (?:di)?coba'
    r'|berhasil|sudah dapat|telah dapat)\b',
    re.IGNORECASE,
)
_FIRST_PERSON = re.compile(r'\b(?:saya|aku|sy)\b', re.IGNORECASE)

# Isi resolution/close_notes yang hanya template atau bukan solusi
_NOTE_TEMPLATES = {
    '', '.', '-', '..', '...', 'solved', 'done', 'ok', 'oke', 'selesai', 'closed', 'close', 'resolved', 'complete',
    'completed', 'sudah', 'sudah diproses', 'sudah dipenuhi', 'permintaan telah dipenuhi', 'permintaan sudah dipenuhi',
    'tiket sudah dijawab', 'sudah ditangani', 'telah ditangani', 'sudah selesai', 'telah selesai', 'sudah dijawab',
}
_NOT_SOLUTION = re.compile(r'dialihkan|bukan layanan|duplikat|double|salah (?:tiket|kirim)|tidak ada respon|cancel', re.IGNORECASE)

MIN_SOLUTION_WORDS = 3


@dataclass(frozen=True)
class Message:
    time: str
    text: str


def split_conversation(raw: object) -> list[Message]:
    """'waktu | teks || waktu | teks' → daftar Message (urut seperti aslinya)."""
    if not isinstance(raw, str) or not raw.strip():
        return []
    messages = []
    for part in raw.split(' || '):
        match = _MESSAGE.match(part)
        if match:
            messages.append(Message(match.group(1), match.group(2).strip()))
        elif part.strip() and messages:
            # Potongan tanpa cap waktu: lanjutan pesan sebelumnya
            messages[-1] = Message(messages[-1].time, f'{messages[-1].text} || {part.strip()}')
    return messages


def _sentences(text: str) -> list[str]:
    return [s.strip(' ,;-') for s in re.split(r'(?<=[.!?])\s+|\n+', text) if s.strip(' ,;-')]


def substantive_text(text: str) -> str:
    """Buang kalimat salam/template; kembalikan sisa yang membawa isi."""
    kept = [s for s in _sentences(text) if not _TEMPLATE.search(s) and not _GREETING.match(s.rstrip('.!, '))]
    return ' '.join(kept).strip()


def _is_solution_candidate(text: str) -> tuple[bool, bool]:
    """(kandidat solusi?, bercirikan petugas?)"""
    body = substantive_text(text)
    if len(body.split()) < MIN_SOLUTION_WORDS + 2:
        return False, False
    sentences = _sentences(body)
    if sentences and all(_REQUEST.search(s) for s in sentences):
        return False, False
    staff = bool(_STAFF.search(text))
    if not staff and _FIRST_PERSON.search(body):
        return False, False  # pesan pegawai ("saya masih tidak bisa ...")
    return True, staff


def extract_solution(messages: list[Message]) -> str | None:
    """Pesan solusi substantif terakhir; pesan bercirikan petugas diutamakan."""
    candidates = []
    for message in messages:
        ok, staff = _is_solution_candidate(message.text)
        if ok:
            candidates.append((staff, message))
    if not candidates:
        return None
    staff_candidates = [m for staff, m in candidates if staff]
    chosen = (staff_candidates or [m for _, m in candidates])[-1]
    return substantive_text(chosen.text)


def meaningful_note(note: object) -> str | None:
    """resolution/close_notes yang bukan template ("solved", "done", ".") dan bukan pengalihan.
    Kalimat template/salam di dalamnya dibuang seperti pada pesan percakapan."""
    if not isinstance(note, str):
        return None
    text = substantive_text(note.strip())
    normalized = re.sub(r'[\s.!]+$', '', text.lower())
    if normalized in _NOTE_TEMPLATES or len(text.split()) < MIN_SOLUTION_WORDS or _NOT_SOLUTION.search(text):
        return None
    return text
