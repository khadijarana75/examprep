"""
vector_store.py
Wraps Chroma so the rest of the app never touches the client directly.
One Chroma collection per uploaded document (Unit 5: namespace design).
"""

import sys

# Windows/older Python ships an sqlite3 too old for Chroma (needs >= 3.35).
# Swap in pysqlite3-binary's newer build before chromadb imports sqlite3 itself.
try:
    import pysqlite3
    sys.modules["sqlite3"] = pysqlite3
    sys.modules["sqlite3.dbapi2"] = pysqlite3.dbapi2
except ImportError:
    pass

import chromadb
from chromadb.config import Settings
import config

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    return _client


def _collection_name(source_name: str) -> str:
    safe = "".join(c if c.isalnum() else "_" for c in source_name)
    return f"{config.CHROMA_COLLECTION_PREFIX}{safe}"


def upsert_chunks(source_name: str, chunks: list[dict], vectors: list[list[float]]):
    if len(chunks) != len(vectors):
        raise ValueError(
            f"chunks ({len(chunks)}) and vectors ({len(vectors)}) length mismatch"
        )

    client = _get_client()
    collection = client.get_or_create_collection(name=_collection_name(source_name))

    ids = [f"{source_name}_{c['metadata']['chunk_index']}" for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]

    collection.upsert(
        ids=ids,
        embeddings=vectors,
        documents=documents,
        metadatas=metadatas,
    )

    return {"collection": _collection_name(source_name), "count": len(chunks)}


def query(source_name: str, query_vector: list[float], top_k: int = 5) -> list[dict]:
    client = _get_client()
    collection = client.get_or_create_collection(name=_collection_name(source_name))

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
    )

    hits = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        hits.append({"text": doc, "metadata": meta, "distance": dist})

    return hits