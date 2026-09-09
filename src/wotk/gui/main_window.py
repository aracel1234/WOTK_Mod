from __future__ import annotations

import json
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from wotk.automation.backend import PyAutoGuiBackend
from wotk.automation.ocr import OcrService
from wotk.automation.runtime import AutomationContext
from wotk.config_store import ConfigStore, safe_name
from wotk.features.individual import IndividualEngine
from wotk.features.login import LoginEngine, LoginSettings
from wotk.features.multi_instance import MultiInstanceEngine
from wotk.features.mysteriland import MysterilandEngine
from wotk.features.supremacy import SupremacyEngine
from wotk.features.war import WarEngine
from wotk.gui.common import (
    CoordinateEditor,
    GlobalTaskController,
    JsonEditor,
    RegionEditor,
    UiBus,
    timestamped,
)
from wotk.gui.templates import (
    INDIVIDUAL_COORD_NAMES,
    INDIVIDUAL_TEMPLATE,
    LOGIN_ACCOUNTS_TEMPLATE,
    LOGIN_TEMPLATE,
    MYSTERILAND_TEMPLATE,
    MYST_STAGE_NAMES,
    MYST_STATIC_NAMES,
    SUP_COORD_NAMES,
    SUPREMACY_TEMPLATE,
    WAR_COORD_NAMES,
    WAR_REGION_NAMES,
    WAR_TEMPLATE,
)
from wotk.logging_setup import configure_logging
from wotk.models import LoginAccount, QuestDelays, SupremacySettings, WarSettings


class ProfilePanel(ttk.Frame):
    def __init__(self, master, app: "WotkApp", title: str, store_path: str, template: dict):
        super().__init__(master, padding=10)
        self.app = app
        self.store_path = store_path
        self.template = template

        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text=title, font=("TkDefaultFont", 13, "bold")).pack(side="left")
        ttk.Label(header, text="Profile").pack(side="left", padx=(20, 4))
        self.profile_var = tk.StringVar(value="default")
        ttk.Entry(header, textvariable=self.profile_var, width=18).pack(side="left")
        ttk.Button(header, text="Save", command=self.save_profile).pack(side="left", padx=3)
        ttk.Button(header, text="Load", command=self.load_profile).pack(side="left", padx=3)
        ttk.Button(header, text="Reset Template", command=self.reset_template).pack(side="left", padx=3)
        ttk.Button(header, text="STOP", command=self.app.controller.stop).pack(side="right")

    def relative_profile(self) -> str:
        return f"{self.store_path}/{safe_name(self.profile_var.get())}.json"

    def save_profile(self) -> None:
        try:
            payload = self.payload_for_save()
            path = self.app.store.save_json(self.relative_profile(), payload)
            self.app.bus.log(f"Saved profile: {path}")
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc), parent=self)

    def load_profile(self) -> None:
        try:
            data = self.app.store.load_json(self.relative_profile())
            if data is None:
                raise FileNotFoundError(f"Profile not found: {self.relative_profile()}")
            self.apply_payload(data)
            self.app.bus.log(f"Loaded profile: {self.relative_profile()}")
        except Exception as exc:
            messagebox.showerror("Load failed", str(exc), parent=self)

    def reset_template(self) -> None:
        self.apply_payload(json.loads(json.dumps(self.template)))

    def payload_for_save(self) -> dict:
        raise NotImplementedError

    def apply_payload(self, data: dict) -> None:
        raise NotImplementedError


