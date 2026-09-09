from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from platformdirs import user_config_dir, user_log_dir


APP_NAME = "WOTK-Mod"
APP_AUTHOR = "WOTK"


def safe_name(value: str, fallback: str = "profile") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", value.strip())
    cleaned = cleaned.strip(" ._")
    return cleaned or fallback


class ConfigStore:
    """Stores mutable user configuration outside the Git repository."""

    def __init__(self, base_dir: str | Path | None = None):
        self.base_dir = Path(base_dir or user_config_dir(APP_NAME, APP_AUTHOR))
        self.log_dir = Path(user_log_dir(APP_NAME, APP_AUTHOR))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        for folder in (
            "login",
            "individual",
            "mysteriland/static",
            "mysteriland/stage",
            "supremacy",
            "war/coordinates",
            "war/ocr",
            "war/settings",
            "multi_instance/instances",
        ):
            (self.base_dir / folder).mkdir(parents=True, exist_ok=True)

    def path(self, relative: str | Path) -> Path:
        rel = Path(relative)
        if rel.is_absolute() or ".." in rel.parts:
            raise ValueError("ConfigStore paths must be relative and cannot contain '..'")
        return self.base_dir / rel

    def load_json(self, relative: str | Path, default: Any = None) -> Any:
        path = self.path(relative)
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    def save_json(self, relative: str | Path, data: Any) -> Path:
        path = self.path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
        fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, path)
        finally:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
        return path

    def list_json(self, relative_dir: str | Path, prefix: str = "") -> list[Path]:
        directory = self.path(relative_dir)
        if not directory.exists():
            return []
        return sorted(
            (p for p in directory.glob(f"{prefix}*.json") if p.is_file()),
            key=lambda p: p.name.lower(),
        )
