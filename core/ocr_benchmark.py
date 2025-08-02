"""Simple Manga-OCR benchmarking utilities."""

from __future__ import annotations

import argparse
import logging
import time
from pathlib import Path
from typing import Any, Dict, List

import cv2
import torch

from .manga_ocr import extract_text


logger = logging.getLogger(__name__)


def benchmark_directory(dir_path: str) -> List[Dict[str, Any]]:
    """Benchmark OCR speed for all images in ``dir_path``.

    Args:
        dir_path: Directory containing image files.

    Returns:
        list[dict[str, Any]]: Timing and text results for each image.
    """

    paths = [
        p
        for p in Path(dir_path).iterdir()
        if p.suffix.lower() in {".png", ".jpg", ".jpeg"}
    ]
    results: List[Dict[str, Any]] = []
    for path in paths:
        img = cv2.imread(str(path))
        if img is None:
            logger.warning("Could not read %s", path)
            continue
        start = time.perf_counter()
        blocks = extract_text(img)
        duration = time.perf_counter() - start
        text = blocks[0][0] if blocks else ""
        results.append({"image": path.name, "time": duration, "text": text})
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark Manga-OCR on bubble images")
    parser.add_argument("input_dir", help="Directory with bubble crops")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logger.info("GPU acceleration: %s", torch.cuda.is_available())
    data = benchmark_directory(args.input_dir)
    total = sum(r["time"] for r in data)
    for r in data:
        logger.info("%s: %.3fs -> %s", r["image"], r["time"], r["text"])
    if data:
        logger.info(
            "Processed %d images in %.2fs (avg %.3fs)",
            len(data),
            total,
            total / len(data),
        )


if __name__ == "__main__":
    main()
