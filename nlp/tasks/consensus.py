"""
consensus.py — AI Hakem (Judge) Sentez Modülü

Hibrit analizin (Lokal + Online) ürettiği iki ayrı varlık listesini alır,
güçlü bir LLM'e hakem yaparak tek, temizlenmiş ve sentezlenmiş bir varlık listesi
üretir.
"""

import logging
from typing import List, Dict, Optional

from nlp.models.manager import _get_online_engine
from nlp.utils.json_parser import _parse_json_response
from nlp.utils.text_utils import _language_instruction, _get_batch_language_profile, clean_html

logger = logging.getLogger(__name__)


def _build_ner_synthesis_prompt(profile: str) -> str:
    """System prompt for the AI judge that merges two NER result lists."""
    return f"""You are a Senior Academic Referee specializing in cross-methodological validation of named entities in qualitative research.

You will receive two named entity lists extracted from the same set of documents by two different NLP methods:
- **Model A (Local)**: A classical BERT-based model. High precision, may miss some entities, no hallucinations.
- **Model B (Online AI)**: A large language model. Broader recall, may hallucinate or include generic concepts.

Your task is to produce a single, optimal, authoritative merged entity list. Follow these rules carefully:
1. **Include an entity if**: Both models agree on it (high confidence), OR if only one model found it AND it is clearly a specific named entity (person, organization, location, social group, date).
2. **Exclude an entity if**: It is a generic concept, common noun, stop word, language name, software tool, or vague abstraction — even if one of the models included it.
3. **Resolve conflicts**: If the models disagree on the label (e.g., LOC vs ORG), pick the most semantically accurate label given the entity text.
4. **Normalize duplicates**: If both models include variants of the same entity (e.g. "Syrian" and "Syrian students"), keep the more specific/correct form.
5. **Confidence score**: Assign a score based on agreement (both agree = high score ~0.9, only one found it = moderate ~0.65).

{_language_instruction(profile)}

Return ONLY valid JSON in this exact format:
{{
  "entities": [
    {{"text": "entity text", "label": "PER|ORG|LOC|DATE|MISC", "score": 0.0, "source": "both|local_only|online_only"}}
  ],
  "synthesis_note": "One sentence summary of what was merged/removed and why."
}}

Do NOT add markdown, code fences, explanations, or extra text outside the JSON."""


def _build_sentiment_synthesis_prompt(profile: str) -> str:
    """System prompt for the AI judge that merges two Sentiment result lists."""
    return f"""You are a Senior QDA Scholar acting as a meta-analytical judge to synthesize divergent sentiment interpretations into a unified academic finding.
You will receive sentiment analysis results for a set of documents from two methods:
- **Model A (Local/BERT)**: Precise classifier for 5 classes (very/negative, neutral, positive/very). High reliability on short texts.
- **Model B (Online AI)**: Reason-based analyzer. Good at catching irony/context.

Your task is to provide a single "Final Decision" for each document's sentiment.
Rules:
1. **Decision**: Pick the most accurate label (very positive, positive, neutral, negative, very negative).
2. **Reasoning**: Write a short (one sentence) explanation of why you chose this label or how you resolved a conflict between A and B.
3. **Confidence**: Assign a confidence score (0.0 to 1.0).

{_language_instruction(profile)}

Return ONLY valid JSON in this exact format:
{{
  "results": [
    {{"doc_id": "...", "label": "...", "score": 0.0, "summary": "reasoning text"}}
  ]
}}"""


def _build_topic_synthesis_prompt(profile: str) -> str:
    """System prompt for the AI judge that merges LDA and AI topic models."""
    return f"""You are an expert in Computer-Assisted Qualitative Data Analysis (CAQDAS), highly skilled at synthesizing automated topics with semantic depth and theoretical coherence.
You will receive:
- **Model A (LDA)**: A set of numerical topics (keywords with weights).
- **Model B (AI)**: A set of semantic topics (labels and descriptions).

Your task is to synthesize them into a single, comprehensive set of topics (max 5 topics).
Rules:
1. **Map Themes**: Align the keywords from LDA with the semantic labels from AI.
2. **Labels**: Create clear, professional topic labels.
3. **Description**: Write a brief overview for each topic.
4. **Document Mapping**: For each document, assign the primary dominant topic.

{_language_instruction(profile)}

Return ONLY valid JSON in this exact format:
{{
  "topics": [
    {{"label": "Topic Name", "words": [["word", 0.9]], "description": "..."}}
  ],
  "doc_topics": [
    {{"doc_id": "...", "dominant_topic": 0}}
  ]
}}"""



