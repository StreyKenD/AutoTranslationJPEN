"""Translation helpers with caching and history."""

from deep_translator import GoogleTranslator
from typing import List
import logging
import sqlite3
import csv
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "translations.db"

_conn = sqlite3.connect(DB_PATH)
_conn.execute(
    "CREATE TABLE IF NOT EXISTS cache (source TEXT PRIMARY KEY, translated TEXT)"
)

HISTORY_CSV = Path(__file__).resolve().parent.parent / "historico_traducoes.csv"


def _lookup_cache(text: str) -> str | None:
    """Return cached translation if available."""
    cur = _conn.execute("SELECT translated FROM cache WHERE source=?", (text,))
    row = cur.fetchone()
    return row[0] if row else None


def _store_cache(text: str, translation: str) -> None:
    """Persist a translation to the cache."""
    try:
        _conn.execute(
            "INSERT OR REPLACE INTO cache (source, translated) VALUES (?, ?)",
            (text, translation),
        )
        _conn.commit()
    except Exception as e:
        logging.error("Cache store failed: %s", e)


def _log_history(source: str, translated: str) -> None:
    """Append a translation pair to ``historico_traducoes.csv``."""
    try:
        write_header = not HISTORY_CSV.exists()
        with open(HISTORY_CSV, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["Japanese", "English"])
            writer.writerow([source, translated])
    except Exception as e:
        logging.error("History log failed: %s", e)


def translate_batch(texts: List[str]) -> List[str]:
    """Translate a list of Japanese strings to English with caching."""
    results: List[str] = ["" for _ in texts]
    to_translate: list[str] = []
    indices: list[int] = []

    for i, t in enumerate(texts):
        cached = _lookup_cache(t)
        if cached is not None:
            results[i] = cached
            _log_history(t, cached)
        else:
            to_translate.append(t)
            indices.append(i)

    if to_translate:
        try:
            translator = GoogleTranslator(source="ja", target="en")
            translated = translator.translate_batch(to_translate)
        except Exception as e:
            logging.error("Google Translate batch error: %s", e)
            translated = ["" for _ in to_translate]

        for idx, src, trans in zip(indices, to_translate, translated):
            results[idx] = trans
            _store_cache(src, trans)
            _log_history(src, trans)

    return results
