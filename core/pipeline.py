# core/pipeline.py
from core.capture import grab_region
from core.yolo_bubble import detect_bubbles
from core.manga_ocr import extract_text
from core.translate import translate_batch
import logging
import cv2
from pathlib import Path
import csv

logger = logging.getLogger(__name__)

# Directory for saving bubble snapshots
BUBBLE_DIR = Path(__file__).resolve().parent.parent / "bubble_logs"
BUBBLE_DIR.mkdir(exist_ok=True)
BUBBLE_CSV = BUBBLE_DIR / "bubbles.csv"


def _log_bubble(crop, text: str, translation: str) -> None:
    """Save bubble image and translation entry."""
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
                writer.writerow(["image", "japanese", "english"])
            writer.writerow([img_path.name, text, translation])
    except Exception as e:  # pragma: no cover
        logger.error("Failed to log bubble image: %s", e)

def process_region(
    img,
    region,
    bubble_padding: int = 0,
    timings=None,
    save_bubble_images: bool = False,
    conf_threshold: float = 0.5,
):
    """Run capture→detection→OCR→translate for a region.

    Parameters
    ----------
    img : ndarray
        Source image in BGR format.
    region : dict
        Screen region metadata.
    bubble_padding : int, optional
        Extra pixels around detected bubbles.
    timings : dict, optional
        Timing information will be stored here.
    save_bubble_images : bool, optional
        If ``True``, cropped bubbles are stored to disk.
    conf_threshold : float, optional
        Warn when estimated OCR confidence is below this value.
    """
    import time
    t0 = time.perf_counter()

    # Step 1: Capture region
    
    t1 = time.perf_counter()
    if timings is not None:
        timings['grab_region'] = t1 - t0

    bubble_crops = detect_bubbles(img, padding=bubble_padding)
    logging.info(f"Detected {len(bubble_crops)} bubbles")
    if not bubble_crops:
        logging.info("No bubbles detected. Skipping OCR.")
        return [], []
    
    debug = img.copy()
    for _, (x1,y1,x2,y2) in bubble_crops:
        cv2.rectangle(debug, (x1,y1),(x2,y2),(0,0,255),2)
    cv2.imwrite("debug_bubbles.png", debug)

    t2 = time.perf_counter()
    if timings is not None:
        timings['detect_bubbles'] = t2 - t1

    # Step 3: OCR with offset correction
    raw_blocks = []
    crop_images = []
    for crop, offset in bubble_crops:
        x1_off, y1_off, _, _ = offset
        ocr_results = extract_text(crop)
        for text, (bx1, by1, bx2, by2), conf, angle in ocr_results:
            global_box = (bx1 + x1_off, by1 + y1_off, bx2 + x1_off, by2 + y1_off)
            raw_blocks.append((text, global_box, conf, angle))
            crop_images.append(crop)
            if conf < conf_threshold:
                logger.warning("Low OCR confidence %.2f for text: %s", conf, text)

    if not raw_blocks:
        logging.info("No OCR text detected in any bubble. Skipping translation.")
        return [], []
    
    logging.info(f"OCR extracted {len(raw_blocks)} bubbles")
    logging.debug(f"Raw OCR blocks: {raw_blocks}")

    t3 = time.perf_counter()
    if timings is not None:
        timings['ocr_extract'] = t3 - t2

    # Step 4: Translate
    texts = [text for text, _, _, _ in raw_blocks]
    translations = translate_batch(texts)
    logging.info("Translation complete")

    if save_bubble_images:
        for crop, src, trans in zip(crop_images, texts, translations):
            _log_bubble(crop, src, trans)

    blocks = [(text, box, conf, angle) for (text, box, conf, angle) in raw_blocks]
    t4 = time.perf_counter()
    if timings is not None:
        timings['translate'] = t4 - t3

    return blocks, translations
