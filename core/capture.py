import mss
import numpy as np
import cv2
import logging

def grab_region(region):
    logging.debug(f'Capturing region: {region}')
    with mss.mss() as sct:
        img = sct.grab(region)
        arr = np.array(img)
        # mss returns BGRA, convert to BGR
        bgr = arr[...,:3][...,::-1]
        if bgr.shape[1] < 1000:
            bgr = cv2.resize(bgr, (bgr.shape[1]*2, bgr.shape[0]*2), interpolation=cv2.INTER_LANCZOS4)
            logging.debug('Image resized for better OCR')
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        _, binarized = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        bgr = cv2.cvtColor(binarized, cv2.COLOR_GRAY2BGR)
        cv2.imwrite('debug_processed.png', bgr)
        logging.info('Region captured and processed, debug image saved')
        return bgr
