# Manga Translator Pipeline — Migration & Improvement Spec

A local tool for translating manga images with automatic bubble detection and overlay.

---

## Quickstart

1. Activate virtualenv:
    ```bash
    .venv\Scripts\activate
    ```

2. Start the application:
    ```bash
    python app.py
    ```

---

## Features

- Background frame grabber keeps video mode responsive and always processes the
  most recent frame.

---

## Recommended Upgrades

- 🤖 **Fine-tune YOLO** for manga speech bubbles.
- 🧠 **Fine-tune Manga-OCR** for manga fonts and layouts.
- 💬 **Subtitle Mode:** Show all translations in a corner overlay.
- 🔄 **Auto-translate:** Trigger on page change (hash/frame diff).
- 🎨 **UI Polish:**
  - Dynamic font sizing per bubble.
  - Outline/drop shadow text for readability.
  - Smooth fade-in overlay animations.
  - Optional subtitle mode with bubble navigation hotkeys.
- ⚡ **Performance:**
  - Avoid redundant resizing.
  - Use original image for YOLO, only resize for OCR.
  - Parallelize OCR and translation (use `ThreadPoolExecutor`).
  - Batch translation requests.
  - Cache translations by original text.
- 🔌 **Translation Engine:**
  - Support offline engines (e.g. Argos, MarianMT, LibreTranslate).
  - Optionally use DeepL via unofficial API.
- 🖼 **Overlay:**
  - Toggle between "replace in-place" and "show nearby".
  - Detect overflow and reposition translation if needed.
  - Tooltip to show both original and translated text.
- 🕒 **Live-Video Mode:**
  - Real-time processing loop, configurable FPS.

---

## Project Goals

1. Replace Tesseract with Manga-OCR for all text extraction.
2. Maintain same I/O: image files, screenshots.
3. Support vertical Japanese text.
4. Optimize speed via batch and parallel processing.
5. Pluggable translation step after OCR.
6. Clear, modular code organization:
    - `capture.py` – capture/load images
    - `ocr.py` – run Manga-OCR
    - `translate.py` – translation APIs/models
    - `ui_overlay.py` – draw overlays
    - `main.py` – CLI & workflow glue

---

## Configuration

All settings in `config.json`:

```json
{
  "hotkeys": {
    "ocr": "f8",
    "toggle_bubbles": "f9",
    "video": "f7",
    "next_bubble": "ctrl+right",
    "prev_bubble": "ctrl+left",
    "copy_translation": "ctrl+c",
    "toggle_subtitles": "ctrl+s",
    "quit": "esc",
    "history": "f6",
    "select_region": "f10"
  },
  "bubble_padding": 8,
  "replace_mode": false,
  "save_bubble_images": false,
  "overflow_to_nearby": false,
  "tooltip_overlay": true,
  "align_smoothing": 0.5,
  "bubble_shape": "ellipse",
  "use_bubble_mask": false,
  "overlay_font": "fonts/animeace2_reg.ttf",
  "overlay_text_color": "#ffffff",
  "overlay_outline_color": "#000000",
  "overlay_bg_alpha": 128,
  "translator": "google",
  "video_fps": 2,
  "ocr_confidence_threshold": 0.5,
  "subtitle_mode": false,
  "highlight_color": "#ffff00",
  "highlight_width": 2
}
```
Customize overlay style with these options:
- `overlay_font` – path to a TTF font for translated text
- `overlay_text_color` – hex color for text (e.g. `"#ffffff"`)
- `overlay_outline_color` – hex color for the text outline
- `overlay_bg_alpha` – background opacity from 0-255 (128 gives 50% transparency)
- `use_bubble_mask` – mask overlays to the detected bubble contour
- `subtitle_mode` – show translations in a corner subtitle box instead of on top of bubbles
- `highlight_color` – hex color for the bubble highlight outline
- `highlight_width` – outline thickness when highlighting a bubble

### Hotkeys

Additional shortcuts help you navigate bubbles:

- **Ctrl+Right** / **Ctrl+Left** – cycle through detected bubbles
- **Ctrl+C** – copy the current bubble's translation
- **Ctrl+S** – toggle subtitle mode on or off

Set "translator": "marian" for offline MarianMT.

"best" uses both Google and Marian, picks the best.

"choose" lets you manually pick each translation.

Dev & Linting
Install dependencies:

bash
Copiar
Editar
pip install -r requirements.txt
pre-commit install
Before commit:

bash
Copiar
Editar
pre-commit run --files $(git diff --name-only)
Advanced AI Translation Tips
Repository context: LLMs work better with full module context, not just isolated files.

RAG + Iterative Debugging: Use retrieval and error feedback for best translation.

Chunk by Functionality: Translate core modules first, utilities next, integrate last.

Automated Testing: Add unit tests to catch translation bugs.

Few-Shot Prompting: Show example translations for LLM prompt context.

UI/UX & Translation Best Practices
Use resource files (JSON/YAML) for UI strings.

Support glossaries and translation memory for consistency.

QA: Reviewer feedback, manual override, round-trip checks.

Segment-based editing, in-context previews, flexible layouts.

pgsql
Copiar
Editar

---

## 5. todolist.txt — *Development To-Do (Cleaned Up)*

```markdown
# Development To-Do List

## 1. Bubble Detection (YOLO)
- [ ] Evaluate current YOLO performance on various manga panel layouts.
- [ ] Gather and annotate test data (especially bubble-heavy, edge cases).
- [ ] Fine-tune YOLO for accuracy on overlapping/irregular bubbles.

## 2. OCR Engine
- [x] Integrate Manga-OCR (handles vertical text, furigana).
- [ ] Evaluate Manga-OCR on complex multi-bubble layouts.
- [x] Capture OCR confidence metrics for low-quality results.

-## 3. Translation Engine
- [x] Benchmark DeepL, Google, and others for speed/quality.
- [x] Build fallback translation paths.
- [ ] Experiment with context-aware LLM translation.

## 4. Live Capture & Overlay
- [ ] Set up live capture (OpenCV/FFmpeg).
- [ ] Overlay renderer: resize dynamically, match style, add outlines.
- [x] Toggle overlay style (in-place or nearby).
- [x] Flexible region selection for live capture.

## 5. Logging & History
- [x] Log each translation (original, translated, timestamp, screenshot).
- [x] Build UI for browsing and exporting history.
- [x] Search history entries and preview bubble crops.
- [x] Export logs as CSV, JSON, or SRT with engine and confidence.
- [x] Show usage stats (total bubbles, common words).

## 6. UX Tuning & Edge Cases
- [x] Detect overflow, auto-resize or switch overlay.
- [x] Hover/click fallback to show both original + translation.
- [x] Keep alignments steady as bubbles move or scale.

## 7. Testing & Validation
- [ ] Assemble test suite (diverse pages/fonts/styles).
- [ ] Measure detection/OCR/translation/overlay accuracy.
- [ ] Iterate and improve on weak points.

## 8. Performance Optimization
- [ ] Profile latency end-to-end.
- [ ] Implement batching or frame-skip if needed.

## 9. Documentation & Future Steps
- [ ] Write quickstart/usage guide.
- [ ] Plan multimodal LLM translation integration.
- [ ] Open-source, gather community feedback.