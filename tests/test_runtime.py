from __future__ import annotations

from wotk.automation.backend import RecordingBackend
from wotk.automation.runtime import AutomationContext, StopToken
from wotk.models import Point


def test_clear_field_uses_ctrl_a_and_backspace():
    backend = RecordingBackend()
    ctx = AutomationContext(backend, StopToken(), lambda _m: None)
    ctx.clear_field(Point(10, 20), delay=0)
    assert backend.operations[0] == ("click", 10, 20)
    assert ("hotkey", "ctrl", "a") in backend.operations
    assert ("press", "backspace") in backend.operations