class LoginPanel(ProfilePanel):
    def __init__(self, master, app):
        super().__init__(master, app, "Auto Login / Register", "login", LOGIN_TEMPLATE)
        ttk.Label(
            self,
            text="Passwords stay in memory only and are not saved by the Profile Save button.",
        ).pack(anchor="w", pady=(0, 6))
        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body)
        right = ttk.Frame(body)
        body.add(left, weight=1)
        body.add(right, weight=1)
        self.config_editor = JsonEditor(left, "Browser settings + coordinates", LOGIN_TEMPLATE, height=22)
        self.config_editor.pack(fill="both", expand=True)
        self.accounts_editor = JsonEditor(right, "Accounts (never saved by Profile Save)", LOGIN_ACCOUNTS_TEMPLATE, height=22)
        self.accounts_editor.pack(fill="both", expand=True)
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Configure Coordinates", command=self.configure_coords).pack(side="left")
        ttk.Button(actions, text="Run Login", command=self.run).pack(side="right")

    def payload_for_save(self) -> dict:
        return self.config_editor.get_json()

    def apply_payload(self, data: dict) -> None:
        self.config_editor.set_json(data)

    def configure_coords(self) -> None:
        try:
            data = self.config_editor.get_json()
            coords = data.setdefault("coordinates", {})
            CoordinateEditor(self, coords.keys() or LOGIN_TEMPLATE["coordinates"].keys(), coords, lambda value: self._set_coords(data, value))
        except Exception as exc:
            messagebox.showerror("Configuration error", str(exc), parent=self)

    def _set_coords(self, data: dict, coords: dict) -> None:
        data["coordinates"] = coords
        self.config_editor.set_json(data)

    def run(self) -> None:
        try:
            cfg = self.config_editor.get_json()
            accounts_raw = self.accounts_editor.get_json()
            if not isinstance(accounts_raw, list):
                raise ValueError("Accounts JSON must be a list")
            accounts = [LoginAccount.from_dict(item) for item in accounts_raw]
            settings = LoginSettings(**cfg["settings"])
            coords = cfg["coordinates"]
        except Exception as exc:
            messagebox.showerror("Invalid input", str(exc), parent=self)
            return

        def target(token, log):
            ctx = AutomationContext(PyAutoGuiBackend(), token, log)
            return LoginEngine(ctx, coords, settings).run(accounts)

        self.app.start_task("Auto Login", target)


class IndividualPanel(ProfilePanel):
    def __init__(self, master, app):
        super().__init__(master, app, "Auto Quest - Individual", "individual", INDIVIDUAL_TEMPLATE)
        self.editor = JsonEditor(self, "Individual configuration", INDIVIDUAL_TEMPLATE, height=26)
        self.editor.pack(fill="both", expand=True)
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Configure Coordinates", command=self.configure_coords).pack(side="left")
        ttk.Button(actions, text="Run", command=self.run).pack(side="right")

    def payload_for_save(self):
        return self.editor.get_json()

    def apply_payload(self, data):
        self.editor.set_json(data)

    def configure_coords(self):
        data = self.editor.get_json()
        coords = data.setdefault("coordinates", {})
        CoordinateEditor(self, INDIVIDUAL_COORD_NAMES, coords, lambda value: self._set_coords(data, value))

    def _set_coords(self, data, coords):
        data["coordinates"] = coords
        self.editor.set_json(data)

    def run(self):
        try:
            cfg = self.editor.get_json()
            stages = int(cfg.get("stages", 10))
            delays = QuestDelays(**cfg.get("delays", {}))
            coords = cfg["coordinates"]
        except Exception as exc:
            messagebox.showerror("Invalid input", str(exc), parent=self)
            return

        def target(token, log):
            ctx = AutomationContext(PyAutoGuiBackend(), token, log)
            return IndividualEngine(ctx, coords, delays).run(stages=stages)

        self.app.start_task("Individual", target)


