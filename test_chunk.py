from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from models import document_processor
import config

path = Path("uploads/sample.pdf")
text = document_processor.extract_text(path)

print(f"Raw text length: {len(text)}")
print("--- Raw text sample (chars 0-1000) ---")
print(repr(text[:1000]))

splitter = RecursiveCharacterTextSplitter(
    chunk_size=config.CHUNK_SIZE,
    chunk_overlap=config.CHUNK_OVERLAP,
    separators=["\n\n", "\n", ". ", " ", ""],
)
raw_chunks = splitter.split_text(text)
print(f"\nRaw chunks before filtering: {len(raw_chunks)}")
if raw_chunks:
    print("--- First raw chunk ---")
    print(repr(raw_chunks[0]))