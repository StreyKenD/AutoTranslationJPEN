# core/pipeline.py
from core.capture import grab_region
from core.yolo_bubble import detect_bubbles
from core.manga_ocr import extract_text
from core.translate import translate_batch
import logging
import cv2

logger = logging.getLogger(__name__)

def process_region(img, region, timings=None):
    """
    Full pipeline: capture -> detect bubbles -> OCR -> translate
    Returns: (blocks, translations)
    blocks: list of tuples (text, (x1, y1, x2, y2), conf, angle)
    """
    import time
    t0 = time.perf_counter()

    # Step 1: Capture region
    
    t1 = time.perf_counter()
    if timings is not None:
        timings['grab_region'] = t1 - t0

    bubble_crops = detect_bubbles(img)
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
    for crop, offset in bubble_crops:
        x1_off, y1_off, _, _ = offset
        ocr_results = extract_text(crop)
        for text, (bx1, by1, bx2, by2), conf, angle in ocr_results:
            global_box = (bx1 + x1_off, by1 + y1_off, bx2 + x1_off, by2 + y1_off)
            raw_blocks.append((text, global_box, conf, angle))

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

    blocks = [(text, box, conf, angle) for (text, box, conf, angle) in raw_blocks]
    t4 = time.perf_counter()
    if timings is not None:
        timings['translate'] = t4 - t3

    return blocks, translations
