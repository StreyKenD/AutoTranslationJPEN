# Manga Translation Overlay (Japanese → English)

This file guides OpenAI Codex to assist with refactoring, feature improvements, and testing in this project.

## Project Structure
- `capture.py` – screen capture logic
- `ocr.py` – runs Manga‑OCR on bubble regions
- `translate.py` – translates Japanese text (via API or local model)
- `ui_overlay.py` – draws translated subtitles or bubble overlays
- `main.py` – CLI / application orchestration
- `history/` – logs, search, CSV/SRT export utilities

## Coding Style & Conventions
- Use **Python 3.10+**, with type annotations (PEP‑484)
- Format code with `black` and check with `flake8`
- Docstrings should follow Google style
- Meaningful names: e.g. `detect_bubbles()`, `render_subtitle()`, `ocr_confidence`
- Avoid code duplication; reuse helpers (e.g. cropping, caching)

## Testing & Quality Checks
- Tests live in `tests/` directory; file names end in `_test.py`
- Use `pytest`; Codex should run `pytest --maxfail=1 --disable-warnings -q`
- Use a caching test dataset with sample bubble screenshots & expected OCR output
- Simulate translation buttons / overlay rendering via headless tests in pytest

## Tasks & PR Guidelines
- Each PR should target one core area (bubble detection, overlay, performance)
- PR title format: **[Area] Concise description** (e.g. `[OCR] Add confidence threshold fallback`)
- Summary must include:
  - What was changed
  - How you validated it (tests, manual verification)
  - Performance or UX improvements
- If touching UI, include a screenshot or log sample

## Development Flow for Codex
- Always run full test suite and `black`, `flake8` before completing a task
- For UI / overlay changes, Codex should open a demo overlay image for review
- For performance optimizations, include before/after timing metrics in comments

## Translation Task Notes
- Use caching—if `translate_cached(text)` exists, Codex should call it to avoid duplicate API calls
- Avoid real network calls in tests; mock translation engine with stub outputs

## Feature Guidance
- Bubble detection should support overlapping, irregular shapes; consider YOLOv8 or real‑time segmentation
- OCR must read vertical Japanese; prefer Manga‑OCR
- Overlay renderer should support in-bubble and subtitle modes; respect style guidelines
