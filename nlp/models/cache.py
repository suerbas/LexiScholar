import os
import sys
import time
import logging
import gc
from typing import Any, Optional, List, Dict
from threading import Lock
from dataclasses import dataclass, field
from nlp.utils.constants import hf_pipelines_enabled, _NLP_CFG

logger = logging.getLogger(__name__)

@dataclass
class _ModelEntry:
    pipe: Any
    last_used: float = field(default_factory=time.time)
    task: str = ""
    lang: str = ""

def _get_device():
    if not hf_pipelines_enabled():
        return -1
    try:
        import torch
        return 0 if torch.cuda.is_available() else -1
    except ImportError:
        return -1

def _get_model_path(model_id: str, folder: str) -> str:
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    local = os.path.join(base, "resources", "models", folder)
    return local if os.path.exists(local) else model_id

def _get_models_base_dir() -> str:
    base = sys._MEIPASS if getattr(sys, "frozen", False) else os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base, "resources", "models")

class NLPModelCache:
    def __init__(self):
        try:
            from cachetools import TTLCache
            class _EvictingTTLCache(TTLCache):
                def __init__(self, maxsize, ttl, on_evict):
                    super().__init__(maxsize=maxsize, ttl=ttl)
                    self._on_evict = on_evict

                def popitem(self):
                    key, value = super().popitem()
                    try: self._on_evict()
                    except Exception: pass
                    return key, value

                def expire(self, time=None):
                    expired = list(super().expire(time=time))
                    if expired:
                        try: self._on_evict()
                        except Exception: pass
                    return expired

            self._lock = Lock()
            self._cache = _EvictingTTLCache(maxsize=2, ttl=600, on_evict=self._cleanup_gpu)
        except ImportError:
            logger.warning("cachetools not available, falling back to simple dict cache")
            self._cache = {}
            self._lock = Lock()
            self._cache_times = {}

    def get_sentiment(self, lang: str) -> Optional[Any]:
        return self._get("sentiment-analysis", lang)

    def get_ner(self, lang: str) -> Optional[Any]:
        return self._get("ner", lang)

    def get_embedding(self, lang: str) -> Optional[Any]:
        return self._get("embedding", lang)

    def unload_all(self) -> None:
        with self._lock:
            self._cache.clear()
            if hasattr(self, '_cache_times'):
                self._cache_times.clear()
        self._cleanup_gpu()
        logger.info("NLPModelCache: tüm modeller serbest bırakıldı.")

    def loaded_models(self) -> list[str]:
        with self._lock:
            return list(self._cache.keys())

    def _get(self, task: str, lang: str) -> Optional[Any]:
        key = f"{task}:{lang}"
        with self._lock:
            if key in self._cache:
                if not hasattr(self, '_cache_times'):
                    return self._cache[key]
                if self._is_valid_fallback(key):
                    return self._cache[key]
                self._evict_model(key)

            pipe = self._load_pipe(task, lang)
            if pipe is not None:
                self._cache[key] = pipe
                if hasattr(self, '_cache_times'):
                    self._cache_times[key] = time.time()
            return pipe

    def _is_valid_fallback(self, key: str) -> bool:
        if not hasattr(self, '_cache_times'):
            return True
        return (time.time() - self._cache_times.get(key, 0)) < 600

    def _evict_model(self, key: str) -> None:
        if key in self._cache:
            model = self._cache.pop(key, None)
            if hasattr(self, '_cache_times'):
                self._cache_times.pop(key, None)
            if model is not None:
                del model
                self._cleanup_gpu()

    def _cleanup_gpu(self) -> None:
        if not hf_pipelines_enabled():
            return
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass

    def _load_pipe(self, task: str, lang: str) -> Optional[Any]:
        if not hf_pipelines_enabled():
            return None
        try:
            if task == "embedding":
                from sentence_transformers import SentenceTransformer
                folder = "bge_m3"
                path = _get_model_path("BAAI/bge-m3", folder)
                logger.info(f"NLPModelCache: embedding model yükleniyor [{lang}]")
                return SentenceTransformer(path)

            from transformers import pipeline
            if task == "sentiment-analysis":
                model_id = ("savasy/bert-base-turkish-sentiment-cased" if lang == "tr" else "distilbert-base-uncased-finetuned-sst-2-english")
                folder = "sentiment_tr" if lang == "tr" else "sentiment_en"
            else:
                model_id = ("savasy/bert-base-turkish-ner-cased" if lang == "tr" else "dslim/bert-base-NER")
                folder = "ner_tr" if lang == "tr" else "ner_en"

            path = _get_model_path(model_id, folder)
            kwargs = {"aggregation_strategy": "simple"} if task == "ner" else {}
            logger.info(f"NLPModelCache: model yükleniyor [{task}:{lang}]")
            return pipeline(task, model=path, tokenizer=path, device=_get_device(), **kwargs)
        except Exception as e:
            logger.error(f"Model yüklenemedi [{task}:{lang}]: {e}", exc_info=True)
            return None

_cache = NLPModelCache()
