"""
upload_controller.py
Orchestrates the full ingest pipeline for one uploaded document:
extract -> chunk -> embed -> store.
"""

import config
from models import document_processor, chunker, embedding_model, vector_store


def handle_upload(filename: str, file_bytes: bytes) -> dict:
    dest = config.UPLOAD_DIR / filename
    dest.write_bytes(file_bytes)

    raw_text = document_processor.extract_text(dest)
    if not raw_text.strip():
        raise ValueError("Could not extract any text from this file.")

    chunks = chunker.chunk_text(raw_text, source_name=filename)
    if not chunks:
        raise ValueError("Document produced no usable chunks after splitting.")

    vectors = embedding_model.embed_texts([c["text"] for c in chunks])
    result = vector_store.upsert_chunks(filename, chunks, vectors)

    return {
        "filename": filename,
        "chars_extracted": len(raw_text),
        "chunks_indexed": result["count"],
        "collection": result["collection"],
    }