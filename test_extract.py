from pathlib import Path
from models import document_processor

# change this to a real PDF you have handy
path = Path("uploads/sample.pdf")
text = document_processor.extract_text(path)

print(f"Extracted {len(text)} characters")
print("--- First 500 chars ---")
print(text[:500])