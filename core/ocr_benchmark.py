"""Simple Manga-OCR benchmarking utilities."""

import argparse
import logging
import time
from pathlib import Path

import cv2
import torch

from .manga_ocr import extract_text


def benchmark_directory(dir_path: str):
    """Benchmark OCR speed for all images in ``dir_path``."""
    paths = [p for p in Path(dir_path).iterdir() if p.suffix.lower() in {'.png', '.jpg', '.jpeg'}]
    results = []
    for path in paths:
        img = cv2.imread(str(path))
        if img is None:
            logging.warning("Could not read %s", path)
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
    logging.info("GPU acceleration: %s", torch.cuda.is_available())
    data = benchmark_directory(args.input_dir)
    total = sum(r["time"] for r in data)
    for r in data:
        logging.info("%s: %.3fs -> %s", r["image"], r["time"], r["text"])
    if data:
        logging.info("Processed %d images in %.2fs (avg %.3fs)", len(data), total, total / len(data))


if __name__ == "__main__":
    main()
