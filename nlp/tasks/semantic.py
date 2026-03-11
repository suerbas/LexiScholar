import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from nlp.models.manager import _get_models_base_dir, _has_local_model_files
from ui.common_ui import show_info

logger = logging.getLogger(__name__)

from nlp.models.cache import _cache

def get_bge_model_dir() -> str:
    return os.path.join(_get_models_base_dir(), "bge_m3")

def is_semantic_model_available() -> bool:
    return _has_local_model_files("bge_m3")

def load_semantic_model():
    """Load the BAAI/bge-m3 dense embedder using decentralized cache."""
    if not is_semantic_model_available():
        raise RuntimeError("Model_Missing")

    model = _cache.get_embedding("multilingual")
    if model is None:
        raise RuntimeError("Model yüklenemedi: Bellek veya yükleme hatası.")
    return model


def get_embedding(text: str) -> np.ndarray:
    """Generate dense embedding for a single text."""
    model = load_semantic_model()
    # BGE-M3 handles long texts reasonably, but we ensure string input
    embedding = model.encode(str(text), normalize_embeddings=True)
    return embedding


def get_embeddings_batch(texts: List[str]) -> List[np.ndarray]:
    """Generate normalized embeddings for batch of texts."""
    model = load_semantic_model()
    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return embeddings


def compute_similarities(query_embedding: np.ndarray, doc_embeddings: List[np.ndarray]) -> np.ndarray:
    """Compute cosine similarities between a query and a list of docs."""
    # Since embeddings are normalized, dot product == cosine similarity
    doc_matrix = np.vstack(doc_embeddings)
    similarities = doc_matrix @ query_embedding.T
    return similarities.flatten()


def semantic_search(query: str, segments: List[Dict[str, Any]], top_k: int = 50) -> List[Dict[str, Any]]:
    """
    Perform semantic search over a list of coded segments.
    Segments must have 'segment_text'.
    If segment has 'embedding' blob (numpy bytes), uses it, otherwise computes it on the fly.
    """
    if not segments:
        return []

    try:
        query_emb = get_embedding(query)
    except RuntimeError as e:
        # Re-raise to let UI handle the prompt to download
        raise e

    # Prepare document embeddings
    doc_embeddings = []
    texts_to_embed = []
    indices_to_embed = []

    for i, seg in enumerate(segments):
        emb_bytes = seg.get('embedding')
        if emb_bytes and isinstance(emb_bytes, bytes):
            try:
                emb = np.frombuffer(emb_bytes, dtype=np.float32)
                doc_embeddings.append(emb)
                continue
            except Exception:
                pass # Fallback to computing
        
        # We need to compute it
        doc_embeddings.append(None) # Place holder
        text = seg.get('segment_text', '')
        texts_to_embed.append(text)
        indices_to_embed.append(i)

    # Compute missing embeddings (on the fly for search if not saved to DB yet)
    if texts_to_embed:
        try:
            computed_embs = get_embeddings_batch(texts_to_embed)
            for idx, emb in zip(indices_to_embed, computed_embs):
                doc_embeddings[idx] = emb
                # We could ideally save this back to DB here, but dao is separate.
        except Exception as e:
            logger.error(f"Error computing batch embeddings: {e}")
            raise RuntimeError("Segment vektörleri oluşturulamadı.")

    # Calculate similarity
    similarities = compute_similarities(query_emb, doc_embeddings)

    # Attach scores and sort
    results = []
    for i, seg in enumerate(segments):
        # Create a copy to avoid modifying the original if it's cached
        res = dict(seg)
        # Using native float for JSON serialization safety if needed
        res['semantic_score'] = float(similarities[i])
        results.append(res)
    
    # Sort descending and take top_k
    results.sort(key=lambda x: x['semantic_score'], reverse=True)
    return results[:top_k]

def build_cluster_map_data(segments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Takes segments, computes/extracts embeddings, and runs UMAP + HDBSCAN
    to generate 2D coordinates and cluster labels.
    """
    if len(segments) < 3:
        raise ValueError("Kümeleme analizi için en az 3 segment gerekli.")
        
    try:
        import umap
        import hdbscan
    except ImportError:
        raise RuntimeError("Kütüphane_Eksik: umap-learn ve hdbscan gerekli.")
        
    # Gather embeddings
    embeddings = []
    texts_to_embed = []
    indices_to_embed = []
    
    for i, seg in enumerate(segments):
        emb_bytes = seg.get('embedding')
        if emb_bytes and isinstance(emb_bytes, bytes):
            try:
                emb = np.frombuffer(emb_bytes, dtype=np.float32)
                embeddings.append(emb)
                continue
            except Exception: pass
            
        embeddings.append(None)
        texts_to_embed.append(seg.get('segment_text', ''))
        indices_to_embed.append(i)
        
    if texts_to_embed:
        computed_embs = get_embeddings_batch(texts_to_embed)
        for idx, emb in zip(indices_to_embed, computed_embs):
            embeddings[idx] = emb
            
    matrix = np.vstack(embeddings)
    
    # Dimensionality Reduction (UMAP)
    # We use cosine metric since BGE-M3 is trained for cosine similarity
    n_neighbors = min(15, len(segments) - 1)
    reducer = umap.UMAP(n_neighbors=n_neighbors, min_dist=0.1, metric='cosine', random_state=42)
    coords_2d = reducer.fit_transform(matrix)
    
    # Clustering (HDBSCAN) - Optional, we might just color by existing Codes
    labels = []
    try:
        # Only cluster if enough data
        if len(segments) > 10:
            clusterer = hdbscan.HDBSCAN(min_cluster_size=max(3, len(segments) // 20), metric='euclidean')
            labels = clusterer.fit_predict(coords_2d).tolist()
        else:
            labels = [-1] * len(segments)
    except Exception as e:
        logger.warning(f"HDBSCAN clustering failed: {e}")
        labels = [-1] * len(segments)
        
    # Prepare result format for JS charting mapping
    points = []
    for i, seg in enumerate(segments):
        points.append({
            'id': seg.get('id', i),
            'text': seg.get('segment_text', '')[:200] + '...',
            'code': seg.get('code_name', 'Bilinmeyen Kod'),
            'doc': seg.get('document_title', 'Adsız Belge'),
            'x': float(coords_2d[i, 0]),
            'y': float(coords_2d[i, 1]),
            'cluster': int(labels[i])
        })
        
    return {"points": points}
