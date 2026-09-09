from __future__ import annotations

from wotk.features.login import REQUIRED_COORDINATES as LOGIN_COORDS
from wotk.features.war import BASE_POINTS as WAR_BASE_POINTS
from wotk.features.war import BASE_REGIONS as WAR_BASE_REGIONS


def points(names):
    return {name: {"x": 0, "y": 0} for name in names}


def regions(names):
    return {name: {"x": 0, "y": 0, "width": 0, "height": 0} for name in names}


LOGIN_TEMPLATE = {
    "settings": {
        "browser_executable": r"C:\Program Files (x86)\UCBrowser\Application\UCBrowser.exe",
        "browser_window_pattern": "UC",
        "landing_url": "https://www.heyshell.com/cot/",
        "startup_delay": 5.0,
        "navigation_delay": 2.0,
        "action_delay": 0.6,
    },
    "coordinates": points(LOGIN_COORDS),
}
LOGIN_ACCOUNTS_TEMPLATE = [
    {
        "username": "",
        "password": "",
        "confirm_password": "",
        "action_type": "login",
        "server_number": "7",
    }
]

INDIVIDUAL_COORD_NAMES = (
    "challenge_button",
    "crusade_button",
    "individual_button",
    "fight_button",
    "quick_combat",
    "ok_button",
    "claim_button",
    "reset_button",
    "exit_button",
) + tuple(f"stage_{i}" for i in range(1, 11)) + tuple(f"reward_{i}" for i in range(1, 11))
INDIVIDUAL_TEMPLATE = {
    "stages": 10,
    "delays": {"default": 0.5, "navigation": 1.0, "combat": 2.0, "reward": 1.5},
    "coordinates": points(INDIVIDUAL_COORD_NAMES),
}

MYST_STATIC_NAMES = (
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
MYST_STAGE_NAMES = tuple(f"stage_{i}" for i in range(1, 6)) + tuple(f"reward_{i}" for i in range(1, 6))
MYST_DAYS = ("senin", "selasa", "rabu", "kamis", "jumat", "sabtu")
MYSTERILAND_TEMPLATE = {
    "day": "senin",
    "stages": 5,
    "swipe_stage": 5,
    "swipe_count": 1,
    "delay": 0.5,
    "static_coordinates": points(MYST_STATIC_NAMES),
    "stage_coordinates_by_day": {day: points(MYST_STAGE_NAMES) for day in MYST_DAYS},
}

SUP_COORD_NAMES = (
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
) + tuple(f"Challenge_Battle_{i}" for i in range(1, 7)) + tuple(f"Hero_{i}" for i in range(1, 9))
SUPREMACY_TEMPLATE = {
    "settings": {
        "max_loops": 10,
        "initial_phase_loops": 6,
        "total_heroes": 8,
        "heroes_per_battle": 4,
        "max_hero_usage": 6,
        "selected_challenge": 1,
    },
    "action_delay": 1.5,
    "hero_delay": 0.5,
    "coordinates": points(SUP_COORD_NAMES),
}

WAR_COORD_NAMES = tuple(WAR_BASE_POINTS) + (
    "assault_search",
    "assault_field_search",
    "assault_confirm_search",
    "assault_city",
    "assault_button",
    "march_confirm",
)
WAR_REGION_NAMES = tuple(WAR_BASE_REGIONS) + (
    "defender_area",
    "no_hero_area",
    "assault_area",
    "player_general_area",
    "enemy_general_area",
)
WAR_TEMPLATE = {
    "settings": {
        "account_count": 2,
        "target_color": "merah",
        "account_colors": ["hijau", "biru"],
        "city_route": ["Dongxing", "Mianzhu", "WeiXian"],
        "cycle_minutes": 31.0,
        "march_enabled": True,
        "max_march_hops": 20,
        "assault_retries": 3,
        "post_cycle_pause": 3.0,
        "use_general_threshold": False,
        "march_threshold": 3,
    },
    "runtime": {
        "default_delay": 0.5,
        "combat_delay": 2.0,
        "tab_delay": 0.8,
        "march_check_interval_seconds": 300.0,
        "tesseract_cmd": "",
        "max_cycles": None,
        "initialize_maps": True,
    },
    "coordinates": points(WAR_COORD_NAMES),
    "ocr_regions": regions(WAR_REGION_NAMES),
}
