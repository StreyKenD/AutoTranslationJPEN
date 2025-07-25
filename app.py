import tkinter as tk
import keyboard
from core.capture import grab_region
from core.yolo_bubble import detect_bubbles, sort_bubbles_for_japanese
from core.ocr import extract_text_from_bubbles, ocr_single_bubble
from core.translate import translate_batch
from core.ui_overlay import destroy_status_overlay, show_overlay, show_status_overlay
from core.logger import setup_logger
import logging
import cv2
from core.ui_pillow_bubble import draw_bubbles_on_canvas
import time
import numpy as np
from typing import Tuple

setup_logger()

def main():
    region = {"top": 128, "left": 575, "width": 768, "height": 864}
    block_rects = []
    bubbles_visible = True
    bubble_canvas_items = []

    def toggle_bubbles():
        nonlocal bubbles_visible, block_rects, bubble_canvas_items
        bubbles_visible = not bubbles_visible
        if not bubbles_visible:
            for r in block_rects:
                r.destroy()
            block_rects.clear()
            for item in bubble_canvas_items:
                bubble_canvas.delete(item)
            bubble_canvas_items.clear()
            logging.info("Bubbles hidden")
        else:
            logging.info("Bubbles toggle ON — will reappear after next OCR cycle")

    def run_ocr_cycle():
        nonlocal block_rects
        nonlocal bubble_canvas_items
        timings = {}
        t0 = time.perf_counter()
        logging.info("Starting OCR cycle")

        for r in block_rects:
            r.destroy()
        block_rects.clear()

        destroy_status_overlay()
        show_status_overlay(root, region, "Getting image...")

        img = grab_region(region)
        t1 = time.perf_counter()
        timings['grab_region'] = t1 - t0

        destroy_status_overlay()
        show_status_overlay(root, region, "Getting bubbles...")

        bubble_crops = detect_bubbles(img)
        bubble_crops = sort_bubbles_for_japanese(bubble_crops)
        logging.info(f"Detected {len(bubble_crops)} bubbles")
        # logging.debug(f"Bubble crops: {bubble_crops}")
        if not bubble_crops:
            logging.info("No bubbles detected. Skipping OCR.")
            show_status_overlay(root, region, "No bubbles found.")
            return
        
        t2 = time.perf_counter()
        timings['detect_bubbles'] = t2 - t1

        destroy_status_overlay()
        show_status_overlay(root, region, "Getting texts...")
        raw_blocks = []
        for crop, offset in bubble_crops:
            raw_blocks.extend(extract_text_from_bubbles([(crop, offset)]))

        if not raw_blocks:
            logging.info("No OCR text detected in any bubble. Skipping translation.")
            show_status_overlay(root, region, "No text found.")
            return
        logging.info(f"OCR extracted {len(raw_blocks)} bubbles")

        logging.debug(f"Raw OCR blocks: {raw_blocks}")
        blocks = []
        for text, (x1, y1, x2, y2), conf, angle in raw_blocks:
            blocks.append((text, (x1, y1, x2, y2), conf, angle))
        logging.debug(f"OCR blocks: {blocks}")

        # Show OCR text first (no translation yet)
        block_rects = show_overlay(root, region, blocks, show_translation=False)

        t3 = time.perf_counter()
        timings['OCR - time to get text from image'] = t3 - t2

        destroy_status_overlay()
        show_status_overlay(root, region, "Getting translations...")
        # Collect just the OCR texts
        texts = [b[0] for b in blocks]
        translations = translate_batch(texts)
        logging.info("Translation complete")

        # Clear any prior overlays
        if blocks and translations:
            bubble_canvas_items = draw_bubbles_on_canvas(bubble_canvas, blocks, translations, region)

        for r in block_rects:
            r.destroy()
        block_rects = show_overlay(root, region, blocks, translations, show_translation=True)
        logging.info("Overlay updated")

        t4 = time.perf_counter()
        timings['time to get translations and show on screen'] = t4 - t3

        logging.info("Timings per stage: " + ", ".join(f"{k}={v*1000:.1f}ms" for k,v in timings.items()))

        show_status_overlay(root, region, "Complete!")

    # Tkinter root window
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-transparentcolor", "white")
    root.configure(bg="white")

    region_rectangle = tk.Toplevel(root)
    region_rectangle.overrideredirect(True)
    region_rectangle.attributes("-topmost", True)
    region_rectangle.geometry(f"{region['width']}x{region['height']}+{region['left']}+{region['top']}")
    try:
        region_rectangle.attributes("-transparentcolor", "cyan")
        canvas = tk.Canvas(region_rectangle, width=region['width'], height=region['height'], bg='cyan', highlightthickness=0)
    except Exception:
        canvas = tk.Canvas(region_rectangle, width=region['width'], height=region['height'], bg='white', highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_rectangle(2, 2, region['width']-2, region['height']-2, outline="red", width=4)
    region_rectangle.lift(root)

    # after you draw the red capture rectangle in main():
    overlay = tk.Toplevel(root)
    overlay.overrideredirect(True)
    overlay.attributes("-topmost", True)
    overlay.geometry(f"{region['width']}x{region['height']}+{region['left']}+{region['top']}")

    MAGENTA = "#FF00FF"

    # Tell Tkinter: treat MAGENTA pixels as fully transparent
    overlay.attributes("-transparentcolor", MAGENTA)

    # Create a canvas whose background is that same MAGENTA color
    bubble_canvas = tk.Canvas(
        overlay,
        width=region['width'],
        height=region['height'],
        bg=MAGENTA,
        highlightthickness=0
    )
    bubble_canvas.pack(fill="both", expand=True)
    bubble_canvas.create_oval(0, 0, 5, 5, fill='red')

    keyboard.add_hotkey('f8', run_ocr_cycle)
    keyboard.add_hotkey('f9', toggle_bubbles)
    keyboard.add_hotkey('esc', root.destroy)
    logging.info("Application started. Press F8 to run OCR, ESC to exit.")
    root.mainloop()

if __name__ == "__main__":
    main()