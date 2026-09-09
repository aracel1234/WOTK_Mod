from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from wotk.models import Point


class AutomationBackend(Protocol):
    def click(self, x: int, y: int) -> None: ...
    def write(self, text: str, interval: float = 0.02) -> None: ...
    def hotkey(self, *keys: str) -> None: ...
    def press(self, key: str) -> None: ...
    def scroll(self, amount: int) -> None: ...
    def position(self) -> Point: ...
    def screenshot(self, region: tuple[int, int, int, int] | None = None) -> Any: ...
    def size(self) -> Point: ...


class PyAutoGuiBackend:
    """Thin lazy wrapper around PyAutoGUI so headless tests can import the package."""

    def __init__(self, pause: float = 0.1, failsafe: bool = True):
        import pyautogui

        pyautogui.FAILSAFE = failsafe
        pyautogui.PAUSE = pause
        self._py = pyautogui

    def click(self, x: int, y: int) -> None:
        self._py.click(x, y)

    def write(self, text: str, interval: float = 0.02) -> None:
        self._py.write(text, interval=interval)

    def hotkey(self, *keys: str) -> None:
        self._py.hotkey(*keys)

    def press(self, key: str) -> None:
        self._py.press(key)

    def scroll(self, amount: int) -> None:
        self._py.scroll(amount)

    def position(self) -> Point:
        pos = self._py.position()
        return Point(int(pos.x), int(pos.y))

    def screenshot(self, region: tuple[int, int, int, int] | None = None):
        return self._py.screenshot(region=region)

    def size(self) -> Point:
        size = self._py.size()
        return Point(int(size.width), int(size.height))


@dataclass(slots=True)
class RecordingBackend:
    """Deterministic backend used by tests and dry-run validation."""

    operations: list[tuple[Any, ...]] = field(default_factory=list)
    screen_size: Point = field(default_factory=lambda: Point(1920, 1080))
    pointer: Point = field(default_factory=lambda: Point(0, 0))

    def click(self, x: int, y: int) -> None:
        self.operations.append(("click", x, y))
        self.pointer = Point(x, y)

    def write(self, text: str, interval: float = 0.02) -> None:
        self.operations.append(("write", text, interval))

    def hotkey(self, *keys: str) -> None:
        self.operations.append(("hotkey", *keys))

    def press(self, key: str) -> None:
        self.operations.append(("press", key))

    def scroll(self, amount: int) -> None:
        self.operations.append(("scroll", amount))

    def position(self) -> Point:
        return self.pointer

    def screenshot(self, region: tuple[int, int, int, int] | None = None):
        from PIL import Image

        if region:
            _, _, width, height = region
        else:
            width, height = self.screen_size.x, self.screen_size.y
        self.operations.append(("screenshot", region))
        return Image.new("RGB", (max(width, 1), max(height, 1)), "white")

    def size(self) -> Point:
        return self.screen_size
