## 2. BRAINSTORMING.md — *Project Brainstorming (Refined)*

```markdown
# Project Brainstorming

## Vision
- Deliver a **local, offline "Google Lens"** for manga translation.
- Ensure all processing is done **entirely on the user's PC** (no cloud).

## Core Components
- **Capture:** Grab screen regions or load images for analysis.
- **Bubble Detection:** Use a YOLO model to locate manga speech bubbles.
- **OCR:** Extract Japanese text with Manga-OCR.
- **Translation:** Integrate offline models (e.g., MarianMT, Argos) or optional online APIs.
- **Overlay:** Draw translated text directly onto the original manga image.

## Short-Term Goals
- Improve pipeline speed and stability.
- Add a simple, configurable UI overlay (adjustable fonts, drop-shadows).
- Implement translation caching to skip repeated work.

## Long-Term Ideas
- Fine-tune models for manga-specific bubble shapes and fonts.
- Enable a low-FPS real-time video mode.
- Allow users to correct translations and build a feedback-improved model.

## Current Pain Points
- **Bubble Detection:** Fails on small, irregular, or overlapping shapes.
- **OCR:** Slow on complex fonts; struggles with decorative text.
- **Translation:** Quality and phrasing vary, especially with online APIs due to latency.
- **Overlay:** Sometimes flickers or is misaligned.
- **Hotkeys:** Currently hardcoded, not user-configurable.
- **No History:** Past translations are not searchable or logged.

## Potential Improvements
- Train YOLO on diverse manga samples (small, irregular, overlapping bubbles).
- Batch OCR and leverage GPU acceleration.
- Add/enable offline translators (Argos, MarianMT) to remove API limits.
- Allow users to configure hotkeys, fonts, and overlay colors in a config file.
- Cache and log all translations (e.g., SQLite, CSV).
- Explore using Qt for smoother overlay rendering and animation.