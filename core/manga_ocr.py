# manga_ocr_module.py
from manga_ocr import MangaOcr
from PIL import Image
import numpy as np

# Initialize OCR once (loads ~400 MB model at startup) :contentReference[oaicite:1]{index=1}
_mocr = MangaOcr()

def extract_text(img):
    if isinstance(img, np.ndarray):
        img = Image.fromarray(img)
    elif not isinstance(img, Image.Image):
        raise ValueError(f"img must be a path or PIL.Image, got {type(img)}")
    
    try:
        result = _mocr(img)
        # Wrap result to match your pipeline format
        # Assuming dummy box and confidence since MangaOcr doesn't return them
        return [(result, (0, 0, img.width, img.height), 1.0, 0)]
    except Exception as e:
        print("OCR Error:", e)
        return []
