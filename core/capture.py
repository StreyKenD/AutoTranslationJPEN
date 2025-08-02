"""Screen capture helpers."""

from __future__ import annotations

import logging
import os

import cv2
import mss
import numpy as np


logger = logging.getLogger(__name__)
os.makedirs("debug", exist_ok=True)
DEBUG_IMAGES = os.environ.get("DEBUG_IMAGES") == "1"


def get_screen_region(monitor: int = 0) -> dict[str, int]:
    """Return the bounding box for the given monitor.

    Args:
        monitor: Monitor index as understood by :mod:`mss`. ``0`` represents
            the virtual screen spanning all monitors, while ``1`` selects the
            primary monitor.

    Returns:
        dict[str, int]: Mapping with ``left``, ``top``, ``width`` and
        ``height`` keys describing the monitor's region.
    """

    with mss.mss() as sct:
        mon = sct.monitors[monitor]
    return {
        "left": mon["left"],
        "top": mon["top"],
        "width": mon["width"],
        "height": mon["height"],
    }


def grab_region(region: dict[str, int], target_width: int | None = None) -> np.ndarray:
    """Capture a screen region.

    Args:
        region: Mapping with ``left``, ``top``, ``width`` and ``height`` keys.
        target_width: If provided and the captured frame is narrower, scale the
            image to this width while preserving aspect ratio.

    Returns:
        np.ndarray: Captured frame in RGB order.
    """

    with mss.mss() as sct:
        frame = sct.grab(region)

    img = cv2.cvtColor(np.array(frame), cv2.COLOR_BGRA2RGB)
    if target_width and img.shape[1] < target_width:
        scale = target_width / img.shape[1]
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    if DEBUG_IMAGES:
        cv2.imwrite("debug/00_captured.png", img)
    return img


def grab_screen(target_width: int | None = None, monitor: int = 0) -> np.ndarray:
    """Capture the entire screen.

    Args:
        target_width: If provided and the captured frame is narrower, scale the
            image to this width while preserving aspect ratio.
        monitor: Monitor index as understood by :func:`get_screen_region`.

    Returns:
        np.ndarray: Captured frame in RGB order.
    """

    region = get_screen_region(monitor)
    return grab_region(region, target_width=target_width)
