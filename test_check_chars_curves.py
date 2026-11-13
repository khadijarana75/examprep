import pdfplumber

with pdfplumber.open("uploads/sample.pdf") as pdf:
    page = pdf.pages[8]

    table1_region = page.crop((0, 64, page.width, 164))

    print(f"chars in region: {len(table1_region.chars)}")
    print(f"curves in region: {len(table1_region.curves)}")
    print(f"lines in region: {len(table1_region.lines)}")
    print(f"rects in region: {len(table1_region.rects)}")

    if table1_region.curves:
        print("\n--- Sample curve ---")
        print(table1_region.curves[0])