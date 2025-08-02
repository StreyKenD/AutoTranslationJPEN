"""Background frame grabber for real-time capture.

This module implements a threaded frame grabber that continuously captures
screen frames in a separate thread. Keeping the capture loop independent of the
processing loop follows the guidance in ``DOC.md`` for a frame-synchronised
pipeline that always works on the latest frame while dropping older ones.
"""

from __future__ import annotations

import threading
import time
from typing import Optional

import numpy as np

from .capture import get_screen_region, grab_region


class FrameGrabber:
    """Continuously capture a screen region in the background.

    Args:
        region: Dictionary describing the region to capture. Must contain
            ``top``, ``left``, ``width`` and ``height`` keys. If ``None``, the
            primary monitor is used.
        fps: Target capture rate in frames per second.
    """

    def __init__(self, region: dict[str, int] | None = None, fps: int = 30) -> None:
        self.region = region or get_screen_region(1)
        self.fps = fps
        self._frame: Optional[np.ndarray] = None
        self._running = False
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Start the capture thread if not already running."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the capture thread and wait for it to finish."""
        self._running = False
        if self._thread:
            self._thread.join()

    def _run(self) -> None:
        interval = 1 / max(self.fps, 1)
        while self._running:
            frame = grab_region(self.region)
            with self._lock:
                self._frame = frame
            time.sleep(interval)

    def get_latest(self) -> Optional[np.ndarray]:
        """Return a copy of the most recently captured frame.

        Returns:
            Optional[np.ndarray]: Latest captured frame or ``None`` if no frame
            has been captured yet.
        """

        with self._lock:
            return None if self._frame is None else self._frame.copy()
