"""Configuration loader for customizable settings."""

import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "hotkeys": {
        "ocr": "f8",
        "toggle_bubbles": "f9",
        "video": "f7",
        "next_bubble": "ctrl+right",
        "prev_bubble": "ctrl+left",
        "copy_translation": "ctrl+c",
        "toggle_subtitles": "ctrl+s",
        "quit": "esc",
        "history": "f6"
    },
    "bubble_padding": 8,
    "replace_mode": False,
    "save_bubble_images": False,
    "overflow_to_nearby": False,
    "tooltip_overlay": True,
    "align_smoothing": 0.5,
    "bubble_shape": "ellipse",
    "use_bubble_mask": False,
    "overlay_font": "fonts/animeace2_reg.ttf",
    "overlay_text_color": "#ffffff",
    "overlay_outline_color": "#000000",
    "overlay_bg_alpha": 128,
    "translator": "google",
    "video_fps": 2,
    "ocr_confidence_threshold": 0.5,
    "subtitle_mode": False,
    "highlight_color": "#ffff00",
    "highlight_width": 2,
}

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def load_config():
    """Load configuration from ``config.json`` if present."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse %s: %s", CONFIG_PATH, e)
        except Exception as e:
            logger.error("Failed to load config: %s", e)
        else:
            DEFAULT_CONFIG.update(data)
    return DEFAULT_CONFIG
