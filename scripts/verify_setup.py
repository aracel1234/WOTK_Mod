from __future__ import annotations

import importlib.util
import os
import platform
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from wotk.automation.ocr import resolve_tesseract_cmd  # noqa: E402


def status(ok: bool, label: str, detail: str = "") -> None:
    mark = "OK" if ok else "WARN"
    suffix = f" - {detail}" if detail else ""
    print(f"[{mark:4}] {label}{suffix}")


def main() -> int:
    print("WOTK Mod 2.0 setup verification\n")
    is_windows = platform.system() == "Windows"
    status(is_windows, "Operating system", platform.platform())
    status(sys.version_info >= (3, 11), "Python", sys.version.split()[0])

    modules = {
        "pyautogui": "desktop automation",
        "pygetwindow": "window discovery",
        "PIL": "screenshots/image handling",
        "numpy": "OCR preprocessing",
        "cv2": "OCR preprocessing",
        "pytesseract": "OCR bridge",
        "platformdirs": "user config paths",
        "pynput": "global emergency hotkey",
    }
    for module, purpose in modules.items():
        status(importlib.util.find_spec(module) is not None, f"Python module {module}", purpose)

    tess = resolve_tesseract_cmd()
    status(bool(tess), "Tesseract OCR", tess or "not found; required for Auto War OCR")

    sandbox = Path(r"C:\Program Files\Sandboxie-Plus\Start.exe")
    status(sandbox.exists(), "Sandboxie-Plus default path", str(sandbox))

    git = shutil.which("git")
    status(bool(git), "Git", git or "not found")

    if os.environ.get("WOTK_TESSERACT_CMD"):
        print(f"\nWOTK_TESSERACT_CMD={os.environ['WOTK_TESSERACT_CMD']}")

    print("\nWarnings are expected on non-Windows development/CI machines.")
    print("All shipped coordinates are templates; local calibration is still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