def synthesize_entity_results_online(
    hybrid_ner_data: Dict,
    model: Optional[str] = None,
    judge_model: Optional[str] = None
) -> Dict:
    """
    Takes the result from a hybrid NER run and asks an LLM 'judge' model
    to synthesize the two entity lists into a single authoritative result.

    Args:
        hybrid_ner_data: The dict returned by _aggregate_entity_documents(mode='hybrid').
        model: The model used for the original online analysis (for display purposes).
        judge_model: The LLM model to use as judge. Defaults to the configured model.

    Returns:
        A dict in the same format as a standard "online" NER result, with mode='synthesized'.
    """
    from llm_engine import OpenRouterEngine
    engine_temp = OpenRouterEngine()
    
    if judge_model is None:
        judge_model = engine_temp.get_judge_model()
        
    engine = _get_online_engine()
    if not engine or not engine.is_configured():
        return {
            "error": "API Key Ayarlanmamış veya engine hazır değil.",
            "mode": "synthesized"
        }

    documents = hybrid_ner_data.get("documents", [])
    if not documents:
        return {"error": "Sentezlenecek belge verisi bulunamadı.", "mode": "synthesized"}

    # Detect language from original texts if available
    lang_profile = "tr"  # default
    all_texts = []
    for doc in documents:
        local_ents = doc.get("local_entities", [])
        online_ents = doc.get("online_entities", [])
        all_texts.append(" ".join([e.get("text", "") for e in local_ents + online_ents]))
    if all_texts:
        lang_profile = _get_batch_language_profile(all_texts)

    # Build per-document prompts and synthesize
    synthesized_documents = []
    model_used = judge_model or model

    for doc in documents:
        doc_id = doc.get("doc_id", "")
        title = doc.get("title", "Belge")
        local_ents = doc.get("local_entities", [])
        online_ents = doc.get("online_entities", [])

        if not local_ents and not online_ents:
            synthesized_documents.append({
                "doc_id": doc_id, "title": title,
                "entities": [], "synthesis_note": "No entities found."
            })
            continue

        # Format the two lists for the prompt
        def fmt_list(lst: List[Dict]) -> str:
            if not lst:
                return "(boş / hiçbir varlık bulunamadı)"
            return "\n".join([f"- {e.get('text', '')} [{e.get('label', 'MISC')}] (score: {e.get('score', 0.5):.2f})" for e in lst])

        user_prompt = (
            f"Document: \"{title}\"\n\n"
            f"Model A (Local/BERT) found these entities:\n{fmt_list(local_ents)}\n\n"
            f"Model B (Online AI) found these entities:\n{fmt_list(online_ents)}\n\n"
            f"Please synthesize into a single authoritative entity list following your instructions."
        )

        try:
            response_text = engine.generate_completion(
                prompt=user_prompt,
                system_prompt=_build_ner_synthesis_prompt(lang_profile),
                model=model_used,
                temperature=0.1,
                max_tokens=2048
            )
            data = _parse_json_response(response_text)
            synthesized_entities = data.get("entities", [])
            synthesis_note = data.get("synthesis_note", "")

            synthesized_documents.append({
                "doc_id": doc_id,
                "title": title,
                "entities": synthesized_entities,
                "synthesis_note": synthesis_note
            })

        except Exception as e:
            logger.error(f"Synthesis error for '{title}': {e}")
            # Fallback: merge both lists (simple union)
            seen = set()
            merged = []
            for ent in local_ents + online_ents:
                key = f"{ent.get('text', '').lower()}:{ent.get('label', 'MISC')}"
                if key not in seen:
                    seen.add(key)
                    merged.append(ent)
            synthesized_documents.append({
                "doc_id": doc_id,
                "title": title,
                "entities": merged,
                "synthesis_note": f"Hata nedeniyle basit birleştirme uygulandı: {str(e)}"
            })

    # Aggregate just like normal NER
    all_by_label = {}
    for doc in synthesized_documents:
        for ent in doc.get("entities", []):
            label = ent.get("label", "MISC")
            if label not in all_by_label:
                all_by_label[label] = []
            all_by_label[label].append(ent.get("text", ""))

    return {
        "documents": synthesized_documents,
        "all_entities": {k: list(set(v)) for k, v in all_by_label.items()},
        "summary": {k: len(set(v)) for k, v in all_by_label.items()},
        "local_entities": {},
        "online_entities": {},
        "mode": "synthesized",
        "model_name": model_used or "Hakem AI"
    }


