# app.py (single-canvas refactor)
import tkinter as tk
import keyboard
import logging

from PIL import Image
from core.logger import setup_logger
from core.pipeline import process_region
from core.ui.overlay import destroy_status_overlay, show_status_overlay
from core.ui.drawer import draw_translated_bubbles
from core.capture import grab_region

setup_logger()
logger = logging.getLogger(__name__)

REGION = {"top": 128, "left": 575, "width": 768, "height": 864}
CANVAS_BG = "#FF00FF"  # transparent key color


def build_root_window():
    """Create a transparent, always-on-top root window."""
    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-transparentcolor", "white")
    root.configure(bg="white")
    return root


def build_overlay_canvas(root, region):
    """
    Create a single overlay canvas for border + bubbles.
    """
    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.geometry(f"{region['width']}x{region['height']}+{region['left']}+{region['top']}")
    # treat CANVAS_BG as transparent
    try:
        win.attributes("-transparentcolor", CANVAS_BG)
    except tk.TclError:
        pass

    canvas = tk.Canvas(
        win,
        width=region['width'],
        height=region['height'],
        bg=CANVAS_BG,
        highlightthickness=0
    )
    canvas.pack(fill="both", expand=True)

    canvas.create_rectangle(
        0, 0,
        region['width'] - 1,
        region['height'] - 1,
        outline='red',
        width=4
    )

    return canvas


def main():
    root = build_root_window()
    canvas = build_overlay_canvas(root, REGION)

    bubble_items = []
    bubbles_visible = True

    def toggle_bubbles():
        nonlocal bubbles_visible, bubble_items
        bubbles_visible = not bubbles_visible
        # remove drawn items
        for item in bubble_items:
            canvas.delete(item)
        bubble_items.clear()
        logger.info("Bubbles %s", "shown" if bubbles_visible else "hidden")

    def run_ocr_cycle():
        nonlocal bubble_items, bubbles_visible
        logger.info("Starting OCR cycle")

        destroy_status_overlay()
        show_status_overlay(root, REGION, "Processing image...")

        # clear old bubbles
        for item in bubble_items:
            canvas.delete(item)
        bubble_items.clear()

        # 1) grab raw screen as NumPy array
        raw = grab_region(REGION)

        # 2) convert BGR→RGB if needed, then to PIL
        try:
            import cv2
            raw_rgb = cv2.cvtColor(raw, cv2.COLOR_BGR2RGB)
        except ImportError:
            raw_rgb = raw
        region_img = Image.fromarray(raw_rgb)

        # 3) run detection/OCR/translation on the raw NumPy image
        blocks, translations = process_region(raw, REGION)

        # Debug: draw border rectangles in blue
        for text, (x1, y1, x2, y2), conf, angle in blocks:
            x_screen = x1
            y_screen = y1
            w, h = x2 - x1, y2 - y1
            # draw debug outline relative to canvas
            rect = canvas.create_rectangle(x_screen, y_screen, x_screen + w, y_screen + h,
                                           outline='blue', width=2)
            bubble_items.append(rect)

        # draw translated bubbles if visible
        if bubbles_visible and blocks and translations:
            bubble_items = draw_translated_bubbles(canvas, region_img, blocks, translations, REGION)
            bubble_items.extend(bubble_items)

        logger.info("Overlay updated")
        show_status_overlay(root, REGION, "Complete!", auto_destroy_ms=1000)

    keyboard.add_hotkey('f8', run_ocr_cycle)
    keyboard.add_hotkey('f9', toggle_bubbles)
    keyboard.add_hotkey('esc', root.destroy)

    logger.info("App ready. Press F8 to start OCR, ESC to quit.")
    root.mainloop()


if __name__ == "__main__":
    main()
