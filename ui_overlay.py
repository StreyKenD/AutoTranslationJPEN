"""Control overlay window for translation app."""

from __future__ import annotations

from typing import Callable, Optional

try:
    from PyQt5 import QtCore, QtWidgets
except ImportError as exc:  # pragma: no cover - PyQt5 may be optional
    QtCore = None  # type: ignore[assignment]
    QtWidgets = None  # type: ignore[assignment]
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None


if QtWidgets is not None:

    class ControlOverlay(QtWidgets.QWidget):
        """Semi-transparent always-on-top overlay with control buttons.

        The overlay window ignores mouse events outside the control buttons,
        allowing users to interact with the underlying manga reader. Buttons
        emit callbacks for toggling overlays, pausing translation, and viewing
        logs.
        """

        def __init__(
            self,
            on_toggle_overlay: Optional[Callable[[], None]] = None,
            on_pause: Optional[Callable[[bool], None]] = None,
            on_view_log: Optional[Callable[[], None]] = None,
            parent: Optional[QtWidgets.QWidget] = None,
        ) -> None:
            """Initialize control overlay.

            Args:
                on_toggle_overlay: Callback for toggling translation overlays.
                on_pause: Callback when translation is paused or resumed.
                on_view_log: Callback for toggling the history panel.
                parent: Optional parent widget.
            """
            super().__init__(parent)
            self._on_toggle_overlay = on_toggle_overlay
            self._on_pause = on_pause
            self._on_view_log = on_view_log
            self._build_ui()

        def _build_ui(self) -> None:
            """Configure window flags and create control buttons."""
            self.setWindowFlags(
                QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
            )
            self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
            # Allow click-through outside of buttons. On Windows this maps to
            # WS_EX_LAYERED | WS_EX_TRANSPARENT styles.
            self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
            self.setWindowOpacity(0.5)
            screen = QtWidgets.QApplication.primaryScreen()
            if screen is not None:
                self.setGeometry(screen.geometry())

            # Container for interactive controls (not transparent for mouse
            # events)
            container = QtWidgets.QWidget(self)
            container.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)
            layout = QtWidgets.QHBoxLayout(container)
            layout.setContentsMargins(8, 8, 8, 8)

            self.toggle_btn = QtWidgets.QPushButton("Toggle Overlay")
            self.toggle_btn.clicked.connect(self._handle_toggle_overlay)
            layout.addWidget(self.toggle_btn)

            self.pause_btn = QtWidgets.QPushButton("Pause Translation")
            self.pause_btn.setCheckable(True)
            self.pause_btn.clicked.connect(self._handle_pause)
            layout.addWidget(self.pause_btn)

            self.log_btn = QtWidgets.QPushButton("View Log")
            self.log_btn.clicked.connect(self._handle_view_log)
            layout.addWidget(self.log_btn)

            # Position controls in the top-left corner by default
            container.adjustSize()
            container.move(0, 0)

        # Callback handlers -------------------------------------------------
        def _handle_toggle_overlay(self) -> None:
            """Invoke the toggle overlay callback if provided."""
            if self._on_toggle_overlay is not None:
                self._on_toggle_overlay()

        def _handle_pause(self, checked: bool) -> None:
            """Invoke the pause callback with the button state."""
            if self._on_pause is not None:
                self._on_pause(checked)

        def _handle_view_log(self) -> None:
            """Invoke the view log callback if provided."""
            if self._on_view_log is not None:
                self._on_view_log()

else:  # pragma: no cover - triggered when PyQt5 is missing

    class ControlOverlay:  # type: ignore[override]
        """Fallback implementation used when PyQt5 is unavailable."""

        def __init__(self, *_, **__) -> None:  # pragma: no cover - runtime guard
            raise ImportError(
                "PyQt5 is required to use ControlOverlay"
            ) from _IMPORT_ERROR


__all__ = ["ControlOverlay"]
