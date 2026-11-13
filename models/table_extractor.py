"""
table_extractor.py
Unit 11 — Multi-Modal RAG (tables).

Three-tier strategy, tried in order:
  1. Line-based detection (fast, works when the PDF has real drawn line borders)
  2. Text-alignment-based detection (works for borderless-but-real-text tables) —
     DISABLED by default; too prone to false positives on ordinary two-column
     article layouts, which look structurally similar to a table
  3. OCR fallback (for tables whose text is vector-drawn glyph outlines or
     scanned images, where no character data exists to extract at all) —
     only triggered when a page has an actual "TABLE" caption AND heavy
     vector/rect structure AND near-zero real extractable text
"""

from pathlib import Path
import re
import pytesseract
import config

pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH


def extract_tables(file_path: Path) -> list[dict]:
    import pdfplumber

    results = []

    with pdfplumber.open(str(file_path)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            found_usable_table = False

            for table in tables:
                if not table or len(table) < 2:
                    continue
                markdown = _table_to_markdown(table)
                if markdown:
                    results.append({"text": markdown, "page": page_num, "method": "text"})
                    found_usable_table = True

            # OCR fallback only when tier-1 found nothing actually usable
            if not found_usable_table and _has_undetected_table_caption(page):
                ocr_result = _ocr_table_region(page, page_num)
                if ocr_result:
                    results.append(ocr_result)

    return results


def _has_undetected_table_caption(page) -> bool:
    """
    Trigger OCR only when a page has a real "TABLE <roman numeral>" caption
    (academic papers' actual structural marker) that tier-1 detection failed
    to extract as a real table. Whitespace between "TABLE" and the numeral
    is optional — pdfplumber sometimes extracts them with no space at all
    (e.g. "TABLEI" instead of "TABLE I") due to kerning/spacing quirks.
    """
    text = page.extract_text() or ""
    return bool(re.search(r"\bTABLE\s*[IVXLC]+\b", text, re.IGNORECASE))


def _ocr_table_region(page, page_num: int) -> dict | None:
    im = page.to_image(resolution=300)
    text = pytesseract.image_to_string(im.original)

    text = text.strip()
    if not text or len(text) < 20:
        return None

    return {"text": text, "page": page_num, "method": "ocr"}


def _table_to_markdown(table: list[list]) -> str:
    rows = [[cell.strip() if cell else "" for cell in row] for row in table]
    rows = [r for r in rows if any(cell for cell in r)]

    if len(rows) < 2:
        return ""

    header = rows[0]
    separator = ["---"] * len(header)
    body = rows[1:]

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in body:
        padded = row + [""] * (len(header) - len(row))
        lines.append("| " + " | ".join(padded[:len(header)]) + " |")

    return "\n".join(lines)