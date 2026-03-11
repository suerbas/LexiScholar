import logging
from typing import List, Dict
from nlp.utils.text_utils import clean_html, detect_language, anonymize_text, _get_batch_language_profile
from nlp.utils.constants import TURKISH_STOP_WORDS, ENGLISH_STOP_WORDS, TOPIC_MAX_FEATURES, TOPIC_MAX_ITER, TOPIC_MIN_DOCS, _NLP_CFG
from nlp.models.manager import _get_online_engine
from nlp.models.prompts import _build_topic_system_prompt
from nlp.utils.json_parser import _parse_json_response

logger = logging.getLogger(__name__)

def extract_topics(texts: List[Dict], n_topics: int = 5, top_words: int = 10) -> Dict:
    try:
        from sklearn.feature_extraction.text import CountVectorizer
        from sklearn.decomposition import LatentDirichletAllocation
    except ImportError: return {"topics": [], "doc_topics": [], "error": "scikit-learn is not installed."}
    if len(texts) < 2: return {"topics": [], "doc_topics": [], "error": "At least 2 documents are required for topic modeling."}
    
    clean_texts = [clean_html(doc["text"]) for doc in texts]
    valid_indices = [i for i, t in enumerate(clean_texts) if len(t) > 50]
    if len(valid_indices) < TOPIC_MIN_DOCS: return {"topics": [], "doc_topics": [], "error": "Not enough text content found in documents."}
    
    valid_texts, valid_docs = [clean_texts[i] for i in valid_indices], [texts[i] for i in valid_indices]
    n_topics = min(n_topics, len(valid_texts))
    lang = detect_language(" ".join(valid_texts[:3]))
    stop_words = list(TURKISH_STOP_WORDS) if lang == "tr" else list(ENGLISH_STOP_WORDS)
    
    vectorizer = CountVectorizer(max_df=0.9, min_df=1 if len(valid_texts) < 5 else 2, max_features=TOPIC_MAX_FEATURES, stop_words=stop_words, token_pattern=r'\b[a-zA-ZçğıöşüÞĞİÖŞÜâîûêô]{3,}\b')
    try:
        dtm = vectorizer.fit_transform(valid_texts)
        feature_names = vectorizer.get_feature_names_out()
        lda = LatentDirichletAllocation(n_components=n_topics, random_state=_NLP_CFG.TOPIC_RANDOM_STATE if _NLP_CFG else 42, max_iter=TOPIC_MAX_ITER, learning_method='batch')
        doc_topic_dist = lda.fit_transform(dtm)
        
        topics = []
        for idx, weights in enumerate(lda.components_):
            top_indices = weights.argsort()[-top_words:][::-1]
            words = [(feature_names[i], round(float(weights[i]), 4)) for i in top_indices]
            topics.append({"id": idx, "words": words, "label": f"Konu {idx + 1}: {' / '.join(w for w, _ in words[:3])}"})
            
        doc_topics = []
        for i, doc in enumerate(valid_docs):
            weights = [round(float(w), 4) for w in doc_topic_dist[i]]
            doc_topics.append({"doc_id": doc["doc_id"], "title": doc.get("title", "Belge"), "topic_weights": weights, "dominant_topic": int(doc_topic_dist[i].argmax())})
        return {"topics": topics, "doc_topics": doc_topics, "model_name": "LDA", "mode": "local"}
    except Exception as e: return {"topics": [], "doc_topics": [], "error": str(e)}

def extract_topics_online(texts: List[Dict], n_topics: int = 5, model: str = None) -> Dict:
    engine = _get_online_engine()
    if not engine or not engine.is_configured(): return {"topics": [], "doc_topics": [], "error": "API Key Ayarlanmamış", "model_name": "N/A", "mode": "online"}
    if len(texts) < 2: return {"topics": [], "doc_topics": [], "error": "At least 2 documents are required for topic modeling."}
    
    clean_texts, valid_docs = [], []
    for doc in texts:
        ct = clean_html(doc["text"])
        if len(ct) > 50: clean_texts.append(anonymize_text(ct)[:1500]); valid_docs.append(doc)
    if len(valid_docs) < 2: return {"topics": [], "doc_topics": [], "error": "Not enough text content found in documents."}
    
    n_topics = min(n_topics, len(valid_docs))
    lang_profile = _get_batch_language_profile([doc["text"] for doc in valid_docs])
    combined_text = "\n\n---DOC---\n\n".join([f"[Document {i+1}: {d.get('title', 'Document')}]: {t}" for i, (d, t) in enumerate(zip(valid_docs, clean_texts))])
    
    try:
        response_text = engine.generate_completion(prompt=f"Analyze these documents and extract {n_topics} topics:\n\n{combined_text[:8000]}", system_prompt=_build_topic_system_prompt(n_topics, lang_profile), model=model, temperature=0.3, max_tokens=4096)
        data = _parse_json_response(response_text)
        topics, doc_topics = data.get("topics", []), data.get("doc_topics", [])
        if not isinstance(topics, list) or not isinstance(doc_topics, list): return {"topics": [], "doc_topics": [], "error": "Invalid response format", "model_name": "Error", "mode": "online"}
        
        for topic in topics:
            if "words" in topic and isinstance(topic["words"], list): topic["words"] = [[w, float(s)] for w, s in topic["words"][:10]]
        for dt in doc_topics:
            if "topic_weights" in dt and isinstance(dt["topic_weights"], list):
                try: dt["topic_weights"] = [round(float(w), 4) if w is not None else 0.0 for w in dt["topic_weights"]]
                except: dt["topic_weights"] = [0.25] * len(dt["topic_weights"])
            if "dominant_topic" in dt:
                try: dt["dominant_topic"] = int(dt["dominant_topic"])
                except: dt["dominant_topic"] = 0
        return {"topics": topics, "doc_topics": doc_topics, "model_name": model or "Online AI", "mode": "online"}
    except Exception as e:
        logger.error(f"Online topic extraction error: {e}")
        return {"topics": [], "doc_topics": [], "error": f"Hata: {str(e)}", "model_name": "Error", "mode": "online"}

