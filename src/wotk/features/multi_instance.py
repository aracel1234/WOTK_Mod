from __future__ import annotations

import json
import threading
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from wotk.automation.backend import AutomationBackend
from wotk.automation.runtime import AutomationContext, StopToken
from wotk.automation.hotkeys import EmergencyHotkey
from wotk.automation.sandboxie import SandboxieManager
from wotk.automation.windowing import WindowManager
from wotk.models import ConfigurationError, Point, normalize_points, require_points


@dataclass(slots=True)
class MultiInstanceMaster:
    sandboxie_path: str
    max_instances: int = 5
    instance_startup_delay: float = 30.0
    thread_pool_size: int = 5
    base_delay: float = 1.0
    click_timeout: float = 5.0
    max_retries: int = 3
    emergency_hotkey: str = "ctrl+shift+q"
    thread_check_interval: float = 10.0
    max_thread_lifetime: float = 3600.0

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MultiInstanceMaster":
        sandbox = data.get("sandboxie_settings", {})
        global_settings = data.get("global_settings", {})
        threading_cfg = data.get("threading_config", {})
        obj = cls(
            sandboxie_path=str(
                sandbox.get("sandboxie_path", r"C:\Program Files\Sandboxie-Plus\Start.exe")
            ),
            max_instances=int(sandbox.get("max_instances", 5)),
            instance_startup_delay=float(sandbox.get("instance_startup_delay", 30)),
            thread_pool_size=int(threading_cfg.get("thread_pool_size", 5)),
            base_delay=float(global_settings.get("base_delay", 1.0)),
            click_timeout=float(global_settings.get("click_timeout", 5.0)),
            max_retries=int(global_settings.get("max_retries", 3)),
            emergency_hotkey=str(global_settings.get("emergency_hotkey", "ctrl+shift+q")),
            thread_check_interval=float(threading_cfg.get("thread_check_interval", 10)),
            max_thread_lifetime=float(threading_cfg.get("max_thread_lifetime", 3600)),
        )
        if not 1 <= obj.max_instances <= 20:
            raise ConfigurationError("max_instances must be between 1 and 20")
        if not 1 <= obj.thread_pool_size <= 20:
            raise ConfigurationError("thread_pool_size must be between 1 and 20")
        if (
            obj.instance_startup_delay < 0
            or obj.base_delay < 0
            or obj.click_timeout <= 0
            or obj.max_retries < 1
            or obj.thread_check_interval <= 0
            or obj.max_thread_lifetime <= 0
        ):
            raise ConfigurationError("Invalid master timing/retry configuration")
        return obj


@dataclass(slots=True)
class InstanceConfig:
    instance_id: int
    sandbox_name: str
    account_name: str
    farming_mode: str
    game_executable: str
    window_title_pattern: str
    window_index: int
    expected_window_size: tuple[int, int] | None
    offset: Point
    points: dict[str, Point]
    enemy_coords: list[Point] = field(default_factory=list)
    arena_sup_coords: list[Point] = field(default_factory=list)
    arena_myst_coords: list[Point] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)
    max_cycles: int = 1
    cycle_delay: float = 10.0

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "InstanceConfig":
        info = data.get("instance_info", {})
        game = data.get("game_settings", {})
        coord_data = dict(data.get("coordinates", {}))
        timing = data.get("timing_settings", {})
        expected = game.get("expected_window_size")

        def pop_list(name: str) -> list[Point]:
            raw = coord_data.pop(name, [])
            if raw is None:
                return []
            if not isinstance(raw, list):
                raise ConfigurationError(f"{name} must be a list of [x, y] points")
            return [Point.from_raw(item) for item in raw]

        enemy_coords = pop_list("enemy_coords")
        arena_sup_coords = pop_list("arena_sup_coords")
        arena_myst_coords = pop_list("arena_myst_coords")
        obj = cls(
            instance_id=int(info.get("instance_id", 0)),
            sandbox_name=str(info.get("sandbox_name", "")).strip(),
            account_name=str(info.get("account_name", "")).strip() or "Unnamed",
            farming_mode=str(info.get("farming_mode", "individual")).strip().lower(),
            game_executable=str(game.get("game_executable", "")).strip(),
            window_title_pattern=str(
                game.get("window_title_pattern", "Clash of Three Kingdoms")
            ).strip(),
            window_index=int(game.get("window_index", 0)),
            expected_window_size=(int(expected[0]), int(expected[1]))
            if expected and len(expected) == 2
            else None,
            offset=Point.from_raw(game.get("offset_correction", [0, 0])),
            points=normalize_points(coord_data),
            enemy_coords=enemy_coords,
            arena_sup_coords=arena_sup_coords,
            arena_myst_coords=arena_myst_coords,
            timings={str(k): float(v) for k, v in timing.items()},
            max_cycles=int(data.get("max_cycles", 1)),
            cycle_delay=float(data.get("cycle_delay", 10.0)),
        )
        obj.validate()
        return obj

    def validate(self) -> None:
        if self.instance_id < 1:
            raise ConfigurationError("instance_id must be >= 1")
        if not self.sandbox_name:
            raise ConfigurationError(f"Instance {self.instance_id}: sandbox_name is required")
        if not self.game_executable:
            raise ConfigurationError(f"Instance {self.instance_id}: game_executable is required")
        if not self.window_title_pattern:
            raise ConfigurationError(f"Instance {self.instance_id}: window_title_pattern is required")
        if self.farming_mode not in {"individual", "supremacy", "mysteriland"}:
            raise ConfigurationError(
                f"Instance {self.instance_id}: farming_mode must be individual/supremacy/mysteriland"
            )
        if self.max_cycles < 1 or self.cycle_delay < 0:
            raise ConfigurationError(f"Instance {self.instance_id}: invalid cycle settings")
        if self.farming_mode == "individual" and not self.enemy_coords:
            raise ConfigurationError(f"Instance {self.instance_id}: enemy_coords is required")
        if self.farming_mode == "supremacy" and not self.arena_sup_coords:
            raise ConfigurationError(f"Instance {self.instance_id}: arena_sup_coords is required")
        if self.farming_mode == "mysteriland" and not self.arena_myst_coords:
            raise ConfigurationError(f"Instance {self.instance_id}: arena_myst_coords is required")


