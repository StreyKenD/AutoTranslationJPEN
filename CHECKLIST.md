# Project Checklist

## Completed
- Replaced Tesseract with Manga-OCR for higher accuracy
- Added hotkey configuration via `config.json`
- Implemented translation caching using SQLite
- Logged translations to `historico_traducoes.csv`
- Batched translations with `GoogleTranslator.translate_batch`
- Optional debug image capture via `DEBUG_IMAGES` flag
- Introduced pre-commit and flake8 configuration
- Created `AGENTS.md` with contribution guidelines
- Added optional offline translation using MarianMT
- Saved bubble screenshots with translations
- Enabled real-time video processing mode
- Measure OCR confidence to flag low-quality text
- Detect overflow and draw translations nearby when needed
- Hover/click tooltips show original text
- Alignment smoothing for moving bubbles

## To Do
- Evaluate and fine-tune YOLO bubble detector
- Build a smoother overlay with adjustable fonts and shadows
- Provide searchable UI for translation history ✅
- Assemble automated test suite and profiling tools
- Document quickstart and usage guides
- Gather and annotate pages for YOLO training
- Benchmark DeepL and other translators
- Add toggle for in-place versus nearby overlays ✅
- Profile pipeline latency and test batching
