"""
reranker.py
Unit 8 — Re-Ranking Retrieved Results.
Cross-encoders score a (query, chunk) pair directly, which is slower but
far more accurate than embedding similarity alone. We use it to re-order
a small candidate set after first-stage retrieval, not to search the
whole collection.
"""

from sentence_transformers import CrossEncoder
import config

_reranker = None


def _get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(config.RERANKER_MODEL_NAME)
    return _reranker


def rerank(query: str, hits: list[dict], top_k: int = 5) -> list[dict]:
    """
    Re-score and re-order retrieval hits using a cross-encoder.
    hits: list of {"text", "metadata", "distance"} from vector_store.query()
    Returns the same dicts, re-ordered, each with an added "rerank_score",
    truncated to top_k.
    """
    if not hits:
        return []

    model = _get_reranker()
    pairs = [(query, h["text"]) for h in hits]
    scores = model.predict(pairs)

    for hit, score in zip(hits, scores):
        hit["rerank_score"] = float(score)

    reranked = sorted(hits, key=lambda h: h["rerank_score"], reverse=True)
    return reranked[:top_k]