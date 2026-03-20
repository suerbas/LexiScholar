import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from nlp.models.cache import _get_models_base_dir, _cache

logger = logging.getLogger(__name__)

_online_engine = None

def _get_online_engine():
    global _online_engine
    if _online_engine is None:
        try:
            from llm_engine import OpenRouterEngine
            _online_engine = OpenRouterEngine()
        except ImportError:
            logger.warning("llm_engine.py not found, online analysis disabled.")
    return _online_engine

def _get_model_registry() -> List[Dict[str, Any]]:
    return [
        {"id": "savasy/bert-base-turkish-sentiment-cased", "folder": "sentiment_tr", "label": "Duygu Analizi (TR)", "task": "sentiment-analysis", "lang": "tr"},
        {"id": "distilbert-base-uncased-finetuned-sst-2-english", "folder": "sentiment_en", "label": "Sentiment Analysis (EN)", "task": "sentiment-analysis", "lang": "en"},
        {"id": "savasy/bert-base-turkish-ner-cased", "folder": "ner_tr", "label": "Varlık Tanıma (TR)", "task": "ner", "lang": "tr"},
        {"id": "dslim/bert-base-NER", "folder": "ner_en", "label": "Named Entity Recognition (EN)", "task": "ner", "lang": "en"},
        {"id": "BAAI/bge-m3", "folder": "bge_m3", "label": "Gelişmiş Anlamsal Arama (Çok Dilli)", "task": "embedding", "lang": "multilingual", "optional": True}
    ]

def _get_model_meta_path(folder: str) -> str:
    return os.path.join(_get_models_base_dir(), folder, ".model_meta.json")

def _read_model_meta(folder: str) -> Dict[str, Any]:
    meta_path = _get_model_meta_path(folder)
    if not os.path.exists(meta_path): return {}
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception: return {}

def _write_model_meta(folder: str, data: Dict[str, Any]) -> None:
    model_dir = os.path.join(_get_models_base_dir(), folder)
    os.makedirs(model_dir, exist_ok=True)
    meta_path = _get_model_meta_path(folder)
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _has_local_model_files(folder: str) -> bool:
    model_dir = os.path.join(_get_models_base_dir(), folder)
    if not os.path.isdir(model_dir): return False
    try:
        return len([n for n in os.listdir(model_dir) if n != ".model_meta.json"]) > 0
    except Exception: return False

def check_local_model_updates(download_updates: bool = False, models_to_download: List[str] = None) -> Dict[str, Any]:
    report = {"checked": [], "updated": [], "current": [], "missing": [], "errors": []}
    try:
        from huggingface_hub import model_info, snapshot_download
    except ImportError as e:
        report["errors"].append(f"huggingface_hub kütüphanesi gerekli: {e}")
        return report

    for item in _get_model_registry():
        folder, label, model_id = item["folder"], item["label"], item["id"]
        local_dir = os.path.join(_get_models_base_dir(), folder)
        local_exists = _has_local_model_files(folder)
        local_meta = _read_model_meta(folder)

        try:
            # Use files_metadata=True to ensure sibling sizes are included
            remote = model_info(model_id, files_metadata=True)
            remote_sha = getattr(remote, "sha", None) or "unknown"
            
            # Calculate total size from siblings
            size_bytes = 0
            if hasattr(remote, "siblings") and remote.siblings:
                size_bytes = sum(getattr(f, "size", 0) or 0 for f in remote.siblings)
            
            # Fallback for some model types where siblings might still be missing sizes
            if size_bytes == 0:
                from huggingface_hub import list_repo_tree
                try:
                    files = list_repo_tree(model_id)
                    size_bytes = sum(getattr(f, "size", 0) or 0 for f in files if hasattr(f, "size") and f.size)
                except Exception:
                    pass
            
            local_sha = local_meta.get("sha")
            status = {
                "label": label, 
                "model_id": model_id, 
                "folder": folder, 
                "local_exists": local_exists, 
                "local_sha": local_sha, 
                "remote_sha": remote_sha, 
                "size_bytes": size_bytes,
                "updated": False, 
                "status": "current"
            }

            if not local_exists: status["status"] = "missing"; report["missing"].append(status)
            elif local_sha == remote_sha: status["status"] = "current"; report["current"].append(status)
            else: status["status"] = "outdated"

            # Check if this model should be downloaded
            should_download = download_updates and status["status"] in {"missing", "outdated"}
            if should_download and models_to_download is not None:
                if model_id not in models_to_download:
                    should_download = False

            if should_download:
                snapshot_download(repo_id=model_id, local_dir=local_dir, local_dir_use_symlinks=False, revision=remote_sha)
                _write_model_meta(folder, {"model_id": model_id, "sha": remote_sha, "label": label, "updated_at": time.strftime("%Y-%m-%d %H:%M:%S")})
                status["updated"] = True; status["status"] = "updated"; report["updated"].append(status)
                _cache.unload_all()
            report["checked"].append(status)
        except Exception as e: report["errors"].append(f"{label}: {e}")
    return report

def get_nlp_memory_info() -> dict:
    loaded = _cache.loaded_models()
    return {"loaded": loaded, "count": len(loaded), "max": 2}

def unload_all_models():
    """Tüm yüklü NLP modellerini bellekten temizler."""
    _cache.unload_all()
