import re
import logging
from typing import List, Dict, Optional
from nlp.utils.text_utils import clean_html, detect_language, anonymize_text, _get_text_language_profile
from nlp.utils.constants import (
    TURKISH_STOP_WORDS, ENGLISH_STOP_WORDS, NER_BLACKLIST, NER_GROUP_HEADWORDS,
    NER_GROUP_DESCRIPTORS, NER_LANGUAGE_HEADWORDS, NER_GROUP_CONNECTORS,
    NER_ORG_SUFFIXES, NER_ORG_DISALLOWED, ENTITY_VARIANT_MAP
)
from nlp.models.cache import _cache
from nlp.models.manager import _get_online_engine
from nlp.models.prompts import _build_ner_system_prompt
from nlp.utils.json_parser import _parse_json_response

logger = logging.getLogger(__name__)

def _looks_like_group_entity(text: str) -> bool:
    return _canonicalize_group_entity(text) is not None

def _canonicalize_group_entity(text: str) -> Optional[str]:
    tokens = [token for token in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü'-]+", text) if token]
    if len(tokens) < 2: return None
    lowered = [token.lower() for token in tokens]
    for index in range(len(tokens) - 1):
        if lowered[index] in NER_GROUP_CONNECTORS: continue
        if lowered[index] in NER_GROUP_DESCRIPTORS and lowered[index + 1] in NER_GROUP_HEADWORDS:
            return f"{tokens[index]} {tokens[index + 1]}"
    return None

def _looks_like_language_phrase(text: str) -> bool:
    tokens = [token for token in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü'-]+", text.lower()) if token]
    if len(tokens) < 1: return False
    if tokens[-1] not in NER_LANGUAGE_HEADWORDS: return False
    return any(token in NER_GROUP_DESCRIPTORS for token in tokens[:-1])

def _is_likely_org_entity(text: str) -> bool:
    tokens = [token for token in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü'-]+", text.lower()) if token]
    if not tokens: return False
    if any(token in NER_ORG_DISALLOWED for token in tokens): return False
    if any(token in NER_LANGUAGE_HEADWORDS for token in tokens): return False
    if tokens[-1] in NER_ORG_SUFFIXES: return True
    if any(token.isupper() and len(token) >= 2 for token in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü]+", text)): return True
    if len(tokens) >= 2 and all(token[:1].isupper() for token in text.split() if token[:1].isalpha()): return True
    return False

def _entity_canonical_key(text: str, label: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip())
    lowered = normalized.lower()
    if label == "MISC":
        canonical_group = _canonicalize_group_entity(normalized)
        if canonical_group:
            normalized = canonical_group
            lowered = normalized.lower()
    lowered = ENTITY_VARIANT_MAP.get(lowered, lowered)
    lowered = re.sub(r"\b(the|and)\s+", "", lowered, flags=re.IGNORECASE)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    return f"{label}:{lowered}"

def _entity_display_text(text: str, label: str) -> str:
    canonical_key = _entity_canonical_key(text, label)
    _, value = canonical_key.split(":", 1)
    mapped = ENTITY_VARIANT_MAP.get(value, value)
    if mapped in {"Syria", "Turkey", "Izmir", "Syrian students", "Syrian student", "Turkish students", "Turkish student"}:
        return mapped
    return " ".join(part.capitalize() if label == "MISC" and not part.isascii() else part.capitalize() if part.islower() else part for part in mapped.split())

def _confidence_bucket(score: float) -> str:
    if score >= 0.85: return "Yüksek"
    if score >= 0.65: return "Orta"
    return "Düşük"

def _extract_contextual_group_entities(text: str) -> List[Dict]:
    tokens = [token for token in re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşü'-]+", text) if token]
    entities = []
    seen = set()
    for i in range(len(tokens) - 1):
        phrase = f"{tokens[i]} {tokens[i + 1]}".strip()
        canonical = _canonicalize_group_entity(phrase)
        if not canonical or _looks_like_language_phrase(canonical): continue
        key = canonical.lower()
        if key in seen: continue
        seen.add(key)
        entities.append({"text": canonical, "label": "MISC", "score": 0.6})
    return entities

def _is_valid_entity_text(text: str, label: str) -> bool:
    cleaned = text.strip()
    if not cleaned: return False
    cleaned_lower = cleaned.lower()
    if cleaned_lower in (TURKISH_STOP_WORDS | ENGLISH_STOP_WORDS | NER_BLACKLIST): return False
    if _looks_like_language_phrase(cleaned): return False
    if len(cleaned) < 3 or len(cleaned.split()) > 4: return False
    if re.fullmatch(r'[\W\d_]+', cleaned): return False
    if label == "MISC":
        canonical = _canonicalize_group_entity(cleaned)
        return canonical is not None and not _looks_like_language_phrase(canonical)
    if label == "ORG": return _is_likely_org_entity(cleaned)
    if cleaned_lower in NER_GROUP_DESCRIPTORS: return False
    return True

def _normalize_entities(entities: List[Dict], source_text: str = "", include_contextual_groups: bool = False) -> List[Dict]:
    normalized = []
    seen = {}
    combined_entities = list(entities)
    if source_text and include_contextual_groups:
        combined_entities.extend(_extract_contextual_group_entities(source_text))
    for ent in combined_entities:
        text_value = str(ent.get("text", "")).strip().replace(" ##", "").replace("##", "")
        label = str(ent.get("label", "MISC")).upper().strip()
        if label == "MISC":
            canonical_group = _canonicalize_group_entity(text_value)
            if canonical_group: text_value = canonical_group
        if label not in {"PER", "ORG", "LOC", "DATE", "MISC"}: continue
        if not _is_valid_entity_text(text_value, label): continue
        score_value = round(float(ent.get("score", 0.5)), 4)
        canonical_key = _entity_canonical_key(text_value, label)
        display_text = _entity_display_text(text_value, label)
        existing_index = seen.get(canonical_key)
        if existing_index is not None:
            if score_value > normalized[existing_index].get("score", 0.0):
                normalized[existing_index]["score"] = score_value
                normalized[existing_index]["text"] = display_text
                normalized[existing_index]["confidence_level"] = _confidence_bucket(score_value)
            continue
        seen[canonical_key] = len(normalized)
        normalized.append({
            "text": display_text, "label": label, "score": score_value,
            "canonical_key": canonical_key, "confidence_level": _confidence_bucket(score_value)
        })
    return normalized

def _aggregate_entity_documents(documents: List[Dict], mode: str = "local") -> Dict:
    all_by_label, local_by_label, online_by_label = {}, {}, {}
    for doc in documents:
        if mode == "hybrid":
            merged_entities = doc.get("local_entities", []) + doc.get("online_entities", [])
            for ent in doc.get("local_entities", []):
                l = ent.get("label", "MISC")
                if l not in local_by_label: local_by_label[l] = []
                local_by_label[l].append(ent.get("text", ""))
            for ent in doc.get("online_entities", []):
                l = ent.get("label", "MISC")
                if l not in online_by_label: online_by_label[l] = []
                online_by_label[l].append(ent.get("text", ""))
        else:
            merged_entities = doc.get("entities", [])
        for ent in merged_entities:
            l = ent.get("label", "MISC")
            if l not in all_by_label: all_by_label[l] = []
            all_by_label[l].append(ent.get("text", ""))
    summary = {k: len(set(v)) for k, v in all_by_label.items()}
    return {
        "documents": documents, "all_entities": {k: list(set(v)) for k, v in all_by_label.items()},
        "summary": summary, "local_entities": {k: list(set(v)) for k, v in local_by_label.items()},
        "online_entities": {k: list(set(v)) for k, v in online_by_label.items()}, "mode": mode
    }

def extract_entities_online(text: str, model: str = None) -> List[Dict]:
    engine = _get_online_engine()
    if not engine or not engine.is_configured(): return []
    clean_text = clean_html(text)
    if not clean_text or len(clean_text) < 10: return []
    safe_text = anonymize_text(clean_text, mask_person_names=False)
    lang_profile = _get_text_language_profile(clean_text)
    try:
        response_text = engine.generate_completion(
            prompt=f"Extract named entities from this text:\n\n{safe_text[:2500]}",
            system_prompt=_build_ner_system_prompt(lang_profile),
            model=model, temperature=0.1
        )
        data = _parse_json_response(response_text)
        entities = data.get("entities", []) if isinstance(data, dict) else []
        return _normalize_entities(entities, source_text=clean_text, include_contextual_groups=True)
    except Exception as e:
        logger.error(f"Online NER error: {e}")
        return []

def compare_entity_results(local_entities: List[Dict], online_entities: List[Dict]) -> Dict:
    local_map = {e.get("canonical_key") or _entity_canonical_key(e.get("text", ""), e.get("label", "MISC")): e for e in local_entities}
    online_map = {e.get("canonical_key") or _entity_canonical_key(e.get("text", ""), e.get("label", "MISC")): e for e in online_entities}
    local_set, online_set = set(local_map.keys()), set(online_map.keys())
    overlap, only_local, only_online = local_set & online_set, local_set - online_set, online_set - local_set
    comparison_rows = []
    for key in sorted(overlap | only_local | only_online):
        local_ent, online_ent = local_map.get(key), online_map.get(key)
        label = (local_ent or online_ent or {}).get("label", "MISC")
        display_text = (local_ent or online_ent or {}).get("text", "")
        ls = float(local_ent.get("score", 0.0)) if local_ent else 0.0
        os = float(online_ent.get("score", 0.0)) if online_ent else 0.0
        if local_ent and online_ent: status, conf = "shared", "Yüksek"
        elif online_ent: status, conf = "online_only", _confidence_bucket(max(os, 0.75))
        else: status, conf = "local_only", _confidence_bucket(ls)
        comparison_rows.append({"text": display_text, "label": label, "status": status, "local_score": round(ls, 4), "online_score": round(os, 4), "confidence_level": conf})
    return {"shared_count": len(overlap), "local_only_count": len(only_local), "online_only_count": len(only_online), "entities": comparison_rows}

def extract_entities(text: str) -> List[Dict]:
    clean_text = clean_html(text)
    lang = detect_language(clean_text)
    pipe = _cache.get_ner(lang)
    if not pipe: return _fallback_entities(clean_text, lang)
    raw = pipe(clean_text[:1500])
    results, all_stop = [], TURKISH_STOP_WORDS | ENGLISH_STOP_WORDS | NER_BLACKLIST
    for e in raw:
        word = e.get("word", "").strip()
        if word.startswith("##"): continue
        word = word.replace(" ##", "").replace("##", "")
        if word.lower() in all_stop or not _is_valid_entity_text(word, e.get("entity_group", "MISC")): continue
        results.append({"text": word, "label": e["entity_group"], "score": round(float(e["score"]), 4)})
    return _normalize_entities(results, source_text=clean_text, include_contextual_groups=True)

def _fallback_entities(text: str, lang: str) -> List[Dict]:
    candidates = re.findall(r"\b[A-ZÇĞİÖŞÜ][a-zçğıöşü]+(?:\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)*\b", text)
    seen, results = set(), []
    for token in candidates:
        cleaned = token.strip()
        if len(cleaned) < 2 or cleaned.lower() in seen: continue
        label = "ORG" if "Üniversite" in cleaned or "University" in cleaned else "PER"
        if not _is_valid_entity_text(cleaned, label): continue
        seen.add(cleaned.lower()); results.append({"text": cleaned, "label": label, "score": 0.51})
    return _normalize_entities(results, source_text=text, include_contextual_groups=True)
