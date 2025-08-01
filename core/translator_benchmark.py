"""Benchmark different translation engines."""

import argparse
import logging
import time
from pathlib import Path
from typing import List

from .translate import set_engine, translate_batch


def load_texts(path: str) -> List[str]:
    """Return non-empty lines from ``path``."""
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def benchmark(texts: List[str], engines: List[str]):
    """Benchmark ``engines`` on ``texts``."""
    results = []
    for eng in engines:
        set_engine(eng)
        start = time.perf_counter()
        out = translate_batch(texts)
        duration = time.perf_counter() - start
        results.append({"engine": eng, "time": duration, "output": out})
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark translation engines")
    parser.add_argument("text_file", help="File with Japanese lines")
    parser.add_argument(
        "--engines",
        nargs="+",
        default=["google", "deepl", "marian", "libre", "best"],
        help="Engines to test",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    texts = load_texts(args.text_file)
    data = benchmark(texts, args.engines)
    for item in data:
        logging.info("%s: %.3fs", item["engine"], item["time"])
        if texts and item["output"]:
            logging.info("Sample: %s -> %s", texts[0], item["output"][0])
    if texts:
        logging.info("Average time per line:")
        for item in data:
            logging.info("  %s: %.3f s", item["engine"], item["time"] / len(texts))


if __name__ == "__main__":
    main()
