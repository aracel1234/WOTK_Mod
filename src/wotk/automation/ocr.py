from __future__ import annotations

import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from wotk.automation.runtime import AutomationContext
from wotk.models import Region


@dataclass(frozen=True, slots=True)
class OcrResult:
    text: str
    normalized: str

    def contains(self, target: str) -> bool:
        return normalize_text(target) in self.normalized


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def resolve_tesseract_cmd(explicit: str | None = None) -> str | None:
    candidates = [
        explicit,
        os.environ.get("WOTK_TESSERACT_CMD"),
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


class OcrService:
    def __init__(
        self,
        context: AutomationContext,
        tesseract_cmd: str | None = None,
        preprocess: bool = True,
    ):
        self.context = context
        self.tesseract_cmd = resolve_tesseract_cmd(tesseract_cmd)
        self.preprocess = preprocess

    def verify_available(self) -> None:
        if not self.tesseract_cmd:
            raise RuntimeError(
                "Tesseract OCR was not found. Install Tesseract or set WOTK_TESSERACT_CMD."
            )

    def read(self, region: Region) -> OcrResult:
        self.verify_available()
        import numpy as np
        import pytesseract

        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        image = self.context.backend.screenshot((region.x, region.y, region.width, region.height))
        if self.preprocess:
            import cv2

            gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            _, processed = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            text = pytesseract.image_to_string(processed, lang="eng", config="--psm 6")
        else:
            text = pytesseract.image_to_string(image, lang="eng", config="--psm 6")
        result = OcrResult(text=text.strip(), normalized=normalize_text(text))
        self.context.log(f"OCR: {result.text!r}")
        return result

    def contains(self, region: Region, target: str) -> bool:
        return self.read(region).contains(target)

    def contains_any(self, region: Region, targets: Iterable[str]) -> tuple[bool, str | None, OcrResult]:
        result = self.read(region)
        for target in targets:
            if result.contains(target):
                return True, target, result
        return False, None, result
