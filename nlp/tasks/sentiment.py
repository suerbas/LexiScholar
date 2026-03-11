import logging
import re
from typing import Dict
from nlp.utils.text_utils import clean_html, detect_language, anonymize_text, _get_text_language_profile
from nlp.utils.constants import SentimentThresholds, SentimentLevel
from nlp.models.cache import _cache
from nlp.models.manager import _get_online_engine
from nlp.models.prompts import _build_sentiment_system_prompt
from nlp.utils.json_parser import _parse_json_response

logger = logging.getLogger(__name__)

def analyze_sentiment(text: str, doc_title: str = "") -> Dict:
    clean_text = clean_html(text)
    if not clean_text or len(clean_text) < 10:
        return {"label": "neutral", "score": 0.5, "level": 3, "summary": "Kısa metin"}
    
    lang = detect_language(clean_text)
    pipe = _cache.get_sentiment(lang)
    if not pipe:
        return _fallback_sentiment(clean_text, lang)
    
    res = pipe(clean_text[:512])[0]
    score = res['score']
    label = res['label'].lower()
    
    if label in ('positive', 'label_1') or 'pos' in label:
        polarity = score
    elif label in ('negative', 'label_0') or 'neg' in label:
        polarity = -score
    else:
        polarity = 0
    
    t = SentimentThresholds()
    if polarity > t.VERY_POSITIVE: 
        lvl = SentimentLevel.VERY_POSITIVE; final = "very positive"; tr = "Çok Pozitif"
    elif polarity > t.POSITIVE: 
        lvl = SentimentLevel.POSITIVE; final = "positive"; tr = "Pozitif"
    elif polarity > t.NEUTRAL_MIN: 
        lvl = SentimentLevel.NEUTRAL; final = "neutral"; tr = "Nötr"
    elif polarity > t.NEGATIVE: 
        lvl = SentimentLevel.NEGATIVE; final = "negative"; tr = "Negatif"
    else: 
        lvl = SentimentLevel.VERY_NEGATIVE; final = "very negative"; tr = "Çok Negatif"

    return {
        "label": final,
        "score": (polarity + 1)/2,
        "level": lvl.value,
        "summary": f"{tr} ({lang.upper()})"
    }

def analyze_sentiment_online(text: str, model: str = None) -> Dict:
    engine = _get_online_engine()
    if not engine or not engine.is_configured():
        return {"label": "error", "score": 0.5, "level": 3, "summary": "API Key Ayarlanmamış"}

    clean_text = clean_html(text)
    if not clean_text or len(clean_text) < 10:
        return {"label": "neutral", "score": 0.5, "level": 3, "summary": "Kısa metin"}

    safe_text = anonymize_text(clean_text)
    lang_profile = _get_text_language_profile(clean_text)

    try:
        prompt = f"Analyze the sentiment of the following text and follow the requested output language policy:\n\n{safe_text[:2500]}"
        response_text = engine.generate_completion(
            prompt=prompt,
            system_prompt=_build_sentiment_system_prompt(lang_profile),
            model=model,
            temperature=0.1
        )
        
        data = _parse_json_response(response_text)
        label = data.get("label", "neutral").lower()
        score = float(data.get("score", 0.5))
        summary = data.get("summary", "")
        
        level_map = {"very negative": 1, "negative": 2, "neutral": 3, "positive": 4, "very positive": 5}
        level = level_map.get(label, 3)
        
        if label == "very positive": polarity = 0.8
        elif label == "positive": polarity = 0.4
        elif label == "negative": polarity = -0.4
        elif label == "very negative": polarity = -0.8
        else: polarity = 0.0
        
        polarity = polarity * score
        mapping_score = (polarity + 1) / 2

        return {
            "label": label,
            "score": mapping_score,
            "confidence": score,
            "level": level,
            "summary": f"{summary} (Online/{lang_profile.upper()})"
        }
    except Exception as e:
        logger.error(f"Online sentiment error: {e}")
        return {"label": "error", "score": 0.5, "level": 3, "summary": f"Hata: {str(e)}"}

def _fallback_sentiment(text: str, lang: str) -> Dict:
    tr_pos = {"iyi", "güzel", "harika", "memnun", "başarılı", "olumlu", "mutlu"}
    tr_neg = {"kötü", "berbat", "sorun", "hata", "olumsuz", "üzgün", "başarısız"}
    en_pos = {"good", "great", "excellent", "happy", "positive", "success", "satisfied"}
    en_neg = {"bad", "terrible", "problem", "error", "negative", "sad", "failure"}
    words = re.findall(r"\b[\wçğıöşüÇĞİÖŞÜ]+\b", text.lower())
    if not words:
        return {"label": "neutral", "score": 0.5, "level": 3, "summary": f"Nötr ({lang.upper()})"}
    pos_set = tr_pos if lang == "tr" else en_pos
    neg_set = tr_neg if lang == "tr" else en_neg
    pos_hits = sum(1 for w in words if w in pos_set)
    neg_hits = sum(1 for w in words if w in neg_set)
    sentiment_raw = (pos_hits - neg_hits) / max(len(words), 1)
    polarity = max(-1.0, min(1.0, sentiment_raw * 4))
    t = SentimentThresholds()
    if polarity > t.VERY_POSITIVE: return {"label": "very positive", "score": (polarity + 1) / 2, "level": 5, "summary": f"Çok Pozitif ({lang.upper()})"}
    if polarity > t.POSITIVE: return {"label": "positive", "score": (polarity + 1) / 2, "level": 4, "summary": f"Pozitif ({lang.upper()})"}
    if polarity > t.NEUTRAL_MIN: return {"label": "neutral", "score": (polarity + 1) / 2, "level": 3, "summary": f"Nötr ({lang.upper()})"}
    if polarity > t.NEGATIVE: return {"label": "negative", "score": (polarity + 1) / 2, "level": 2, "summary": f"Negatif ({lang.upper()})"}
    return {"label": "very negative", "score": (polarity + 1) / 2, "level": 1, "summary": f"Çok Negatif ({lang.upper()})"}
