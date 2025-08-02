"""Translation helpers with caching and history."""

from __future__ import annotations

from deep_translator import (
    DeeplTranslator,
    GoogleTranslator,
    LibreTranslator,
)

try:
    from transformers import MarianMTModel, MarianTokenizer
    import torch
except Exception:  # pragma: no cover - optional dependency
    MarianMTModel = None
    MarianTokenizer = None
    torch = None
import csv
import logging
import sqlite3
from pathlib import Path
from threading import Lock

DB_PATH = Path(__file__).resolve().parent.parent / "translations.db"


_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_DB_LOCK = Lock()

_conn.execute(
    "CREATE TABLE IF NOT EXISTS cache (source TEXT PRIMARY KEY, translated TEXT)"
)

HISTORY_CSV = Path(__file__).resolve().parent.parent / "historico_traducoes.csv"

logger = logging.getLogger(__name__)

TRANSLATOR = "google"
_model = None
_tokenizer = None


def _prompt_choice(source: str, g_trans: str, m_trans: str) -> str:
    """Display a popup to let the user pick a translation.

    Args:
        source: Original Japanese text.
        g_trans: Translation from Google.
        m_trans: Translation from MarianMT.

    Returns:
        str: Chosen translation.
    """
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()

    top = tk.Toplevel(root)
    top.title("Choose translation")
    top.attributes("-topmost", True)

    width = 320
    top.geometry(f"{width}x200+{top.winfo_screenwidth()-width-10}+50")

    tk.Label(top, text=source, wraplength=width - 20, justify="left").pack(
        padx=10, pady=5, anchor="w"
    )

    result = {"val": g_trans}

    def _set(text: str) -> None:
        result["val"] = text
        top.destroy()
        root.destroy()

    tk.Button(
        top,
        text=g_trans,
        wraplength=width - 20,
        justify="left",
        command=lambda: _set(g_trans),
    ).pack(fill="both", padx=10, pady=5)
    tk.Button(
        top,
        text=m_trans,
        wraplength=width - 20,
        justify="left",
        command=lambda: _set(m_trans),
    ).pack(fill="both", padx=10, pady=5)

    top.mainloop()
    return result["val"]


def set_engine(engine: str) -> None:
    """Select translation engine.

    Args:
        engine: Desired engine name. Supported values are ``google``, ``deepl``,
            ``marian``, ``libre``, ``best`` and ``choose``. ``best`` runs Google
            and MarianMT and picks the longest result for each sentence.
            ``choose`` shows both results in a popup so the user can pick one.
    """

    global TRANSLATOR, _model, _tokenizer
    engine = engine.lower()
    if engine in {"marian", "best", "choose"} and MarianMTModel and MarianTokenizer:
        if _model is None or _tokenizer is None:
            try:
                _tokenizer = MarianTokenizer.from_pretrained(
                    "Helsinki-NLP/opus-mt-ja-en"
                )
                _model = MarianMTModel.from_pretrained("Helsinki-NLP/opus-mt-ja-en")
            except Exception as e:  # pragma: no cover
                logger.error("Failed to load MarianMT model: %s", e)
                if engine == "marian":
                    engine = "google"
    elif engine not in {"google", "deepl", "marian", "libre", "best", "choose"}:
        logger.warning("Unknown translator '%s', falling back to Google", engine)
        engine = "google"
    TRANSLATOR = engine


def _lookup_cache(text: str) -> str | None:
    """Return cached translation if available."""
    with _DB_LOCK:
        cur = _conn.execute("SELECT translated FROM cache WHERE source=?", (text,))
        row = cur.fetchone()

    return row[0] if row else None


def _store_cache(text: str, translation: str) -> None:
    """Persist a translation to the cache.

    Args:
        text: Source string.
        translation: Translated result.
    """
    try:
        with _DB_LOCK:
            _conn.execute(
                "INSERT OR REPLACE INTO cache (source, translated) VALUES (?, ?)",
                (text, translation),
            )
            _conn.commit()

    except Exception as e:
        logger.error("Cache store failed: %s", e)


def _log_history(source: str, translated: str, engine: str) -> None:
    """Append a translation pair with engine info to ``historico_traducoes.csv``.

    Args:
        source: Original Japanese text.
        translated: English translation.
        engine: Name of the translation engine used.
    """
    try:
        write_header = not HISTORY_CSV.exists()
        with open(HISTORY_CSV, "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["Japanese", "English", "Engine"])
            writer.writerow([source, translated, engine])
    except Exception as e:
        logger.error("History log failed: %s", e)


def _translate_engine(engine: str, texts: list[str]) -> list[str]:
    """Translate ``texts`` using the specified engine."""

    try:
        if engine == "google":
            translator = GoogleTranslator(source="ja", target="en")
            return translator.translate_batch(texts)
        if engine == "deepl":
            translator = DeeplTranslator(source="JA", target="EN")
            return translator.translate_batch(texts)
        if engine == "libre":
            translator = LibreTranslator(source="ja", target="en")
            return translator.translate_batch(texts)
        if engine == "marian" and _model and _tokenizer:
            inputs = _tokenizer(texts, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = _model.generate(**inputs)
            return _tokenizer.batch_decode(outputs, skip_special_tokens=True)
    except Exception as e:  # pragma: no cover - network or model failures
        logger.error("%s translate error: %s", engine, e)
    return ["" for _ in texts]


def translate_batch(texts: list[str]) -> list[str]:
    """Translate a list of Japanese strings to English with caching.

    Args:
        texts: List of Japanese strings.

    Returns:
        list[str]: Translated strings in the same order.
    """

    results: list[str] = ["" for _ in texts]
    to_translate: list[str] = []
    indices: list[int] = []

    for i, t in enumerate(texts):
        cached = _lookup_cache(t)
        if cached is not None:
            results[i] = cached
            _log_history(t, cached, TRANSLATOR)
        else:
            to_translate.append(t)
            indices.append(i)

    if to_translate:
        if TRANSLATOR in {"best", "choose"}:
            google_trans = _translate_engine("google", to_translate)
            marian_trans = _translate_engine("marian", to_translate)
            translated = []
            for src, g, m in zip(to_translate, google_trans, marian_trans):
                if TRANSLATOR == "best":
                    translated.append(m if len(m) >= len(g) and m else g)
                else:
                    if g == m or not m:
                        translated.append(g)
                    else:
                        translated.append(_prompt_choice(src, g, m))
        else:
            engines = [TRANSLATOR] + [
                e for e in ["google", "deepl", "marian", "libre"] if e != TRANSLATOR
            ]
            translated = ["" for _ in to_translate]
            used_engine = TRANSLATOR
            for eng in engines:
                translated = _translate_engine(eng, to_translate)
                if any(translated):
                    logger.info("Translated with %s", eng)
                    used_engine = eng
                    break

        for idx, src, trans in zip(indices, to_translate, translated):
            results[idx] = trans
            _store_cache(src, trans)
            log_engine = used_engine if "used_engine" in locals() else TRANSLATOR
            _log_history(src, trans, log_engine)

    return results
