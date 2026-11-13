import pdfplumber

with pdfplumber.open("uploads/sample.pdf") as pdf:
    for i, page in enumerate(pdf.pages, start=1):
        text = page.extract_text() or ""
        if "table" in text.lower():
            print(f"Page {i} mentions 'table'")