from __future__ import annotations

import time
from dataclasses import dataclass

from wotk.models import Point


@dataclass(frozen=True, slots=True)
class WindowRect:
    left: int
    top: int
    width: int
    height: int

    def absolute(self, relative: Point, offset: Point | None = None) -> Point:
        offset = offset or Point(0, 0)
        return Point(self.left + relative.x + offset.x, self.top + relative.y + offset.y)

    def contains(self, point: Point) -> bool:
        return (
            self.left <= point.x < self.left + self.width
            and self.top <= point.y < self.top + self.height
        )


class WindowManager:
    def find(self, title_pattern: str, index: int = 0):
        import pygetwindow as gw

        windows = [w for w in gw.getAllWindows() if title_pattern.lower() in (w.title or "").lower()]
        windows = [w for w in windows if getattr(w, "width", 0) > 0 and getattr(w, "height", 0) > 0]
        if not windows:
            return None
        if index < 0 or index >= len(windows):
            return None
        return windows[index]

    def wait_for(self, title_pattern: str, index: int = 0, timeout: float = 60.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            window = self.find(title_pattern, index=index)
            if window is not None:
                return window
            time.sleep(0.5)
        return None

    def focus(self, window, maximize: bool = False) -> bool:
        try:
            if getattr(window, "isMinimized", False):
                window.restore()
            if maximize and not getattr(window, "isMaximized", False):
                window.maximize()
            window.activate()
            return True
        except Exception:
            return False

    def client_rect(self, window) -> WindowRect:
        hwnd = getattr(window, "_hWnd", None)
        if hwnd:
            try:
                import win32gui

                left_top = win32gui.ClientToScreen(hwnd, (0, 0))
                right_bottom = win32gui.ClientToScreen(hwnd, win32gui.GetClientRect(hwnd)[2:])
                return WindowRect(
                    left=int(left_top[0]),
                    top=int(left_top[1]),
                    width=int(right_bottom[0] - left_top[0]),
                    height=int(right_bottom[1] - left_top[1]),
                )
            except Exception:
                pass
        return WindowRect(
            left=int(window.left),
            top=int(window.top),
            width=int(window.width),
            height=int(window.height),
        )
