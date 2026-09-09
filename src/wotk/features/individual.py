from __future__ import annotations

from typing import Mapping

from wotk.automation.runtime import AutomationContext
from wotk.models import Point, QuestDelays, normalize_points, require_points


STATIC_POINTS = (
    "challenge_button",
    "crusade_button",
    "individual_button",
    "fight_button",
    "quick_combat",
    "ok_button",
    "claim_button",
)


class IndividualEngine:
    def __init__(
        self,
        context: AutomationContext,
        coordinates: Mapping[str, Point | dict | list | tuple],
        delays: QuestDelays | None = None,
    ):
        self.context = context
        self.points = normalize_points(coordinates)
        self.delays = delays or QuestDelays()
        self.delays.validate()
        require_points(self.points, STATIC_POINTS)

    def _validate_stages(self, stages: int) -> None:
        if not 1 <= stages <= 10:
            raise ValueError("stages must be between 1 and 10")
        required = []
        for stage in range(1, stages + 1):
            required.extend((f"stage_{stage}", f"reward_{stage}"))
        require_points(self.points, required)

    def enter_mode(self) -> None:
        c, p, d = self.context, self.points, self.delays
        c.click(p["challenge_button"], "Challenge", d.navigation)
        c.click(p["crusade_button"], "Crusade", d.navigation)
        c.click(p["individual_button"], "Individual", d.navigation)

    def run(self, stages: int = 10, enter_mode: bool = True) -> None:
        self._validate_stages(stages)
        c, p, d = self.context, self.points, self.delays
        if enter_mode:
            self.enter_mode()
        for stage in range(1, stages + 1):
            c.check()
            c.log(f"Individual stage {stage}/{stages}")
            c.click(p[f"stage_{stage}"], f"Stage {stage}", d.default)
            c.click(p["fight_button"], "Fight", d.combat)
            c.click(p["quick_combat"], "Quick Combat", d.combat)
            c.click(p["ok_button"], "OK", d.default)
            c.click(p[f"reward_{stage}"], f"Reward {stage}", d.reward)
            c.click(p["claim_button"], "Claim", d.reward)
        c.log("Individual quest completed")

    def reset(self) -> None:
        require_points(self.points, ("reset_button",))
        self.context.click(self.points["reset_button"], "Reset", self.delays.navigation)

    def exit(self) -> None:
        require_points(self.points, ("exit_button",))
        self.context.click(self.points["exit_button"], "Exit", self.delays.navigation)
