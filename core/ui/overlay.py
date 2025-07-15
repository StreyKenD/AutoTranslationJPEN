# ui/overlay.py
import tkinter as tk
import logging

logger = logging.getLogger(__name__)
_current_status_win = None

def show_status_overlay(root, region, message, auto_destroy_ms=None):
    """
    Shows a status message in a floating transparent window above the capture region.
    """
    global _current_status_win

    if _current_status_win is not None:
        try:
            _current_status_win.destroy()
        except tk.TclError:
            pass

    width = region['width']
    x = region['left']
    y = region['top'] - 40

    status_win = tk.Toplevel(root)
    status_win.overrideredirect(True)
    status_win.attributes("-topmost", True)
    status_win.geometry(f"{width}x30+{x}+{y}")

    try:
        status_win.attributes("-transparentcolor", "white")
        bg = 'white'
        fg = 'black'
    except tk.TclError:
        bg = 'black'
        fg = 'white'

    canvas = tk.Canvas(status_win, width=width, height=30, bg=bg, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_text(width // 2, 15, text=message, fill=fg, font=("Arial", 14, "bold"))

    if auto_destroy_ms is not None:
        status_win.after(auto_destroy_ms, status_win.destroy)

    _current_status_win = status_win
    return status_win

def destroy_status_overlay():
    """Closes the currently shown status overlay if any."""
    global _current_status_win
    if _current_status_win is not None:
        try:
            _current_status_win.destroy()
        except tk.TclError:
            pass
        _current_status_win = None

def create_overlay_canvas(window, width, height, fallback_color="white", transparent_color="cyan"):
    try:
        window.attributes("-transparentcolor", transparent_color)
        bg = transparent_color
    except Exception:
        bg = fallback_color
    return tk.Canvas(window, width=width, height=height, bg=bg, highlightthickness=0)

def show_overlay(root, region, blocks, translations=None, show_translation=True):
    """
    Creates transparent top-level windows to highlight blocks (not recommended with image-based overlays).
    """
    block_rects = []

    for block in blocks:
        text, (x1, y1, x2, y2), conf, angle = block
        w, h = x2 - x1, y2 - y1
        x_screen = x1
        y_screen = y1

        rect = tk.Toplevel(root)
        rect.overrideredirect(True)
        rect.attributes("-topmost", True)
        rect.geometry(f"{w}x{h}+{x_screen}+{y_screen}")

        canvas = create_overlay_canvas(rect, w, h)
        canvas.pack(fill="both", expand=True)

        block_rects.append(rect)

    return block_rects