class MysterilandPanel(ProfilePanel):
    def __init__(self, master, app):
        super().__init__(master, app, "Auto Quest - Mysteriland", "mysteriland", MYSTERILAND_TEMPLATE)
        self.editor = JsonEditor(self, "Mysteriland configuration (save one profile per day if coordinates differ)", MYSTERILAND_TEMPLATE, height=25)
        self.editor.pack(fill="both", expand=True)
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Static Coordinates", command=self.configure_static).pack(side="left", padx=2)
        ttk.Button(actions, text="Stage Coordinates", command=self.configure_stage).pack(side="left", padx=2)
        ttk.Button(actions, text="Swipe", command=self.swipe).pack(side="right", padx=2)
        ttk.Button(actions, text="Run Stages", command=self.run).pack(side="right", padx=2)

    def payload_for_save(self):
        return self.editor.get_json()

    def apply_payload(self, data):
        self.editor.set_json(data)

    def configure_static(self):
        data = self.editor.get_json()
        values = data.setdefault("static_coordinates", {})
        CoordinateEditor(self, MYST_STATIC_NAMES, values, lambda v: self._set(data, "static_coordinates", v))

    def configure_stage(self):
        data = self.editor.get_json()
        day = str(data.get("day", "senin")).lower().strip()
        by_day = data.setdefault("stage_coordinates_by_day", {})
        values = by_day.setdefault(day, {})

        def save_day(value):
            by_day[day] = value
            data["stage_coordinates_by_day"] = by_day
            self.editor.set_json(data)

        CoordinateEditor(self, MYST_STAGE_NAMES, values, save_day)

    def _set(self, data, key, value):
        data[key] = value
        self.editor.set_json(data)

    def _engine_target(self, operation: str):
        cfg = self.editor.get_json()
        static = cfg["static_coordinates"]
        day = str(cfg.get("day", "senin")).lower().strip()
        by_day = cfg.get("stage_coordinates_by_day", {})
        stage = by_day.get(day, cfg.get("stage_coordinates", {}))
        if not stage:
            raise ValueError(f"No stage coordinates configured for day: {day}")
        delay = float(cfg.get("delay", 0.5))
        stages = int(cfg.get("stages", 5))
        swipe_stage = int(cfg.get("swipe_stage", 5))
        swipe_count = int(cfg.get("swipe_count", 1))

        def target(token, log):
            ctx = AutomationContext(PyAutoGuiBackend(), token, log)
            engine = MysterilandEngine(ctx, static, stage, delay)
            if operation == "run":
                return engine.run(stages=stages)
            return engine.swipe(stage=swipe_stage, count=swipe_count)

        return target

    def run(self):
        try:
            target = self._engine_target("run")
        except Exception as exc:
            messagebox.showerror("Invalid input", str(exc), parent=self)
            return
        self.app.start_task("Mysteriland", target)

    def swipe(self):
        try:
            target = self._engine_target("swipe")
        except Exception as exc:
            messagebox.showerror("Invalid input", str(exc), parent=self)
            return
        self.app.start_task("Mysteriland Swipe", target)


class SupremacyPanel(ProfilePanel):
    def __init__(self, master, app):
        super().__init__(master, app, "Auto Quest - Supremacy", "supremacy", SUPREMACY_TEMPLATE)
        self.editor = JsonEditor(self, "Supremacy configuration", SUPREMACY_TEMPLATE, height=26)
        self.editor.pack(fill="both", expand=True)
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Configure Coordinates", command=self.configure_coords).pack(side="left")
        ttk.Button(actions, text="Run", command=self.run).pack(side="right")

    def payload_for_save(self):
        return self.editor.get_json()

    def apply_payload(self, data):
        self.editor.set_json(data)

    def configure_coords(self):
        data = self.editor.get_json()
        values = data.setdefault("coordinates", {})
        CoordinateEditor(self, SUP_COORD_NAMES, values, lambda v: self._set_coords(data, v))

    def _set_coords(self, data, value):
        data["coordinates"] = value
        self.editor.set_json(data)

    def run(self):
        try:
            cfg = self.editor.get_json()
            settings = SupremacySettings(**cfg.get("settings", {}))
            coords = cfg["coordinates"]
            action_delay = float(cfg.get("action_delay", 1.5))
            hero_delay = float(cfg.get("hero_delay", 0.5))
        except Exception as exc:
            messagebox.showerror("Invalid input", str(exc), parent=self)
            return

        def target(token, log):
            ctx = AutomationContext(PyAutoGuiBackend(), token, log)
            return SupremacyEngine(ctx, coords, settings, action_delay, hero_delay).run()

        self.app.start_task("Supremacy", target)


