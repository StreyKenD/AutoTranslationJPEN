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


from PIL import Image, ImageDraw, ImageFont, ImageTk
import textwrap

def draw_bubbles_on_canvas(canvas, blocks, translations, region):
    canvas_items = []

    if not hasattr(canvas, "images"):
        canvas.images = []

    canvas.images.clear()

    for (text, (x1, y1, x2, y2), conf, angle), translated in zip(blocks, translations):
        try:
            # Bubble size settings
            max_width = 220
            max_height = 120
            width = min(max_width, max(150, x2 - x1))
            height = min(max_height, max(60, y2 - y1))
            padding = 10

            # Create transparent image
            img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)

            # Draw rounded white bubble with black border
            draw.rounded_rectangle(
                (0, 0, width, height),
                radius=20,
                fill=(255, 255, 255, 240),
                outline=(0, 0, 0),
                width=3
            )

            # Load font
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()

            # Wrap text manually
            line_width = 25
            wrapped_text = textwrap.fill(translated, width=line_width)
            lines = wrapped_text.split('\n')

            # Measure text block height for vertical centering
            line_height = font.getbbox("A")[3] + 4  # height + line spacing
            total_text_height = len(lines) * line_height

            for i, line in enumerate(lines):
                line_width_px = font.getbbox(line)[2]
                x = (width - line_width_px) // 2
                y = (height - total_text_height) // 2 + i * line_height
                draw.text((x, y), line, fill="black", font=font)

            # Convert to Tk image
            photo = ImageTk.PhotoImage(img)
            canvas.images.append(photo)

            # Draw centered
            cx = x1 + (x2 - x1) // 2
            cy = y1 + (y2 - y1) // 2
            item = canvas.create_image(cx, cy, image=photo, anchor="center")
            canvas_items.append(item)

        except Exception as e:
            print(f"[draw_bubbles_on_canvas] Error drawing bubble: {e}")

    return canvas_items
