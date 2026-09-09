from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Callable


def _normalize_hotkey(value: str) -> str:
    parts = [part.strip().lower() for part in value.split("+") if part.strip()]
    aliases = {"control": "ctrl", "escape": "esc"}
    normalized: list[str] = []
    for part in parts:
        part = aliases.get(part, part)
        if part in {"ctrl", "shift", "alt", "esc", "tab", "enter", "space"} or part.startswith("f") and part[1:].isdigit():
            normalized.append(f"<{part}>")
        else:
            normalized.append(part)
    if not normalized:
        raise ValueError("Emergency hotkey cannot be empty")
    return "+".join(normalized)


class EmergencyHotkey(AbstractContextManager):
    """Best-effort global hotkey listener backed by pynput."""

    def __init__(self, hotkey: str, callback: Callable[[], None], log: Callable[[str], None] = print):
        self.hotkey = hotkey
        self.callback = callback
        self.log = log
        self.listener = None

    def __enter__(self):
        try:
            from pynput import keyboard

            normalized = _normalize_hotkey(self.hotkey)
            self.listener = keyboard.GlobalHotKeys({normalized: self.callback})
            self.listener.start()
            self.log(f"Emergency hotkey active: {self.hotkey}")
        except Exception as exc:
            self.log(f"Emergency hotkey unavailable: {exc}. PyAutoGUI FAILSAFE and GUI Stop remain active.")
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.listener is not None:
            try:
                self.listener.stop()
            except Exception:
                pass
        return False
