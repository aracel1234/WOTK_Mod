from __future__ import annotations

import threading
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass, field

from wotk.automation.backend import AutomationBackend
from wotk.models import Point


class StopRequested(RuntimeError):
    """Internal cooperative-cancellation signal."""


class StopToken:
    def __init__(self):
        self._event = threading.Event()

    def stop(self) -> None:
        self._event.set()

    @property
    def stopped(self) -> bool:
        return self._event.is_set()

    def check(self) -> None:
        if self.stopped:
            raise StopRequested("Automation stopped by user")

    def sleep(self, seconds: float) -> None:
        if seconds <= 0:
            self.check()
            return
        if self._event.wait(seconds):
            raise StopRequested("Automation stopped by user")


@dataclass(slots=True)
class AutomationContext:
    backend: AutomationBackend
    stop_token: StopToken
    log: Callable[[str], None] = print
    input_lock: threading.RLock = field(default_factory=threading.RLock)

    def check(self) -> None:
        self.stop_token.check()

    def sleep(self, seconds: float) -> None:
        self.stop_token.sleep(seconds)

    @contextmanager
    def exclusive_input(self):
        self.check()
        with self.input_lock:
            self.check()
            yield

    def click(self, point: Point, label: str = "", delay: float = 0.0) -> None:
        if not point.configured:
            raise ValueError(f"Coordinate {label or point!r} is not configured")
        with self.exclusive_input():
            self.backend.click(point.x, point.y)
        if label:
            self.log(f"Clicked {label} at ({point.x}, {point.y})")
        self.sleep(delay)

    def write(self, text: str, interval: float = 0.02, delay: float = 0.0) -> None:
        with self.exclusive_input():
            self.backend.write(text, interval=interval)
        self.sleep(delay)

    def press(self, key: str, delay: float = 0.0) -> None:
        with self.exclusive_input():
            self.backend.press(key)
        self.sleep(delay)

    def hotkey(self, *keys: str, delay: float = 0.0) -> None:
        with self.exclusive_input():
            self.backend.hotkey(*keys)
        self.sleep(delay)

    def scroll(self, amount: int, delay: float = 0.0) -> None:
        with self.exclusive_input():
            self.backend.scroll(amount)
        self.sleep(delay)

    def clear_field(self, point: Point, label: str = "field", delay: float = 0.2) -> None:
        """Reliably replaces legacy triple-click/delete behavior."""
        self.click(point, label=label, delay=0.1)
        self.hotkey("ctrl", "a", delay=0.05)
        self.press("backspace", delay=delay)

    def switch_tab(self, delay: float = 0.8) -> None:
        self.hotkey("ctrl", "tab", delay=delay)

    def click_screen_center(self, delay: float = 0.0) -> None:
        size = self.backend.size()
        self.click(Point(size.x // 2, size.y // 2), label="screen center", delay=delay)
