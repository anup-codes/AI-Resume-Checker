import os
from ocr import EasyOcrProcessor
from config import OUTPUT_PATH
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import tempfile



def get_ocr_processor():
    """Creates and returns configured OCR processor."""
    config = {
        "storage_type": "local",
        "storage_path": OUTPUT_PATH
    }
    os.makedirs(config["storage_path"], exist_ok=True)
    return EasyOcrProcessor(config)


def extract_text_with_ocr(file_path):
    """
    Runs OCR on image or PDF and returns extracted text.
    Always returns a string (never None).
    """
    processor = get_ocr_processor()
    file_path_lower = file_path.lower()

    text = ""  # default fallback

    # --------------------------
    # IMAGE FILES
    # --------------------------
    if file_path_lower.endswith((".png", ".jpg", ".jpeg")):
        text = processor.process_image(file_path) or ""
        print("IMAGE OCR OUTPUT:", text)
        

    # --------------------------
    # PDF FILES
    # --------------------------
    elif file_path_lower.endswith(".pdf"):

    # Extract embedded text first
        reader = PdfReader(file_path)
        text = "".join(page.extract_text() or "" for page in reader.pages)

        # If extracted text is too small, run OCR
        if len(text.strip()) < 100:

            images = convert_from_path(
                file_path,
                dpi=300,
                poppler_path="C:\\poppler-25.12.0\\Library\\bin"
            )

            ocr_text = ""

            for image in images:
                image = image.convert("L")  # grayscale

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp:
                    image.save(temp.name, "PNG")
                    ocr_text += processor.process_image(temp.name) or ""

            text = ocr_text
            print("IMAGE OCR OUTPUT:", text.encode("utf-8", errors="ignore").decode("utf-8"))


            


    # --------------------------
    # UNSUPPORTED FILES
    # --------------------------
    else:
        text = ""
    
    print("FINAL EXTRACTED TEXT LENGTH:", len(text))
    print("FINAL EXTRACTED TEXT PREVIEW:", text[:500])


    # Final safeguard: always return a string
    return text or ""