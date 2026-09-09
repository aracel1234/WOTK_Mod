# Architecture

## Layers

```text
Tkinter GUI
   │
   ├── UiBus / GlobalTaskController
   │
Feature engines
(Login / Individual / Mysteriland / Supremacy / War / Multi-instance)
   │
Automation primitives
(PyAutoGUI backend / StopToken / OCR / WindowManager / Sandboxie / hotkeys)
   │
Windows desktop + game/browser
```

Feature engines do not directly manipulate Tk widgets. This keeps business flow testable with the
`RecordingBackend` and avoids Tkinter thread violations.

## Cooperative cancellation

Every feature receives one `StopToken`. `AutomationContext.sleep()` uses `Event.wait()` rather than
`time.sleep()`, so Stop can interrupt waits. Every click/hotkey checks the token before input.

## Physical input lock

Desktop mouse and keyboard input are global. For multi-instance mode, every worker receives the same
`threading.RLock`. A relative click is executed atomically as:

1. acquire shared input lock;
2. focus expected window;
3. get current client rect;
4. convert relative point to absolute point;
5. bounds-check transformed point;
6. issue one click;
7. release lock;
8. wait outside the lock.

This is intentionally different from naive per-instance PyAutoGUI threads.

## Client-relative coordinates

For Sandboxie instances, coordinates are stored relative to game client area. `WindowManager` uses
Win32 `ClientToScreen` when available and falls back to the outer window geometry otherwise.

`absolute = client_origin + relative + offset_correction`

The optional offset exists only for fine adjustment; a large offset is a sign that calibration or
DPI scaling is wrong.

## OCR

`OcrService` captures a configured screen rectangle and, by default:

1. converts RGB → grayscale;
2. applies a small Gaussian blur;
3. applies Otsu binary thresholding;
4. runs Tesseract with English language and `--psm 6`;
5. lowercases and collapses whitespace for matching.

The service does not silently swallow Tesseract errors. Auto War can decide which OCR failures are
recoverable.

## Configuration persistence

Mutable profiles live under the OS user configuration directory through `platformdirs`. `ConfigStore`
writes JSON atomically using a temporary file + `os.replace`, reducing corruption risk if the
process stops during a save.

Auto Login account data is intentionally separate from the persisted profile.
