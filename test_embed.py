from pathlib import Path
from models import document_processor, chunker, embedding_model

path = Path("uploads/sample.pdf")
text = document_processor.extract_text(path)
chunks = chunker.chunk_text(text, source_name="sample.pdf")

print(f"Chunks to embed: {len(chunks)}")

texts = [c["text"] for c in chunks]
vectors = embedding_model.embed_texts(texts)

print(f"Vectors returned: {len(vectors)}")
print(f"Vector dimension: {len(vectors[0])}")
print("--- First 5 values of first vector ---")
print(vectors[0][:5])