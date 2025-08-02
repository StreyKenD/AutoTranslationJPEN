"""Overlay drawing helpers."""
import textwrap
import logging
import tkinter as tk
from PIL import (
    Image,
    ImageDraw,
    ImageFont,
    ImageTk,
    ImageFilter,
    ImageColor,
)

# Settings (can be moved to config.py later)
FONT_PATH     = "fonts/animeace2_reg.ttf"
MIN_FONT_SIZE = 12            # minimum font size
BLUR_RADIUS   = 5             # radius for background blur
LINE_SPACING  = 4             # spacing between lines
BG_ALPHA      = 128           # alpha for white overlay (0-255)
CORNER_RADIUS = 10            # corner radius for overlay box
TEXT_COLOR    = (255, 255, 255, 255)
OUTLINE_COLOR = (0, 0, 0, 255)

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
    bubble_shape: str = "ellipse",
    use_bubble_mask: bool = False,
    prev_coords: dict | None = None,
    smoothing: float = 0.0,
    coord_out: dict | None = None,
    font_path: str = FONT_PATH,
    text_color: str | tuple = TEXT_COLOR,
    outline_color: str | tuple = OUTLINE_COLOR,
    bg_alpha: int = BG_ALPHA,
):
    """Draw translated bubbles on the canvas with optional UX helpers.

    Parameters
    ----------
    canvas : ``tkinter.Canvas``
        Canvas to draw on.
    region_img : ``PIL.Image``
        Captured region image.
    blocks : list
        Tuples ``(text, (x1, y1, x2, y2), conf, angle, contour)``.
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
    bubble_shape : str, optional
        Either ``"ellipse"`` or ``"rect"`` to control overlay geometry.
    use_bubble_mask : bool, optional
        Mask overlays using the precise bubble contour when available.
    prev_coords : dict, optional
        Previous coordinates keyed by translation for alignment smoothing.
    smoothing : float, optional
        Blend factor for position smoothing ``0``-``1``.
    coord_out : dict, optional
        Dictionary populated with the final coordinates for each translation.
    font_path : str, optional
        Path to a TTF font used for the translated text.
    text_color : str or tuple, optional
        Fill color for the translated text.
    outline_color : str or tuple, optional
        Outline color around the text for readability.
    bg_alpha : int, optional
        Alpha value for the bubble background (0-255).
        ``128`` corresponds to 50% transparency.
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
    if isinstance(text_color, str):
        tc = ImageColor.getrgb(text_color)
        text_color = (*tc, 255)
    if isinstance(outline_color, str):
        oc = ImageColor.getrgb(outline_color)
        outline_color = (*oc, 255)

    for (orig, (x1, y1, x2, y2), conf, angle, contour), translated in zip(blocks, translations):
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
                bg = Image.new("RGBA", patch.size, (255, 255, 255, bg_alpha))
            else:
                bg = patch.filter(ImageFilter.GaussianBlur(BLUR_RADIUS)).convert("RGBA")
                white = Image.new("RGBA", bg.size, (255, 255, 255, 255))
                bg = Image.blend(bg, white, bg_alpha / 255)

            # 2. Prepare overlay image and draw semi-transparent background
            img = Image.new("RGBA", (w, h))

            mask = Image.new("L", (w, h), 0)
            mask_draw = ImageDraw.Draw(mask)
            shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            if use_bubble_mask and contour is not None:
                rel = [(px - x1, py - y1) for px, py in contour]
                mask_draw.polygon(rel, fill=255)
                shadow_draw.polygon(rel, fill=(0, 0, 0, 120))
            elif bubble_shape == "ellipse":
                mask_draw.ellipse([(0, 0), (w, h)], fill=255)
                shadow_draw.ellipse([(0, 0), (w, h)], fill=(0, 0, 0, 120))
            else:
                mask_draw.rounded_rectangle([(0, 0), (w, h)], radius=CORNER_RADIUS, fill=255)
                shadow_draw.rounded_rectangle([(0, 0), (w, h)], radius=CORNER_RADIUS, fill=(0, 0, 0, 120))
            shadow_blurred = shadow.filter(ImageFilter.GaussianBlur(6))
            img.paste(shadow_blurred, (0, 0), shadow_blurred)

            img.paste(bg, (0, 0), mask)
            draw = ImageDraw.Draw(img, "RGBA")

            # 3. Determine dynamic font size
            font_size = min(
                max(MIN_FONT_SIZE, int(h * 0.25)),
                max(MIN_FONT_SIZE, int(w * 0.12))  # this caps font size if bubble is narrow
            )

            overflow = False
            while True:
                try:
                    font = ImageFont.truetype(font_path, font_size)
                except IOError:
                    logger.warning("Failed to load font at %s, using default.", font_path)
                    font = ImageFont.load_default()

                max_chars = max(10, w // (font_size * 2 // 3))
                wrapped = textwrap.fill(translated, width=max_chars)
                lines = wrapped.split("\n")

                try:
                    line_height = font.getbbox("A")[3] + LINE_SPACING
                except Exception:
                    line_height = 16 + LINE_SPACING

                total_text_height = len(lines) * line_height
                width_overflow = False
                for ln in lines:
                    try:
                        tw = font.getbbox(ln)[2]
                    except AttributeError:
                        tw = draw.textlength(ln, font=font)
                    if tw > w - 10:
                        width_overflow = True
                        break

                if (total_text_height <= h - 10 and not width_overflow) or font_size <= MIN_FONT_SIZE:
                    overflow = total_text_height > h - 10 or width_overflow
                    break
                font_size -= 1

            if overflow and overflow_to_nearby:
                x_draw = x2 + 10
                if x_draw + w > region["left"] + region["width"]:
                    x_draw = x1 - w - 10
                y_draw = y1
                arrow_color = "#%02x%02x%02x" % text_color[:3]
                arrow = canvas.create_line(
                    x1 + w // 2,
                    y1 + h // 2,
                    x_draw,
                    y_draw + h // 2,
                    arrow=tk.LAST,
                    fill=arrow_color,
                    width=2,
                )
                canvas_items.append(arrow)
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
                                (x_text + dx, y_text + dy),
                                line,
                                font=font,
                                fill=outline_color,
                            )
                # main text
                draw.text(
                    (x_text, y_text),
                    line,
                    font=font,
                    fill=text_color,
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
