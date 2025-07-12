import tkinter as tk
import logging
import os
import cv2
import numpy as np

_current_status_win = None

# Logging setup
log_path = os.path.join(os.path.dirname(__file__), '..', 'app.log')
logging.basicConfig(
    filename=log_path,
    filemode='a',
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.DEBUG
)

def draw_translations(image, data):
    img = image.copy()
    for orig, trans, box, conf in data:
        x1, y1, x2, y2 = box
        cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)
        overlay = img.copy()
        cv2.rectangle(overlay, (x1, y1-30), (x2, y1), (0,0,0), -1)
        alpha = 0.6
        img = cv2.addWeighted(overlay, alpha, img, 1-alpha, 0)
        cv2.putText(img, trans, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2, cv2.LINE_AA)
        logging.debug(f'Drew overlay: orig={orig}, trans={trans}, box={box}, conf={conf}')
    return img

def create_overlay_canvas(window, width, height, fallback_color="white", transparent_color="cyan"):
    try:
        window.attributes("-transparentcolor", transparent_color)
        bg = transparent_color
    except Exception:
        bg = fallback_color
    return tk.Canvas(window, width=width, height=height, bg=bg, highlightthickness=0)

def show_status_overlay(root, region, message, auto_destroy_ms=None):
    """
    Shows a status line above the capture region.
    
    If auto_destroy_ms is set (an integer), the window will self‑destroy
    after that many milliseconds. If auto_destroy_ms is None, it will stay
    up indefinitely until you call destroy_status_overlay().
    """
    global _current_status_win
    # kill any previous status window
    if _current_status_win is not None:
        try:
            _current_status_win.destroy()
        except tk.TclError:
            pass

    w, _ = region['width'], region['height']
    status_win = tk.Toplevel(root)
    status_win.overrideredirect(True)
    status_win.attributes("-topmost", True)
    status_win.geometry(f"{w}x30+{region['left']}+{region['top']-40}")
    try:
        status_win.attributes("-transparentcolor", "white")
        bg = 'white'
        fg = 'black'
    except tk.TclError:
        bg = 'black'
        fg = 'white'

    canvas = tk.Canvas(status_win, width=w, height=30, bg=bg, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_text(w // 2, 15, text=message, fill=fg, font=("Arial", 14, "bold"))

    # only schedule destroy if a duration was given
    if auto_destroy_ms is not None:
        status_win.after(auto_destroy_ms, status_win.destroy)

    _current_status_win = status_win
    return status_win

def show_overlay(root, region, blocks, translations=None, show_translation=True):
    import textwrap
    block_rects = []

    for i, block in enumerate(blocks):
        text, (x1,y1,x2,y2), conf, angle = block
        w, h = x2 - x1, y2 - y1

        # compute screen coords
        x_screen = region['left'] + x1
        y_screen = region['top']  + y1

        rect = tk.Toplevel(root)
        rect.overrideredirect(True)
        rect.attributes("-topmost", True)
        rect.geometry(f"{w}x{h}+{x_screen}+{y_screen}")

        canvas = create_overlay_canvas(rect, w, h)
        canvas.pack(fill="both", expand=True)



        block_rects.append(rect)
    return block_rects

def destroy_status_overlay():
    """Call this when you want to clear any permanent status."""
    global _current_status_win
    if _current_status_win is not None:
        try:
            _current_status_win.destroy()
        except tk.TclError:
            pass
        _current_status_win = None