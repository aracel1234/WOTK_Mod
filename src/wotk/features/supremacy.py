from __future__ import annotations

from typing import Mapping

from wotk.automation.runtime import AutomationContext
from wotk.models import Point, SupremacySettings, normalize_points, require_points


CHALLENGE_NAMES = (
    "Yellow Rebellion",
    "Battle of D. Zhuo",
    "Lords of J.Dong",
    "Xiao Hu Gui Tian",
    "Battle of Guan Du",
    "San Gu Mao Lu",
    "Battle Of Chi Bi",
    "He Fei Cin Cheng",
    "War Of Tong Guan",
    "Burning Fire",
    "Six Expeditions",
    "Conquer The North",
)

BASE_POINTS = (
    "Challenge_Setup",
    "Crusade",
    "Challenge_Loop",
    "Confirm",
    "Fight",
    "Quick_Combat",
    "OK",
    "Claim",
    "Start",
    "OK_After_Start",
)


class SupremacyEngine:
    def __init__(
        self,
        context: AutomationContext,
        coordinates: Mapping[str, Point | dict | list | tuple],
        settings: SupremacySettings | None = None,
        action_delay: float = 1.5,
        hero_delay: float = 0.5,
    ):
        self.context = context
        self.points = normalize_points(coordinates)
        self.settings = settings or SupremacySettings()
        self.settings.validate()
        self.action_delay = float(action_delay)
        self.hero_delay = float(hero_delay)
        require_points(self.points, BASE_POINTS)
        require_points(self.points, tuple(f"Challenge_Battle_{i}" for i in range(1, 7)))
        require_points(self.points, tuple(f"Hero_{i}" for i in range(1, self.settings.total_heroes + 1)))
        self.hero_usage = {i: 0 for i in range(1, self.settings.total_heroes + 1)}

    def enter_selected_challenge(self) -> None:
        s, c, p = self.settings, self.context, self.points
        c.log(f"Opening Supremacy challenge {s.selected_challenge}: {CHALLENGE_NAMES[s.selected_challenge - 1]}")
        c.click(p["Challenge_Setup"], "Challenge Setup", self.action_delay)
        c.click(p["Crusade"], "Crusade", self.action_delay)
        slot = s.selected_challenge
        if slot > 6:
            c.scroll(-3, delay=1.0)
            slot -= 6
        c.click(p[f"Challenge_Battle_{slot}"], f"Challenge slot {slot}", 1.0)
        c.click(p["Start"], "Start", self.action_delay)
        c.click(p["OK_After_Start"], "OK after Start", self.action_delay)

    def _choose_heroes(self) -> list[int]:
        available = [
            hero
            for hero, usage in self.hero_usage.items()
            if usage < self.settings.max_hero_usage
        ]
        if len(available) < self.settings.heroes_per_battle:
            # If every hero has reached the configured usage cap, begin a fresh rotation.
            if not available:
                self.context.log("Hero usage cap reached for all heroes; resetting rotation counters")
                self.hero_usage = {i: 0 for i in self.hero_usage}
                available = list(self.hero_usage)
            else:
                self.context.log(
                    "Not enough heroes below usage cap; selecting the remaining available heroes"
                )
        available.sort(key=lambda h: (self.hero_usage[h], h))
        return available[: self.settings.heroes_per_battle]

    def _select_heroes(self) -> list[int]:
        selected = self._choose_heroes()
        if not selected:
            raise RuntimeError("No heroes available for phase 2")
        for hero in selected:
            self.context.click(self.points[f"Hero_{hero}"], f"Hero {hero}", self.hero_delay)
            self.hero_usage[hero] += 1
        return selected

    def _battle(self, with_heroes: bool) -> None:
        c, p = self.context, self.points
        c.click(p["Challenge_Loop"], "Challenge", self.action_delay)
        if with_heroes:
            heroes = self._select_heroes()
            c.log(f"Selected heroes: {heroes}")
        c.click(p["Confirm"], "Confirm", self.action_delay)
        c.click(p["Fight"], "Fight", self.action_delay)
        c.click(p["Quick_Combat"], "Quick Combat", self.action_delay)
        c.click(p["OK"], "OK", self.action_delay)
        c.click(p["Claim"], "Claim", self.action_delay)

    def run(self, enter_mode: bool = True) -> dict[str, object]:
        if enter_mode:
            self.enter_selected_challenge()
        successful = 0
        for loop_index in range(self.settings.max_loops):
            self.context.check()
            with_heroes = loop_index >= self.settings.initial_phase_loops
            phase = 2 if with_heroes else 1
            self.context.log(
                f"Supremacy loop {loop_index + 1}/{self.settings.max_loops} (phase {phase})"
            )
            self._battle(with_heroes=with_heroes)
            successful += 1
        summary = {"successful_loops": successful, "hero_usage": dict(self.hero_usage)}
        self.context.log(f"Supremacy completed: {summary}")
        return summary
