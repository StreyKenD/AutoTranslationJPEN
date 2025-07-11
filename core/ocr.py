import cv2
from paddleocr import PaddleOCR, TextRecognition
import numpy as np
from typing import List, Tuple
import logging
from core.capture import enhance_for_ocr_debug


# Initialize OCR
default_ocr = PaddleOCR(
    lang='japan',
    use_angle_cls=True,
    text_recognition_model_name="PP-OCRv5_server_rec",
    device='gpu:0',
    det_db_box_thresh=0.1,
    det_db_unclip_ratio=2.0
)

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

            logging.debug(f"OCR result for bubble {idx}: {result[0]}")
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

    grouped = group_vertical_blocks(all_blocks)
    merged_blocks = merge_block_groups(grouped)

    logging.info(f"Merged vertical blocks: {merged_blocks}")

    return merged_blocks

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
        # Sort vertically (top to bottom) for vertical Japanese
        group = sorted(group, key=lambda b: b[1][1])  # sort by y1

        text = ''.join([b[0] for b in group])  # use line break to preserve vertical layout
        x1 = min(b[1][0] for b in group)
        y1 = min(b[1][1] for b in group)
        x2 = max(b[1][2] for b in group)
        y2 = max(b[1][3] for b in group)
        score = sum(b[2] for b in group) / len(group)
        angle = group[0][3]
        merged.append((text, (x1, y1, x2, y2), score, angle))
    return merged
