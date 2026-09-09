from __future__ import annotations

from wotk.automation.backend import RecordingBackend
from wotk.automation.runtime import AutomationContext, StopToken
from wotk.features.supremacy import BASE_POINTS, SupremacyEngine
from wotk.models import SupremacySettings


def make_coords():
    names = list(BASE_POINTS)
    names += [f"Challenge_Battle_{i}" for i in range(1, 7)]
    names += [f"Hero_{i}" for i in range(1, 9)]
    return {name: {"x": i + 1, "y": i + 2} for i, name in enumerate(names)}


def test_supremacy_phase_two_rotates_heroes():
    backend = RecordingBackend()
    ctx = AutomationContext(backend, StopToken(), lambda _m: None)
    settings = SupremacySettings(
        max_loops=3,
        initial_phase_loops=1,
        total_heroes=8,
        heroes_per_battle=4,
        max_hero_usage=6,
        selected_challenge=1,
    )
    result = SupremacyEngine(ctx, make_coords(), settings, action_delay=0, hero_delay=0).run()
    usage = result["hero_usage"]
    assert sum(usage.values()) == 8
    assert set(v for v in usage.values()) == {1}


def test_challenge_7_scrolls_before_reusing_slot_1():
    backend = RecordingBackend()
    ctx = AutomationContext(backend, StopToken(), lambda _m: None)
    settings = SupremacySettings(max_loops=1, initial_phase_loops=1, selected_challenge=7)
    engine = SupremacyEngine(ctx, make_coords(), settings, action_delay=0, hero_delay=0)
    engine.enter_selected_challenge()
    assert ("scroll", -3) in backend.operations
