"""Configuration loader for customizable settings."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict


logger = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    "bubble_padding": 8,
    "bubble_min_width": 25,
    "bubble_min_height": 25,
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


def load_config(path: str | Path | None = None) -> Dict[str, Any]:
    """Load configuration from a JSON file.

    Args:
        path: Optional path to the configuration file. Defaults to
            ``config.json`` at the repository root when ``None``.

    Returns:
        dict[str, Any]: Merged configuration dictionary.
    """

    cfg_path = Path(path) if path else CONFIG_PATH
    config = DEFAULT_CONFIG.copy()
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse %s: %s", cfg_path, e)
        except Exception as e:  # pragma: no cover - unexpected IO errors
            logger.error("Failed to load config: %s", e)
        else:
            config.update(data)
    return config
