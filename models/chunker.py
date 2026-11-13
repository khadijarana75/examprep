"""
chunker.py
Splits extracted document text into overlapping chunks for embedding + retrieval.
Unit 3 — recursive character-based splitting (default). Semantic chunking
comes later as an optional upgrade, not needed for a first working pipeline.
"""

import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
import config


def chunk_text(raw_text: str, source_name: str) -> list[dict]:
    """
    Split raw_text into chunks, each carrying metadata:
      - source: filename the chunk came from
      - page: page number this chunk starts on (tracked cumulatively, not
        just guessed from tags inside the chunk itself)
      - chunk_index: position among all chunks for this document
    Returns a list of dicts: {"text": ..., "metadata": {...}}
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    raw_chunks = splitter.split_text(raw_text)

    chunks = []
    running_page = 1

    for i, chunk in enumerate(raw_chunks):
        tags_in_chunk = re.findall(r"\[PAGE (\d+)\]", chunk)
        if tags_in_chunk:
            running_page = int(tags_in_chunk[0])
            next_running_page = int(tags_in_chunk[-1])
        else:
            next_running_page = running_page

        clean_text = re.sub(r"\[PAGE \d+\]\n?", "", chunk).strip()

        if not clean_text:
            running_page = next_running_page
            continue

        chunks.append({
            "text": clean_text,
            "metadata": {
                "source": source_name,
                "page": running_page,
                "chunk_index": i,
            },
        })

        running_page = next_running_page

    return chunks