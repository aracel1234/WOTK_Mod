from __future__ import annotations

from wotk.automation.hotkeys import _normalize_hotkey


def test_normalize_hotkey():
    assert _normalize_hotkey("ctrl+shift+q") == "<ctrl>+<shift>+q"
