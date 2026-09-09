from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from wotk.automation.runtime import AutomationContext
from wotk.automation.windowing import WindowManager
from wotk.models import LoginAccount, Point, normalize_points, require_points


REQUIRED_COORDINATES = (
    "login_username",
    "login_password",
    "login_button",
    "signup_button",
    "reg_username",
    "reg_password",
    "reg_confirm",
    "reg_button",
    "play_now",
    "address_bar",
    "id_button",
    "logout_button",
)


@dataclass(slots=True)
class LoginSettings:
    browser_executable: str
    browser_window_pattern: str = "UC"
    landing_url: str = "https://www.heyshell.com/cot/"
    startup_delay: float = 5.0
    navigation_delay: float = 2.0
    action_delay: float = 0.6

    def validate(self) -> None:
        if not Path(self.browser_executable).exists():
            raise FileNotFoundError(f"Browser executable not found: {self.browser_executable}")
        for name in ("startup_delay", "navigation_delay", "action_delay"):
            value = float(getattr(self, name))
            if not 0 <= value <= 120:
                raise ValueError(f"{name} must be between 0 and 120 seconds")


class LoginEngine:
    """Automates the legacy UC Browser login/register flow without persisting secrets."""

    def __init__(
        self,
        context: AutomationContext,
        coordinates: Mapping[str, Point | dict | list | tuple],
        settings: LoginSettings,
        window_manager: WindowManager | None = None,
    ):
        self.context = context
        self.points = normalize_points(coordinates)
        self.settings = settings
        self.window_manager = window_manager or WindowManager()
        require_points(self.points, REQUIRED_COORDINATES)
        self.settings.validate()

    def _go_to(self, url: str) -> None:
        ctx = self.context
        ctx.click(self.points["address_bar"], "address bar", 0.1)
        ctx.hotkey("ctrl", "a", delay=0.05)
        ctx.write(url, interval=0.01)
        ctx.press("enter", delay=self.settings.navigation_delay)

    def _login(self, account: LoginAccount) -> None:
        ctx = self.context
        p = self.points
        ctx.clear_field(p["login_username"], "login username")
        ctx.write(account.username)
        ctx.clear_field(p["login_password"], "login password")
        ctx.write(account.password)
        ctx.click(p["login_button"], "login button", self.settings.navigation_delay)

    def _register(self, account: LoginAccount) -> None:
        ctx = self.context
        p = self.points
        ctx.click(p["signup_button"], "sign up", self.settings.action_delay)
        for key, value in (
            ("reg_username", account.username),
            ("reg_password", account.password),
            ("reg_confirm", account.confirm_password),
        ):
            ctx.clear_field(p[key], key)
            ctx.write(value)
        ctx.click(p["reg_button"], "register button", self.settings.action_delay)
        ctx.click(p["play_now"], "play now", self.settings.navigation_delay)

    def _select_server(self, account: LoginAccount) -> None:
        # The legacy flow opens the server hostname after login/register.
        server_url = f"https://s{account.server_number}.cot.heyshell.com/"
        self._go_to(server_url)

    def _logout_current_account(self) -> None:
        ctx = self.context
        ctx.click(self.points["id_button"], "ID/account button", self.settings.action_delay)
        ctx.click(self.points["logout_button"], "logout", self.settings.navigation_delay)

    def run(self, accounts: list[LoginAccount], launch_browser: bool = True) -> None:
        if not accounts:
            raise ValueError("At least one account is required")
        for account in accounts:
            account.validate()

        ctx = self.context
        if launch_browser:
            ctx.log(f"Launching browser: {self.settings.browser_executable}")
            subprocess.Popen([self.settings.browser_executable])
            ctx.sleep(self.settings.startup_delay)
            window = self.window_manager.wait_for(
                self.settings.browser_window_pattern,
                timeout=max(5.0, self.settings.startup_delay + 10),
            )
            if window is not None:
                self.window_manager.focus(window, maximize=True)

        for index, account in enumerate(accounts, start=1):
            ctx.check()
            ctx.log(f"Account {index}/{len(accounts)}: {account.action_type}")
            if index == 1:
                self._go_to(self.settings.landing_url)
            else:
                ctx.hotkey("ctrl", "t", delay=0.5)
                self._go_to(self.settings.landing_url)
                self._logout_current_account()

            if account.action_type == "register":
                self._register(account)
            else:
                self._login(account)
            self._select_server(account)
        ctx.log("Login automation completed")
