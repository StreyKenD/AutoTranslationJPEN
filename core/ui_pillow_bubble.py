# core/ui_pillow_bubble.py
import os
import textwrap
from PIL import Image, ImageDraw, ImageFont, ImageTk
import logging

# Adjust these paths & settings to your taste
FONT_PATH = "arial.ttf"            # or path to any .ttf you like
FONT_SIZE = 14
RADIUS    = 12
PADDING   = 8  # extra padding inside bubble

# cache Tk PhotoImages to avoid GC
_photo_cache = {}

def make_bubble_image(text: str, w: int, h: int) -> Image.Image:
    # Create transparent RGBA image
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except IOError:
        font = ImageFont.load_default()
        logging.warning(f"Failed to load {FONT_PATH}, using default font")

    # Draw rounded rectangle background
    draw.rounded_rectangle(
        [(0, 0), (w, h)],
        radius=RADIUS,
        fill=(255, 255, 255, 255),    # **solid** white
        outline=(0, 0, 0, 255),       # black border
        width=2
    )

    # Wrap and measure text
    wrapped = textwrap.fill(text, width=max(10, w // (FONT_SIZE - 2)))

    try:
            # Pillow ≥ 8.0.0
            bbox = draw.multiline_textbbox((0, 0), wrapped, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
    except AttributeError:
        # Older Pillow: fallback to textbbox for each line
        lines = wrapped.split("\n")
        tw = max(draw.textbbox((0,0), line, font=font)[2] for line in lines)
        line_heights = [draw.textbbox((0,0), line, font=font)[3] - draw.textbbox((0,0), line, font=font)[1]
                        for line in lines]
        th = sum(line_heights)

    # Center text
    x = (w - tw) // 2
    y = (h - th) // 2
    draw.multiline_text(
        (x, y),
        wrapped,
        font=font,
        fill=(0, 0, 0, 255),      # **pure black**
        align="center"
    )

    return im

def draw_bubbles_on_canvas(canvas, blocks, translations, region):
    """
    Clears the canvas and draws each bubble+translation image at the correct spot.
    blocks: List of (text, (x1,y1,x2,y2), conf, angle)
    translations: List of strings
    region: dict with 'left','top'
    """
    global _photo_cache
    new_cache = {}
    canvas.delete("all")

    for i, ((_, (x1, y1, x2, y2), conf, angle), trans) in enumerate(zip(blocks, translations)):
        w, h = x2 - x1, y2 - y1
        key = (i, trans, w, h)
        if key in _photo_cache:
            photo = _photo_cache[key]
        else:
            pil_im = make_bubble_image(trans, w, h)
            photo = ImageTk.PhotoImage(pil_im)
            new_cache[key] = photo

        # draw at (x1,y1) relative to region
        canvas.create_image(
            x1, y1,
            image=photo,
            anchor="nw"
        )

    # replace cache
    _photo_cache = new_cache
