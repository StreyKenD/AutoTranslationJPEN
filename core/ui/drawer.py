# ui/drawer.py (refactored with dynamic font and real blurred background)
import textwrap
import logging
import tkinter as tk
from PIL import (
    Image, ImageDraw, ImageFont,
    ImageTk, ImageFilter,
)

# Settings (can be moved to config.py later)
FONT_PATH     = "fonts/animeace2_reg.ttf"
MIN_FONT_SIZE = 12            # minimum font size
BLUR_RADIUS   = 5             # radius for background blur
LINE_SPACING  = 4             # spacing between lines
BG_ALPHA      = 180           # alpha for white overlay (0-255)
CORNER_RADIUS = 10            # corner radius for overlay box

logger = logging.getLogger(__name__)

def draw_translated_bubbles(
    canvas,
    region_img,
    blocks,
    translations,
    region,
    replace_mode: bool = False,
    overflow_to_nearby: bool = False,
    show_tooltip: bool = True,
    prev_coords: dict | None = None,
    smoothing: float = 0.0,
    coord_out: dict | None = None,
):
    """Draw translated bubbles on the canvas with optional UX helpers.

    Parameters
    ----------
    canvas : ``tkinter.Canvas``
        Canvas to draw on.
    region_img : ``PIL.Image``
        Captured region image.
    blocks : list
        Tuples ``(text, (x1, y1, x2, y2), conf, angle)``.
    translations : list
        Translated strings matching ``blocks`` order.
    region : dict
        Region info with ``left``, ``top``, ``width`` and ``height``.
    replace_mode : bool
        If ``True``, draw on a plain white background instead of
        using the blurred patch.
    overflow_to_nearby : bool, optional
        When ``True``, draw text beside the bubble if it cannot fit inside.
    show_tooltip : bool, optional
        Display the original + translated text on hover.
    prev_coords : dict, optional
        Previous coordinates keyed by translation for alignment smoothing.
    smoothing : float, optional
        Blend factor for position smoothing ``0``-``1``.
    coord_out : dict, optional
        Dictionary populated with the final coordinates for each translation.
    """
    canvas_items = []
    if not hasattr(canvas, "images"):
        canvas.images = []
    canvas.images.clear()

    if prev_coords is None:
        prev_coords = {}
    if coord_out is None:
        coord_out = {}

    tooltip_win = None

    def show_tip(event, text):
        nonlocal tooltip_win
        if tooltip_win is not None:
            tooltip_win.destroy()
        x = event.x_root + 10
        y = event.y_root + 10
        tooltip_win = tk.Toplevel(canvas)
        tooltip_win.overrideredirect(True)
        tooltip_win.geometry(f"+{x}+{y}")
        label = tk.Label(tooltip_win, text=text, bg="yellow", font=("Arial", 10))
        label.pack()

    def hide_tip(event=None):
        nonlocal tooltip_win
        if tooltip_win is not None:
            tooltip_win.destroy()
            tooltip_win = None

    hide_tip()
    for (orig, (x1, y1, x2, y2), conf, angle), translated in zip(blocks, translations):
        try:
            w, h = x2 - x1, y2 - y1

            # 1. Crop and blur the actual background patch
            region_x = region["left"]
            region_y = region["top"]

            x1_rel = x1 - region_x
            y1_rel = y1 - region_y
            x2_rel = x2 - region_x
            y2_rel = y2 - region_y

            patch = region_img.crop((x1_rel, y1_rel, x2_rel, y2_rel))
            if replace_mode:
                bg = Image.new("RGBA", patch.size, (255, 255, 255, BG_ALPHA))
            else:
                bg = patch.filter(ImageFilter.GaussianBlur(BLUR_RADIUS))
                overlay = Image.new("RGBA", bg.size, (0, 0, 0, 80))
                bg = Image.alpha_composite(bg.convert("RGBA"), overlay)
                white_wash = Image.new("RGBA", bg.size, (255, 255, 255, BG_ALPHA))
                bg = Image.alpha_composite(bg, white_wash)

            # 2. Prepare overlay image and draw semi-transparent background
            img = Image.new("RGBA", (w, h))

            shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rounded_rectangle([(0, 0), (w, h)], radius=CORNER_RADIUS, fill=(0, 0, 0, 120))
            shadow_blurred = shadow.filter(ImageFilter.GaussianBlur(6))
            img.paste(shadow_blurred, (0, 0), shadow_blurred)

            img.paste(bg, (0, 0))
            draw = ImageDraw.Draw(img, "RGBA")

            # 3. Determine dynamic font size
            font_size = min(
                max(MIN_FONT_SIZE, int(h * 0.25)),
                max(MIN_FONT_SIZE, int(w * 0.12))  # this caps font size if bubble is narrow
            )

            overflow = False
            while True:
                try:
                    font = ImageFont.truetype(FONT_PATH, font_size)
                except IOError:
                    logger.warning(f"Failed to load font at {FONT_PATH}, using default.")
                    font = ImageFont.load_default()

                max_chars = max(10, w // (font_size * 2 // 3))
                wrapped = textwrap.fill(translated, width=max_chars)
                lines = wrapped.split("\n")

                try:
                    line_height = font.getbbox("A")[3] + LINE_SPACING
                except Exception:
                    line_height = 16 + LINE_SPACING

                total_text_height = len(lines) * line_height

                if total_text_height <= h - 10 or font_size <= MIN_FONT_SIZE:
                    overflow = total_text_height > h - 10
                    break
                font_size -= 1

            if overflow and overflow_to_nearby:
                x_draw = x2 + 10
                if x_draw + w > region["left"] + region["width"]:
                    x_draw = x1 - w - 10
                y_draw = y1
            else:
                x_draw = x1
                y_draw = y1

            if translated in prev_coords:
                px, py = prev_coords[translated]
                x_draw = int(px * smoothing + x_draw * (1 - smoothing))
                y_draw = int(py * smoothing + y_draw * (1 - smoothing))

            # 6. Draw each line centered
            for i, line in enumerate(lines):
                try:
                    text_w = font.getbbox(line)[2]
                except AttributeError:
                    text_w = draw.textlength(line, font=font)
                x_text = (w - text_w) // 2
                y_text = (h - total_text_height) // 2 + i * line_height
                # shadow
                for dx in (-1, 0, 1):
                    for dy in (-1, 0, 1):
                        if dx or dy:
                            draw.text(
                                (x_text+dx, y_text+dy),
                                line,
                                font=font,
                                fill=(0, 0, 0, 255)
                            )
                # main text
                draw.text(
                    (x_text, y_text),
                    line,
                    font=font,
                    fill=(255, 255, 255, 255)
                )

            # 7. Convert to PhotoImage and draw on canvas
            photo = ImageTk.PhotoImage(img)
            canvas.images.append(photo)
            item = canvas.create_image(x_draw, y_draw, image=photo, anchor="nw")
            canvas_items.append(item)
            coord_out[translated] = (x_draw, y_draw)

            if show_tooltip:
                tooltip = f"{orig}\n{translated}"
                canvas.tag_bind(item, "<Enter>", lambda e, t=tooltip: show_tip(e, t))
                canvas.tag_bind(item, "<Leave>", hide_tip)
                canvas.tag_bind(item, "<Button-1>", lambda e, t=tooltip: show_tip(e, t))

        except Exception as e:
            logger.error(f"[draw_translated_bubbles] Error: {e}")

    return canvas_items
