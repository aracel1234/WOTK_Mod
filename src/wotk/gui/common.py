from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, scrolledtext, ttk
from typing import Any, Callable, Iterable

from wotk.automation.backend import PyAutoGuiBackend
from wotk.automation.runtime import StopRequested, StopToken
from wotk.models import Point, Region


class UiBus:
    def __init__(self):
        self._queue: queue.Queue[tuple[str, Any]] = queue.Queue()

    def log(self, message: str) -> None:
        self._queue.put(("log", str(message)))

    def state(self, label: str, state: str) -> None:
        self._queue.put(("state", (label, state)))

    def error(self, title: str, message: str) -> None:
        self._queue.put(("error", (title, message)))

    def success(self, title: str, message: str) -> None:
        self._queue.put(("success", (title, message)))

    def drain(self) -> list[tuple[str, Any]]:
        items: list[tuple[str, Any]] = []
        while True:
            try:
                items.append(self._queue.get_nowait())
            except queue.Empty:
                return items


class GlobalTaskController:
    """Runs one top-level automation at a time and keeps Tk operations on the UI thread."""

    def __init__(self, bus: UiBus):
        self.bus = bus
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._stop_token: StopToken | None = None
        self._label = ""

    @property
    def running(self) -> bool:
        with self._lock:
            return bool(self._thread and self._thread.is_alive())

    def start(self, label: str, target: Callable[[StopToken, Callable[[str], None]], Any]) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                raise RuntimeError(f"Another automation is already running: {self._label}")
            token = StopToken()
            self._stop_token = token
            self._label = label

            def worker() -> None:
                self.bus.state(label, "Running")
                self.bus.log(f"=== {label} started ===")
                try:
                    result = target(token, self.bus.log)
                    if token.stopped:
                        self.bus.state(label, "Stopped")
                        self.bus.log(f"=== {label} stopped ===")
                    else:
                        self.bus.state(label, "Completed")
                        self.bus.log(f"=== {label} completed: {result!r} ===")
                except StopRequested:
                    self.bus.state(label, "Stopped")
                    self.bus.log(f"=== {label} stopped by user ===")
                except Exception as exc:
                    self.bus.state(label, "Error")
                    self.bus.log(f"ERROR {label}: {exc}")
                    self.bus.error(label, str(exc))

            self._thread = threading.Thread(target=worker, name=f"wotk-{label}", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        with self._lock:
            token = self._stop_token
            label = self._label
        if token:
            token.stop()
            self.bus.log(f"Stop requested for {label}")


class JsonEditor(ttk.Frame):
    def __init__(self, master, title: str, initial: Any, height: int = 16):
        super().__init__(master)
        ttk.Label(self, text=title, font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        self.text = scrolledtext.ScrolledText(self, height=height, wrap="none", undo=True)
        self.text.pack(fill="both", expand=True, pady=(4, 0))
        self.set_json(initial)

    def get_json(self) -> Any:
        raw = self.text.get("1.0", "end").strip()
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}") from exc

    def set_json(self, value: Any) -> None:
        self.text.delete("1.0", "end")
        self.text.insert("1.0", json.dumps(value, indent=2, ensure_ascii=False))


class CoordinateEditor(tk.Toplevel):
    def __init__(
        self,
        master,
        names: Iterable[str],
        values: dict[str, Any],
        on_save: Callable[[dict[str, dict[str, int]]], None],
    ):
        super().__init__(master)
        self.title("Coordinate Editor")
        self.geometry("650x620")
        self.transient(master)
        self.on_save = on_save
        self.entries: dict[str, tuple[ttk.Entry, ttk.Entry]] = {}

        wrapper = ttk.Frame(self, padding=10)
        wrapper.pack(fill="both", expand=True)
        canvas = tk.Canvas(wrapper, highlightthickness=0)
        scrollbar = ttk.Scrollbar(wrapper, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for row, name in enumerate(names):
            raw = values.get(name, {"x": 0, "y": 0})
            try:
                point = Point.from_raw(raw)
            except Exception:
                point = Point(0, 0)
            ttk.Label(inner, text=name, width=28).grid(row=row, column=0, sticky="w", padx=4, pady=3)
            x_entry = ttk.Entry(inner, width=8)
            y_entry = ttk.Entry(inner, width=8)
            x_entry.insert(0, str(point.x))
            y_entry.insert(0, str(point.y))
            x_entry.grid(row=row, column=1, padx=4)
            y_entry.grid(row=row, column=2, padx=4)
            ttk.Button(
                inner,
                text="Capture (2s)",
                command=lambda n=name: self._capture(n),
            ).grid(row=row, column=3, padx=4)
            self.entries[name] = (x_entry, y_entry)

        footer = ttk.Frame(self, padding=10)
        footer.pack(fill="x")
        ttk.Label(footer, text="Move the mouse to the desired point after pressing Capture.").pack(side="left")
        ttk.Button(footer, text="Save", command=self._save).pack(side="right", padx=4)
        ttk.Button(footer, text="Cancel", command=self.destroy).pack(side="right", padx=4)

    def _capture(self, name: str) -> None:
        self.iconify()

        def finish() -> None:
            try:
                position = PyAutoGuiBackend().position()
                x_entry, y_entry = self.entries[name]
                for entry, value in ((x_entry, position.x), (y_entry, position.y)):
                    entry.delete(0, "end")
                    entry.insert(0, str(value))
            except Exception as exc:
                messagebox.showerror("Capture failed", str(exc), parent=self)
            finally:
                self.deiconify()
                self.lift()

        self.after(2000, finish)

    def _save(self) -> None:
        output: dict[str, dict[str, int]] = {}
        try:
            for name, (x_entry, y_entry) in self.entries.items():
                output[name] = {"x": int(x_entry.get()), "y": int(y_entry.get())}
        except ValueError:
            messagebox.showerror("Invalid coordinate", "X and Y must be integers.", parent=self)
            return
        self.on_save(output)
        self.destroy()


class RegionEditor(tk.Toplevel):
    def __init__(
        self,
        master,
        names: Iterable[str],
        values: dict[str, Any],
        on_save: Callable[[dict[str, dict[str, int]]], None],
    ):
        super().__init__(master)
        self.title("OCR Region Editor")
        self.geometry("780x520")
        self.transient(master)
        self.on_save = on_save
        self.entries: dict[str, tuple[ttk.Entry, ttk.Entry, ttk.Entry, ttk.Entry]] = {}
        self.top_left: dict[str, Point] = {}

        frame = ttk.Frame(self, padding=10)
        frame.pack(fill="both", expand=True)
        headers = ("Region", "X", "Y", "Width", "Height", "Capture")
        for col, label in enumerate(headers):
            ttk.Label(frame, text=label, font=("TkDefaultFont", 9, "bold")).grid(
                row=0, column=col, padx=4, pady=4
            )
        for row, name in enumerate(names, start=1):
            raw = values.get(name, {"x": 0, "y": 0, "width": 0, "height": 0})
            try:
                region = Region.from_raw(raw)
            except Exception:
                region = Region(0, 0, 0, 0)
            ttk.Label(frame, text=name, width=24).grid(row=row, column=0, sticky="w", padx=4, pady=4)
            entries = []
            for col, value in enumerate((region.x, region.y, region.width, region.height), start=1):
                entry = ttk.Entry(frame, width=8)
                entry.insert(0, str(value))
                entry.grid(row=row, column=col, padx=3)
                entries.append(entry)
            ttk.Button(frame, text="Set TL", command=lambda n=name: self._capture_tl(n)).grid(row=row, column=5, padx=2)
            ttk.Button(frame, text="Set BR", command=lambda n=name: self._capture_br(n)).grid(row=row, column=6, padx=2)
            self.entries[name] = tuple(entries)  # type: ignore[assignment]

        footer = ttk.Frame(self, padding=10)
        footer.pack(fill="x")
        ttk.Label(footer, text="Capture top-left first, then bottom-right. Each capture waits 2 seconds.").pack(side="left")
        ttk.Button(footer, text="Save", command=self._save).pack(side="right", padx=4)
        ttk.Button(footer, text="Cancel", command=self.destroy).pack(side="right", padx=4)

    def _get_pointer_after_delay(self, callback: Callable[[Point], None]) -> None:
        self.iconify()

        def finish() -> None:
            try:
                callback(PyAutoGuiBackend().position())
            except Exception as exc:
                messagebox.showerror("Capture failed", str(exc), parent=self)
            finally:
                self.deiconify()
                self.lift()

        self.after(2000, finish)

    def _capture_tl(self, name: str) -> None:
        def update(point: Point) -> None:
            self.top_left[name] = point
            x, y, _w, _h = self.entries[name]
            for entry, value in ((x, point.x), (y, point.y)):
                entry.delete(0, "end")
                entry.insert(0, str(value))

        self._get_pointer_after_delay(update)

    def _capture_br(self, name: str) -> None:
        def update(point: Point) -> None:
            x_entry, y_entry, w_entry, h_entry = self.entries[name]
            try:
                tl = self.top_left.get(name, Point(int(x_entry.get()), int(y_entry.get())))
            except ValueError:
                raise ValueError("Set a valid top-left point first")
            x, y = min(tl.x, point.x), min(tl.y, point.y)
            width, height = abs(point.x - tl.x), abs(point.y - tl.y)
            for entry, value in ((x_entry, x), (y_entry, y), (w_entry, width), (h_entry, height)):
                entry.delete(0, "end")
                entry.insert(0, str(value))

        self._get_pointer_after_delay(update)

    def _save(self) -> None:
        output: dict[str, dict[str, int]] = {}
        try:
            for name, entries in self.entries.items():
                x, y, width, height = (int(entry.get()) for entry in entries)
                output[name] = {"x": x, "y": y, "width": width, "height": height}
        except ValueError:
            messagebox.showerror("Invalid region", "All region values must be integers.", parent=self)
            return
        self.on_save(output)
        self.destroy()


def timestamped(message: str) -> str:
    return f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
