import os
import mss
import cv2
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG)
os.makedirs("debug", exist_ok=True)

def grab_region(region: dict, target_width: int = 1000) -> np.ndarray:
    with mss.mss() as sct:
        frame = sct.grab(region)
    img = np.array(frame)[..., :3][..., ::-1]  # BGRA → BGR

    h, w = img.shape[:2]
    if w < target_width:
        scale = target_width / w
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    return img

# import os
# import mss
# import cv2
# import numpy as np
# import logging

# logging.basicConfig(level=logging.DEBUG)
# os.makedirs("debug", exist_ok=True)

# def grab_and_preprocess(region: dict,
#                         target_width: int = 1000) -> np.ndarray:
#     # 1) Capture
#     with mss.mss() as sct:
#         frame = sct.grab(region)
#     bgr = np.array(frame)[..., :3][..., ::-1]
#     cv2.imwrite("debug/00_captured.png", bgr)

#     # 2) Resize
#     h, w = bgr.shape[:2]
#     if w < target_width:
#         scale = target_width / w
#         bgr = cv2.resize(bgr, None, fx=scale, fy=scale,
#                          interpolation=cv2.INTER_CUBIC)
#     cv2.imwrite("debug/01_resized.png", bgr)

#     # 3a) Gray
#     gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
#     cv2.imwrite("debug/02_gray.png", gray)

#     # 3b) CLAHE
#     clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
#     gray = clahe.apply(gray)
#     cv2.imwrite("debug/03_clahe.png", gray)

#     # 3c) Blur
#     gray = cv2.medianBlur(gray, 3)
#     cv2.imwrite("debug/04_blur.png", gray)

#     # ── START IMPROVED BUBBLE MASK ──
#     # 4a) Estimate smooth background by closing with a large kernel
#     kernel_bg = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (40,40))
#     bg = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel_bg)
#     cv2.imwrite("debug/05_tophat_bg.png", bg)

#     # 4b) Top-hat = bg − gray; bright bumps light up
#     tophat = cv2.subtract(bg, gray)
#     cv2.imwrite("debug/06_tophat.png", tophat)

#     # 4c) Threshold the top-hat result
#     #    adjust '15' lower/higher if you miss/falsely hit bubbles
#     _, cand = cv2.threshold(tophat, 10, 255, cv2.THRESH_BINARY)
#     cv2.imwrite("debug/07_tophat_thresh.png", cand)

#     # 4d) Close tiny gaps so each bubble becomes one region
#     ker_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7,7))
#     closed = cv2.morphologyEx(cand, cv2.MORPH_CLOSE, ker_close, iterations=2)
#     cv2.imwrite("debug/08_tophat_closed.png", closed)

#     # 4e) Contour-based filtering for solidity & ellipse-fit
#     contours, _ = cv2.findContours(
#         closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
#     )
#     bubble_mask = np.zeros_like(gray)

#     for cnt in contours:
#         area = cv2.contourArea(cnt)
#         if area < 1000 or area > 200_000:
#             continue

#         # bounding box aspect ratio
#         x, y, w_b, h_b = cv2.boundingRect(cnt)
#         ar = w_b / float(h_b) if h_b else 1.0
#         if ar < 0.5 or ar > 3.0:
#             continue

#         # solidity = area / convex-hull area
#         hull = cv2.convexHull(cnt)
#         hull_area = cv2.contourArea(hull)
#         solidity = float(area) / hull_area if hull_area > 0 else 0
#         if solidity < 0.9:
#             continue

#         # ellipse eccentricity check (optional)
#         if len(cnt) >= 5:
#             ellipse = cv2.fitEllipse(cnt)
#             (MA, ma) = max(ellipse[1]), min(ellipse[1])
#             ecc = np.sqrt(1 - (ma/MA)**2)
#             if ecc > 0.8:
#                 continue

#         # passes all tests – mark it
#         cv2.drawContours(bubble_mask, [cnt], -1, (255,), -1)

#     cv2.imwrite("debug/09_refined_mask.png", bubble_mask)

#     # 5) Apply bubble mask to the gray image
#     bubble_area = cv2.bitwise_and(gray, gray, mask=bubble_mask)
#     cv2.imwrite("debug/08_bubble_area.png", bubble_area)

#     # 6) CC on bubble_area to keep only text‐sized blobs
#     n_lbl, labels, stats, _ = cv2.connectedComponentsWithStats(bubble_area, connectivity=8)
#     text_mask = np.zeros_like(gray)
#     for lbl in range(1, n_lbl):
#         area = stats[lbl, cv2.CC_STAT_AREA]
#         if 50 < area < 2000:
#             text_mask[labels == lbl] = 255
#     cv2.imwrite("debug/09_text_mask.png", text_mask)

#     # 7) Final isolate text strokes
#     final = cv2.bitwise_and(gray, gray, mask=text_mask)
#     cv2.imwrite("debug/10_final.png", final)

#     return cv2.cvtColor(final, cv2.COLOR_GRAY2BGR)
