# manga_ocr_module.py
from manga_ocr import MangaOcr
from PIL import Image
import numpy as np
import cv2
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


def detect_text_orientation(img: Image.Image) -> str:
    """Return ``horizontal``, ``vertical`` or ``mixed`` for the given image."""
    arr = np.array(img.convert("L"))
    sobelx = cv2.Sobel(arr, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(arr, cv2.CV_64F, 0, 1, ksize=3)
    horiz = np.mean(np.abs(sobelx))
    vert = np.mean(np.abs(sobely))
    if horiz > vert * 1.2:
        return "horizontal"
    if vert > horiz * 1.2:
        return "vertical"
    return "mixed"

def extract_text(img):
    """Return recognized text, box, confidence and angle for ``img``."""
    if isinstance(img, np.ndarray):
        img = Image.fromarray(img)
    elif not isinstance(img, Image.Image):
        raise ValueError(f"img must be a path or PIL.Image, got {type(img)}")

    try:
        orient = detect_text_orientation(img)
        if orient == "vertical":
            proc_img = img.rotate(90, expand=True)
            angle = 90
        else:
            proc_img = img
            angle = 0

        result = _mocr(proc_img)
        conf = estimate_confidence(result)
        return [(result, (0, 0, img.width, img.height), conf, angle)]
    except Exception as e:
        print("OCR Error:", e)
        return []
