import pdfplumber

with pdfplumber.open("uploads/sample.pdf") as pdf:
    page = pdf.pages[8]

    table_settings = {
        "vertical_strategy": "explicit",
        "horizontal_strategy": "explicit",
        "explicit_vertical_lines": page.rects,
        "explicit_horizontal_lines": page.rects,
    }

    tables = page.extract_tables(table_settings=table_settings)
    print(f"Tables found: {len(tables)}")

    for i, table in enumerate(tables):
        print(f"\n--- Table {i+1} ({len(table)} rows) ---")
        for row in table[:5]:  # just first 5 rows to keep output readable
            print(row)