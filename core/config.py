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
    "translator": "google",
    "video_fps": 2,
    "ocr_confidence_threshold": 0.5
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