class WarPanel(ProfilePanel):
    def __init__(self, master, app):
        super().__init__(master, app, "Auto War + OCR March/Assault", "war/settings", WAR_TEMPLATE)
        self.editor = JsonEditor(self, "War configuration", WAR_TEMPLATE, height=25)
        self.editor.pack(fill="both", expand=True)
        actions = ttk.Frame(self)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Coordinates", command=self.configure_coords).pack(side="left", padx=2)
        ttk.Button(actions, text="OCR Regions", command=self.configure_regions).pack(side="left", padx=2)
        ttk.Button(actions, text="Run", command=self.run).pack(side="right")

    def payload_for_save(self):
        return self.editor.get_json()

    def apply_payload(self, data):
        self.editor.set_json(data)

    def configure_coords(self):
        data = self.editor.get_json()
        values = data.setdefault("coordinates", {})
        CoordinateEditor(self, WAR_COORD_NAMES, values, lambda v: self._set(data, "coordinates", v))

    def configure_regions(self):
        data = self.editor.get_json()
        values = data.setdefault("ocr_regions", {})
        RegionEditor(self, WAR_REGION_NAMES, values, lambda v: self._set(data, "ocr_regions", v))

    def _set(self, data, key, value):
        data[key] = value
        self.editor.set_json(data)

    def run(self):
        try:
            cfg = self.editor.get_json()
            settings = WarSettings(**cfg["settings"])
            runtime = cfg.get("runtime", {})
            coords = cfg["coordinates"]
            regions = cfg["ocr_regions"]
            max_cycles = runtime.get("max_cycles")
            max_cycles = int(max_cycles) if max_cycles is not None else None
        except Exception as exc:
            messagebox.showerror("Invalid input", str(exc), parent=self)
            return

        def target(token, log):
            ctx = AutomationContext(PyAutoGuiBackend(), token, log)
            ocr = OcrService(ctx, tesseract_cmd=runtime.get("tesseract_cmd") or None)
            engine = WarEngine(
                ctx,
                coords,
                regions,
                settings,
                ocr,
                default_delay=float(runtime.get("default_delay", 0.5)),
                combat_delay=float(runtime.get("combat_delay", 2.0)),
                tab_delay=float(runtime.get("tab_delay", 0.8)),
                march_check_interval_seconds=float(runtime.get("march_check_interval_seconds", 300)),
            )
            return engine.run(
                max_cycles=max_cycles,
                initialize_maps=bool(runtime.get("initialize_maps", True)),
            )

        self.app.start_task("Auto War", target)