def extract_topics_hybrid(texts: List[Dict], n_topics: int = 5, model: str = None) -> Dict:
    try:
        local_result = extract_topics(texts, n_topics=n_topics)
        if local_result.get("error"): return {"error": local_result["error"], "mode": "hybrid"}
        online_result = extract_topics_online(texts, n_topics=n_topics, model=model)
        if "error" in online_result: return local_result
        comparison = _compare_topic_results(local_result, online_result)
        return {"mode": "hybrid", "local": {"topics": local_result.get("topics", []), "doc_topics": local_result.get("doc_topics", []), "model_name": "LDA"}, "online": {"topics": online_result.get("topics", []), "doc_topics": online_result.get("doc_topics", []), "model_name": online_result.get("model_name", "AI")}, "comparison": comparison}
    except Exception as e:
        logger.error(f"Hybrid topic extraction error: {e}")
        return {"error": f"Hibrit konu modelleme hatası: {str(e)}", "mode": "hybrid"}

def _compare_topic_results(local_result: Dict, online_result: Dict) -> Dict:
    if local_result.get("error") or online_result.get("error"): return {"topic_alignment": [], "doc_differences": [], "summary": {"farklı": 0, "yakın": 0, "uyumlu": 0}}
    local_topics, online_topics = local_result.get("topics", []), online_result.get("topics", [])
    local_doc_topics, online_doc_topics = local_result.get("doc_topics", []), online_result.get("doc_topics", [])
    if not (local_topics and online_topics and local_doc_topics and online_doc_topics): return {"topic_alignment": [], "doc_differences": [], "summary": {"farklı": 0, "yakın": 0, "uyumlu": 0}}
    
    topic_alignment = []
    for i, lt in enumerate(local_topics):
        local_words = set([w.lower() for w, _ in lt.get("words", [])])
        best_match = {"local_id": i, "online_id": None, "overlap_score": 0, "status": "farklı"}
        for j, ot in enumerate(online_topics):
            online_words = set([w.lower() for w, _ in ot.get("words", [])])
            if local_words and online_words:
                overlap = len(local_words & online_words) / len(local_words | online_words)
                if overlap > best_match["overlap_score"]: best_match["online_id"], best_match["overlap_score"] = j, round(overlap, 2)
        if best_match["overlap_score"] >= 0.5: best_match["status"] = "uyumlu"
        elif best_match["overlap_score"] >= 0.2: best_match["status"] = "yakın"
        topic_alignment.append(best_match)
    
    doc_differences, min_docs = [], min(len(local_doc_topics), len(online_doc_topics))
    for i in range(min_docs):
        ld, od = local_doc_topics[i], online_doc_topics[i]
        local_dom, online_dom = ld.get("dominant_topic", 0), od.get("dominant_topic", 0)
        alignment = next((a for a in topic_alignment if a["local_id"] == local_dom), None)
        status = "farklı"
        if alignment and alignment["online_id"] == online_dom:
            if alignment["status"] in ("uyumlu", "yakın"): status = alignment["status"]
        doc_differences.append({"doc_id": ld.get("doc_id"), "title": ld.get("title", "Belge"), "local_dominant": local_dom, "online_dominant": online_dom, "status": status})
    
    summary = {"uyumlu": 0, "yakın": 0, "farklı": 0}
    for d in doc_differences: summary[d["status"]] += 1
    return {"topic_alignment": topic_alignment, "doc_differences": doc_differences, "summary": summary}
