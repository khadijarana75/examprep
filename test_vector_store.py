from pathlib import Path
from models import document_processor, chunker, embedding_model, vector_store

path = Path("uploads/sample.pdf")
source_name = "sample.pdf"

text = document_processor.extract_text(path)
chunks = chunker.chunk_text(text, source_name=source_name)
vectors = embedding_model.embed_texts([c["text"] for c in chunks])

result = vector_store.upsert_chunks(source_name, chunks, vectors)
print(f"Upserted: {result}")

# now do a real similarity search — change this query to something
# you know is actually discussed in your sample.pdf
topic = "What method is used for denoising the beam images?"
query_vector = embedding_model.embed_query(topic)
hits = vector_store.query(source_name, query_vector, top_k=3)

print(f"\n--- Top {len(hits)} results for: '{topic}' ---")
for i, hit in enumerate(hits):
    print(f"\n[{i+1}] distance={hit['distance']:.4f} page={hit['metadata']['page']}")
    print(hit["text"][:300])