from paddleocr import PaddleOCR
import numpy as np
from typing import List, Tuple
import logging

# Initialize OCR
default_ocr = PaddleOCR(
    lang='japan',
    use_angle_cls=True,
    det_db_box_thresh=0.3
)

def extract_text_from_bubbles(
    bubble_images: List[Tuple[np.ndarray, Tuple[int, int, int, int]]]
) -> List[Tuple[str, Tuple[int, int, int, int], float, int]]:
    all_blocks = []

    for idx, (crop, (x_offset, y_offset, _, _)) in enumerate(bubble_images):
        try:
            result = default_ocr.predict(crop)
            if not result or not isinstance(result[0], dict):
                logging.warning(f"OCR result for bubble {idx} is empty or invalid.")
                continue

            r = result[0]
            texts = r.get("rec_texts", [])
            scores = r.get("rec_scores", [])
            polys = r.get("rec_polys", [])
            angles = r.get("textline_orientation_angles", [])

            bubble_text = []
            min_x, min_y, max_x, max_y = 9999, 9999, 0, 0
            total_conf = 0
            count = 0

            for text, score, poly, angle in zip(texts, scores, polys, angles):
                if not text or score < 0.5:
                    continue
                bubble_text.append(text)
                xs = [pt[0] for pt in poly]
                ys = [pt[1] for pt in poly]
                x1, y1, x2, y2 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
                min_x = min(min_x, x1)
                min_y = min(min_y, y1)
                max_x = max(max_x, x2)
                max_y = max(max_y, y2)
                total_conf += score
                count += 1

            if bubble_text:
                merged_text = "\n".join(bubble_text)  # or " ".join(...) for inline
                conf = total_conf / count
                x1 = x_offset + min_x
                y1 = y_offset + min_y
                x2 = x_offset + max_x
                y2 = y_offset + max_y
                all_blocks.append((merged_text, (x1, y1, x2, y2), conf, 1))
                logging.debug(f"Merged bubble text: \"{merged_text}\"")

        except Exception as e:
            logging.error(f"OCR failed on bubble {idx}: {e}")
            continue

    logging.info(f"Grouped OCR blocks: {len(all_blocks)}")
    return all_blocks



def group_vertical_blocks(blocks, max_dx=30, max_dy=20):
    # Sort top-to-bottom, left-to-right
    blocks = sorted(blocks, key=lambda b: (b[1][0], b[1][1]))
    groups = []

    for block in blocks:
        added = False
        for group in groups:
            last = group[-1]
            lx1, ly1, lx2, ly2 = last[1]
            bx1, by1, bx2, by2 = block[1]
            if abs(bx1 - lx1) <= max_dx and abs(by1 - ly2) <= max_dy:
                group.append(block)
                added = True
                break
        if not added:
            groups.append([block])
    return groups

def merge_block_groups(groups):
    merged = []
    for group in groups:
        text = ''.join([b[0] for b in group])
        x1 = min(b[1][0] for b in group)
        y1 = min(b[1][1] for b in group)
        x2 = max(b[1][2] for b in group)
        y2 = max(b[1][3] for b in group)
        score = sum(b[2] for b in group) / len(group)
        angle = group[0][3]
        merged.append((text, (x1, y1, x2, y2), score, angle))
    return merged