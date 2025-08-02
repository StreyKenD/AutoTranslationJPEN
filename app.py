# app.py (single-canvas refactor)
import csv
import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, simpledialog
import keyboard
import logging

from PIL import Image
from core.logger import setup_logger
from core.pipeline import process_region
from core.translate import set_engine
from core.ui.overlay import (
    destroy_status_overlay,
    fade_in,
    fade_out,
    show_status_overlay,
)
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

    search_var = tk.StringVar()
    tk.Entry(win, textvariable=search_var).pack(fill="x")

    list_frame = tk.Frame(win)
    list_frame.pack(fill="both", expand=True)
    listbox = tk.Listbox(list_frame, width=60)
    listbox.pack(side="left", fill="both", expand=True)
    scroll = tk.Scrollbar(list_frame, command=listbox.yview)
    scroll.pack(side="right", fill="y")
    listbox.configure(yscrollcommand=scroll.set)

    preview_label = tk.Label(win)
    preview_label.pack(fill="both")

    history: list[dict] = []
    try:
        with open("bubble_logs/bubbles.csv", "r", encoding="utf-8") as bf:
            reader = csv.DictReader(bf)
            for row in reader:
                history.append(
                    {
                        "jp": row.get("japanese", ""),
                        "en": row.get("english", ""),
                        "img": row.get("image", ""),
                        "engine": row.get("engine", ""),
                        "conf": row.get("confidence", ""),
                        "edited": row.get("edited", "0"),
                    }
                )
    except FileNotFoundError:
        pass
    if not history:
        listbox.insert(tk.END, "No history found")

    stats_label = tk.Label(win)
    stats_label.pack(fill="x")
    if history:
        total = len(history)
        words = {}
        for entry in history:
            for w in entry["en"].split():
                words[w.lower()] = words.get(w.lower(), 0) + 1
        common = sorted(words.items(), key=lambda x: x[1], reverse=True)[:3]
        common_words = ", ".join(f"{w} ({c})" for w, c in common)
        stats_label.config(text=f"Total: {total} | Top words: {common_words}")

    filtered: list[int] = []

    def refresh_list(*_args):
        term = search_var.get().lower()
        listbox.delete(0, tk.END)
        filtered.clear()
        for idx, entry in enumerate(history):
            if term in entry["jp"].lower() or term in entry["en"].lower():
                marker = "*" if entry.get("edited") in {"1", 1, True} else ""
                listbox.insert(tk.END, f"{entry['jp']} -> {entry['en']}{marker}")
                filtered.append(idx)

    search_var.trace_add("write", refresh_list)
    refresh_list()

    def _update_preview(event=None):
        sel = listbox.curselection()
        if not sel:
            preview_label.config(image="")
            preview_label.image = None
            return
        idx = filtered[sel[0]]
        entry = history[idx]
        img_path = Path("bubble_logs") / entry.get("img", "")
        try:
            img = Image.open(img_path)
            img.thumbnail((200, 200))
            from PIL import ImageTk

            photo = ImageTk.PhotoImage(img)
            preview_label.config(image=photo)
            preview_label.image = photo
        except Exception as exc:
            logger.error("Failed to load preview: %s", exc)
            preview_label.config(image="")
            preview_label.image = None

    listbox.bind("<<ListboxSelect>>", _update_preview)

    def open_image():
        sel = listbox.curselection()
        if not sel:
            return
        idx = filtered[sel[0]]
        entry = history[idx]
        img_path = Path("bubble_logs") / entry.get("img", "")
        try:
            Image.open(img_path).show()
        except Exception as exc:
            logger.error("Failed to open bubble image: %s", exc)

    def export_json():
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if not path:
            return
        data = [
            {
                "japanese": h["jp"],
                "english": h["en"],
                "engine": h.get("engine", ""),
                "confidence": h.get("conf", ""),
                "edited": bool(int(h.get("edited", 0))),
            }
            for h in history
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def export_csv():
        path = filedialog.asksaveasfilename(defaultextension=".csv")
        if not path:
            return
        with open(path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Japanese", "English", "Engine", "Confidence", "Edited"])
            for h in history:
                writer.writerow([
                    h["jp"],
                    h["en"],
                    h.get("engine", ""),
                    h.get("conf", ""),
                    h.get("edited", "0"),
                ])

    def export_srt():
        path = filedialog.asksaveasfilename(defaultextension=".srt")
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            for i, h in enumerate(history, start=1):
                start = i - 1
                end = i
                f.write(f"{i}\n00:00:{start:02d},000 --> 00:00:{end:02d},000\n{h['en']}\n\n")

    def edit_translation():
        sel = listbox.curselection()
        if not sel:
            return
        idx = filtered[sel[0]]
        entry = history[idx]
        new_text = simpledialog.askstring(
            "Edit Translation", "English:", initialvalue=entry["en"], parent=win
        )
        if new_text is None:
            return
        entry["en"] = new_text
        entry["edited"] = "1"
        refresh_list()
        try:
            with open("bubble_logs/bubbles.csv", "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["image", "japanese", "english", "engine", "confidence", "edited"])
                for e in history:
                    writer.writerow([
                        e.get("img", ""),
                        e["jp"],
                        e["en"],
                        e.get("engine", ""),
                        e.get("conf", ""),
                        e.get("edited", "0"),
                    ])
        except Exception as exc:
            logger.error("Failed to update history CSV: %s", exc)

    btn_frame = tk.Frame(win)
    btn_frame.pack(fill="x")
    tk.Button(btn_frame, text="Open Image", command=open_image).pack(side="left")
    tk.Button(btn_frame, text="Edit", command=edit_translation).pack(side="left")
    tk.Button(btn_frame, text="Export JSON", command=export_json).pack(side="left")
    tk.Button(btn_frame, text="Export CSV", command=export_csv).pack(side="left")
    tk.Button(btn_frame, text="Export SRT", command=export_srt).pack(side="left")

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
    use_bubble_mask = bool(cfg.get("use_bubble_mask", False))
    font_path = cfg.get("overlay_font", "fonts/animeace2_reg.ttf")
    text_color = cfg.get("overlay_text_color", "#ffffff")
    outline_color = cfg.get("overlay_outline_color", "#000000")
    bg_alpha = int(cfg.get("overlay_bg_alpha", 180))
    highlight_color = cfg.get("highlight_color", "#ffff00")
    highlight_width = int(cfg.get("highlight_width", 2))

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

    current_blocks: list = []
    current_translations: list = []
    selected_idx = -1
    highlight_rect = None

    subtitle_visible = bool(cfg.get("subtitle_mode", False))
    subtitle_win = None
    subtitle_label = None

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
        """Show or hide translated bubbles with a fade animation."""
        nonlocal bubbles_visible
        bubbles_visible = not bubbles_visible
        state = "normal" if bubbles_visible else "hidden"
        for item in bubble_items:
            canvas.itemconfigure(item, state=state)
        if highlight_rect:
            canvas.itemconfigure(highlight_rect, state=state)
        if bubbles_visible:
            fade_in(canvas.master, 200)
        else:
            fade_out(canvas.master, 200, destroy=False)
        logger.info("Bubbles %s", "shown" if bubbles_visible else "hidden")
        msg = "Bubbles shown" if bubbles_visible else "Bubbles hidden"
        show_status_overlay(root, REGION, msg, auto_destroy_ms=1000)

    def highlight_current() -> None:
        """Highlight the currently selected bubble."""
        nonlocal highlight_rect
        if highlight_rect:
            canvas.delete(highlight_rect)
            highlight_rect = None
        if selected_idx < 0 or selected_idx >= len(current_blocks):
            return
        _, (x1, y1, x2, y2), *_ = current_blocks[selected_idx]
        highlight_rect = canvas.create_rectangle(
            x1 - REGION["left"],
            y1 - REGION["top"],
            x2 - REGION["left"],
            y2 - REGION["top"],
            outline=highlight_color,
            width=highlight_width,
        )

    def update_subtitles(lines: list[str]) -> None:
        """Display translations in a subtitle window."""
        nonlocal subtitle_win, subtitle_label
        if not subtitle_visible:
            return
        if subtitle_win is None:
            subtitle_win = tk.Toplevel(root)
            subtitle_win.overrideredirect(True)
            subtitle_win.attributes("-topmost", True)
            w = REGION["width"]
            x = REGION["left"]
            y = REGION["top"] + REGION["height"] + 5
            subtitle_win.geometry(f"{w}x80+{x}+{y}")
            try:
                subtitle_win.attributes("-transparentcolor", "white")
                bg = "white"
                fg = "black"
            except tk.TclError:
                bg = "black"
                fg = "white"
            subtitle_label = tk.Label(subtitle_win, bg=bg, fg=fg, justify="left", wraplength=w, font=("Arial", 14))
            subtitle_label.pack(fill="both", expand=True)
        subtitle_label.config(text="\n".join(lines))

    def toggle_subtitles() -> None:
        """Toggle subtitle display."""
        nonlocal subtitle_visible
        subtitle_visible = not subtitle_visible
        if not subtitle_visible and subtitle_win is not None:
            subtitle_win.destroy()
            show_status_overlay(root, REGION, "Subtitles off", auto_destroy_ms=1000)
        elif subtitle_visible:
            update_subtitles(current_translations)
            show_status_overlay(root, REGION, "Subtitles on", auto_destroy_ms=1000)

    def cycle_next() -> None:
        """Select the next detected bubble."""
        nonlocal selected_idx
        if not current_blocks:
            return
        selected_idx = (selected_idx + 1) % len(current_blocks)
        highlight_current()

    def cycle_prev() -> None:
        """Select the previous detected bubble."""
        nonlocal selected_idx
        if not current_blocks:
            return
        selected_idx = (selected_idx - 1) % len(current_blocks)
        highlight_current()

    def copy_current() -> None:
        """Copy the current bubble's translation to the clipboard."""
        if selected_idx < 0 or selected_idx >= len(current_translations):
            return
        root.clipboard_clear()
        root.clipboard_append(current_translations[selected_idx])
        show_status_overlay(root, REGION, "Copied!", auto_destroy_ms=1000)

    def run_ocr_cycle():
        nonlocal last_coords, current_blocks, current_translations, selected_idx, highlight_rect
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
        current_blocks = blocks
        current_translations = translations
        selected_idx = -1
        if highlight_rect:
            canvas.delete(highlight_rect)
            highlight_rect = None

        if subtitle_visible:
            update_subtitles(translations)

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
                use_bubble_mask=use_bubble_mask,
                font_path=font_path,
                text_color=text_color,
                outline_color=outline_color,
                bg_alpha=bg_alpha,
            )
            bubble_items.extend(new_items)
            last_coords = coords
        fade_in(canvas.master, 200)

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
    keyboard.add_hotkey(hotkeys.get('next_bubble', 'ctrl+right'), cycle_next)
    keyboard.add_hotkey(hotkeys.get('prev_bubble', 'ctrl+left'), cycle_prev)
    keyboard.add_hotkey(hotkeys.get('copy_translation', 'ctrl+c'), copy_current)
    keyboard.add_hotkey(hotkeys.get('toggle_subtitles', 'ctrl+s'), toggle_subtitles)
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
