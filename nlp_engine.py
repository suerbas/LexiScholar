"""
NLP Engine for LexiScholar
Provides keyword extraction, sentiment analysis, topic modeling, and NER.
"""

import re
import json
import logging
import os
import heapq
from typing import List, Dict, Tuple, Optional, Any
from collections import Counter
from threading import Lock
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

try:
    from config import NLP as _NLP_CFG
except ImportError:
    _NLP_CFG = None  # Test/standalone modunda config yoksa sabitler kullanılır

# Config yüklenemezse kullanılacak varsayılanlar (inline fallback)
_TOPIC_MAX_FEATURES = _NLP_CFG.TOPIC_MAX_FEATURES if _NLP_CFG else 2_000
_TOPIC_MAX_ITER     = _NLP_CFG.TOPIC_MAX_ITER     if _NLP_CFG else 20
_TOPIC_MIN_CHARS    = _NLP_CFG.TOPIC_MIN_CHARS    if _NLP_CFG else 50
_TOPIC_MIN_DOCS     = _NLP_CFG.TOPIC_MIN_DOCS     if _NLP_CFG else 2
_KWIC_WINDOW        = _NLP_CFG.KWIC_DEFAULT_CONTEXT_WINDOW if _NLP_CFG else 10
_PORTRAIT_GRID      = _NLP_CFG.PORTRAIT_GRID_SIZE  if _NLP_CFG else 10
_LANG_MIN_CHARS     = _NLP_CFG.LANG_DETECT_MIN_CHARS if _NLP_CFG else 10
_LANG_FALLBACK      = _NLP_CFG.LANG_DETECT_FALLBACK if _NLP_CFG else "tr"


def _hf_pipelines_enabled() -> bool:
    raw = os.environ.get("LEXISCHOLAR_ENABLE_HF_PIPELINES")
    if raw is not None:
        return raw.strip().lower() in ("1", "true", "yes", "on")
    # Enabled by default on all platforms for quality
    return True

# ============================================================================
# Utilities & Constants
# ============================================================================

TURKISH_STOP_WORDS = {
    've', 'bir', 'bu', 'de', 'da', 'ile', 'için', 'ama', 'ancak', 'fakat',
    'gibi', 'daha', 'çok', 'en', 'her', 'ne', 'nasıl', 'neden', 'nerede',
    'olan', 'olarak', 'oldu', 'olup', 'olmak', 'kadar', 'dolayı', 'rağmen',
    'sonra', 'önce', 'şekilde', 'böyle', 'diğer', 'aynı', 'yani', 'ise',
    'ben', 'sen', 'biz', 'siz', 'onlar', 'benim', 'senin', 'onun',
    'bunun', 'şu', 'şey', 'var', 'yok', 'değil', 'mı', 'mi', 'mu', 'mü',
    'ya', 'ki', 'hem', 'bile', 'diye', 'üzere', 'tarafından',
    'arasında', 'karşı', 'göre', 'hakkında', 'dolayısıyla', 'nedeniyle'
}

ENGLISH_STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're",
    "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he',
    'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's",
    'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what',
    'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is',
    'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having',
    'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or',
    'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about',
    'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above',
    'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under',
    'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some',
    'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
    's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now',
    'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn',
    "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn',
    "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't",
    'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn',
    "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn',
    "wouldn't"
}

NER_BLACKLIST = {
    "xenophobia", "xenofobia", "access", "lack", "scholarship", "funds", 
    "employment", "possibility", "possibilities", "discrimination",
    "market", "thing", "things", "language", "skills", "academy", "society",
    "staj", "bilgisayar", "kursları", "üniversiteler", "türkçe", "ingilizce",
    "tofel", "icdl", "university", "üniversite"
}

@dataclass(frozen=True)
class SentimentThresholds:
    VERY_POSITIVE: float = 0.55
    POSITIVE: float = 0.15
    NEUTRAL_MIN: float = -0.15
    NEGATIVE: float = -0.55

class SentimentLevel(Enum):
    VERY_NEGATIVE = 1
    NEGATIVE = 2
    NEUTRAL = 3
    POSITIVE = 4
    VERY_POSITIVE = 5

