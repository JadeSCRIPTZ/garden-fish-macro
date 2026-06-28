from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Literal

try:
    import pyautogui
except ImportError:
    pyautogui = None

from .config import MacroConfig, config_path, load_config, save_config
from .runner import GardenMacroRunner

LogLevel = Literal["accent", "ok", "warn", "error", "dim"]


class GardenMacroApp:
    COLORS = {
        "accent": "#7dd3fc",
        "ok": "#86efac",
        "warn": "#fcd34d",
        "error": "#fca5a5",
        "dim": "#94a3b8",
    }

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Garden Fish Macro")
        self.root.geometry("720x640")
        self.root.configure(bg="#0f172a")
        self.config = load_config()
        self.runner = GardenMacroRunner(self._log, self._set_state)
        self._build_ui()
        self._bind_hotkeys()

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0f172a")
        style.configure("TLabel", background="#0f172a", foreground="#e2e8f0")
        style.configure("TButton", padding=6)
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))

        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Garden Fish Vacuum Macro", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            frame,
            text="F8 start/stop  |  F9 sample fish pixel  |  F10 sample row-end pixel  |  Esc stop",
        ).pack(anchor="w", pady=(0, 8))

        self.state_var = tk.StringVar(value="IDLE")
        ttk.Label(frame, textvariable=self.state_var, font=("Consolas", 12, "bold")).pack(anchor="w")

        stats = ttk.Frame(frame)
        stats.pack(fill="x", pady=8)
        self.rows_var = tk.StringVar(value="Rows: 0")
        self.fish_var = tk.StringVar(value="Fish runs: 0")
        self.scans_var = tk.StringVar(value="Scans: 0")
        for var in (self.rows_var, self.fish_var, self.scans_var):
            ttk.Label(stats, textvariable=var).pack(side="left", padx=(0, 16))

        form = ttk.Frame(frame)
        form.pack(fill="x", pady=8)

        self.fish_x = self._entry(form, "Fish pixel X", str(self.config.fish_pixel.x), 0)
        self.fish_y = self._entry(form, "Fish pixel Y", str(self.config.fish_pixel.y), 1)
        self.fish_r = self._entry(form, "Fish R", str(self.config.fish_pixel.rgb[0]), 2)
        self.fish_g = self._entry(form, "Fish G", str(self.config.fish_pixel.rgb[1]), 3)
        self.fish_b = self._entry(form, "Fish B", str(self.config.fish_pixel.rgb[2]), 4)

        self.row_x = self._entry(form, "Row-end X", str(self.config.row_end_pixel.x), 0, 2)
        self.row_y = self._entry(form, "Row-end Y", str(self.config.row_end_pixel.y), 1, 2)
        self.row_r = self._entry(form, "Row-end R", str(self.config.row_end_pixel.rgb[0]), 2, 2)
        self.row_g = self._entry(form, "Row-end G", str(self.config.row_end_pixel.rgb[1]), 3, 2)
        self.row_b = self._entry(form, "Row-end B", str(self.config.row_end_pixel.rgb[2]), 4, 2)

        self.forward = self._entry(form, "Forward duration (s)", str(self.config.forward_duration), 0, 4)
        self.vacuum = self._entry(form, "Vacuum duration (s)", str(self.config.vacuum_duration), 1, 4)
        self.tp_wait = self._entry(form, "TP wait (s)", str(self.config.tp_wait), 2, 4)
        self.home_wait = self._entry(form, "Home wait (s)", str(self.config.home_wait), 3, 4)

        buttons = ttk.Frame(frame)
        buttons.pack(fill="x", pady=8)
        ttk.Button(buttons, text="Save Config", command=self._save_config).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Start (F8)", command=self.start).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Stop (Esc)", command=self.stop).pack(side="left")

        ttk.Label(frame, text=f"Config: {config_path()}").pack(anchor="w")
        self.log = tk.Text(frame, height=16, bg="#020617", fg="#e2e8f0", wrap="word")
        self.log.pack(fill="both", expand=True, pady=(8, 0))
        self.log.configure(state="disabled")
        self._log("Ready. Calibrate pixel positions with F9/F10 while hovering the HUD corner.", "dim")

    def _entry(self, parent: ttk.Frame, label: str, value: str, col: int, row: int = 0) -> tk.StringVar:
        ttk.Label(parent, text=label).grid(row=row, column=col * 2, sticky="w", padx=(0, 6), pady=2)
        var = tk.StringVar(value=value)
        ttk.Entry(parent, textvariable=var, width=8).grid(row=row, column=col * 2 + 1, sticky="w", padx=(0, 12), pady=2)
        return var

    def _bind_hotkeys(self) -> None:
        self.root.bind("<F8>", lambda _e: self.toggle())
        self.root.bind("<Escape>", lambda _e: self.stop())
        self.root.bind("<F9>", lambda _e: self._sample_pixel("fish"))
        self.root.bind("<F10>", lambda _e: self._sample_pixel("row"))
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _log(self, message: str, level: LogLevel = "dim") -> None:
        def write() -> None:
            self.log.configure(state="normal")
            self.log.insert("end", message + "\n", level)
            self.log.tag_configure(level, foreground=self.COLORS[level])
            self.log.see("end")
            self.log.configure(state="disabled")

        self.root.after(0, write)

    def _set_state(self, state: str) -> None:
        self.root.after(0, lambda: self.state_var.set(state))

    def _refresh_stats(self) -> None:
        if self.runner.running:
            self.rows_var.set(f"Rows: {self.runner.stats.rows_completed}")
            self.fish_var.set(f"Fish runs: {self.runner.stats.fish_collected}")
            self.scans_var.set(f"Scans: {self.runner.stats.scans}")
            self.root.after(200, self._refresh_stats)

    def _build_config_from_ui(self) -> MacroConfig:
        from .detector import PixelTarget

        config = MacroConfig(
            fish_pixel=PixelTarget(
                int(self.fish_x.get()),
                int(self.fish_y.get()),
                (int(self.fish_r.get()), int(self.fish_g.get()), int(self.fish_b.get())),
                self.config.fish_pixel.tolerance,
            ),
            row_end_pixel=PixelTarget(
                int(self.row_x.get()),
                int(self.row_y.get()),
                (int(self.row_r.get()), int(self.row_g.get()), int(self.row_b.get())),
                self.config.row_end_pixel.tolerance,
            ),
            poll_interval=self.config.poll_interval,
            forward_duration=float(self.forward.get()),
            tp_delay=self.config.tp_delay,
            tp_wait=float(self.tp_wait.get()),
            vacuum_duration=float(self.vacuum.get()),
            home_wait=float(self.home_wait.get()),
            fish_cooldown=self.config.fish_cooldown,
            row_end_cooldown=self.config.row_end_cooldown,
            keys=self.config.keys,
        )
        if pyautogui is not None:
            screen = pyautogui.size()
            config.validate(screen.width, screen.height)
        else:
            config.validate()
        return config

    def _save_config(self) -> None:
        try:
            self.config = self._build_config_from_ui()
            path = save_config(self.config)
            self._log(f"Saved config to {path}.", "ok")
        except Exception as exc:
            messagebox.showerror("Config error", str(exc))

    def _sample_pixel(self, target: str) -> None:
        if pyautogui is None:
            messagebox.showerror("Missing dependency", "Install requirements first.")
            return
        x, y = pyautogui.position()
        rgb = pyautogui.pixel(x, y)
        if target == "fish":
            self.fish_x.set(str(x))
            self.fish_y.set(str(y))
            self.fish_r.set(str(rgb[0]))
            self.fish_g.set(str(rgb[1]))
            self.fish_b.set(str(rgb[2]))
            self._log(f"Sampled fish pixel at ({x}, {y}) RGB{rgb}.", "accent")
        else:
            self.row_x.set(str(x))
            self.row_y.set(str(y))
            self.row_r.set(str(rgb[0]))
            self.row_g.set(str(rgb[1]))
            self.row_b.set(str(rgb[2]))
            self._log(f"Sampled row-end pixel at ({x}, {y}) RGB{rgb}.", "accent")

    def start(self) -> None:
        if self.runner.running:
            return
        try:
            self.config = self._build_config_from_ui()
            self.runner.start(self.config)
            self._refresh_stats()
            self._log("Macro running.", "ok")
        except Exception as exc:
            messagebox.showerror("Start failed", str(exc))

    def stop(self) -> None:
        if self.runner.running:
            self.runner.stop()
            self._log("Stop requested.", "dim")

    def toggle(self) -> None:
        if self.runner.running:
            self.stop()
        else:
            self.start()

    def _on_close(self) -> None:
        self.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    GardenMacroApp().run()
