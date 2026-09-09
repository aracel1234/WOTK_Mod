from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from wotk.config_store import ConfigStore  # noqa: E402
from wotk.gui.templates import (  # noqa: E402
    INDIVIDUAL_TEMPLATE,
    LOGIN_TEMPLATE,
    MYSTERILAND_TEMPLATE,
)


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def clone(value):
    return json.loads(json.dumps(value))


def main() -> int:
    local = ROOT / "config" / "local"
    store = ConfigStore()

    login_path = local / "migrated_login_coordinates.json"
    if login_path.exists():
        profile = clone(LOGIN_TEMPLATE)
        profile["coordinates"] = read(login_path)
        target = store.save_json("login/migrated_legacy.json", profile)
        print(f"Imported login calibration -> {target}")

    individual_path = local / "migrated_individual_coordinates.json"
    if individual_path.exists():
        profile = clone(INDIVIDUAL_TEMPLATE)
        profile["coordinates"].update(read(individual_path))
        target = store.save_json("individual/migrated_legacy.json", profile)
        print(f"Imported Individual calibration -> {target}")

    mysteriland_path = local / "migrated_mysteriland_static_partial.json"
    if mysteriland_path.exists():
        profile = clone(MYSTERILAND_TEMPLATE)
        profile["static_coordinates"].update(read(mysteriland_path))
        target = store.save_json("mysteriland/migrated_legacy_partial.json", profile)
        print(f"Imported partial Mysteriland calibration -> {target}")
        print("Mysteriland remains incomplete: recapture every 0,0 point before running.")

    print("No credentials were imported.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
