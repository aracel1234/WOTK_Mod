from __future__ import annotations

import re
import time
from collections.abc import Mapping

from wotk.automation.ocr import OcrService
from wotk.automation.runtime import AutomationContext
from wotk.models import (
    COLOR_TO_CITY,
    MarchState,
    Point,
    Region,
    WarSettings,
    normalize_points,
    normalize_regions,
    require_points,
    require_regions,
)


BASE_POINTS = (
    "bendera_biru",
    "search",
    "field_search",
    "konfirmasi_search",
    "nama_kota",
    "fight",
    "dispatch",
    "minimize",
    "watch",
    "march",
    "back",
    "exit",
)
BASE_REGIONS = ("watch_area", "select_city_area")


class WarEngine:
    """Multi-account Auto War + chained March/Assault flow.

    The implementation follows the latest flow in the supporting specification:
    Fight -> Dispatch -> Minimize -> Watch -> March -> select next city -> Assault,
    with OCR checks for Watch, the city-selection prompt and the optional
    "No hero can march"/Assault indicators.
    """

    def __init__(
        self,
        context: AutomationContext,
        coordinates: Mapping[str, Point | dict | list | tuple],
        ocr_regions: Mapping[str, Region | dict | list | tuple],
        settings: WarSettings,
        ocr: OcrService,
        default_delay: float = 0.5,
        combat_delay: float = 2.0,
        tab_delay: float = 0.8,
        march_check_interval_seconds: float = 300.0,
    ):
        self.context = context
        self.points = normalize_points(coordinates)
        self.regions = normalize_regions(ocr_regions)
        self.settings = settings
        self.ocr = ocr
        self.default_delay = float(default_delay)
        self.combat_delay = float(combat_delay)
        self.tab_delay = float(tab_delay)
        self.march_check_interval_seconds = float(march_check_interval_seconds)
        self.settings.validate()
        require_points(self.points, BASE_POINTS)
        require_regions(self.regions, BASE_REGIONS)
        for name, value in (
            ("default_delay", self.default_delay),
            ("combat_delay", self.combat_delay),
            ("tab_delay", self.tab_delay),
            ("march_check_interval_seconds", self.march_check_interval_seconds),
        ):
            if value < 0:
                raise ValueError(f"{name} cannot be negative")
        self.states = [MarchState() for _ in range(self.settings.account_count)]

    def _optional_point(self, name: str, fallback: str | None = None) -> Point | None:
        point = self.points.get(name)
        if point and point.configured:
            return point
        if fallback:
            point = self.points.get(fallback)
            if point and point.configured:
                return point
        return None

    def _optional_region(self, name: str) -> Region | None:
        region = self.regions.get(name)
        return region if region and region.configured else None

    def _search_city(self, city: str, assault: bool = False) -> None:
        c = self.context
        if assault:
            search = self._optional_point("assault_search", "search")
            field = self._optional_point("assault_field_search", "field_search")
            confirm = self._optional_point("assault_confirm_search", "konfirmasi_search")
            city_point = self._optional_point("assault_city", "nama_kota")
        else:
            search = self.points["search"]
            field = self.points["field_search"]
            confirm = self.points["konfirmasi_search"]
            city_point = self.points["nama_kota"]
        assert search and field and confirm and city_point
        c.click(search, "Search", self.default_delay)
        c.clear_field(field, "city search field", self.default_delay)
        c.write(city, interval=0.03, delay=self.default_delay)
        c.click(confirm, "Confirm Search", self.default_delay)
        c.click(city_point, f"City {city}", self.default_delay)

    def _switch_account(self) -> None:
        self.context.switch_tab(delay=self.tab_delay)

    def change_maps(self) -> None:
        c = self.context
        c.log("Changing map on every account")
        for account_index in range(self.settings.account_count):
            c.check()
            c.click(
                self.points["bendera_biru"],
                f"Blue flag account {account_index + 1}",
                self.default_delay,
            )
            self._switch_account()
        c.log("Map change loop completed; returned to starting tab")

    def find_initial_target(self) -> str:
        city = COLOR_TO_CITY[self.settings.target_color]
        self._search_city(city)
        return city

    def auto_fight_current_account(self, account_index: int) -> None:
        c, p = self.context, self.points
        c.log(f"Account {account_index + 1}: auto fight")
        c.click(p["fight"], "Fight", self.combat_delay)
        c.click(p["dispatch"], "Dispatch", self.default_delay)
        c.click(p["minimize"], "Minimize", self.default_delay)

    def _has_watch(self) -> bool:
        return self.ocr.contains(self.regions["watch_area"], "watch")

    def _log_defender_if_present(self) -> None:
        region = self._optional_region("defender_area")
        if region is not None:
            try:
                if self.ocr.contains(region, "defender"):
                    self.context.log("Defender text detected")
            except Exception as exc:
                self.context.log(f"Defender OCR check skipped: {exc}")

    def _select_prompt_visible(self) -> bool:
        return self.ocr.contains(
            self.regions["select_city_area"],
            "please select the city you want to visit",
        )

    def _no_hero_can_march(self) -> bool:
        region = self._optional_region("no_hero_area")
        if region is None:
            return False
        return self.ocr.contains(region, "no hero can march")

    def _verify_assault_indicator(self) -> bool:
        region = self._optional_region("assault_area")
        if region is None:
            return True
        return self.ocr.contains(region, "assault")

    def _general_threshold_met(self) -> bool:
        if not self.settings.use_general_threshold:
            return True
        player_region = self._optional_region("player_general_area")
        enemy_region = self._optional_region("enemy_general_area")
        if player_region is None or enemy_region is None:
            raise RuntimeError(
                "General threshold mode requires player_general_area and enemy_general_area"
            )

        def read_count(region: Region, label: str) -> int:
            result = self.ocr.read(region)
            match = re.search(r"-?\d+", result.text.replace(",", ""))
            if not match:
                raise RuntimeError(f"Could not read {label} general count from OCR: {result.text!r}")
            return int(match.group())

        player_count = read_count(player_region, "player")
        enemy_count = read_count(enemy_region, "enemy")
        difference = player_count - enemy_count
        self.context.log(
            f"March threshold: player={player_count}, enemy={enemy_count}, "
            f"difference={difference}, required={self.settings.march_threshold}"
        )
        return difference >= self.settings.march_threshold

    def _perform_assault(self, target_city: str) -> bool:
        c = self.context
        for attempt in range(1, self.settings.assault_retries + 1):
            c.check()
            c.log(
                f"Assault {target_city}: attempt {attempt}/{self.settings.assault_retries}"
            )
            try:
                self._search_city(target_city, assault=True)
                if not self._verify_assault_indicator():
                    raise RuntimeError("Assault indicator was not detected")
                assault_button = self._optional_point("assault_button")
                if assault_button is not None:
                    c.click(assault_button, "Assault", self.default_delay)
                march_confirm = self._optional_point("march_confirm")
                if march_confirm is not None:
                    c.click(march_confirm, "March Confirm", self.default_delay)
                return True
            except Exception as exc:
                c.log(f"Assault attempt failed: {exc}")
                if attempt < self.settings.assault_retries:
                    c.sleep(self.default_delay)
        return False

    def march_chain(self, account_index: int) -> int:
        """Continue chained city assaults until Watch/March is unavailable."""
        if not self.settings.march_enabled:
            return 0
        c, p = self.context, self.points
        state = self.states[account_index]
        hops = 0

        # Latest flow checks Watch by selecting the current city again after Minimize.
        c.click(p["nama_kota"], "Current City", self.default_delay)
        while hops < self.settings.max_march_hops:
            c.check()
            try:
                if not self._has_watch():
                    self._log_defender_if_present()
                    c.log(f"Account {account_index + 1}: Watch not available; march chain ends")
                    c.click(p["exit"], "Exit", self.default_delay)
                    break
            except Exception as exc:
                state.fail_count += 1
                c.log(f"Watch OCR failed: {exc}")
                break

            try:
                if not self._general_threshold_met():
                    c.log("General-count March threshold is not met; march chain ends")
                    c.click(p["exit"], "Exit", self.default_delay)
                    break
            except Exception as exc:
                state.fail_count += 1
                c.log(f"General-count threshold check failed: {exc}")
                break

            c.click(p["watch"], "Watch", self.default_delay)
            c.click(p["march"], "March", self.default_delay)

            try:
                if self._no_hero_can_march():
                    c.log("No hero can march; returning to previous screen")
                    c.click(p["back"], "Back", self.default_delay)
                    break
                if not self._select_prompt_visible():
                    state.fail_count += 1
                    c.log("March city-selection prompt was not detected; returning")
                    c.click(p["back"], "Back", self.default_delay)
                    break
            except Exception as exc:
                state.fail_count += 1
                c.log(f"March OCR check failed: {exc}")
                c.click(p["back"], "Back", self.default_delay)
                break

            next_city = state.next_city(self.settings.city_route)
            if next_city is None:
                c.log("All configured march targets have been used")
                c.click(p["back"], "Back", self.default_delay)
                break

            if self._perform_assault(next_city):
                state.mark_success(next_city, self.settings.city_route)
                hops += 1
                c.log(
                    f"Account {account_index + 1}: assault success -> {next_city}; "
                    f"continuing Watch/March chain"
                )
                # The successfully assaulted target becomes the new 'city 1'.
                # We are already on that city after search/assault, so re-check Watch.
                continue

            state.fail_count += 1
            state.last_target = next_city
            c.log(f"Account {account_index + 1}: assault failed -> {next_city}")
            c.click(p["back"], "Back", self.default_delay)
            break

        if hops >= self.settings.max_march_hops:
            c.log("March chain stopped at configured max_march_hops safety limit")
        return hops

    def fight_round(self) -> None:
        target_city = COLOR_TO_CITY[self.settings.target_color]
        self.context.log(f"Starting fight round against {target_city}")
        for account_index in range(self.settings.account_count):
            self.context.check()
            self.context.log(
                f"Account {account_index + 1}/{self.settings.account_count} "
                f"(alliance {self.settings.account_colors[account_index]})"
            )
            self.find_initial_target()
            self.auto_fight_current_account(account_index)
            self.march_chain(account_index)
            self._switch_account()
        self.context.log("Fight round completed; returned to starting tab")

    def march_recheck_round(self) -> None:
        self.context.log("Periodic March re-check across all accounts")
        for account_index in range(self.settings.account_count):
            self.context.check()
            try:
                self.march_chain(account_index)
            finally:
                self._switch_account()

    def _wait_cycle_with_march_checks(self) -> None:
        cycle_seconds = self.settings.cycle_minutes * 60.0
        if cycle_seconds <= 0:
            return
        deadline = time.monotonic() + cycle_seconds
        while True:
            self.context.check()
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return
            interval = min(self.march_check_interval_seconds, remaining)
            self.context.log(f"Cycle timer: waiting {interval:.0f}s before next March check")
            self.context.sleep(interval)
            if time.monotonic() < deadline and self.settings.march_enabled:
                self.march_recheck_round()

    def run(self, max_cycles: int | None = None, initialize_maps: bool = True) -> dict[str, object]:
        """Run Auto War.

        max_cycles=None means run continuously until Stop/Failsafe. A finite value is useful for
        testing or scheduled one-shot runs.
        """
        if max_cycles is not None and max_cycles < 1:
            raise ValueError("max_cycles must be >= 1 or None")
        self.ocr.verify_available()
        if initialize_maps:
            self.change_maps()

        cycles = 0
        while max_cycles is None or cycles < max_cycles:
            self.context.check()
            cycles += 1
            self.context.log(f"=== Auto War cycle {cycles} ===")
            self.fight_round()
            if max_cycles is not None and cycles >= max_cycles:
                break
            self._wait_cycle_with_march_checks()
            self.context.sleep(self.settings.post_cycle_pause)

        summary = {
            "cycles": cycles,
            "accounts": [
                {
                    "success_count": state.success_count,
                    "fail_count": state.fail_count,
                    "last_target": state.last_target,
                    "used": sorted(state.used),
                }
                for state in self.states
            ],
        }
        self.context.log(f"Auto War finished: {summary}")
        return summary
