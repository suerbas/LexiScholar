import re
import logging
from typing import List, Dict, Optional
from nlp.utils.constants import LANG_MIN_CHARS, LANG_FALLBACK

logger = logging.getLogger(__name__)

def clean_html(text: str) -> str:
    text = re.sub(r'<(style|script).*?>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[^;]+;', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def detect_language(text: str, fallback: str = LANG_FALLBACK) -> str:
    clean_text = clean_html(text).strip()
    if len(clean_text) < LANG_MIN_CHARS:
        return fallback

    try:
        from langdetect import detect
        lang_code = detect(clean_text)
        if lang_code == "tr":
            return "tr"
        if lang_code in ("en",):
            return "en"
        return fallback
    except ImportError:
        logger.debug("langdetect kurulu değil, karakter heuristiğine geçiliyor.")
    except Exception as e:
        logger.debug(f"langdetect hatası: {e} — heuristiğe geçiliyor.")

    lower = f" {clean_text.lower()} "
    en_markers = {' the ', ' and ', ' in ', ' that ', ' with ', ' for ', ' of ', ' to '}
    en_hits = sum(1 for w in en_markers if w in f" {lower} ")
    if any(c in lower for c in "çğıöşü"):
        return "tr"
    if en_hits >= 2:
        return "en"
    return fallback

def anonymize_text(text: str, mask_person_names: bool = True) -> str:
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[E-POSTA]', text)
    text = re.sub(r'\b[1-9][0-9]{10}\b', '[TC-KİMLİK]', text)
    text = re.sub(r'(\+90|0)?\s*\(?([0-9]{3})\)?\s*([0-9]{3})\s*([0-9]{2})\s*([0-9]{2})', '[TELEFON]', text)
    text = re.sub(r'\b([0-9]{1,2}[./-][0-9]{1,2}[./-][0-9]{2,4}|[0-9]{2,4}[./-][0-9]{1,2}[./-][0-9]{1,2})\b', '[TARİH]', text)
    if mask_person_names:
        text = re.sub(r'\b([A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)\b', '[KİŞİ]', text)
    text = re.sub(r'\b([A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+(İlçe|Mah\.|Cad\.|Sok\.|No\.|Kapı))\b', '[ADRES]', text)
    return text

def _get_text_language_profile(text: str) -> str:
    clean_txt = clean_html(text)
    detected = detect_language(clean_txt)
    lower = f" {clean_txt.lower()} "
    has_turkish_chars = any(c in lower for c in "çğıöşü")
    en_markers = {' the ', ' and ', ' in ', ' that ', ' that ', ' with ', ' for ', ' of ', ' to '}
    en_hits = sum(1 for w in en_markers if w in f" {lower} ")
    if detected == "tr" and en_hits >= 2:
        return "mixed"
    if detected == "en" and has_turkish_chars:
        return "mixed"
    return detected

def _get_batch_language_profile(texts: List[str]) -> str:
    profiles = {p for p in (_get_text_language_profile(text) for text in texts if clean_html(text).strip())}
    if not profiles:
        return LANG_FALLBACK
    if len(profiles) == 1:
        return profiles.pop()
    return "mixed"

def _language_instruction(profile: str) -> str:
    if profile == "en":
        return "Respond in English. Think and write in English. Do not translate the source content into Turkish."
    if profile == "tr":
        return "Türkçe yanıt ver. Metni Türkçe düşün ve Türkçe yaz. Kaynak içeriği İngilizceye çevirme."
    return "If the input is mixed-language, preserve that behavior. Use the dominant language for the short explanation, but keep entity names, topic labels, and keywords in the language used by the source text. Do not force Turkish if the source is English."
