from __future__ import annotations

from typing import Mapping

from wotk.automation.runtime import AutomationContext
from wotk.models import Point, normalize_points, require_points


STATIC_POINTS = (
    "challenge",
    "crusade",
    "mysteriland",
    "enter_challenge",
    "fight",
    "quick_combat",
    "ok",
    "swipe_1x",
    "swipe_5x",
    "exit",
)


class MysterilandEngine:
    def __init__(
        self,
        context: AutomationContext,
        static_coordinates: Mapping[str, Point | dict | list | tuple],
        stage_coordinates: Mapping[str, Point | dict | list | tuple],
        delay: float = 0.5,
    ):
        self.context = context
        self.static = normalize_points(static_coordinates)
        self.stage = normalize_points(stage_coordinates)
        self.delay = float(delay)
        if not 0 <= self.delay <= 60:
            raise ValueError("delay must be between 0 and 60 seconds")
        require_points(self.static, STATIC_POINTS)

    def _validate_stages(self, stages: int) -> None:
        if not 1 <= stages <= 5:
            raise ValueError("stages must be between 1 and 5")
        required = []
        for stage in range(1, stages + 1):
            required.extend((f"stage_{stage}", f"reward_{stage}"))
        require_points(self.stage, required)

    def enter_mode(self) -> None:
        c, p = self.context, self.static
        c.click(p["challenge"], "Challenge", self.delay)
        c.click(p["crusade"], "Crusade", self.delay)
        c.click(p["mysteriland"], "Mysteriland", self.delay)

    def run(self, stages: int = 5, enter_mode: bool = True) -> None:
        self._validate_stages(stages)
        c, p = self.context, self.static
        if enter_mode:
            self.enter_mode()
        for stage in range(1, stages + 1):
            c.check()
            c.log(f"Mysteriland stage {stage}/{stages}")
            c.click(self.stage[f"stage_{stage}"], f"Stage {stage}", self.delay)
            c.click(p["enter_challenge"], "Enter Challenge", self.delay)
            c.click(p["fight"], "Fight", self.delay)
            c.click(p["quick_combat"], "Quick Combat", self.delay)
            c.click(p["ok"], "OK", self.delay)
            c.click(self.stage[f"reward_{stage}"], f"Reward {stage}", self.delay)
        c.log("Mysteriland quest completed")

    def swipe(self, stage: int, count: int = 1) -> None:
        if stage not in range(1, 6):
            raise ValueError("stage must be between 1 and 5")
        if count not in {1, 5}:
            raise ValueError("swipe count must be 1 or 5")
        require_points(self.stage, (f"stage_{stage}",))
        key = "swipe_1x" if count == 1 else "swipe_5x"
        c = self.context
        c.click(self.stage[f"stage_{stage}"], f"Stage {stage}", self.delay)
        c.click(self.static[key], f"Swipe {count}x", self.delay)
        c.click_screen_center(delay=self.delay)
        c.log(f"Mysteriland swipe {count}x completed")

    def exit(self) -> None:
        self.context.click(self.static["exit"], "Exit", self.delay)
