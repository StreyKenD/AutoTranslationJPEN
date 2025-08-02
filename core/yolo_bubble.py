# core/yolo_bubble.py
from ultralytics import YOLO
import cv2
import numpy as np
import logging
import os

model = YOLO("models/comic-speech-bubble-detector.pt")  # Adjust path
DEBUG_IMAGES = os.environ.get("DEBUG_IMAGES") == "1"

def detect_bubbles(image: np.ndarray, padding: int = 0, return_contours: bool = False) -> list:
    """Detect speech bubbles and optionally pad the boxes.

    Parameters
    ----------
    image : np.ndarray
        Source image in BGR order.
    padding : int, optional
        Extra pixels around detected boxes.
    return_contours : bool, optional
        If ``True``, also return the bubble contour points.
    """
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
            contour = None
            if return_contours:
                gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if cnts:
                    contour = max(cnts, key=cv2.contourArea).reshape(-1, 2) + np.array([x1, y1])
            data = (crop, (x1, y1, x2, y2)) if not return_contours else (crop, (x1, y1, x2, y2), contour)
            crops.append(data)
            if DEBUG_IMAGES:
                cv2.imwrite("debug/10_final.png", crop)
    return crops

def sort_bubbles_for_japanese(bubbles: list) -> list:
    """
    Given a list of (crop, (x1,y1,x2,y2)), return them sorted
    so the rightmost bubble is first (Japanese vertical reading).
    """
    return sorted(bubbles, key=lambda b: b[1][0], reverse=True)
