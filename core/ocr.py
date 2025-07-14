import cv2
from paddleocr import PaddleOCR, TextRecognition
import numpy as np
from typing import List, Tuple
import logging
from core.capture import enhance_for_ocr_debug


# Initialize OCR
default_ocr = PaddleOCR(
    text_recognition_model_name="PP-OCRv5_server_rec",
    text_detection_model_name="PP-OCRv5_server_det",
    use_textline_orientation=True,
    device="gpu:0"
)

def ocr_single_bubble(
    crop: np.ndarray,
    x_off: int,
    y_off: int,
    min_score: float = 0.5
) -> tuple[str, tuple[int,int,int,int], float]:
    """
    OCR one bubble crop, merge its vertical lines (top→bottom),
    and return (merged_text, full_image_box, avg_conf).
    """
    # 1) Run OCR on crop
    res = default_ocr.predict(crop)
    if not res or not isinstance(res[0], dict):
        return "", (x_off, y_off, x_off, y_off), 0.0
    r = res[0]
    texts  = r.get("rec_texts", [])
    scores = r.get("rec_scores", [])
    polys  = r.get("rec_polys", [])

    # 2) Collect lines as (y1, text, box, score)
    lines = []
    for text, score, poly in zip(texts, scores, polys):
        if not text or score < min_score:
            continue
        xs = [pt[0] for pt in poly]
        ys = [pt[1] for pt in poly]
        x1, y1 = int(min(xs)), int(min(ys))
        x2, y2 = int(max(xs)), int(max(ys))
        lines.append((y1, text, (x1, y1, x2, y2), score))

    if not lines:
        return "", (x_off, y_off, x_off, y_off), 0.0

    # 3) Sort top→bottom
    lines.sort(key=lambda l: l[0])

    # 4) Merge text inline and average confidence
    merged_text = "".join(l[1] for l in lines)
    avg_conf = sum(l[3] for l in lines) / len(lines)

    # 5) Build full-image box
    x1 = x_off + min(l[2][0] for l in lines)
    y1 = y_off + min(l[2][1] for l in lines)
    x2 = x_off + max(l[2][2] for l in lines)
    y2 = y_off + max(l[2][3] for l in lines)

    return merged_text, (x1, y1, x2, y2), avg_conf


def extract_text_from_bubbles(
    bubble_images: List[Tuple[np.ndarray, Tuple[int, int, int, int]]]
) -> List[Tuple[str, Tuple[int, int, int, int], float, int]]:
    all_blocks = []

    for idx, (crop, (x_offset, y_offset, _, _)) in enumerate(bubble_images):
        try:
            cv2.imwrite(f"debug/crop_{idx}_before.png", crop)
            crop = enhance_for_ocr_debug(crop)
            cv2.imwrite(f"debug/crop_{idx}_after.png", crop)

            result = default_ocr.predict(crop)
            if not result or not isinstance(result[0], dict):
                logging.warning(f"OCR result for bubble {idx} is empty or invalid.")
                continue
# 
            # logging.debug(f"OCR result for bubble {idx}: {result[0]}")
            logging.debug(f"texts: {result[0].get('rec_texts', [])}")

            r = result[0]
            texts = r.get("rec_texts", [])
            scores = r.get("rec_scores", [])
            polys = r.get("rec_polys", [])
            angles = r.get("textline_orientation_angles", [])

            lines = []

            for text, score, poly, angle in zip(texts, scores, polys, angles):
                if not text or score < 0.5:
                    continue
                xs = [pt[0] for pt in poly]
                ys = [pt[1] for pt in poly]
                x1, y1, x2, y2 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
                lines.append(((y1, text), (x1, y1, x2, y2), score))

            if lines:
                # Sort top to bottom
                lines.sort(key=lambda l: l[0][0])

                bubble_text = [line[0][1] for line in lines]
                total_conf = sum(l[2] for l in lines)
                count = len(lines)

                min_x = min(l[1][0] for l in lines)
                min_y = min(l[1][1] for l in lines)
                max_x = max(l[1][2] for l in lines)
                max_y = max(l[1][3] for l in lines)

                merged_text = "".join(bubble_text)
                conf = total_conf / count
                x1 = x_offset + min_x
                y1 = y_offset + min_y
                x2 = x_offset + max_x
                y2 = y_offset + max_y
                all_blocks.append((merged_text, (x1, y1, x2, y2), conf, 1))
                logging.debug(f"Merged bubble text (sorted): \"{merged_text}\"")

        except Exception as e:
            logging.error(f"OCR failed on bubble {idx}: {e}")
            continue

    logging.info(f"Grouped OCR blocks: {len(all_blocks)}")

    # --- ensure bubbles themselves come out in right-to-left reading order ---
    # each block: (text, (x1,y1,x2,y2), conf, angle)
    all_blocks.sort(key=lambda b: b[1][0], reverse=True)
    logging.info(f"OCR blocks after right-to-left sort: {all_blocks}")
    return all_blocks

def extract_text_full_image(
    image: np.ndarray,
    min_score: float = 0.5
) -> list[tuple[str, tuple[int,int,int,int], float]]:
    """
    Runs OCR on the whole image. Returns list of
      (text, (x1,y1,x2,y2), score)
    """
    res = default_ocr.predict(image)
    if not res or not isinstance(res[0], dict):
        return []
    r = res[0]
    texts  = r.get("rec_texts", [])
    scores = r.get("rec_scores", [])
    polys  = r.get("rec_polys", [])

    blocks = []
    for text, score, poly in zip(texts, scores, polys):
        if not text or score < min_score:
            continue
        xs, ys = zip(*poly)
        x1, y1 = int(min(xs)), int(min(ys))
        x2, y2 = int(max(xs)), int(max(ys))
        blocks.append((text, (x1, y1, x2, y2), float(score)))
    return blocks