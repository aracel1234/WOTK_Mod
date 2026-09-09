from __future__ import annotations

from wotk.automation.backend import RecordingBackend
from wotk.automation.runtime import AutomationContext, StopToken
from wotk.features.war import BASE_POINTS, WarEngine
from wotk.models import WarSettings


class FakeOcr:
    def __init__(self):
        self.watch_results = iter([True, False])

    def verify_available(self):
        return None

    def contains(self, _region, target):
        if target == "watch":
            return next(self.watch_results)
        if target == "please select the city you want to visit":
            return True
        if target == "assault":
            return True
        if target == "no hero can march":
            return False
        if target == "defender":
            return False
        return False


def test_march_chain_attacks_immediate_next_city():
    coordinates = {
        name: {"x": index + 1, "y": index + 101}
        for index, name in enumerate(BASE_POINTS)
    }
    regions = {
        "watch_area": {"x": 1, "y": 1, "width": 20, "height": 20},
        "select_city_area": {"x": 30, "y": 30, "width": 20, "height": 20},
    }
    settings = WarSettings(
        account_count=1,
        target_color="merah",
        account_colors=["hijau"],
        city_route=["Dongxing", "Mianzhu", "WeiXian"],
        cycle_minutes=0.01,
        max_march_hops=3,
    )
    backend = RecordingBackend()
    ctx = AutomationContext(backend, StopToken(), lambda _m: None)
    engine = WarEngine(
        ctx,
        coordinates,
        regions,
        settings,
        FakeOcr(),  # type: ignore[arg-type]
        default_delay=0,
        combat_delay=0,
        tab_delay=0,
        march_check_interval_seconds=0,
    )
    hops = engine.march_chain(0)
    assert hops == 1
    writes = [op[1] for op in backend.operations if op[0] == "write"]
    assert writes == ["Mianzhu"]
