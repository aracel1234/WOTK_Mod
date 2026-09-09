# Changelog

## 2.0.0

- Rebuilt the project as a Python package with a unified Tkinter Control Center.
- Added cooperative Stop handling and PyAutoGUI FAILSAFE support.
- Added thread-safe GUI event delivery instead of updating Tk widgets from worker threads.
- Centralized coordinate clicking, field clearing, delays, configuration validation, and logging.
- Added Auto Login, Individual, Mysteriland, Supremacy, Auto War, and Sandboxie multi-instance
  engines.
- Implemented client-relative multi-instance coordinate transformation and serialized physical
  input to prevent threads from fighting over one global mouse/keyboard.
- Added OCR-based Auto War Watch/March/Assault flow, including optional `No hero can march`,
  Defender, and Assault checks.
- Fixed the March route off-by-one behavior by tracking the current route index explicitly.
- Reworked Supremacy phase-2 hero selection into a bounded least-used rotation.
- Removed user-specific absolute paths and bundled Tesseract binaries from the repository design.
- Added sanitized examples, tests, CI, setup verification, build scripts, migration guidance, and
  security documentation.
