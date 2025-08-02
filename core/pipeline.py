# core/pipeline.py
"""End-to-end pipeline for bubble detection, OCR and translation."""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, List, Tuple

import cv2
import numpy as np

from core.manga_ocr import extract_text
from core.translate import TRANSLATOR, translate_batch
from core.yolo_bubble import detect_bubbles

logger = logging.getLogger(__name__)

# Directory for saving bubble snapshots
BUBBLE_DIR = Path(__file__).resolve().parent.parent / "bubble_logs"
BUBBLE_DIR.mkdir(exist_ok=True)
BUBBLE_CSV = BUBBLE_DIR / "bubbles.csv"


def _log_bubble(
    crop: np.ndarray,
    text: str,
    translation: str,
    engine: str,
    conf: float,
    edited: bool = False,
) -> None:
    """Save bubble image and translation entry with metadata."""

    import time

    img_path = BUBBLE_DIR / f"bubble_{int(time.time()*1000)}.png"
    try:
        cv2.imwrite(str(img_path), crop)
    except Exception as e:  # pragma: no cover - image write failure
        logger.error("Failed to save bubble image: %s", e)
    write_header = not BUBBLE_CSV.exists()
    try:
        with open(BUBBLE_CSV, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(
                    [
                        "image",
                        "japanese",
                        "english",
                        "engine",
                        "confidence",
                        "edited",
                    ]
                )
            writer.writerow(
                [img_path.name, text, translation, engine, f"{conf:.2f}", int(edited)]
            )
    except Exception as e:  # pragma: no cover
        logger.error("Failed to log bubble image: %s", e)


def process_region(
    img: np.ndarray,
    region: dict[str, int],
    bubble_padding: int = 0,
    timings: dict[str, float] | None = None,
    save_bubble_images: bool = False,
    conf_threshold: float = 0.5,
    min_width: int = 25,
    min_height: int = 25,
) -> Tuple[List[Tuple[str, Tuple[int, int, int, int], float, int, Any]], List[str]]:
    """Run detection, OCR and translation for a region.

    Args:
        img: Source image in BGR format.
        region: Screen region metadata (currently unused).
        bubble_padding: Extra pixels around detected bubbles.
        timings: Optional dict to store timing information.
        save_bubble_images: If ``True``, cropped bubbles are stored to disk.
        conf_threshold: Warn when estimated OCR confidence is below this value.
        min_width: Minimum bubble width in pixels.
        min_height: Minimum bubble height in pixels.

    Returns:
        tuple[list, list[str]]: OCR blocks and corresponding translations.
    """

    import time

    t0 = time.perf_counter()

    # Step 1: Capture region (caller provides ``img``)

    t1 = time.perf_counter()
    if timings is not None:
        timings["grab_region"] = t1 - t0

    bubble_crops = detect_bubbles(
        img,
        padding=bubble_padding,
        min_width=min_width,
        min_height=min_height,
        return_contours=True,
    )
    logging.info("Detected %d bubbles", len(bubble_crops))
    if not bubble_crops:
        logging.info("No bubbles detected. Skipping OCR.")
        return [], []

    debug = img.copy()
    for _, (x1, y1, x2, y2), *_ in bubble_crops:
        cv2.rectangle(debug, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.imwrite("debug_bubbles.png", debug)

    t2 = time.perf_counter()
    if timings is not None:
        timings["detect_bubbles"] = t2 - t1

    # Step 3: OCR with offset correction
    raw_blocks: List[Tuple[str, Tuple[int, int, int, int], float, int, Any]] = []
    crop_images: List[np.ndarray] = []
    for data in bubble_crops:
        if len(data) == 3:
            crop, offset, contour = data
        else:
            crop, offset = data
            contour = None
        x1_off, y1_off, _, _ = offset
        ocr_results = extract_text(crop)
        for text, (bx1, by1, bx2, by2), conf, angle in ocr_results:
            global_box = (bx1 + x1_off, by1 + y1_off, bx2 + x1_off, by2 + y1_off)
            raw_blocks.append((text, global_box, conf, angle, contour))
            crop_images.append(crop)
            if conf < conf_threshold:
                logger.warning("Low OCR confidence %.2f for text: %s", conf, text)

    if not raw_blocks:
        logging.info("No OCR text detected in any bubble. Skipping translation.")
        return [], []

    logging.info("OCR extracted %d bubbles", len(raw_blocks))
    logging.debug("Raw OCR blocks: %s", raw_blocks)

    t3 = time.perf_counter()
    if timings is not None:
        timings["ocr_extract"] = t3 - t2

    # Step 4: Translate
    texts = [text for text, *_ in raw_blocks]
    translations = translate_batch(texts)
    logging.info("Translation complete")

    if save_bubble_images:
        conf_values = [b[2] for b in raw_blocks]
        for crop, src, trans, conf in zip(
            crop_images, texts, translations, conf_values
        ):
            _log_bubble(crop, src, trans, TRANSLATOR, conf)

    blocks = [
        (text, box, conf, angle, contour)
        for (text, box, conf, angle, contour) in raw_blocks
    ]
    t4 = time.perf_counter()
    if timings is not None:
        timings["translate"] = t4 - t3

    return blocks, translations