class RelativeInstanceRunner:
    """Runs one instance while serializing global physical input.

    Worker threads can prepare independently, but every focus + click is protected by a
    shared RLock because PyAutoGUI drives a single OS mouse/keyboard device.
    """

    def __init__(
        self,
        config: InstanceConfig,
        context: AutomationContext,
        window_manager: WindowManager,
        default_delay: float = 1.0,
        window_timeout: float = 60.0,
        max_retries: int = 3,
    ):
        self.config = config
        self.context = context
        self.window_manager = window_manager
        self.default_delay = default_delay
        self.window_timeout = window_timeout
        self.max_retries = max_retries
        self.window = None

    def _delay(self, name: str, fallback: float | None = None) -> float:
        fallback = self.default_delay if fallback is None else fallback
        return float(
            self.config.timings.get(
                f"{name}_delay", self.config.timings.get(name, fallback)
            )
        )

    def acquire_window(self):
        window = self.window_manager.wait_for(
            self.config.window_title_pattern,
            index=self.config.window_index,
            timeout=self.window_timeout,
        )
        if window is None:
            raise RuntimeError(
                f"Instance {self.config.instance_id}: window not found: "
                f"{self.config.window_title_pattern!r} index={self.config.window_index}"
            )
        self.window = window
        rect = self.window_manager.client_rect(window)
        if self.config.expected_window_size:
            expected_width, expected_height = self.config.expected_window_size
            if abs(rect.width - expected_width) > 20 or abs(rect.height - expected_height) > 20:
                self.context.log(
                    f"Instance {self.config.instance_id}: warning client size "
                    f"{rect.width}x{rect.height}; expected approximately "
                    f"{expected_width}x{expected_height}"
                )
        return window

    def click_rel(self, point: Point, label: str, delay: float = 0.0) -> None:
        if not point.configured:
            raise ConfigurationError(
                f"Instance {self.config.instance_id}: coordinate {label!r} is not configured"
            )
        c = self.context
        last_error: Exception | None = None
        absolute = None
        for attempt in range(1, self.max_retries + 1):
            c.check()
            try:
                with c.exclusive_input():
                    if self.window is None:
                        self.acquire_window()
                    if not self.window_manager.focus(self.window):
                        self.window = None
                        self.acquire_window()
                        if not self.window_manager.focus(self.window):
                            raise RuntimeError(
                                f"Instance {self.config.instance_id}: could not focus window"
                            )
                    rect = self.window_manager.client_rect(self.window)
                    absolute = rect.absolute(point, self.config.offset)
                    if not rect.contains(absolute):
                        raise RuntimeError(
                            f"Instance {self.config.instance_id}: transformed coordinate for "
                            f"{label} is outside client area"
                        )
                    c.backend.click(absolute.x, absolute.y)
                break
            except Exception as exc:
                last_error = exc
                self.window = None
                c.log(
                    f"Instance {self.config.instance_id}: {label} attempt "
                    f"{attempt}/{self.max_retries} failed: {exc}"
                )
                if attempt < self.max_retries:
                    c.sleep(min(0.5 * attempt, 2.0))
        else:
            raise RuntimeError(
                f"Instance {self.config.instance_id}: {label} failed after "
                f"{self.max_retries} attempts: {last_error}"
            )
        assert absolute is not None
        c.log(
            f"Instance {self.config.instance_id}: {label} rel=({point.x},{point.y}) "
            f"abs=({absolute.x},{absolute.y})"
        )
        c.sleep(delay)

    def _point(self, name: str) -> Point:
        point = self.config.points.get(name)
        if point is None:
            raise ConfigurationError(
                f"Instance {self.config.instance_id}: missing coordinate {name}"
            )
        return point

    def _navigate(self, mode_button: str) -> None:
        self.click_rel(self._point("challenge_btn"), "Challenge", self._delay("navigation"))
        self.click_rel(self._point("crusade_btn"), "Crusade", self._delay("navigation"))
        self.click_rel(self._point(mode_button), mode_button, self._delay("navigation"))

    def individual_cycle(self) -> None:
        p = self.config.points
        require_points(
            p,
            (
                "challenge_btn",
                "crusade_btn",
                "individual_btn",
                "fight_btn",
                "quick_btn",
                "ok_btn",
                "claim_btn",
            ),
        )
        self._navigate("individual_btn")
        for index, enemy in enumerate(self.config.enemy_coords, 1):
            self.click_rel(enemy, f"Enemy {index}", self._delay("base"))
            self.click_rel(self._point("fight_btn"), "Fight", self._delay("fight", 3.0))
            self.click_rel(
                self._point("quick_btn"), "Quick Combat", self._delay("combat", 2.0)
            )
            self.click_rel(self._point("ok_btn"), "OK", self._delay("base"))
            self.click_rel(self._point("claim_btn"), "Claim", self._delay("claim", 2.0))

    def supremacy_cycle(self) -> None:
        p = self.config.points
        require_points(
            p,
            (
                "challenge_btn",
                "crusade_btn",
                "supremacy_btn",
                "start_btn",
                "ok_btn",
                "challenge_btn_sup",
                "confirm_btn",
                "fight_btn",
                "quick_btn",
                "claim_btn",
            ),
        )
        self._navigate("supremacy_btn")
        for index, arena in enumerate(self.config.arena_sup_coords, 1):
            self.click_rel(arena, f"Supremacy arena {index}", self._delay("base"))
            for key, label, delay_name, fallback in (
                ("start_btn", "Start", "start", 1.5),
                ("ok_btn", "OK", "confirmation", 1.0),
                ("challenge_btn_sup", "Challenge", "challenge", 1.0),
                ("confirm_btn", "Confirm", "confirmation", 1.0),
                ("fight_btn", "Fight", "fight", 3.0),
                ("quick_btn", "Quick Combat", "combat", 2.0),
                ("ok_btn", "OK Result", "base", self.default_delay),
                ("claim_btn", "Claim", "claim", 2.0),
            ):
                self.click_rel(self._point(key), label, self._delay(delay_name, fallback))

    def mysteriland_cycle(self) -> None:
        p = self.config.points
        require_points(
            p,
            (
                "challenge_btn",
                "crusade_btn",
                "mysteriland_btn",
                "fight_btn",
                "quick_btn",
                "ok_btn",
            ),
        )
        self._navigate("mysteriland_btn")
        challenge = p.get("challenge_btn_sup", p["challenge_btn"])
        for index, arena in enumerate(self.config.arena_myst_coords, 1):
            self.click_rel(arena, f"Mysteriland arena {index}", self._delay("base"))
            self.click_rel(challenge, "Challenge", self._delay("challenge", 1.0))
            self.click_rel(self._point("fight_btn"), "Fight", self._delay("fight", 3.0))
            self.click_rel(
                self._point("quick_btn"), "Quick Combat", self._delay("combat", 2.0)
            )
            self.click_rel(self._point("ok_btn"), "OK", self._delay("base"))
            claim = p.get("claim_btn")
            if claim and claim.configured:
                self.click_rel(claim, "Claim", self._delay("claim", 2.0))

    def run(self) -> dict[str, Any]:
        self.acquire_window()
        for cycle in range(1, self.config.max_cycles + 1):
            self.context.check()
            self.context.log(
                f"Instance {self.config.instance_id}: {self.config.farming_mode} "
                f"cycle {cycle}/{self.config.max_cycles}"
            )
            if self.config.farming_mode == "individual":
                self.individual_cycle()
            elif self.config.farming_mode == "supremacy":
                self.supremacy_cycle()
            else:
                self.mysteriland_cycle()
            if cycle < self.config.max_cycles:
                self.context.sleep(self.config.cycle_delay)
        return {"instance_id": self.config.instance_id, "status": "completed"}


