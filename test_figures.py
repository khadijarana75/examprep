from pathlib import Path
from models import figure_extractor

path = Path("uploads/sample.pdf")
captions = figure_extractor.extract_figure_captions(path)

print(f"Captions found: {len(captions)}")
for c in captions:
    print(f"\nPage {c['page']}: {c['text']}")