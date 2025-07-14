import os
import mss
import cv2
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG)
os.makedirs("debug", exist_ok=True)

def grab_region(region: dict, target_width: int = 1000) -> np.ndarray:
    """
    Capture the given screen region, optionally resize it to at least target_width,
    and return both the processed image and the scale factor used.
    """
    # 1) Capture
    with mss.mss() as sct:
        frame = sct.grab(region)
    img = cv2.cvtColor(np.array(frame), cv2.COLOR_BGRA2RGB)
    cv2.imwrite("debug/00_captured.png", img)

    return img

def enhance_for_ocr_debug(
    img: np.ndarray,
    debug_dir: str = "debug/ocr_steps"
) -> np.ndarray:
    """
    Enhance cropped bubble image for better OCR accuracy.
    At each major step, save a debug image in `debug_dir`.
    """
    os.makedirs(debug_dir, exist_ok=True)
    step = 0

    def save(step_name: str, image: np.ndarray):
        nonlocal step
        path = os.path.join(debug_dir, f"{step:02d}_{step_name}.png")
        cv2.imwrite(path, image)
        step += 1

    try:
        # 00) Original capture
        save("original", img)

        TARGET_MIN = 200

        # 01) Upscale if too small
        h, w = img.shape[:2]
        min_dim = min(h, w)
        if min_dim < TARGET_MIN:
            scale = TARGET_MIN / min_dim
            img = cv2.resize(
                img, None,
                fx=scale, fy=scale,
                interpolation=cv2.INTER_LANCZOS4
            )
            save("upscaled", img)
        else:
            save("skip_upscale", img)

        # 02) Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        save("gray", gray)

        # 03) CLAHE on grayscale
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray_clahe = clahe.apply(gray)
        save("clahe", gray_clahe)

        # 04) Otsu threshold → binary
        th = cv2.adaptiveThreshold(
            gray_clahe, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=15,
            C=5
        )
        save("adapt_th_on_clahe", th)

        # 05) Morphological dilation (thickens thin strokes)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        dilated = cv2.dilate(th, kernel, iterations=1)
        save("dilated", dilated)

        # back to BGR so PaddleOCR can accept it
        final_bgr = cv2.cvtColor(dilated, cv2.COLOR_GRAY2BGR)
        save("final_bgr", final_bgr)

        return final_bgr

    except Exception as e:
        logging.error(f"enhance_for_ocr_debug failed at step {step}: {e}")
        # fallback: return the last successfully processed image
        return img

