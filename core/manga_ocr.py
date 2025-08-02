"""Utilities for running Manga-OCR and post-processing results."""

from __future__ import annotations

import logging
import re
from typing import List, Tuple

import cv2
import numpy as np
from PIL import Image
from manga_ocr import MangaOcr


logger = logging.getLogger(__name__)

# Initialize OCR once (loads ~400 MB model at startup)
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


def extract_text(
    img: Image.Image | np.ndarray,
) -> List[Tuple[str, Tuple[int, int, int, int], float, int]]:
    """Return recognized text blocks for ``img``.

    Args:
        img: Image array or ``PIL.Image`` to process.

    Returns:
        list[tuple[str, tuple[int, int, int, int], float, int]]: Recognized
            text, bounding box, confidence score and rotation angle.
    """

    if isinstance(img, np.ndarray):
        img = Image.fromarray(img)
    elif not isinstance(img, Image.Image):  # pragma: no cover - defensive branch
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
    except Exception as e:  # pragma: no cover - OCR failures are rare
        logger.error("OCR Error: %s", e)
        return []
