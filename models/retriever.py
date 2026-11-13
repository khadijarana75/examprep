"""
retriever.py
Unit 6/7/8 combined: runs multi-query retrieval against the vector store,
merges + dedupes hits from all query variants, then reranks the merged
set down to a final top_k.
"""

from models import embedding_model, vector_store, reranker, query_expansion


def retrieve(source_name: str, topic: str, candidates_per_query: int = 5, final_top_k: int = 5) -> list[dict]:
    """
    Full retrieval pipeline for one topic:
      1. Expand the topic into a few phrasings (Unit 7)
      2. Embed + search each phrasing against the vector store (Unit 6)
      3. Merge and dedupe hits by chunk_index
      4. Rerank the merged set with a cross-encoder (Unit 8)
    """
    queries = query_expansion.expand_query(topic)

    seen_chunk_indexes = set()
    merged_hits = []

    for q in queries:
        query_vector = embedding_model.embed_query(q)
        hits = vector_store.query(source_name, query_vector, top_k=candidates_per_query)

        for h in hits:
            idx = h["metadata"]["chunk_index"]
            if idx not in seen_chunk_indexes:
                seen_chunk_indexes.add(idx)
                merged_hits.append(h)

    return reranker.rerank(topic, merged_hits, top_k=final_top_k)