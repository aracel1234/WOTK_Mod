from __future__ import annotations

from wotk.automation.backend import RecordingBackend
from wotk.automation.runtime import AutomationContext, StopToken
from wotk.features.mysteriland import MysterilandEngine, STATIC_POINTS


def test_mysteriland_one_stage_sequence():
    static = {name: {"x": i + 1, "y": i + 50} for i, name in enumerate(STATIC_POINTS)}
    stage = {
        "stage_1": {"x": 100, "y": 101},
        "reward_1": {"x": 102, "y": 103},
    }
    backend = RecordingBackend()
    ctx = AutomationContext(backend, StopToken(), lambda _m: None)
    MysterilandEngine(ctx, static, stage, delay=0).run(stages=1)
    assert ("click", 100, 101) in backend.operations
    assert ("click", 102, 103) in backend.operations


def test_mysteriland_swipe_uses_screen_center():
    static = {name: {"x": i + 1, "y": i + 50} for i, name in enumerate(STATIC_POINTS)}
    stage = {"stage_5": {"x": 100, "y": 101}}
    backend = RecordingBackend()
    ctx = AutomationContext(backend, StopToken(), lambda _m: None)
    MysterilandEngine(ctx, static, stage, delay=0).swipe(stage=5, count=5)
    assert ("click", 960, 540) in backend.operations