def clean_html(text: str) -> str:
    text = re.sub(r'<(style|script).*?>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[^;]+;', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

def detect_language(text: str, fallback: str = "tr") -> str:
    """
    Metnin dilini tespit eder: Türkçe ('tr') veya İngilizce ('en').

    Önce `langdetect` kullanır (istatistiksel model).
    Kaldırılmış / kurulmamış ise karakter+kelime heuristiğine döner.
    Desteklenmeyen herhangi bir dil tespit edilirse `fallback` döner.

    Args:
        text:     Düz veya HTML metin.
        fallback: Belirsiz / hata durumunda dönecek dil kodu. Varsayılan: 'tr'.
    """
    clean_text = clean_html(text).strip()
    if len(clean_text) < _LANG_MIN_CHARS:
        return fallback

    # — 1. YOL: langdetect (tercih edilen) —
    try:
        from langdetect import detect, LangDetectException
        lang_code = detect(clean_text)
        # langdetect ISO-639 kodları döndürür; biz sadece tr/en ayırıyoruz
        if lang_code == "tr":
            return "tr"
        if lang_code in ("en",):
            return "en"
        # Başka bir dil tespit edildiyse fallback
        return fallback
    except ImportError:
        logger.debug("langdetect kurulu değil, karakter heuristiğine geçiliyor.")
    except Exception as e:
        logger.debug(f"langdetect hatası: {e} — heuristiğe geçiliyor.")

    # — 2. YOL: Karakter + kelime heuristiği (fallback) —
    lower = clean_text.lower()
    if any(c in "çğıöşü" for c in lower):
        return "tr"
    en_markers = {' the ', ' and ', ' in ', ' that ', ' with ', ' for ', ' of ', ' to '}
    if sum(1 for w in en_markers if w in f" {lower} ") >= 2:
        return "en"
    return fallback

# ============================================================================
# NLP Model Cache — TTL tabanlı otomatik bellek yönetimi
# ============================================================================

import time
import gc

# Aynı anda bellekte tutulabilecek maksimum model sayısı
# (sentiment_tr, sentiment_en, ner_tr, ner_en toplamı)
_MAX_CACHED_MODELS = 2        # Toplam 2 model → ~800–900 MB max
_MODEL_TTL_SECONDS = 600      # 10 dakika kullanılmazsa → otomatik eviction


@dataclass
class _ModelEntry:
    """Bir transformer pipeline'ının bellek izleri ile birlikte kaydı."""
    pipe: Any
    last_used: float = field(default_factory=time.time)
    task: str = ""
    lang: str = ""


class NLPModelCache:
    """
    Thread-safe NLP model cache using cachetools.TTLCache.
    
    Features:
    - Automatic TTL eviction (10 minutes)
    - Maximum 2 models in memory
    - GPU cache cleanup on eviction
    - Clean, minimal code using standard library
    """

    def __init__(self):
        try:
            from cachetools import TTLCache

            class _EvictingTTLCache(TTLCache):
                def __init__(self, maxsize, ttl, on_evict):
                    super().__init__(maxsize=maxsize, ttl=ttl)
                    self._on_evict = on_evict

                def popitem(self):
                    key, value = super().popitem()
                    try:
                        self._on_evict()
                    except Exception:
                        pass
                    return key, value

                def expire(self, time=None):
                    expired = list(super().expire(time=time))
                    if expired:
                        try:
                            self._on_evict()
                        except Exception:
                            pass
                    return expired

            self._lock = Lock()
            self._cache = _EvictingTTLCache(maxsize=2, ttl=600, on_evict=self._cleanup_gpu)
        except ImportError:
            logger.warning("cachetools not available, falling back to simple dict cache")
            self._cache = {}
            self._lock = Lock()
            self._cache_times = {}

    # ── Public API ──────────────────────────────────────────────────────────

    def get_sentiment(self, lang: str) -> Optional[Any]:
        return self._get("sentiment-analysis", lang)

    def get_ner(self, lang: str) -> Optional[Any]:
        return self._get("ner", lang)

    def unload_all(self) -> None:
        """Tüm modelleri RAM'den boşaltır."""
        with self._lock:
            self._cache.clear()
            if hasattr(self, '_cache_times'):
                self._cache_times.clear()
        self._cleanup_gpu()
        logger.info("NLPModelCache: tüm modeller serbest bırakıldı.")

    def loaded_models(self) -> list[str]:
        """Şu an bellekte bulunan model anahtarlarının listesini döner."""
        with self._lock:
            return list(self._cache.keys())

    # ── İç mekanizma ────────────────────────────────────────────────────────

    def _get(self, task: str, lang: str) -> Optional[Any]:
        key = f"{task}:{lang}"
        
        with self._lock:
            # Check cache (TTLCache handles TTL automatically)
            if key in self._cache:
                if not hasattr(self, '_cache_times'):
                    return self._cache[key]
                if self._is_valid_fallback(key):
                    return self._cache[key]
                self._evict_model(key)

            # Load new model
            pipe = self._load_pipe(task, lang)
            if pipe is not None:
                self._cache[key] = pipe
                if hasattr(self, '_cache_times'):
                    self._cache_times[key] = time.time()
            return pipe

    def _is_valid_fallback(self, key: str) -> bool:
        """Fallback TTL check for simple dict cache."""
        if not hasattr(self, '_cache_times'):
            return True
        now = time.time()
        last_used = self._cache_times.get(key, 0)
        return (now - last_used) < 600  # 10 minutes

    def _evict_model(self, key: str) -> None:
        """Remove model from cache and cleanup GPU memory."""
        if key in self._cache:
            model = self._cache.pop(key, None)
            if hasattr(self, '_cache_times'):
                self._cache_times.pop(key, None)
            
            if model is not None:
                del model
                self._cleanup_gpu()

    def _cleanup_gpu(self) -> None:
        """Clean up GPU memory."""
        if not _hf_pipelines_enabled():
            return
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def _load_pipe(self, task: str, lang: str) -> Optional[Any]:
        if not _hf_pipelines_enabled():
            logger.info(f"NLPModelCache: HF pipeline disabled [{task}:{lang}]")
            return None
        try:
            from transformers import pipeline
            if task == "sentiment-analysis":
                model_id = ("savasy/bert-base-turkish-sentiment-cased"
                            if lang == "tr" else
                            "distilbert-base-uncased-finetuned-sst-2-english")
                folder = "sentiment_tr" if lang == "tr" else "sentiment_en"
            else:
                model_id = ("savasy/bert-base-turkish-ner-cased"
                            if lang == "tr" else "dslim/bert-base-NER")
                folder = "ner_tr" if lang == "tr" else "ner_en"

            path = _get_model_path(model_id, folder)
            kwargs = {"aggregation_strategy": "simple"} if task == "ner" else {}
            logger.info(f"NLPModelCache: model yükleniyor [{task}:{lang}]")
            return pipeline(task, model=path, tokenizer=path,
                            device=_get_device(), **kwargs)
        except Exception as e:
            logger.error(f"Model yüklenemedi [{task}:{lang}]: {e}", exc_info=True)
            return None


_cache = NLPModelCache()


def _get_device():
    if not _hf_pipelines_enabled():
        return -1
    try:
        import torch
        return 0 if torch.cuda.is_available() else -1
    except ImportError:
        return -1


def _get_model_path(model_id: str, folder: str) -> str:
    import os
    import sys
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(__file__)
    local = os.path.join(base, "resources", "models", folder)
    return local if os.path.exists(local) else model_id


def get_nlp_memory_info() -> dict:
    """
    Status bar widget'ı için anlık NLP bellek bilgisini döner.
    Örnek: {'loaded': ['sentiment:tr'], 'count': 1, 'max': 2}
    """
    loaded = _cache.loaded_models()
    return {
        "loaded": loaded,
        "count": len(loaded),
        "max": _MAX_CACHED_MODELS,
    }



# ============================================================================
# Core Functions
# ============================================================================

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
    
    # Correct polarity mapping based on model label
    if label in ('positive', 'label_1') or 'pos' in label:
        polarity = score
    elif label in ('negative', 'label_0') or 'neg' in label:
        polarity = -score
    else:
        # Neutral or unexpected label
        polarity = 0
    
    # Initialize thresholds instance
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

def extract_entities(text: str) -> List[Dict]:
    clean_text = clean_html(text)
    lang = detect_language(clean_text)
    pipe = _cache.get_ner(lang)
    if not pipe:
        return _fallback_entities(clean_text, lang)

    raw = pipe(clean_text[:1500])

    results = []
    # Combined stop list for aggressive filtering
    all_stop = TURKISH_STOP_WORDS | ENGLISH_STOP_WORDS | NER_BLACKLIST

    for e in raw:
        word = e.get("word", "").strip()

        # BERT WordPiece sızıntısını temizle:
        # 1) Sadece "##..." token'larını (baştaki parça olmayan) atla
        if word.startswith("##"):
            continue
        # 2) ## içeren ama başlıkta olmayan parçaları birleştir (temizle)
        word = word.replace(" ##", "").replace("##", "")
        
        # 3) Filtreleme Mantığı:
        word_lower = word.lower()
        if word_lower in all_stop:
            continue
        
        # Çok uzun ifadeler (5 kelimeden fazla) genellikle model hatasıdır
        if len(word.split()) > 5:
            continue

        # Tek karakter / boş artıkları atla
        if len(word) < 2:
            continue

        results.append({
            "text": word,
            "label": e["entity_group"],
            "score": round(float(e["score"]), 4),
        })

    return results


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
    if polarity > t.VERY_POSITIVE:
        return {"label": "very positive", "score": (polarity + 1) / 2, "level": 5, "summary": f"Çok Pozitif ({lang.upper()})"}
    if polarity > t.POSITIVE:
        return {"label": "positive", "score": (polarity + 1) / 2, "level": 4, "summary": f"Pozitif ({lang.upper()})"}
    if polarity > t.NEUTRAL_MIN:
        return {"label": "neutral", "score": (polarity + 1) / 2, "level": 3, "summary": f"Nötr ({lang.upper()})"}
    if polarity > t.NEGATIVE:
        return {"label": "negative", "score": (polarity + 1) / 2, "level": 2, "summary": f"Negatif ({lang.upper()})"}
    return {"label": "very negative", "score": (polarity + 1) / 2, "level": 1, "summary": f"Çok Negatif ({lang.upper()})"}


def _fallback_entities(text: str, lang: str) -> List[Dict]:
    candidates = re.findall(r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)*\b", text)
    seen = set()
    results = []
    for token in candidates:
        cleaned = token.strip()
        low = cleaned.lower()
        if len(cleaned) < 2 or low in seen:
            continue
        seen.add(low)
        label = "ORG" if "Üniversite" in cleaned or "University" in cleaned else "PER"
        results.append({"text": cleaned, "label": label, "score": 0.51})
    return results

def extract_keywords(text: str, top_n: int = 10, ngram_size: int = 2, dedup_lim: float = 0.9) -> List[Dict]:
    """
    Extract keywords using YAKE algorithm.
    
    Args:
        text: Source text
        top_n: Number of keywords to return
        ngram_size: Max N-gram size (1, 2, or 3)
        dedup_lim: Deduplication threshold (default 0.9). 
                   Lower value = more diverse keywords (less overlap).
    """
    try:
        import yake
        clean_t = clean_html(text)
        lang = detect_language(clean_t)
        
        # YAKE Parameters
        # n: max n-gram size
        # dedupLim: deduplication threshold
        # top: number of keywords
        # windowsSize: context window
        kw_extractor = yake.KeywordExtractor(
            lan=lang, 
            n=ngram_size,
            dedupLim=dedup_lim,
            top=top_n, 
            features=None
        )
        
        keywords = kw_extractor.extract_keywords(clean_t)
        
        # Post-Processing:
        # 1. Eğer kullanıcı 2'li (bigram) veya 3'lü seçim yaptıysa, tekli kelimeleri (unigram) temizle
        if ngram_size > 1:
            keywords = [k for k in keywords if len(k[0].split()) > 1]
        
        # 2. Stopwords kontrolü (YAKE bazen kaçırabiliyor veya kullanıcı dilini yanlış biliyor)
        all_stop = TURKISH_STOP_WORDS | ENGLISH_STOP_WORDS
        keywords = [k for k in keywords if k[0].lower() not in all_stop]

        # YAKE returns (keyword, score) where LOWER score is BETTER.
        # We convert it to (keyword, importance) where HIGHER is BETTER for visualization.
        return [{"keyword": k, "score": max(0, 1 - s)} for k, s in keywords]
    except ImportError: return []

def extract_topics(texts: List[Dict], n_topics: int = 5, top_words: int = 10) -> Dict:
    """Extract topics from multiple documents using LDA."""
    try:
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.decomposition import LatentDirichletAllocation
    except ImportError:
        return {"topics": [], "doc_topics": [], "error": "scikit-learn is not installed."}
    
    if len(texts) < 2:
        return {"topics": [], "doc_topics": [], "error": "At least 2 documents are required for topic modeling."}
    
    clean_texts = [clean_html(doc["text"]) for doc in texts]
    valid_indices = [i for i, t in enumerate(clean_texts) if len(t) > 50]
    
    if len(valid_indices) < _TOPIC_MIN_DOCS:
        return {"topics": [], "doc_topics": [], "error": "Not enough text content found in documents."}
    
    valid_texts = [clean_texts[i] for i in valid_indices]
    valid_docs = [texts[i] for i in valid_indices]
    n_topics = min(n_topics, len(valid_texts))
    
    # Detect majority language for stop words
    sample_text = " ".join(valid_texts[:3])
    lang = detect_language(sample_text)
    stop_words = list(TURKISH_STOP_WORDS) if lang == "tr" else list(ENGLISH_STOP_WORDS)
    
    vectorizer = CountVectorizer(
        max_df=0.9,
        min_df=1 if len(valid_texts) < 5 else 2,
        max_features=_TOPIC_MAX_FEATURES,
        stop_words=stop_words,
        token_pattern=r'\b[a-zA-ZçğıöşüÞĞİÖŞÜâîûêô]{3,}\b'
    )
    
    try:
        dtm = vectorizer.fit_transform(valid_texts)
        feature_names = vectorizer.get_feature_names_out()
        lda = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=_NLP_CFG.TOPIC_RANDOM_STATE if _NLP_CFG else 42,
            max_iter=_TOPIC_MAX_ITER,
            learning_method='batch'
        )
        doc_topic_dist = lda.fit_transform(dtm)
        
        topics = []
        for idx, weights in enumerate(lda.components_):
            top_indices = weights.argsort()[-top_words:][::-1]
            words = [(feature_names[i], round(float(weights[i]), 4)) for i in top_indices]
            topics.append({"id": idx, "words": words, "label": f"Konu {idx + 1}: {' / '.join(w for w, _ in words[:3])}"})
            
        doc_topics = []
        for i, doc in enumerate(valid_docs):
            weights = [round(float(w), 4) for w in doc_topic_dist[i]]
            doc_topics.append({
                "doc_id": doc["doc_id"], "title": doc.get("title", "Belge"),
                "topic_weights": weights, "dominant_topic": int(doc_topic_dist[i].argmax())
            })
        return {"topics": topics, "doc_topics": doc_topics}
    except Exception as e:
        return {"topics": [], "doc_topics": [], "error": str(e)}

