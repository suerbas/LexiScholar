import os
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

try:
    from config import NLP as _NLP_CFG
except ImportError:
    _NLP_CFG = None

# Config based fallbacks
TOPIC_MAX_FEATURES = _NLP_CFG.TOPIC_MAX_FEATURES if _NLP_CFG else 2_000
TOPIC_MAX_ITER     = _NLP_CFG.TOPIC_MAX_ITER     if _NLP_CFG else 20
TOPIC_MIN_CHARS    = _NLP_CFG.TOPIC_MIN_CHARS    if _NLP_CFG else 50
TOPIC_MIN_DOCS     = _NLP_CFG.TOPIC_MIN_DOCS     if _NLP_CFG else 2
KWIC_WINDOW        = _NLP_CFG.KWIC_DEFAULT_CONTEXT_WINDOW if _NLP_CFG else 10
PORTRAIT_GRID      = _NLP_CFG.PORTRAIT_GRID_SIZE  if _NLP_CFG else 10
LANG_MIN_CHARS     = _NLP_CFG.LANG_DETECT_MIN_CHARS if _NLP_CFG else 10
LANG_FALLBACK      = _NLP_CFG.LANG_DETECT_FALLBACK if _NLP_CFG else "tr"

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
    "tofel", "icdl", "university", "üniversite", "word", "excel", "tu"
}

NER_GROUP_HEADWORDS = {
    "student", "students", "worker", "workers", "people", "person", "persons",
    "family", "families", "refugee", "refugees", "migrant", "migrants",
    "child", "children", "woman", "women", "man", "men", "citizen", "citizens",
    "community", "communities", "öğrenci", "öğrenciler", "işçi", "işçiler",
    "insan", "insanlar", "aile", "aileler", "mülteci", "mülteciler", "göçmen",
    "göçmenler", "çocuk", "çocuklar", "kadın", "kadınlar", "erkek", "erkekler",
    "vatandaş", "vatandaşlar", "topluluk", "topluluklar"
}

NER_GROUP_DESCRIPTORS = {
    "syrian", "syrians", "turkish", "turk", "turks", "english", "afghan",
    "afghans", "arab", "arabs", "kurdish", "kurd", "kurds", "ukrainian",
    "ukrainians", "iraqi", "iraqis", "iranian", "iranians", "foreign",
    "immigrant", "immigrants", "migrant", "migrants", "refugee", "refugees",
    "suriyeli", "suriyeliler", "türk", "türkler", "ingiliz", "ingilizler",
    "afgan", "afganlar", "arap", "araplar", "kürt", "kürtler", "ukraynalı",
    "ukraynalılar", "ıraklı", "ıraklılar", "iranlı", "iranlılar", "yabancı",
    "yabancılar", "göçmen", "göçmenler", "mülteci", "mülteciler"
}

NER_LANGUAGE_HEADWORDS = {"language", "languages", "dil", "dili", "course", "courses", "program", "programs"}

NER_GROUP_CONNECTORS = {
    "and", "or", "the", "a", "an", "for", "with", "of", "to", "in", "on",
    "at", "by", "from", "into", "their", "our", "his", "her", "its", "these",
    "those", "this", "that", "ve", "veya", "ile", "için", "bir", "bu", "şu",
    "o", "ve", "da", "de", "ile", "gibi"
}

NER_ORG_SUFFIXES = {
    "university", "üniversitesi", "üniversite", "academy", "akademi", "association",
    "foundation", "vakfı", "vakfi", "ministry", "bakanlığı", "bakanligi", "department",
    "kurumu", "kurum", "institute", "enstitüsü", "enstitusu", "agency", "office",
    "organization", "organisation", "center", "centre", "merkezi", "merkez"
}

NER_ORG_DISALLOWED = {
    "yös", "yos", "tofel", "toefl", "ielts", "kurs", "kursu", "kursları", "kurslari",
    "course", "courses", "program", "programs", "skill", "skills", "employment",
    "possibility", "possibilities", "computer", "bilgisayar", "none", "english", "ingilizce"
}

ENTITY_VARIANT_MAP = {
    "suriye": "Syria",
    "türkiye": "Turkey",
    "turkiye": "Turkey",
    "izmir": "Izmir",
    "syrians students": "Syrian students",
    "syrians student": "Syrian student",
    "turks students": "Turkish students",
    "turks student": "Turkish student",
    "suriyeli öğrenciler": "Suriyeli öğrenciler",
    "suriyeli insanlar": "Suriyeli insanlar",
    "türk öğrenciler": "Türk öğrenciler",
    "türk insanlar": "Türk insanlar"
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

def hf_pipelines_enabled() -> bool:
    raw = os.environ.get("LEXISCHOLAR_ENABLE_HF_PIPELINES")
    if raw is not None:
        return raw.strip().lower() in ("1", "true", "yes", "on")
    return True
