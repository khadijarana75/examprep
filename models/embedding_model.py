"""
embedding_model.py
Wraps sentence-transformers so the rest of the app never touches the
model directly. Swappable later (Unit 4: proprietary vs open-source).
"""

from sentence_transformers import SentenceTransformer
import config

_model = None  # loaded once, reused across calls


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embed a list of chunk texts. Returns a list of vectors (one per input text),
    each vector a plain list of floats so it's JSON/Chroma-friendly.
    """
    if not texts:
        return []

    model = _get_model()
    vectors = model.encode(texts, show_progress_bar=False)
    return [v.tolist() for v in vectors]


def embed_query(query: str) -> list[float]:
    """Embed a single query string (e.g. a topic to retrieve for)."""
    return embed_texts([query])[0]