def extract_kwic(text: str, keyword: str, context_window: int = 10) -> List[Dict]:
    """Key Word In Context analysis."""
    clean_text = clean_html(text)
    words = clean_text.split()
    results = []
    kw_lower = keyword.lower()
    
    for i, word in enumerate(words):
        word_clean = re.sub(r'[^\w\s]', '', word).lower()
        if kw_lower in word_clean:
            start = max(0, i - context_window)
            end = min(len(words), i + 1 + context_window)
            results.append({
                "left": " ".join(words[start:i]),
                "keyword": word,
                "right": " ".join(words[i+1:end])
            })
            if len(results) >= 500: break
    return results

def calculate_document_portrait(doc_len: int, segments: List[Dict], grid_size: int = 1200) -> List[str]:
    """Map segments to a color grid."""
    if doc_len <= 0:
        return ["#FFFFFF"] * grid_size
    if grid_size <= 0:
        return []
    grid = ["#F1F5F9"] * grid_size
    cell_size = doc_len / grid_size
    starts = [[] for _ in range(grid_size)]
    ends = [[] for _ in range(grid_size)]
    colors = {}
    for order, seg in enumerate(segments):
        start_pos = max(0, float(seg.get("start", 0)))
        end_pos = min(float(doc_len), float(seg.get("end", 0)))
        if end_pos < start_pos:
            continue
        start_idx = int(start_pos / cell_size)
        end_idx = int(end_pos / cell_size)
        if start_idx >= grid_size:
            continue
        if end_idx < 0:
            continue
        start_idx = max(0, min(grid_size - 1, start_idx))
        end_idx = max(0, min(grid_size - 1, end_idx))
        starts[start_idx].append(order)
        ends[end_idx].append(order)
        colors[order] = seg.get("color", "#CCCCCC")
    active = set()
    heap = []
    for i in range(grid_size):
        if starts[i]:
            for order in starts[i]:
                active.add(order)
                heapq.heappush(heap, -order)
        while heap and (-heap[0]) not in active:
            heapq.heappop(heap)
        if heap:
            grid[i] = colors[-heap[0]]
        if ends[i]:
            for order in ends[i]:
                active.discard(order)
    return grid
