# nlp/__init__.py
"""
NLP Package for LexiScholar.
Refactored from a single god file into a modular package.
"""

from nlp.utils.constants import (
    TURKISH_STOP_WORDS, ENGLISH_STOP_WORDS, NER_BLACKLIST, NER_GROUP_HEADWORDS,
    NER_GROUP_DESCRIPTORS, NER_LANGUAGE_HEADWORDS, NER_GROUP_CONNECTORS,
    NER_ORG_SUFFIXES, NER_ORG_DISALLOWED, ENTITY_VARIANT_MAP,
    SentimentThresholds, SentimentLevel, hf_pipelines_enabled
)
from nlp.utils.text_utils import (
    clean_html, detect_language, anonymize_text, 
    _get_text_language_profile, _get_batch_language_profile, _language_instruction
)
from nlp.utils.json_parser import _parse_json_response
from nlp.models.cache import NLPModelCache, _cache
from nlp.models.manager import (
    check_local_model_updates, get_nlp_memory_info, unload_all_models, _get_online_engine,
    _get_model_registry, _get_model_meta_path, _read_model_meta, _write_model_meta, _has_local_model_files
)
from nlp.models.prompts import (
    _build_sentiment_system_prompt, _build_topic_system_prompt, _build_ner_system_prompt
)
from nlp.tasks.sentiment import (
    analyze_sentiment, analyze_sentiment_online, _fallback_sentiment
)
from nlp.tasks.ner import (
    extract_entities, extract_entities_online, compare_entity_results,
    _normalize_entities, _fallback_entities, _aggregate_entity_documents
)
from nlp.tasks.topic_modeling import (
    extract_topics, extract_topics_online, extract_topics_hybrid, _compare_topic_results
)
from nlp.tasks.keywords import extract_keywords
from nlp.tasks.kwic import extract_kwic
from nlp.tasks.portrait import calculate_document_portrait
from nlp.tasks.consensus import synthesize_entity_results_online
