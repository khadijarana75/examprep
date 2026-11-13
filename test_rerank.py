from pathlib import Path
from models import document_processor, chunker, embedding_model, vector_store, reranker

source_name = "sample.pdf"
topic = "What method is used for denoising the beam images?"

# assumes sample.pdf is already indexed from earlier tests
query_vector = embedding_model.embed_query(topic)
hits = vector_store.query(source_name, query_vector, top_k=10)  # cast a wider net first

print(f"First-stage retrieval: {len(hits)} hits")
print("--- Top 3 BEFORE reranking (by embedding distance) ---")
for h in hits[:3]:
    print(f"distance={h['distance']:.4f} | {h['text'][:100]}")

reranked = reranker.rerank(topic, hits, top_k=3)

print("\n--- Top 3 AFTER reranking (by cross-encoder score) ---")
for h in reranked:
    print(f"rerank_score={h['rerank_score']:.4f} | {h['text'][:100]}")