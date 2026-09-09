from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping


class ConfigurationError(ValueError):
    """Raised when a user configuration is incomplete or invalid."""


@dataclass(frozen=True, slots=True)
class Point:
    x: int
    y: int

    @classmethod
    def from_raw(cls, value: Any) -> "Point":
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            return cls(int(value["x"]), int(value["y"]))
        if isinstance(value, (list, tuple)) and len(value) == 2:
            return cls(int(value[0]), int(value[1]))
        raise ConfigurationError(f"Invalid point value: {value!r}")

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y}

    @property
    def configured(self) -> bool:
        return not (self.x == 0 and self.y == 0)


@dataclass(frozen=True, slots=True)
class Region:
    x: int
    y: int
    width: int
    height: int

    @classmethod
    def from_raw(cls, value: Any) -> "Region":
        if isinstance(value, cls):
            return value
        if isinstance(value, Mapping):
            if {"x", "y", "width", "height"}.issubset(value):
                return cls(
                    int(value["x"]),
                    int(value["y"]),
                    int(value["width"]),
                    int(value["height"]),
                )
            if {"x1", "y1", "x2", "y2"}.issubset(value):
                x1, y1, x2, y2 = (int(value[k]) for k in ("x1", "y1", "x2", "y2"))
                return cls(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        if isinstance(value, (list, tuple)) and len(value) == 4:
            return cls(*(int(v) for v in value))
        raise ConfigurationError(f"Invalid region value: {value!r}")

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y, "width": self.width, "height": self.height}

    @property
    def configured(self) -> bool:
        return self.width > 0 and self.height > 0


@dataclass(slots=True)
class LoginAccount:
    username: str
    password: str
    action_type: str = "login"
    server_number: str = "7"
    confirm_password: str = ""

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "LoginAccount":
        account = cls(
            username=str(data.get("username", "")).strip(),
            password=str(data.get("password", "")),
            action_type=str(data.get("action_type", "login")).lower().strip(),
            server_number=str(data.get("server_number", "7")).strip(),
            confirm_password=str(data.get("confirm_password") or ""),
        )
        account.validate()
        return account

    def validate(self) -> None:
        if self.action_type not in {"login", "register"}:
            raise ConfigurationError("action_type must be 'login' or 'register'")
        if not self.username:
            raise ConfigurationError("username cannot be empty")
        if not self.password:
            raise ConfigurationError(f"password cannot be empty for {self.username}")
        if self.action_type == "register" and not self.confirm_password:
            raise ConfigurationError(f"confirm_password is required for {self.username}")
        if not self.server_number:
            raise ConfigurationError("server_number cannot be empty")

    def to_dict(self, include_secret: bool = True) -> dict[str, Any]:
        return {
            "username": self.username,
            "password": self.password if include_secret else "",
            "confirm_password": self.confirm_password if include_secret else "",
            "action_type": self.action_type,
            "server_number": self.server_number,
        }


@dataclass(slots=True)
class QuestDelays:
    default: float = 0.5
    navigation: float = 1.0
    combat: float = 2.0
    reward: float = 1.5

    def validate(self) -> None:
        for name in ("default", "navigation", "combat", "reward"):
            value = float(getattr(self, name))
            if value < 0 or value > 60:
                raise ConfigurationError(f"{name} delay must be between 0 and 60 seconds")


@dataclass(slots=True)
class SupremacySettings:
    max_loops: int = 10
    initial_phase_loops: int = 6
    total_heroes: int = 8
    heroes_per_battle: int = 4
    max_hero_usage: int = 6
    selected_challenge: int = 1

    def validate(self) -> None:
        if not 1 <= self.max_loops <= 50:
            raise ConfigurationError("max_loops must be between 1 and 50")
        if not 0 <= self.initial_phase_loops <= self.max_loops:
            raise ConfigurationError("initial_phase_loops must be between 0 and max_loops")
        if not 1 <= self.total_heroes <= 8:
            raise ConfigurationError("total_heroes must be between 1 and 8")
        if not 1 <= self.heroes_per_battle <= self.total_heroes:
            raise ConfigurationError("heroes_per_battle must be between 1 and total_heroes")
        if self.max_hero_usage < 1:
            raise ConfigurationError("max_hero_usage must be at least 1")
        if not 1 <= self.selected_challenge <= 12:
            raise ConfigurationError("selected_challenge must be between 1 and 12")


