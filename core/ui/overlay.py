# ui/overlay.py
import tkinter as tk
import logging

logger = logging.getLogger(__name__)
_current_status_win = None

def _animate_alpha(window, start: float, end: float, duration: int = 300) -> None:
    """Smoothly animate window alpha from ``start`` to ``end``."""
    steps = 10
    step_ms = max(1, duration // steps)

    def _step(i: int = 0) -> None:
        alpha = start + (end - start) * (i / steps)
        try:
            window.attributes("-alpha", alpha)
        except tk.TclError:
            return
        if i < steps:
            window.after(step_ms, _step, i + 1)

    _step()

def fade_in(window, duration: int = 300) -> None:
    """Fade in the given window."""
    _animate_alpha(window, 0.0, 1.0, duration)

def fade_out(window, duration: int = 300, destroy: bool = True) -> None:
    """Fade out the given window and optionally destroy it when done."""
    def _on_finish() -> None:
        if destroy:
            try:
                window.destroy()
            except tk.TclError:
                pass

    steps = 10
    step_ms = max(1, duration // steps)

    def _step(i: int = 0) -> None:
        alpha = 1.0 - (i / steps)
        try:
            window.attributes("-alpha", alpha)
        except tk.TclError:
            return
        if i < steps:
            window.after(step_ms, _step, i + 1)
        else:
            _on_finish()

    _step()

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
