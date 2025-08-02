"""Main application entry point for manga translation overlay.

This module wires together capture, OCR, translation and rendering.  The
implementation follows the recommendations in ``DOC.md`` and the project goals
outlined in ``README.md`` by running capture in a background thread and keeping
the GUI responsive.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Optional

import keyboard
import tkinter as tk
from PIL import Image, ImageTk

from core.capture import grab_region
from core.config import load_config
from core.frame_grabber import FrameGrabber
from core.logger import setup_logger
from core.pipeline import process_region
from core.translate import set_engine
from core.ui.drawer import draw_translated_bubbles
from core.ui.overlay import fade_in, fade_out, show_status_overlay


CANVAS_BG = "#FF00FF"  # transparent key colour
DEFAULT_REGION = {"top": 128, "left": 575, "width": 768, "height": 864}


def build_root_window() -> tk.Tk:
    """Return a transparent, always-on-top root window."""

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-transparentcolor", "white")
    root.configure(bg="white")
    return root


def build_overlay_canvas(root: tk.Tk, region: dict) -> tk.Canvas:
    """Create the overlay canvas where translated bubbles are drawn."""

    win = tk.Toplevel(root)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.geometry(
        f"{region['width']}x{region['height']}+{region['left']}+{region['top']}"
    )
    try:
        win.attributes("-transparentcolor", CANVAS_BG)
    except tk.TclError:
        pass

    canvas = tk.Canvas(
        win,
        width=region["width"],
        height=region["height"],
        bg=CANVAS_BG,
        highlightthickness=0,
    )
    canvas.pack(fill="both", expand=True)
    canvas.create_rectangle(
        0,
        0,
        region["width"] - 1,
        region["height"] - 1,
        outline="red",
        width=4,
    )
    return canvas


def update_overlay_region(canvas: tk.Canvas, region: dict) -> None:
    """Resize and reposition the overlay canvas."""

    win = canvas.master
    win.geometry(
        f"{region['width']}x{region['height']}+{region['left']}+{region['top']}"
    )
    canvas.config(width=region["width"], height=region["height"])
    canvas.delete("all")
    canvas.create_rectangle(
        0,
        0,
        region["width"] - 1,
        region["height"] - 1,
        outline="red",
        width=4,
    )


class TranslatorApp:
    """Main GUI application for the translation overlay."""

    def __init__(self) -> None:
        setup_logger()
        self.logger = logging.getLogger(__name__)

        cfg = load_config("config.json")
        self.cfg = cfg
        self.hotkeys = cfg.get("hotkeys", {})

        set_engine(cfg.get("translator", "google"))

        self.region = DEFAULT_REGION.copy()
        self.fps = int(cfg.get("video_fps", 2))
        self.bubble_padding = int(cfg.get("bubble_padding", 0))
        self.replace_mode = bool(cfg.get("replace_mode", False))
        self.save_bubble_images = bool(cfg.get("save_bubble_images", False))
        self.overflow_to_nearby = bool(cfg.get("overflow_to_nearby", False))
        self.tooltip_overlay = bool(cfg.get("tooltip_overlay", True))
        self.align_smoothing = float(cfg.get("align_smoothing", 0.5))
        self.bubble_shape = cfg.get("bubble_shape", "ellipse")
        self.use_bubble_mask = bool(cfg.get("use_bubble_mask", False))
        self.font_path = cfg.get("overlay_font", "fonts/animeace2_reg.ttf")
        self.text_color = cfg.get("overlay_text_color", "#ffffff")
        self.outline_color = cfg.get("overlay_outline_color", "#000000")
        self.bg_alpha = int(cfg.get("overlay_bg_alpha", 128))
        self.conf_threshold = float(cfg.get("ocr_confidence_threshold", 0.5))
        self.highlight_color = cfg.get("highlight_color", "#ffff00")
        self.highlight_width = int(cfg.get("highlight_width", 2))

        self.root = build_root_window()
        self.canvas = build_overlay_canvas(self.root, self.region)

        self.bubble_items: list[int] = []
        self.bubbles_visible = True
        self.last_coords: dict = {}
        self.current_blocks: list = []
        self.current_translations: list = []
        self.selected_idx = -1
        self.highlight_rect: Optional[int] = None

        self.subtitle_visible = bool(cfg.get("subtitle_mode", False))
        self.subtitle_win: Optional[tk.Toplevel] = None
        self.subtitle_label: Optional[tk.Label] = None

        self.frame_grabber = FrameGrabber(self.region, fps=self.fps)
        self.video_running = False
        self._video_id: Optional[str] = None

        self._register_hotkeys()

    # ------------------------------------------------------------------
    # UI helpers
    def _register_hotkeys(self) -> None:
        """Bind keyboard shortcuts from the configuration file."""

        hk = self.hotkeys
        keyboard.add_hotkey(hk.get("ocr", "f8"), self.run_ocr_cycle)
        keyboard.add_hotkey(hk.get("toggle_bubbles", "f9"), self.toggle_bubbles)
        keyboard.add_hotkey(hk.get("video", "f7"), self.toggle_video_mode)
        keyboard.add_hotkey(hk.get("history", "f6"), self.show_history_popup)
        keyboard.add_hotkey(hk.get("select_region", "f10"), self.select_capture_region)
        keyboard.add_hotkey(hk.get("next_bubble", "ctrl+right"), self.cycle_next)
        keyboard.add_hotkey(hk.get("prev_bubble", "ctrl+left"), self.cycle_prev)
        keyboard.add_hotkey(hk.get("copy_translation", "ctrl+c"), self.copy_current)
        keyboard.add_hotkey(hk.get("toggle_subtitles", "ctrl+s"), self.toggle_subtitles)
        keyboard.add_hotkey(hk.get("quit", "esc"), self.root.destroy)

    # ------------------------------------------------------------------
    # Region selection
    def select_capture_region(self) -> None:
        """Let the user drag a rectangle to set the capture region."""

        sel = tk.Toplevel(self.root)
        sel.overrideredirect(True)
        sel.attributes("-topmost", True)
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        try:
            sel.attributes("-transparentcolor", "white")
            bg = "white"
        except tk.TclError:
            bg = "black"
        canvas_sel = tk.Canvas(
            sel,
            width=width,
            height=height,
            bg=bg,
            cursor="cross",
            highlightthickness=0,
        )
        canvas_sel.pack(fill="both", expand=True)

        start = [0, 0]
        rect: Optional[int] = None

        def on_press(event):
            nonlocal rect
            start[0], start[1] = event.x, event.y
            rect = canvas_sel.create_rectangle(
                event.x,
                event.y,
                event.x,
                event.y,
                outline="red",
                width=2,
            )

        def on_drag(event):
            if rect:
                canvas_sel.coords(rect, start[0], start[1], event.x, event.y)

        def on_release(event):
            left = min(start[0], event.x)
            top = min(start[1], event.y)
            w = abs(event.x - start[0])
            h = abs(event.y - start[1])
            self.region = {"left": left, "top": top, "width": w, "height": h}
            sel.destroy()
            update_overlay_region(self.canvas, self.region)
            self.frame_grabber.region = self.region
            show_status_overlay(self.root, self.region, "Region updated", auto_destroy_ms=1000)

        canvas_sel.bind("<ButtonPress-1>", on_press)
        canvas_sel.bind("<B1-Motion>", on_drag)
        canvas_sel.bind("<ButtonRelease-1>", on_release)

    # ------------------------------------------------------------------
    # Overlay rendering
    def run_ocr_cycle(self, use_latest: bool = False) -> None:
        """Capture the region, run OCR/translation and draw overlays."""

        for item in self.bubble_items:
            self.canvas.delete(item)
        self.bubble_items.clear()
        if self.highlight_rect:
            self.canvas.delete(self.highlight_rect)
            self.highlight_rect = None

        if use_latest:
            raw = self.frame_grabber.get_latest()
            if raw is None:
                self.logger.warning("No frame captured yet")
                show_status_overlay(self.root, self.region, "No frame", auto_destroy_ms=1000)
                return
        else:
            raw = grab_region(self.region)

        try:
            import cv2

            raw_rgb = cv2.cvtColor(raw, cv2.COLOR_BGR2RGB)
        except Exception:  # pragma: no cover - optional dependency
            raw_rgb = raw
        region_img = Image.fromarray(raw_rgb)

        timings: dict[str, float] = {}
        blocks, translations = process_region(
            raw,
            self.region,
            self.bubble_padding,
            timings,
            save_bubble_images=self.save_bubble_images,
            conf_threshold=self.conf_threshold,
        )

        self.current_blocks = blocks
        self.current_translations = translations
        self.selected_idx = -1

        if self.subtitle_visible:
            self.update_subtitles(translations)

        if self.bubbles_visible and blocks and translations:
            coords: dict = {}
            new_items = draw_translated_bubbles(
                self.canvas,
                region_img,
                blocks,
                translations,
                self.region,
                replace_mode=self.replace_mode,
                overflow_to_nearby=self.overflow_to_nearby,
                show_tooltip=self.tooltip_overlay,
                prev_coords=self.last_coords,
                smoothing=self.align_smoothing,
                coord_out=coords,
                bubble_shape=self.bubble_shape,
                use_bubble_mask=self.use_bubble_mask,
                font_path=self.font_path,
                text_color=self.text_color,
                outline_color=self.outline_color,
                bg_alpha=self.bg_alpha,
            )
            self.bubble_items.extend(new_items)
            self.last_coords = coords

        fade_in(self.canvas.master, 200)
        self.logger.info("Overlay updated")
        show_status_overlay(self.root, self.region, "Complete!", auto_destroy_ms=1000)

    # ------------------------------------------------------------------
    # Video mode
    def _video_loop(self) -> None:
        self.run_ocr_cycle(use_latest=True)
        if self.video_running:
            self._video_id = self.root.after(
                int(1000 / max(self.fps, 1)), self._video_loop
            )

    def toggle_video_mode(self) -> None:
        """Start or stop continuous processing of the capture region."""

        if self.video_running:
            self.video_running = False
            if self._video_id:
                self.root.after_cancel(self._video_id)
                self._video_id = None
            self.frame_grabber.stop()
            show_status_overlay(
                self.root, self.region, "Video mode stopped", auto_destroy_ms=1000
            )
        else:
            self.video_running = True
            self.frame_grabber.start()
            show_status_overlay(self.root, self.region, "Video mode started")
            self._video_loop()

    # ------------------------------------------------------------------
    # Bubble utilities
    def toggle_bubbles(self) -> None:
        """Show or hide translated bubbles with a fade animation."""

        self.bubbles_visible = not self.bubbles_visible
        state = "normal" if self.bubbles_visible else "hidden"
        for item in self.bubble_items:
            self.canvas.itemconfigure(item, state=state)
        if self.bubbles_visible:
            fade_in(self.canvas.master, 200)
        else:
            fade_out(self.canvas.master, 200)

    def cycle_next(self) -> None:
        """Highlight the next bubble."""

        if not self.current_blocks:
            return
        self.selected_idx = (self.selected_idx + 1) % len(self.current_blocks)
        self._highlight_selected()

    def cycle_prev(self) -> None:
        """Highlight the previous bubble."""

        if not self.current_blocks:
            return
        self.selected_idx = (self.selected_idx - 1) % len(self.current_blocks)
        self._highlight_selected()

    def _highlight_selected(self) -> None:
        if self.highlight_rect:
            self.canvas.delete(self.highlight_rect)
            self.highlight_rect = None
        if self.selected_idx < 0:
            return
        _, (x1, y1, x2, y2), *_ = self.current_blocks[self.selected_idx]
        self.highlight_rect = self.canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            outline=self.highlight_color,
            width=self.highlight_width,
        )

    def copy_current(self) -> None:
        """Copy the selected translation to the clipboard."""

        if self.selected_idx < 0 or not self.current_translations:
            return
        text = self.current_translations[self.selected_idx]
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        show_status_overlay(self.root, self.region, "Copied", auto_destroy_ms=1000)

    # ------------------------------------------------------------------
    # Subtitles
    def toggle_subtitles(self) -> None:
        """Toggle subtitle display window."""

        self.subtitle_visible = not self.subtitle_visible
        if self.subtitle_visible:
            self.update_subtitles(self.current_translations)
        elif self.subtitle_win:
            self.subtitle_win.destroy()
            self.subtitle_win = None
            self.subtitle_label = None

    def update_subtitles(self, translations: list[str]) -> None:
        """Update the subtitle window with current translations."""

        if not self.subtitle_visible:
            return
        if self.subtitle_win is None:
            self.subtitle_win = tk.Toplevel(self.root)
            self.subtitle_win.overrideredirect(True)
            self.subtitle_win.attributes("-topmost", True)
            self.subtitle_label = tk.Label(
                self.subtitle_win, bg="black", fg="white", justify="left"
            )
            self.subtitle_label.pack(fill="both", expand=True)
        self.subtitle_label.config(text="\n".join(translations))
        geom = (
            f"{self.region['width']}x100+{self.region['left']}+"
            f"{self.region['top'] + self.region['height'] + 10}"
        )
        self.subtitle_win.geometry(geom)

    # ------------------------------------------------------------------
    # History popup
    def show_history_popup(self) -> None:
        """Display translation history with image previews."""

        win = tk.Toplevel(self.root)
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
                        }
                    )
        except FileNotFoundError:
            pass

        def refresh_list(*_):
            query = search_var.get().lower()
            listbox.delete(0, tk.END)
            for item in history:
                if query in item["jp"].lower() or query in item["en"].lower():
                    listbox.insert(
                        tk.END,
                        f"{item['jp']} → {item['en']} ({item['engine']})",
                    )

        def on_select(_event):
            idx = listbox.curselection()
            if not idx:
                return
            item = history[idx[0]]
            img_path = Path("bubble_logs") / item["img"]
            if not img_path.exists():
                return
            img = Image.open(img_path)
            img.thumbnail((256, 256))
            img_tk = ImageTk.PhotoImage(img)
            preview_label.configure(image=img_tk)
            preview_label.image = img_tk

        listbox.bind("<<ListboxSelect>>", on_select)
        search_var.trace_add("write", refresh_list)
        refresh_list()

    # ------------------------------------------------------------------
    # Application runner
    def run(self) -> None:
        """Start the Tkinter main loop."""

        self.logger.info(
            "App ready. Press %s for OCR, %s for video, %s to quit.",
            self.hotkeys.get("ocr", "f8").upper(),
            self.hotkeys.get("video", "f7").upper(),
            self.hotkeys.get("quit", "esc").upper(),
        )
        self.root.mainloop()


def main() -> None:
    """Run the application."""

    app = TranslatorApp()
    app.run()


if __name__ == "__main__":
    main()