class MultiInstanceEngine:
    def __init__(
        self,
        backend: AutomationBackend,
        stop_token: StopToken,
        log,
        master: MultiInstanceMaster,
        instances: list[InstanceConfig],
        window_manager: WindowManager | None = None,
    ):
        self.backend = backend
        self.stop_token = stop_token
        self.log = log
        self.master = master
        self.instances = instances
        self.window_manager = window_manager or WindowManager()
        if not instances:
            raise ConfigurationError("At least one instance configuration is required")
        if len(instances) > master.max_instances:
            raise ConfigurationError(
                f"Configured {len(instances)} instances but master max_instances="
                f"{master.max_instances}"
            )
        ids = [cfg.instance_id for cfg in instances]
        if len(ids) != len(set(ids)):
            raise ConfigurationError("Duplicate instance_id values are not allowed")
        self.input_lock = threading.RLock()

    @classmethod
    def from_files(
        cls,
        backend: AutomationBackend,
        stop_token: StopToken,
        log,
        master_path: str | Path,
        instances_dir: str | Path,
    ) -> "MultiInstanceEngine":
        master_data = json.loads(Path(master_path).read_text(encoding="utf-8"))
        master = MultiInstanceMaster.from_dict(master_data)
        instances = [
            InstanceConfig.from_dict(json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(Path(instances_dir).glob("*.json"))
        ]
        return cls(backend, stop_token, log, master, instances)

    def launch_instances(self) -> None:
        manager = SandboxieManager(self.master.sandboxie_path)
        for index, cfg in enumerate(self.instances):
            self.stop_token.check()
            self.log(
                f"Launching instance {cfg.instance_id} in existing Sandboxie box "
                f"{cfg.sandbox_name}"
            )
            manager.launch(cfg.sandbox_name, cfg.game_executable)
            if index < len(self.instances) - 1:
                self.stop_token.sleep(self.master.instance_startup_delay)

    def _run_one(self, cfg: InstanceConfig) -> dict[str, Any]:
        context = AutomationContext(
            backend=self.backend,
            stop_token=self.stop_token,
            log=self.log,
            input_lock=self.input_lock,
        )
        return RelativeInstanceRunner(
            cfg,
            context,
            self.window_manager,
            default_delay=self.master.base_delay,
            window_timeout=self.master.click_timeout,
            max_retries=self.master.max_retries,
        ).run()

    def _log_system_resources(self) -> None:
        try:
            import psutil

            cpu = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            self.log(
                f"System resources: CPU {cpu:.1f}% | RAM {memory.percent:.1f}% "
                f"({memory.available / (1024 ** 3):.1f} GiB available)"
            )
        except Exception as exc:
            self.log(f"System resource monitoring unavailable: {exc}")

    def run(self, launch: bool = False) -> list[dict[str, Any]]:
        if launch:
            self.launch_instances()
        workers = min(self.master.thread_pool_size, len(self.instances))
        self.log(
            f"Starting {len(self.instances)} instance worker(s) with thread_pool_size={workers}. "
            "Physical UI input is serialized for safety."
        )
        results: list[dict[str, Any]] = []
        started_at: dict[Future, float] = {}
        with EmergencyHotkey(self.master.emergency_hotkey, self.stop_token.stop, self.log):
            with ThreadPoolExecutor(
                max_workers=workers, thread_name_prefix="wotk-instance"
            ) as pool:
                futures: dict[Future, InstanceConfig] = {}
                now = time.monotonic()
                for cfg in self.instances:
                    future = pool.submit(self._run_one, cfg)
                    futures[future] = cfg
                    started_at[future] = now

                pending = set(futures)
                while pending:
                    done, pending = wait(
                        pending,
                        timeout=self.master.thread_check_interval,
                        return_when=FIRST_COMPLETED,
                    )
                    self.stop_token.check()
                    now = time.monotonic()
                    for future in list(pending):
                        lifetime = now - started_at[future]
                        if lifetime > self.master.max_thread_lifetime:
                            cfg = futures[future]
                            self.stop_token.stop()
                            for item in pending:
                                item.cancel()
                            raise TimeoutError(
                                f"Instance {cfg.instance_id} exceeded max_thread_lifetime="
                                f"{self.master.max_thread_lifetime}s"
                            )
                    if not done:
                        active = ", ".join(
                            str(futures[item].instance_id) for item in sorted(
                                pending, key=lambda item: futures[item].instance_id
                            )
                        )
                        self.log(f"Multi-instance health check: active instances [{active}]")
                        self._log_system_resources()
                        continue

                    for future in done:
                        cfg = futures[future]
                        try:
                            result = future.result()
                            results.append(result)
                            self.log(f"Instance {cfg.instance_id}: completed")
                        except Exception as exc:
                            self.log(f"Instance {cfg.instance_id}: failed: {exc}")
                            self.stop_token.stop()
                            for item in pending:
                                item.cancel()
                            raise
        return sorted(results, key=lambda item: int(item["instance_id"]))
