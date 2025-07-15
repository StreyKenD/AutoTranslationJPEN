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
