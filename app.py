import tkinter as tk
import keyboard
from core.capture import grab_region
from core.yolo_bubble import detect_bubbles
from core.ocr import extract_text_from_bubbles
from core.translate import translate_batch
from core.ui_overlay import show_overlay, show_status_overlay
from core.logger import setup_logger
import logging
import cv2
from core.ui_pillow_bubble import draw_bubbles_on_canvas

setup_logger()

def main():
    region = {"top": 128, "left": 575, "width": 768, "height": 864}
    block_rects = []

    def run_ocr_cycle():
        nonlocal block_rects
        logging.info("Starting OCR cycle")

        for r in block_rects:
            r.destroy()
        block_rects.clear()

        show_status_overlay(root, region, "Running OCR...", duration=5000)

        img = grab_region(region)

        bubble_crops = detect_bubbles(img)
        logging.info(f"Detected {len(bubble_crops)} bubbles")
        logging.debug(f"Bubble crops: {bubble_crops}")
        if not bubble_crops:
            logging.info("No bubbles detected. Skipping OCR.")
            show_status_overlay(root, region, "No bubbles found.", duration=1000)
            return

        raw_blocks = extract_text_from_bubbles(bubble_crops)

        if not raw_blocks:
            logging.info("No OCR blocks detected. Skipping translation.")
            show_status_overlay(root, region, "No text found.", duration=1000)
            return
        
        blocks = []
        for text, (x1, y1, x2, y2), conf, angle in raw_blocks:
            # x1 = int(x1 / scale)
            # y1 = int(y1 / scale)
            # x2 = int(x2 / scale)
            # y2 = int(y2 / scale)
            blocks.append((text, (x1, y1, x2, y2), conf, angle))


        logging.info(f"OCR extracted {len(blocks)} blocks")

        # Show OCR text first (no translation yet)
        block_rects = show_overlay(root, region, blocks, show_translation=False)

        show_status_overlay(root, region, "Translating...", duration=800)

        texts = [b[0] for b in blocks]
        translations = translate_batch(texts)
        logging.info("Translation complete")

        if blocks and translations:
            draw_bubbles_on_canvas(bubble_canvas, blocks, translations, region)

        for r in block_rects:
            r.destroy()
        block_rects = show_overlay(root, region, blocks, translations, show_translation=True)
        logging.info("Overlay updated")

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
    # try:
    #     overlay.attributes("-transparentcolor", "white")
    #     bubble_canvas = tk.Canvas(overlay,
    #                             width=region['width'],
    #                             height=region['height'],
    #                             bg='white',
    #                             highlightthickness=0)
    # except Exception:
    #     bubble_canvas = tk.Canvas(overlay,
    #                             width=region['width'],
    #                             height=region['height'],
    #                             bg='white',
    #                             highlightthickness=0)
    # bubble_canvas.pack(fill="both", expand=True)

    bubble_canvas.create_oval(0, 0, 5, 5, fill='red')

    keyboard.add_hotkey('f8', run_ocr_cycle)
    keyboard.add_hotkey('esc', root.destroy)
    logging.info("Application started. Press F8 to run OCR, ESC to exit.")
    root.mainloop()

if __name__ == "__main__":
    main()
