# Migration & Improvement Spec: Tesseract → Manga-OCR

.venv\Scripts\activate

python app.py

These aren’t critical now but great upgrades later:

🤖 Fine-tune a YOLO model just for manga speech bubbles

🧠 Fine-tune Manga-OCR with manga fonts

💬 Add subtitle-mode: show all translations in corner

🔄 Auto-translate when page changes using hash/frame diff

✅ D. UI / OVERLAY IMPROVEMENTS
You're very close to Google Lens-level polish. Try these:

1. Add dynamic font resizing
Make the font size adapt to bubble height.

Auto-wrap if translated_text.length * font_size > width.

2. Word-level translation preview (optional)
Show OCR text briefly before translating.

Might help if you want users to optionally skip mistranslations.

3. Outline / drop shadow text for readability
In Pillow:

python
Copiar
Editar
draw.text((x+1, y+1), text, font=font, fill="black")  # shadow
draw.text((x, y), text, font=font, fill="white")      # main

✅ E. PERFORMANCE BOOST
1. Avoid resizing twice
Right now you're resizing before YOLO + OCR.

✅ Use original for YOLO

✅ Resize only for OCR after cropping bubbles

2. Multithread OCR and Translation
OCR and translation can run in parallel per bubble:

Use concurrent.futures.ThreadPoolExecutor

Run extract_text_from_bubbles() and translate_batch() in parallel

4. Performance & Responsiveness
Parallelize OCR & Translation with concurrent.futures.ThreadPoolExecutor so multiple bubbles are processed truly in parallel (your GPU can batch OCR, and translation calls can fire off concurrently).

Cache translations (in a dict keyed by original Japanese text) so repeated bubbles (or repeated presses) don’t re‑translate the same string.

- Use ``GoogleTranslator.translate_batch`` to translate many bubbles in one request.
- Set environment variable ``DEBUG_IMAGES=1`` to save captured/processed images; leave it unset for faster runs.

5. UI Polish
Dynamic font sizing: Measure each bubble’s width/height and pick a font size that maximizes legibility without overflow.

Drop‑shadows or outlines behind text to improve contrast on noisy backgrounds.

Smooth fade‑in animations for the overlay so it doesn’t “pop” abruptly.

6. Translation Engine Options
Swap out Google Translate for an offline engine (e.g. argos-translate or a local LibreTranslate server).

Or try the DeepL unofficial API for higher fidelity, then fall back to Google/LibreTranslate if it’s down.

7. Live‑Video Mode
Instead of “one shot per F8 press,” hook into a continuous capture loop (e.g. tkinter.after or a background thread) to process frames at, say, 2–3 FPS.

Keep your YOLO model loaded once, and reuse it on each frame for near real‑time “manga‑lens” translation.

8. Bubble‑Detector Improvements
Fine‑tune your YOLO model on your own manga pages for better recall/precision.

Or experiment with Transformer‑based detectors (e.g. DETR) if you need higher accuracy on weird layouts.

## 🎯 Goals
1. Replace all Tesseract calls with Manga-OCR.
2. Maintain existing input/output interfaces (e.g. image paths, screenshots).
3. Manga-OCR automatically handles vertical Japanese text.
4. Improve performance: batch processing, GPU support, multithreading as needed.  
5. Plug in translation step after OCR.  
6. Structure code into clear modules:  
   - capture.py    → screenshot / image loading  
   - ocr.py        → text detection & recognition (Manga-OCR)
   - translate.py  → calls translator API or local model  
   - ui_overlay.py → draws translated text onto images / GUI  
   - main.py       → ties it all together, CLI or hotkey trigger  

## 📦 Dependencies
```bash
pip install manga-ocr
pip install deep-translator        # or transformers[torch] for MarianMT
pip install mss keyboard pillow    # screenshot + input + image handling
pip install opencv-python          # overlay drawing
🧩 Module: ocr.py
Initialize:

python
Copiar
Editar
from manga_ocr import MangaOcr
ocr = MangaOcr()
Function: def extract_text(image: np.ndarray) -> List[Tuple[str, Tuple[int,int,int,int]]]:

Input: BGR/GRAY image array

Call ocr.ocr(image, cls=True)

Flatten results to (text, (x1,y1,x2,y2)) for each line.

Return list of (text, bounding box).

⚙️ Module: translate.py
Support: GoogleTranslator (deep-translator) or local MarianMT

Function: def translate_batch(texts: List[str]) -> List[str]:

Detect source language if needed

Translate in bulk to target (e.g. English)

Handle API errors / rate limits gracefully.

🖼 Module: ui_overlay.py
Function: def draw_translations(image: np.ndarray, data: List[Tuple[str, str, bbox]]):

For each (orig, trans, bbox), draw translucent box + text above/beside

Use OpenCV’s putText, rectangle, and optional font scaling.

Consider dynamic font size based on box height.

📸 Module: capture.py
Function: def grab_region(region: Tuple[int, int, int, int] = None) -> np.ndarray:

Use mss or pyautogui.screenshot()

Convert to OpenCV format

Accept optional region or full screen.

🚀 Module: main.py
Parse CLI args (e.g. --gpu, --lang ja, --region 0,0,800,600)

Optionally run in hotkey loop (keyboard.add_hotkey('ctrl+shift+L', process_screen))

Workflow:

img = capture.grab_region()

ocr_data = ocr.extract_text(img)

orig_texts, boxes = unzip(ocr_data)

translations = translate.translate_batch(orig_texts)

result_img = ui_overlay.draw_translations(img, zip(orig_texts, translations, boxes))

cv2.imshow('Lens', result_img) or save to disk

🔧 Performance & Reliability
Batch OCR: if processing many small crops, send them to Manga-OCR in one call.

Error Handling: wrap OCR & translation calls in try/except, log failures.

Logging: use logging module, adjustable verbosity (--debug).

## Configuration
Edit `config.json` to customize hotkeys and other settings. Example:

```json
{
  "hotkeys": {
    "ocr": "f8",
    "toggle_bubbles": "f9",
    "quit": "esc"
  },
  "bubble_padding": 8,
  "replace_mode": false
}
```

Translations are cached in ``translations.db`` to avoid duplicate API calls. A
CSV file ``historico_traducoes.csv`` logs each translation for later reference.

## Development Setup
This project uses *pre-commit* with **flake8** for linting. After cloning, run:

```bash
pip install -r requirements.txt
pre-commit install
```

Before committing, check your changes:

```bash
pre-commit run --files $(git diff --name-only)
```
