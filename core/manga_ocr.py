# manga_ocr_module.py
from manga_ocr import MangaOcr
from PIL import Image
import numpy as np
import re

# Initialize OCR once (loads ~400 MB model at startup) :contentReference[oaicite:1]{index=1}
_mocr = MangaOcr()


JAPANESE_RE = re.compile(r"[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9faf]")


def estimate_confidence(text: str) -> float:
    """Return a simple confidence score based on Japanese character ratio."""
    if not text:
        return 0.0
    matches = len(JAPANESE_RE.findall(text))
    return matches / len(text)

def extract_text(img):
    """Return recognized text, box and confidence for the given image."""
    if isinstance(img, np.ndarray):
        img = Image.fromarray(img)
    elif not isinstance(img, Image.Image):
        raise ValueError(f"img must be a path or PIL.Image, got {type(img)}")
    
    try:
        result = _mocr(img)
        conf = estimate_confidence(result)
        # Wrap result with a heuristic confidence score
        return [(result, (0, 0, img.width, img.height), conf, 0)]
    except Exception as e:
        print("OCR Error:", e)
        return []
