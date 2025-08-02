"""Benchmark different translation engines."""

from __future__ import annotations

import argparse
import logging
import time
from typing import Any, Dict, List

from .translate import set_engine, translate_batch


logger = logging.getLogger(__name__)


def load_texts(path: str) -> List[str]:
    """Return non-empty lines from ``path``."""
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def benchmark(texts: List[str], engines: List[str]) -> List[Dict[str, Any]]:
    """Benchmark ``engines`` on ``texts``."""
    results: List[Dict[str, Any]] = []
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
        logger.info("%s: %.3fs", item["engine"], item["time"])
        if texts and item["output"]:
            logger.info("Sample: %s -> %s", texts[0], item["output"][0])
    if texts:
        logger.info("Average time per line:")
        for item in data:
            logger.info("  %s: %.3f s", item["engine"], item["time"] / len(texts))


if __name__ == "__main__":
    main()