COLOR_TO_CITY = {"hijau": "Mianzhu", "merah": "Dongxing", "biru": "WeiXian"}
VALID_COLORS = tuple(COLOR_TO_CITY)


@dataclass(slots=True)
class WarSettings:
    account_count: int
    target_color: str
    account_colors: list[str]
    city_route: list[str]
    cycle_minutes: float = 31.0
    march_enabled: bool = True
    max_march_hops: int = 20
    assault_retries: int = 3
    post_cycle_pause: float = 3.0
    use_general_threshold: bool = False
    march_threshold: int = 3

    def validate(self) -> None:
        self.target_color = self.target_color.lower().strip()
        self.account_colors = [c.lower().strip() for c in self.account_colors]
        self.city_route = [c.strip() for c in self.city_route if c.strip()]
        if not 1 <= self.account_count <= 10:
            raise ConfigurationError("account_count must be between 1 and 10")
        if self.target_color not in VALID_COLORS:
            raise ConfigurationError(f"target_color must be one of {VALID_COLORS}")
        if len(self.account_colors) != self.account_count:
            raise ConfigurationError("account_colors length must equal account_count")
        for index, color in enumerate(self.account_colors, start=1):
            if color not in VALID_COLORS:
                raise ConfigurationError(f"Account {index}: invalid color {color!r}")
            if color == self.target_color:
                raise ConfigurationError(
                    f"Account {index}: alliance color cannot equal target color ({self.target_color})"
                )
        if not self.city_route:
            self.city_route = [COLOR_TO_CITY[self.target_color]]
        target_city = COLOR_TO_CITY[self.target_color]
        if target_city not in self.city_route:
            self.city_route.insert(0, target_city)
        if self.cycle_minutes <= 0:
            raise ConfigurationError("cycle_minutes must be greater than 0")
        if self.max_march_hops < 1:
            raise ConfigurationError("max_march_hops must be at least 1")
        if self.assault_retries < 1:
            raise ConfigurationError("assault_retries must be at least 1")
        if self.march_threshold < 0:
            raise ConfigurationError("march_threshold cannot be negative")


@dataclass(slots=True)
class MarchState:
    current_index: int = 0
    success_count: int = 0
    fail_count: int = 0
    last_target: str = ""
    used: set[str] = field(default_factory=set)

    def next_city(self, route: Iterable[str]) -> str | None:
        route_list = list(route)
        if not route_list:
            return None
        start = max(0, self.current_index + 1)
        for index in range(start, len(route_list)):
            city = route_list[index]
            if city not in self.used:
                return city
        return None

    def mark_success(self, city: str, route: Iterable[str]) -> None:
        route_list = list(route)
        self.used.add(city)
        self.last_target = city
        self.success_count += 1
        try:
            self.current_index = route_list.index(city)
        except ValueError:
            pass


def normalize_points(mapping: Mapping[str, Any]) -> dict[str, Point]:
    return {name: Point.from_raw(value) for name, value in mapping.items()}


def normalize_regions(mapping: Mapping[str, Any]) -> dict[str, Region]:
    return {name: Region.from_raw(value) for name, value in mapping.items()}


def require_points(points: Mapping[str, Point], names: Iterable[str]) -> None:
    missing = [name for name in names if name not in points or not points[name].configured]
    if missing:
        raise ConfigurationError("Missing/unconfigured coordinates: " + ", ".join(missing))


def require_regions(regions: Mapping[str, Region], names: Iterable[str]) -> None:
    missing = [name for name in names if name not in regions or not regions[name].configured]
    if missing:
        raise ConfigurationError("Missing/unconfigured OCR areas: " + ", ".join(missing))
