# Project Brainstorming

## Vision
- Provide a local "Google Lens" for manga translation
- Run entirely on the user's PC without cloud services

## Core Components
- **Capture**: grab screen regions or load images
- **Bubble Detection**: use YOLO to isolate speech bubbles
- **OCR**: use Manga-OCR for Japanese text
- **Translation**: integrate offline translation models or libraries
- **Overlay**: draw translated text on the original image

## Short-Term Goals
- Polish the existing pipeline for speed and stability
- Add a simple UI overlay with adjustable fonts and shadows
- Cache translations to avoid repeat requests

## Long-Term Ideas
- Train custom models for manga fonts and bubble shapes
- Provide real-time video mode at low FPS
- Allow user corrections to improve translations over time

## Pain Points
- Detection struggles with tiny or irregular bubbles.
  Existing YOLO training mostly covers standard ovals, so overlaps
  and odd shapes often get missed or cut off.
- OCR can be slow and fails on highly stylized fonts.
  Decorative letterforms reduce accuracy and the GPU remains idle,
  making recognition slower than necessary.
- Translation quality varies and currently depends on online APIs.
  Network latency delays results and inconsistent phrasing appears
  between providers.
- Overlay text sometimes flickers or misaligns.
  Bounding boxes shift slightly frame to frame, causing jitter and
  occasional overflow.
- Hotkeys are hard-coded and not customizable.
  Users cannot remap shortcuts, which leads to conflicts with other
  applications.
- No persistent history of past translations.
  Without logging, duplicate bubbles trigger repeated work and there
  is no searchable reference.

## Potential Improvements
- Fine-tune the bubble detector with more manga samples.
  Create a diverse dataset with small, irregular, and overlapping
  bubbles to boost recall.
- Batch OCR calls and use GPU acceleration where available.
  Send multiple crops to Manga-OCR at once to utilize the GPU
  and cut response time.
- Integrate an offline translator such as Argos or MarianMT.
  Running locally avoids API limits and keeps translations
  available offline.
- Add a config file for hotkeys and font settings.
  Provide a YAML or JSON file so users can tweak shortcuts
  and overlay colors.
- Cache results and build a searchable translation log.
  Store recognized text in a SQLite database for quick lookup
  and to avoid repeated work.
- Explore a Qt-based overlay for smoother updates.
  Qt's graphics pipeline could reduce flicker and support
  animations compared to raw OpenCV windows.

