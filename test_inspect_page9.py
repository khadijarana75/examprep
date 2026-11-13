import pdfplumber

with pdfplumber.open("uploads/sample.pdf") as pdf:
    page = pdf.pages[8]  # 0-indexed, so page 9 is index 8

    print("--- Raw text of page 9 ---")
    print(page.extract_text())

    print("\n--- Words with positions (first 40) ---")
    words = page.extract_words()
    for w in words[:40]:
        print(f"x0={w['x0']:.1f} x1={w['x1']:.1f} top={w['top']:.1f} text={w['text']}")

    print(f"\nTotal words on page: {len(words)}")
    print(f"Lines detected (rects/edges): {len(page.lines)} lines, {len(page.rects)} rects")