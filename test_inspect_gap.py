import pdfplumber

with pdfplumber.open("uploads/sample.pdf") as pdf:
    page = pdf.pages[8]

    print(f"Images on page: {len(page.images)}")
    for img in page.images:
        print(f"  image at top={img['top']:.1f} bottom={img['bottom']:.1f} x0={img['x0']:.1f} x1={img['x1']:.1f}")

    print(f"\nRects in the table-caption gap (top 60-260):")
    gap_rects = [r for r in page.rects if 60 <= r['top'] <= 260]
    print(f"  {len(gap_rects)} rects found in that range")
    for r in gap_rects[:15]:
        print(f"  top={r['top']:.1f} bottom={r['bottom']:.1f} x0={r['x0']:.1f} x1={r['x1']:.1f}")

    # crop just that region and render it as an image so we can SEE it
    cropped = page.crop((0, 60, page.width, 260))
    im = cropped.to_image(resolution=150)
    im.save("table_region_debug.png")
    print("\nSaved cropped region to table_region_debug.png — open it and look")