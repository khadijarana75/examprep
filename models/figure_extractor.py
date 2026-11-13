"""
figure_extractor.py
Unit 11 — Multi-Modal RAG (figures).

We don't have a vision-capable model on this Groq account, so we can't
interpret figure *content*. What we CAN do, and what's genuinely useful:
extract figure captions ("Fig. 3 shows...") as their own indexed chunks,
so a question can correctly reference what a given figure demonstrates
even though the model never "saw" the image itself.
"""

from pathlib import Path
import re


def extract_figure_captions(file_path: Path) -> list[dict]:
    import pdfplumber

    results = []

    with pdfplumber.open(str(file_path)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            captions = _find_captions(text)
            for caption in captions:
                results.append({"text": caption, "page": page_num})

    return results


def _find_captions(text: str) -> list[str]:
    """
    Real figure captions sit on their own line in the extracted text
    (confirmed by inspection — e.g. "Fig.2. Samples...without dust."
    appears as a complete standalone line). In-text references like
    "Fig. 7 shows the chosen..." appear embedded inside paragraph lines
    instead. Matching whole lines that START with the Fig pattern reliably
    separates true captions from references, without needing to guess
    where a caption "ends" from punctuation alone.
    """
    pattern = r"^Fig(?:ure)?\.?\s*\d+\.?\s"

    captions = []
    for line in text.split("\n"):
        line = line.strip()
        if re.match(pattern, line, re.IGNORECASE) and len(line) > 10:
            captions.append(line)

    return captions