from typing import List, Dict
from nlp.utils.text_utils import clean_html, detect_language
from nlp.utils.constants import TURKISH_STOP_WORDS, ENGLISH_STOP_WORDS

def extract_keywords(text: str, top_n: int = 10, ngram_size: int = 2, dedup_lim: float = 0.9) -> List[Dict]:
    try:
        import yake
        clean_t = clean_html(text)
        lang = detect_language(clean_t)
        kw_extractor = yake.KeywordExtractor(lan=lang, n=ngram_size, dedupLim=dedup_lim, top=top_n, features=None)
        keywords = kw_extractor.extract_keywords(clean_t)
        if ngram_size > 1: keywords = [k for k in keywords if len(k[0].split()) > 1]
        all_stop = TURKISH_STOP_WORDS | ENGLISH_STOP_WORDS
        keywords = [k for k in keywords if k[0].lower() not in all_stop]
        return [{"keyword": k, "score": max(0, 1 - s)} for k, s in keywords]
    except ImportError: return []
