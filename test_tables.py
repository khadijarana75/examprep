from pathlib import Path
from models import table_extractor

path = Path("uploads/sample.pdf")
tables = table_extractor.extract_tables(path)

print(f"Tables found: {len(tables)}")
for t in tables:
    print(f"\n--- Page {t['page']} ---")
    print(t["text"])