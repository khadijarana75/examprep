import pdfplumber

with pdfplumber.open("uploads/sample.pdf") as pdf:
    page = pdf.pages[8]

    # crop to just the Table I region (roughly top=64 to top=164, based on
    # earlier output showing TABLE II caption starts at top=164.1)
    table1_region = page.crop((0, 64, page.width, 164))
    words = table1_region.extract_words()

    print(f"Words found in Table I region: {len(words)}")
    for w in words:
        print(f"x0={w['x0']:.1f} top={w['top']:.1f} text={w['text']}")