def synthesize_sentiment_results_online(
    hybrid_sentiment_data: List[Dict],
    judge_model: Optional[str] = None
) -> List[Dict]:
    """
    Synthesizes hybrid sentiment results into a single set.
    """
    from llm_engine import OpenRouterEngine
    engine_temp = OpenRouterEngine()
    if judge_model is None:
        judge_model = engine_temp.get_judge_model()

    engine = _get_online_engine()
    if not engine or not engine.is_configured() or not hybrid_sentiment_data:
        return hybrid_sentiment_data

    # Format data for prompt
    data_to_judge = []
    for r in hybrid_sentiment_data:
        data_to_judge.append({
            "doc_id": r.get("id", r.get("doc_id", "unknown")),
            "title": r.get("title", "Belge"),
            "local": r.get("local", {}),
            "online": r.get("online", {})
        })

    user_prompt = f"Analyze and synthesize the following hybrid sentiment results:\n{str(data_to_judge)}"
    
    try:
        response_text = engine.generate_completion(
            prompt=user_prompt,
            system_prompt=_build_sentiment_synthesis_prompt("tr"),
            model=judge_model,
            temperature=0.1
        )
        data = _parse_json_response(response_text)
        results = data.get("results", [])
        
        # Merge back titles from original data
        final_results = []
        titles_map = {r.get("id", r.get("doc_id", "u")): r.get("title") for r in hybrid_sentiment_data}
        for res in results:
            doc_id = res.get("id") or res.get("doc_id")
            res["title"] = titles_map.get(doc_id, "Belge")
            final_results.append(res)
            
        return final_results
    except Exception as e:
        logger.error(f"Sentiment synthesis error: {e}")
        return [{"error": str(e), "doc_id": "error", "label": "error", "score": 0.0, "summary": "Sentezleme hatası."}]


def synthesize_topic_results_online(
    hybrid_topic_data: Dict,
    judge_model: Optional[str] = None
) -> Dict:
    """
    Synthesizes hybrid topic results into a single set.
    """
    from llm_engine import OpenRouterEngine
    engine_temp = OpenRouterEngine()
    if judge_model is None:
        judge_model = engine_temp.get_judge_model()

    engine = _get_online_engine()
    if not engine or not engine.is_configured():
        return hybrid_topic_data

    user_prompt = f"Analyze and synthesize these hybrid topic modeling results into a single authoritative set:\n{str(hybrid_topic_data)}"
    
    try:
        response_text = engine.generate_completion(
            prompt=user_prompt,
            system_prompt=_build_topic_synthesis_prompt("tr"),
            model=judge_model,
            temperature=0.1
        )
        data = _parse_json_response(response_text)
        
        # Add titles back to doc_topics
        titles_map = {}
        for doc in hybrid_topic_data.get("local", {}).get("doc_topics", []):
            titles_map[doc.get("doc_id", "u")] = doc.get("title", "Belge")
            
        final_doc_topics = []
        raw_doc_topics = data.get("doc_topics", []) if isinstance(data, dict) else []
        for dt in raw_doc_topics:
            doc_id = dt.get("doc_id")
            dt["title"] = titles_map.get(doc_id, "Belge")
            final_doc_topics.append(dt)
            
        if isinstance(data, dict):
            data["doc_topics"] = final_doc_topics
            data["model_name"] = judge_model
            data["error"] = ""
            return data
        else:
            return {"topics": [], "doc_topics": [], "error": "Geçersiz AI yanıtı", "mode": "online"}
    except Exception as e:
        logger.error(f"Topic synthesis error: {e}")
        return {"topics": [], "doc_topics": [], "error": f"Sentezleme hatası: {str(e)}", "mode": "online"}
        return data
    except Exception as e:
        logger.error(f"Topic synthesis error: {e}")
        return {"error": str(e), "topics": [], "doc_topics": []}

