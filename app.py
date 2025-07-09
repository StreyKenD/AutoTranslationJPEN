import tkinter as tk
import cv2
import keyboard
from core.capture import grab_region
from core.ocr import extract_text
from core.translate import translate_batch
from core.ui_overlay import show_overlay, show_status_overlay
from core.logger import setup_logger
import logging

setup_logger()

def main():
    region = {"top": 118, "left": 575, "width": 768, "height": 915}
    block_rects = []
    running = False  # To prevent concurrent runs

    def run_ocr_cycle():
        nonlocal block_rects, running
        if running:
            logging.info("OCR cycle already running. Ignoring new request.")
            return
        running = True

        logging.info("Starting OCR cycle")

        # Clear previous overlays
        for r in block_rects:
            r.destroy()
        block_rects.clear()

        show_status_overlay(root, region, "Running OCR...", duration=1000)

        img = grab_region(region)
        logging.debug("Region captured")

        blocks = extract_text(img)
        # Check blocks content for debugging
        for b in blocks:
            logging.debug(f"Block item type and value: {type(b)} - {b}")

        if not blocks:
            logging.info("No OCR blocks detected. Skipping translation.")
            show_status_overlay(root, region, "No text found.", duration=1000)
            running = False
            return

        # Add angle=None since you expect 4-item tuples in show_overlay
        blocks_with_angle = [(*b, None) for b in blocks]

        block_rects = show_overlay(root, region, blocks_with_angle, show_translation=False)

        show_status_overlay(root, region, "Translating...", duration=1000)

        texts = [b[0] for b in blocks]
        translations = translate_batch(texts)
        logging.info("Translation complete")

        for r in block_rects:
            r.destroy()

        block_rects = show_overlay(root, region, blocks_with_angle, translations, show_translation=True)
        logging.info("Overlay updated")

        running = False

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

    keyboard.add_hotkey('f8', run_ocr_cycle)
    keyboard.add_hotkey('esc', root.destroy)
    logging.info("Application started. Press F8 to run OCR, ESC to exit.")
    root.mainloop()


if __name__ == "__main__":
    main()
