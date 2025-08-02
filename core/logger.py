"""Application logging helpers."""

from __future__ import annotations

import logging
from pathlib import Path


def setup_logger(
    log_path: str | Path | None = None, level: int = logging.DEBUG
) -> logging.Logger:
    """Configure and return the root logger.

    Args:
        log_path: Path to the log file. Defaults to ``../app.log``.
        level: Logging level for both file and console handlers.

    Returns:
        logging.Logger: Configured root logger.
    """

    if log_path is None:
        log_path = Path(__file__).resolve().parent.parent / "app.log"
    else:
        log_path = Path(log_path)

    logger = logging.getLogger()
    logger.setLevel(level)

    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
