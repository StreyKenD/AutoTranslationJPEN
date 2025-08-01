# core/yolo_bubble.py
from ultralytics import YOLO
import cv2
import numpy as np
import logging
import os

model = YOLO("models/comic-speech-bubble-detector.pt")  # Adjust path
DEBUG_IMAGES = os.environ.get("DEBUG_IMAGES") == "1"

def detect_bubbles(image: np.ndarray, padding: int = 0) -> list:
    """Detect speech bubbles and optionally pad the boxes."""
    results = model.predict(image, conf=0.3, iou=0.5, verbose=False)[0]

    crops = []
    if results.boxes is not None and results.boxes.xyxy is not None:
        height, width = image.shape[:2]
        for box in results.boxes.xyxy:
            x1, y1, x2, y2 = map(int, box)
            if padding:
                x1 = max(0, x1 - padding)
                y1 = max(0, y1 - padding)
                x2 = min(width, x2 + padding)
                y2 = min(height, y2 + padding)
            crop = image[y1:y2, x1:x2]
            crops.append((crop, (x1, y1, x2, y2)))
            if DEBUG_IMAGES:
                cv2.imwrite("debug/10_final.png", crop)
    return crops

def sort_bubbles_for_japanese(bubbles: list) -> list:
    """
    Given a list of (crop, (x1,y1,x2,y2)), return them sorted
    so the rightmost bubble is first (Japanese vertical reading).
    """
    return sorted(bubbles, key=lambda b: b[1][0], reverse=True)