class MultiInstancePanel(ttk.Frame):
    def __init__(self, master, app: "WotkApp"):
        super().__init__(master, padding=10)
        self.app = app
        ttk.Label(self, text="Multi-Instance (Sandboxie-Plus)", font=("TkDefaultFont", 13, "bold")).pack(anchor="w")
        ttk.Label(
            self,
            text=(
                "Coordinates are client-relative per instance. Worker threads run concurrently, "
                "but physical mouse/keyboard input is serialized to prevent cross-instance misclicks."
            ),
            wraplength=950,
        ).pack(anchor="w", pady=(4, 12))
        form = ttk.Frame(self)
        form.pack(fill="x")
        self.master_var = tk.StringVar()
        self.instances_var = tk.StringVar()
        for row, (label, var, directory) in enumerate(
            (("master_config.json", self.master_var, False), ("Instances folder", self.instances_var, True))
        ):
            ttk.Label(form, text=label, width=20).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(form, textvariable=var).grid(row=row, column=1, sticky="ew", pady=4)
            command = (lambda v=var: self._browse_dir(v)) if directory else (lambda v=var: self._browse_file(v))
            ttk.Button(form, text="Browse", command=command).grid(row=row, column=2, padx=4)
        form.columnconfigure(1, weight=1)
        self.launch_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(self, text="Launch game instances through existing Sandboxie boxes before running", variable=self.launch_var).pack(anchor="w", pady=8)
        buttons = ttk.Frame(self)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="STOP", command=self.app.controller.stop).pack(side="right", padx=3)
        ttk.Button(buttons, text="Run Multi-Instance", command=self.run).pack(side="right", padx=3)

    def _browse_file(self, variable):
        path = filedialog.askopenfilename(parent=self, filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if path:
            variable.set(path)

    def _browse_dir(self, variable):
        path = filedialog.askdirectory(parent=self)
        if path:
            variable.set(path)

    def run(self):
        master_path = self.master_var.get().strip()
        instances_dir = self.instances_var.get().strip()
        if not master_path or not instances_dir:
            messagebox.showerror("Missing input", "Select master_config.json and the instances folder.", parent=self)
            return

        launch = bool(self.launch_var.get())

        def target(token, log):
            backend = PyAutoGuiBackend()
            engine = MultiInstanceEngine.from_files(backend, token, log, master_path, instances_dir)
            return engine.run(launch=launch)

        self.app.start_task("Multi-Instance", target)


class WotkApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("WOTK Mod Control Center 2.0")
        self.geometry("1180x860")
        self.minsize(980, 700)
        self.store = ConfigStore()
        self.logger = configure_logging(self.store.log_dir)
        self.bus = UiBus()
        self.controller = GlobalTaskController(self.bus)
        self.status_var = tk.StringVar(value="Ready")

        top = ttk.Frame(self, padding=(10, 8))
        top.pack(fill="x")
        ttk.Label(top, text="WOTK Mod", font=("TkDefaultFont", 18, "bold")).pack(side="left")
        ttk.Label(top, textvariable=self.status_var).pack(side="right")

        panes = ttk.Panedwindow(self, orient="vertical")
        panes.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        notebook = ttk.Notebook(panes)
        panes.add(notebook, weight=4)
        for label, cls in (
            ("Login", LoginPanel),
            ("Individual", IndividualPanel),
            ("Mysteriland", MysterilandPanel),
            ("Supremacy", SupremacyPanel),
            ("Auto War", WarPanel),
            ("Multi-Instance", MultiInstancePanel),
        ):
            panel = cls(notebook, self)
            notebook.add(panel, text=label)

        log_frame = ttk.Frame(panes)
        panes.add(log_frame, weight=1)
        ttk.Label(log_frame, text="Activity Log", font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.log_text = scrolledtext.ScrolledText(log_frame, height=9, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True)
        self.after(100, self._poll_bus)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def start_task(self, label, target):
        try:
            self.controller.start(label, target)
        except Exception as exc:
            messagebox.showerror("Cannot start", str(exc), parent=self)

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", timestamped(message) + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
        self.logger.info(message)

    def _poll_bus(self):
        for kind, payload in self.bus.drain():
            if kind == "log":
                self._append_log(payload)
            elif kind == "state":
                label, state = payload
                self.status_var.set(f"{label}: {state}")
            elif kind == "error":
                title, message = payload
                messagebox.showerror(title, message, parent=self)
            elif kind == "success":
                title, message = payload
                messagebox.showinfo(title, message, parent=self)
        self.after(100, self._poll_bus)

    def _on_close(self):
        if self.controller.running:
            if not messagebox.askyesno("Exit", "Automation is running. Stop it and exit?", parent=self):
                return
            self.controller.stop()
        self.destroy()


def run_gui() -> None:
    WotkApp().mainloop()
