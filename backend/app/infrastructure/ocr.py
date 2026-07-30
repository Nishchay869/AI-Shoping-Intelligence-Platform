"""Local OCR via Tesseract (pytesseract) - runs on-device, no API key, so this step is fully verifiable offline.

Receipts are a hard OCR case: thermal-printer fonts, low contrast, creased paper. A grayscale + fixed
threshold pass before running tesseract measurably improves character accuracy over feeding it the raw
photo directly, so that preprocessing lives here rather than being left to the caller.
"""
import io
from PIL import Image, ImageOps
import pytesseract

TESSERACT_CONFIG = "--oem 3 --psm 6"  # psm 6: assume a single uniform block of text - a receipt's item column
BINARIZATION_THRESHOLD = 150


def _preprocess(image: Image.Image) -> Image.Image:
    grayscale = ImageOps.grayscale(image)
    return grayscale.point(lambda pixel: 255 if pixel > BINARIZATION_THRESHOLD else 0)


def extract_text(image_bytes: bytes) -> tuple[str, float]:
    """OCR a receipt image. Returns (raw_text with line breaks preserved, mean word confidence in [0, 1])."""
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    processed = _preprocess(image)
    text = pytesseract.image_to_string(processed, config=TESSERACT_CONFIG).strip()

    data = pytesseract.image_to_data(processed, config=TESSERACT_CONFIG, output_type=pytesseract.Output.DICT)
    confidences = [float(conf) for conf in data["conf"] if float(conf) >= 0]  # tesseract emits -1 for non-text regions
    mean_confidence = (sum(confidences) / len(confidences) / 100) if confidences else 0.0
    return text, mean_confidence
