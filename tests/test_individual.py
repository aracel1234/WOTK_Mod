from __future__ import annotations

from wotk.automation.backend import RecordingBackend
from wotk.automation.runtime import AutomationContext, StopToken
from wotk.features.individual import IndividualEngine, STATIC_POINTS
from wotk.models import QuestDelays


def test_individual_one_stage_sequence():
    names = list(STATIC_POINTS) + ["stage_1", "reward_1"]
    coords = {name: {"x": i + 1, "y": i + 101} for i, name in enumerate(names)}
    backend = RecordingBackend()
    ctx = AutomationContext(backend, StopToken(), lambda _m: None)
    delays = QuestDelays(0, 0, 0, 0)
    IndividualEngine(ctx, coords, delays).run(stages=1)
    clicks = [op for op in backend.operations if op[0] == "click"]
    expected_keys = [
        "challenge_button",
        "crusade_button",
        "individual_button",
        "stage_1",
        "fight_button",
        "quick_combat",
        "ok_button",
        "reward_1",
        "claim_button",
    ]
    expected = [
        ("click", coords[key]["x"], coords[key]["y"]) for key in expected_keys
    ]
    assert clicks == expected
