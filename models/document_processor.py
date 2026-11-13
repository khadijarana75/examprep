"""
document_processor.py
Extracts plain text from uploaded PDF / TXT / DOCX files.
"""

from pathlib import Path
import config


class UnsupportedFileType(Exception):
    pass


def extract_text(file_path: Path) -> str:
    """Return plain text content for a supported file type."""
    ext = file_path.suffix.lower()

    if ext not in config.ALLOWED_EXTENSIONS:
        raise UnsupportedFileType(
            f"'{ext}' is not supported. Allowed: {sorted(config.ALLOWED_EXTENSIONS)}"
        )

    if ext == ".txt":
        return file_path.read_text(encoding="utf-8", errors="ignore")

    if ext == ".pdf":
        return _extract_pdf(file_path)

    if ext == ".docx":
        return _extract_docx(file_path)

    raise UnsupportedFileType(ext)


def _extract_pdf(file_path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(file_path))
    pages = []
    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        # tag each page so later chunking can carry page numbers in metadata
        pages.append(f"[PAGE {page_num}]\n{text}")
    return "\n\n".join(pages)


def _extract_docx(file_path: Path) -> str:
    import docx  # python-docx

    doc = docx.Document(str(file_path))
    return "\n".join(p.text for p in doc.paragraphs)