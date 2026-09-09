from __future__ import annotations

from wotk.automation.backend import RecordingBackend
from wotk.automation.runtime import AutomationContext, StopToken


def make_context():
    backend = RecordingBackend()
    logs: list[str] = []
    context = AutomationContext(backend, StopToken(), logs.append)
    return context, backend, logs


def point_map(names):
    return {name: {"x": index * 10 + 1, "y": index * 10 + 2} for index, name in enumerate(names)}
