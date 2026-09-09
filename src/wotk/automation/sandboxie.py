from __future__ import annotations

import subprocess
from pathlib import Path


class SandboxieManager:
    """Launches a program in an existing Sandboxie-Plus sandbox."""

    def __init__(self, start_executable: str):
        self.start_executable = Path(start_executable)

    def validate(self) -> None:
        if not self.start_executable.exists():
            raise FileNotFoundError(f"Sandboxie Start.exe not found: {self.start_executable}")

    def launch(self, sandbox_name: str, executable: str, extra_args: list[str] | None = None):
        self.validate()
        target = Path(executable)
        if not target.exists():
            raise FileNotFoundError(f"Game executable not found: {target}")
        command = [str(self.start_executable), f"/box:{sandbox_name}", str(target)]
        command.extend(extra_args or [])
        return subprocess.Popen(command)
