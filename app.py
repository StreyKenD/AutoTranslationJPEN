# app.py (single-canvas refactor)
import csv
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import keyboard
import logging

from PIL import Image
from core.logger import setup_logger
from core.pipeline import process_region
from core.translate import set_engine
from core.ui.overlay import destroy_status_overlay, show_status_overlay
from core.ui.drawer import draw_translated_bubbles
from core.capture import grab_region
from core.config import load_config

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


def update_overlay_region(canvas, region):
    """Resize and reposition the overlay canvas."""
    win = canvas.master
    win.geometry(f"{region['width']}x{region['height']}+{region['left']}+{region['top']}")
    canvas.config(width=region['width'], height=region['height'])
    canvas.delete('all')
    canvas.create_rectangle(
        0,
        0,
        region['width'] - 1,
        region['height'] - 1,
        outline='red',
        width=4,
    )


def show_history_popup(root) -> None:
    """Display translation history with export options."""
    win = tk.Toplevel(root)
    win.title("Translation History")

    listbox = tk.Listbox(win, width=60)
    listbox.pack(side="left", fill="both", expand=True)
    scroll = tk.Scrollbar(win, command=listbox.yview)
    scroll.pack(side="right", fill="y")
    listbox.configure(yscrollcommand=scroll.set)

    history: list[tuple[str, str]] = []
    try:
        with open("historico_traducoes.csv", "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    jp, en = row[0], row[1]
                    history.append((jp, en))
                    listbox.insert(tk.END, f"{jp} -> {en}")
    except FileNotFoundError:
        listbox.insert(tk.END, "No history found")

    def open_image():
        sel = listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        jp, en = history[idx]
        bubbles = Path("bubble_logs/bubbles.csv")
        if bubbles.exists():
            with open(bubbles, "r", encoding="utf-8") as bf:
                breader = csv.reader(bf)
                next(breader, None)
                for img, j, e in breader:
                    if j == jp and e == en:
                        img_path = Path("bubble_logs") / img
                        try:
                            Image.open(img_path).show()
                        except Exception as exc:
                            logger.error("Failed to open bubble image: %s", exc)
                        return

    def export_json():
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if not path:
            return
        data = [{"jp": jp, "en": en} for jp, en in history]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def export_csv():
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Japanese", "English"])
            writer.writerows(history)

    btn_frame = tk.Frame(win)
    btn_frame.pack(fill="x")
    tk.Button(btn_frame, text="Open Image", command=open_image).pack(side="left")
    tk.Button(btn_frame, text="Export JSON", command=export_json).pack(side="left")
    tk.Button(btn_frame, text="Export CSV", command=export_csv).pack(side="left")

    show_status_overlay(root, REGION, "History opened", auto_destroy_ms=1000)


def main():
    cfg = load_config()
    hotkeys = cfg.get("hotkeys", {})
    bubble_padding = int(cfg.get("bubble_padding", 0))
    replace_mode = bool(cfg.get("replace_mode", False))
    save_bubble_images = bool(cfg.get("save_bubble_images", False))
    overflow_to_nearby = bool(cfg.get("overflow_to_nearby", False))
    tooltip_overlay = bool(cfg.get("tooltip_overlay", True))
    align_smoothing = float(cfg.get("align_smoothing", 0.5))
    bubble_shape = cfg.get("bubble_shape", "ellipse")
    font_path = cfg.get("overlay_font", "fonts/animeace2_reg.ttf")
    text_color = cfg.get("overlay_text_color", "#ffffff")
    outline_color = cfg.get("overlay_outline_color", "#000000")
    bg_alpha = int(cfg.get("overlay_bg_alpha", 180))

    set_engine(cfg.get("translator", "google"))
    fps = int(cfg.get("video_fps", 2))
    conf_threshold = float(cfg.get("ocr_confidence_threshold", 0.5))

    root = build_root_window()
    canvas = build_overlay_canvas(root, REGION)

    bubble_items = []
    bubbles_visible = True
    video_running = False
    loop_id = None
    last_coords = {}

    def select_capture_region():
        """Let the user drag a rectangle to set the capture region."""
        global REGION
        sel = tk.Toplevel(root)
        sel.overrideredirect(True)
        sel.attributes("-topmost", True)
        width = root.winfo_screenwidth()
        height = root.winfo_screenheight()
        try:
            sel.attributes("-transparentcolor", "white")
            bg = "white"
        except tk.TclError:
            bg = "black"
        canvas_sel = tk.Canvas(sel, width=width, height=height, bg=bg, cursor="cross", highlightthickness=0)
        canvas_sel.pack(fill="both", expand=True)

        start = [0, 0]
        rect = None

        def on_press(event):
            nonlocal rect
            start[0] = event.x
            start[1] = event.y
            rect = canvas_sel.create_rectangle(event.x, event.y, event.x, event.y, outline="red", width=2)

        def on_drag(event):
            if rect:
                canvas_sel.coords(rect, start[0], start[1], event.x, event.y)

        def on_release(event):
            left = min(start[0], event.x)
            top = min(start[1], event.y)
            w = abs(event.x - start[0])
            h = abs(event.y - start[1])
            REGION = {"left": left, "top": top, "width": w, "height": h}
            sel.destroy()
            update_overlay_region(canvas, REGION)
            show_status_overlay(root, REGION, "Region updated", auto_destroy_ms=1000)

        canvas_sel.bind("<ButtonPress-1>", on_press)
        canvas_sel.bind("<B1-Motion>", on_drag)
        canvas_sel.bind("<ButtonRelease-1>", on_release)

    def toggle_bubbles():
        """Show or hide translated bubbles and notify the user."""
        nonlocal bubbles_visible
        bubbles_visible = not bubbles_visible
        # remove drawn items
        for item in bubble_items:
            canvas.delete(item)
        bubble_items.clear()
        logger.info("Bubbles %s", "shown" if bubbles_visible else "hidden")
        msg = "Bubbles shown" if bubbles_visible else "Bubbles hidden"
        show_status_overlay(root, REGION, msg, auto_destroy_ms=1000)

    def run_ocr_cycle():
        nonlocal last_coords
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
        timings = {}
        blocks, translations = process_region(
            raw,
            REGION,
            bubble_padding,
            timings,
            save_bubble_images=save_bubble_images,
            conf_threshold=conf_threshold,
        )

        # Previously we drew each detected bubble with a blue rectangle for
        # debugging. Remove these outlines to keep the overlay clean.

        # draw translated bubbles if visible
        if bubbles_visible and blocks and translations:
            coords = {}
            new_items = draw_translated_bubbles(
                canvas,
                region_img,
                blocks,
                translations,
                REGION,
                replace_mode=replace_mode,
                overflow_to_nearby=overflow_to_nearby,
                show_tooltip=tooltip_overlay,
                prev_coords=last_coords,
                smoothing=align_smoothing,
                coord_out=coords,
                bubble_shape=bubble_shape,
                font_path=font_path,
                text_color=text_color,
                outline_color=outline_color,
                bg_alpha=bg_alpha,
            )
            bubble_items.extend(new_items)
            last_coords = coords

        logger.info("Overlay updated")
        logger.info("Stage timings: %s", timings)
        show_status_overlay(root, REGION, "Complete!", auto_destroy_ms=1000)

    def _video_loop():
        nonlocal loop_id
        run_ocr_cycle()
        if video_running:
            loop_id = root.after(int(1000 / max(fps, 1)), _video_loop)

    def toggle_video_mode():
        nonlocal video_running, loop_id
        if video_running:
            video_running = False
            if loop_id:
                root.after_cancel(loop_id)
                loop_id = None
            show_status_overlay(root, REGION, "Video mode stopped", auto_destroy_ms=1000)
        else:
            video_running = True
            show_status_overlay(root, REGION, "Video mode started")
            _video_loop()

    keyboard.add_hotkey(hotkeys.get('ocr', 'f8'), run_ocr_cycle)
    keyboard.add_hotkey(hotkeys.get('toggle_bubbles', 'f9'), toggle_bubbles)
    keyboard.add_hotkey(hotkeys.get('video', 'f7'), toggle_video_mode)
    keyboard.add_hotkey(hotkeys.get('history', 'f6'), lambda: show_history_popup(root))
    keyboard.add_hotkey(hotkeys.get('select_region', 'f10'), select_capture_region)
    keyboard.add_hotkey(hotkeys.get('quit', 'esc'), root.destroy)

    logger.info(
        (
            "App ready. Press %s for OCR, %s for video, %s for region select, "
            "%s for history, %s to quit."
        ),
        hotkeys.get('ocr', 'f8').upper(),
        hotkeys.get('video', 'f7').upper(),
        hotkeys.get('select_region', 'f10').upper(),
        hotkeys.get('history', 'f6').upper(),
        hotkeys.get('quit', 'esc').upper(),
    )
    root.mainloop()


if __name__ == "__main__":
    main()
