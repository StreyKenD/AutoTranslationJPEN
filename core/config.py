"""Configuration loader for customizable settings."""

import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "hotkeys": {
        "ocr": "f8",
        "toggle_bubbles": "f9",
        "quit": "esc"
    },
    "bubble_padding": 8,
    "replace_mode": False
}

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"


def load_config():
    """Load configuration from ``config.json`` if present."""
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            DEFAULT_CONFIG.update(data)
        except Exception as e:
            logger.error("Failed to load config: %s", e)
    return DEFAULT_CONFIG
