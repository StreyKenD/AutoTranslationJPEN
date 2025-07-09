from paddleocr import PaddleOCR
import numpy as np
from typing import List, Tuple
import logging

default_ocr = PaddleOCR(
    lang='japan',
    use_angle_cls=True,
    det_db_box_thresh=0.3
)

# Return: List of (text, (x1, y1, x2, y2), confidence, angle)
def extract_text(image: np.ndarray) -> List[Tuple[str, Tuple[int, int, int, int], float, int]]:
    logging.debug('Starting OCR extraction')

    try:
        results = default_ocr.predict(image)

        if not isinstance(results, list) or len(results) == 0 or not isinstance(results[0], dict):
            logging.error("Unexpected result format from predict()")
            return []

        result = results[0]
        texts = result.get("rec_texts", [])
        scores = result.get("rec_scores", [])
        polys = result.get("rec_polys", [])
        angles = result.get("textline_orientation_angles", [])

        out = []
        for text, score, poly, angle in zip(texts, scores, polys, angles):
            try:
                if not text or score < 0.3:
                    continue

                xs = [p[0] for p in poly]
                ys = [p[1] for p in poly]
                x1, y1, x2, y2 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
                w, h = x2 - x1, y2 - y1

                is_vertical = h > w * 1.2  # More reliable than angle field
                if not is_vertical:
                    logging.debug(f'Skipping non-vertical: "{text}" (w={w}, h={h})')
                    continue

                out.append((text, (x1, y1, x2, y2), float(score), angle))
                logging.debug(f'OCR vertical text: "{text}" conf={score:.2f} box={(x1,y1,x2,y2)} angle={angle}')
            except Exception as e:
                logging.error(f"Error parsing OCR line: {e}")
                continue

        logging.info(f'OCR extraction complete: {len(out)} vertical lines found')
        return out

    except Exception as e:
        logging.error(f'OCR extraction failed: {e}')
        return []


def group_vertical_blocks(blocks, x_threshold=40) -> List[List[Tuple]]:
    groups = []
    for block in sorted(blocks, key=lambda b: b[1][0]):  # sort by x1
        added = False
        for group in groups:
            gx1, _, gx2, _ = group[-1][1]
            if abs(block[1][0] - gx1) < x_threshold or abs(block[1][2] - gx2) < x_threshold:
                group.append(block)
                added = True
                break
        if not added:
            groups.append([block])
    return groups
