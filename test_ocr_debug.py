import pdfplumber
import pytesseract
import config

pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_PATH

with pdfplumber.open("uploads/sample.pdf") as pdf:
    page = pdf.pages[8]  # page 9

    print("Rendering page to image...")
    im = page.to_image(resolution=300)
    im.save("page9_full_debug.png")
    print("Saved page9_full_debug.png")

    print("\nRunning OCR...")
    text = pytesseract.image_to_string(im.original)
    print(f"OCR text length: {len(text)}")
    print("--- OCR output ---")
    print(text)