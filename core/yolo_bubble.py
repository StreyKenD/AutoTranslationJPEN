# core/yolo_bubble.py
from ultralytics import YOLO
import cv2
import numpy as np
import logging

model = YOLO("models/comic-speech-bubble-detector.pt")  # Adjust path

def detect_bubbles(image: np.ndarray) -> list:
    results = model.predict(image, conf=0.3, iou=0.5, verbose=False)[0]

    crops = []
    if results.boxes is not None and results.boxes.xyxy is not None:
        for box in results.boxes.xyxy:
            x1, y1, x2, y2 = map(int, box)
            crop = image[y1:y2, x1:x2]
            crops.append((crop, (x1, y1, x2, y2)))
            cv2.imwrite("debug/10_final.png", crop)
            # logging.debug(f"Saved bubble crop: ")
    return crops
