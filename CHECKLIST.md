✅ Completed Tasks
Switched OCR Engine: Replaced Tesseract with Manga-OCR for better vertical text and furigana recognition.

Hotkey Configuration: Hotkeys and UI actions can now be edited in config.json instead of being hardcoded.

Translation Caching: All translations are cached in SQLite to minimize repeated lookups and speed up UX.

Translation Logging: Every translation and its metadata are logged to historico_traducoes.csv (text, time, bubble screenshot).

Batch Translation: Uses GoogleTranslator.translate_batch for faster and more reliable multi-bubble translation.

Debug Image Capture: Set the DEBUG_IMAGES flag to automatically save screenshots of processing steps for debugging.

Pre-commit & Linting: Enforced code quality with pre-commit and flake8 checks.

Contribution Docs: Added AGENTS.md for team/codebase standards.

Offline Translation (MarianMT): Users can translate manga offline with MarianMT as a fallback or main engine.

Bubble Image Archiving: Cropped speech bubbles with translation context are saved for later review.

Live Video Mode: Real-time processing of video or live screen regions, with overlay display.

OCR Confidence Scoring: Confidence scores from OCR are now recorded and can flag low-quality text.

Dynamic Overlay: When translations overflow or bubbles are too small, the system shows translation "nearby" or overlays with adjusted layout.

Interactive Tooltip: Hover or click a bubble to see the original Japanese and the translation.

Overlay Alignment Smoothing: Reduces flicker and misalignment as bubbles move.

🚧 In Progress / Planned
1. Bubble Detection (YOLO & Alternatives)
Evaluate YOLO Model:

Test bubble detection on a wider variety of manga styles and edge cases (e.g., multiple small bubbles, overlapping, vertical layouts).

Record false positives/negatives and propose model retraining targets.

Data Augmentation:

Gather and label more manga pages with complex speech bubble layouts.

Try synthetic data generation for rare bubble shapes.

Model Fine-tuning:

Fine-tune YOLO or explore transformer-based detectors (like DETR) for improved accuracy on non-standard panels.

Set up automated training scripts.

2. OCR Engine
Multi-bubble Evaluation:

Benchmark Manga-OCR’s output when bubbles are densely packed or have stylized fonts.

Record processing speed, especially with GPU acceleration. **Implemented**

Text Orientation Detection:

Add logic to handle horizontal, vertical, and mixed text bubbles reliably. **Implemented**

Fallback Mechanisms:

Allow switching between OCR engines if Manga-OCR fails (e.g., for highly decorative fonts).

3. Translation Engine
Engine Benchmarking:

Compare DeepL, Google Translate, MarianMT, LibreTranslate, and hybrid approaches for speed, cost, and naturalness. **Implemented**

Failover and Retry:

Build robust fallback: try another engine/API if one fails or rate-limits. **Implemented**

Contextual Awareness:

Experiment with LLM-based context window for better multi-bubble translation coherence.

Multi-language Support:

Allow users to pick source/target languages for non-Japanese manga.

4. Live Capture & Overlay
Flexible Region Selection:

Let users select the screen/window region for live translation, not just fixed coordinates. **Implemented**

Animated Overlay Rendering:

Add smooth transitions/fades, animated positioning for overlays.

Overlay Customization:

Provide options for font, size, color, outline, and background style per user.

User can toggle outline, drop shadow, and bubble mask.

Performance Controls:

Adjustable FPS for live processing (e.g., 1-10 FPS).

Frame-skip/batching for low-power devices.

5. Logging, History & Export
Translation History UI:

Search, filter, and browse past translations with image previews.

Link to manga panel frame or region if available.

Advanced Export:

Export translation logs as JSON, CSV, or subtitle (SRT/ASS) formats.

Option to anonymize sensitive content in export.

Persistent Analytics:

Track most frequent words, bubble size stats, and per-chapter translation counts.

6. UX Tuning & Edge Cases
Overflow Handling:

Detect and handle cases where the translation cannot fit: offer scroll, wrap, or pop-out overlay.

Bubble Matching Robustness:

Maintain correct overlay position even if bubbles move slightly (across frames).

Accessibility:

High-contrast and colorblind-friendly themes.

Keyboard navigation for overlay actions.

7. Testing, Validation & Reliability
Automated Test Suite:

Unit and integration tests for detection, OCR, translation, and overlay.

Regression Benchmarks:

Maintain a test set of challenging manga pages and track accuracy over time.

Crash/Error Reporting:

Log any pipeline errors; alert user in UI and offer suggestions for common fixes.

8. Performance & Scalability
Pipeline Profiling:

End-to-end latency measurement for each step: capture → detect → OCR → translate → overlay.

Parallel Processing:

Use multi-threading/batching to speed up processing, especially for many bubbles.

Resource Management:

Warn if CPU/GPU/memory usage is too high or if system lags.

9. Documentation & User Guidance
Comprehensive Docs:

Write a detailed quickstart guide, full CLI/API usage, FAQ, and troubleshooting.

Video tutorials and annotated screenshots.

Advanced User Guides:

Tips for training custom detectors or translators.

Contribution/how-to-hack guide for developers.

10. Future Features & Experiments
Multimodal LLMs:

Integrate vision-language models for context-aware translation and dialogue.

Real-time Subtitle/Overlay Modes:

Subtitle stream in a fixed corner, optionally color-coded by speaker/bubble.

Community Feedback Loop:

User flag/mistranslation reporting.

Community-submitted manga translation models or dictionaries.

Plugin/Extension System:

Let users add new translators, OCRs, or UI overlays as plugins.

🛠️ Suggested Fixes & Polish
Reduce Overlay Flicker:

Debounce overlay redraws when manga bubbles are nearly stationary.

Optimize Disk Usage:

Purge old debug images/logs after N days or let users set a limit.

Better Hotkey Feedback:

On-screen notification when a hotkey is triggered. **Implemented**

UI Polish:

Smoother, more modern panel styles (rounded corners, blur, etc.).

Codebase Cleanliness:

Refactor for modularity, clearer error handling, and extensible configs.

Contribute new ideas or request features by editing this checklist. Every improvement makes manga translation faster, more robust, and more fun!