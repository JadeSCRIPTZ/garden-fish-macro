from __future__ import annotations

import tkinter as tk
from tkinter import messagebox
from typing import Literal

try:
    import pyautogui
except ImportError:
    pyautogui = None

from garden_macro.config import MacroConfig, config_path, load_config, save_config
from garden_macro.runner import GardenMacroRunner

LogLevel = Literal["accent", "ok", "warn", "error", "dim"]


class GardenMacroApp:
    BG = "#111827"
    CARD = "#1f2937"
    BORDER = "#374151"
    TEXT = "#f3f4f6"
    MUTED = "#9ca3af"
    GREEN = "#22c55e"
    RED = "#ef4444"
    BLUE = "#3b82f6"
    AMBER = "#f59e0b"

    LOG_COLORS = {
        "accent": "#60a5fa",
        "ok": "#4ade80",
        "warn": "#fbbf24",
        "error": "#f87171",
        "dim": "#6b7280",
    }

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("Garden Farm Macro")
        self.root.geometry("460x620")
        self.root.resizable(False, False)
        self.root.configure(bg=self.BG)
        self.config = load_config()
        self.runner = GardenMacroRunner(self._log, self._set_state)
        self._build_ui()
        self._bind_hotkeys()

    def _build_ui(self) -> None:
        header = tk.Frame(self.root, bg=self.BG, padx=20, pady=18)
        header.pack(fill="x")
        tk.Label(
            header,
            text="Garden Farm",
            font=("Segoe UI", 22, "bold"),
            fg=self.TEXT,
            bg=self.BG,
        ).pack(anchor="w")
        tk.Label(
            header,
            text="Auto farm rows with pixel detection",
            font=("Segoe UI", 10),
            fg=self.MUTED,
            bg=self.BG,
        ).pack(anchor="w", pady=(2, 0))

        status_card = tk.Frame(self.root, bg=self.CARD, padx=16, pady=14, highlightthickness=1, highlightbackground=self.BORDER)
        status_card.pack(fill="x", padx=20, pady=(0, 12))
        tk.Label(status_card, text="Status", font=("Segoe UI", 9), fg=self.MUTED, bg=self.CARD).pack(anchor="w")
        self.state_var = tk.StringVar(value="Idle")
        self.state_label = tk.Label(
            status_card,
            textvariable=self.state_var,
            font=("Segoe UI", 16, "bold"),
            fg=self.AMBER,
            bg=self.CARD,
        )
        self.state_label.pack(anchor="w", pady=(4, 8))

        stats_row = tk.Frame(status_card, bg=self.CARD)
        stats_row.pack(fill="x")
        self.rows_var = tk.StringVar(value="0 rows")
        self.scans_var = tk.StringVar(value="0 scans")
        for var in (self.rows_var, self.scans_var):
            tk.Label(
                stats_row,
                textvariable=var,
                font=("Segoe UI", 10),
                fg=self.MUTED,
                bg=self.CARD,
            ).pack(side="left", padx=(0, 16))

        self.start_btn = tk.Button(
            self.root,
            text="Start  F8",
            font=("Segoe UI", 12, "bold"),
            fg="white",
            bg=self.GREEN,
            activebackground="#16a34a",
            activeforeground="white",
            relief="flat",
            padx=20,
            pady=12,
            cursor="hand2",
            command=self.start,
        )
        self.start_btn.pack(fill="x", padx=20, pady=(0, 8))

        self.stop_btn = tk.Button(
            self.root,
            text="Stop  Esc",
            font=("Segoe UI", 11),
            fg="white",
            bg=self.RED,
            activebackground="#dc2626",
            activeforeground="white",
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.stop,
        )
        self.stop_btn.pack(fill="x", padx=20, pady=(0, 14))

        settings = tk.Frame(self.root, bg=self.CARD, padx=16, pady=14, highlightthickness=1, highlightbackground=self.BORDER)
        settings.pack(fill="x", padx=20, pady=(0, 12))
        tk.Label(settings, text="Settings", font=("Segoe UI", 11, "bold"), fg=self.TEXT, bg=self.CARD).pack(anchor="w", pady=(0, 10))

        self.forward = self._field(settings, "Forward time (s)", str(self.config.forward_duration))
        self.row_x = self._field(settings, "Pixel X", str(self.config.row_end_pixel.x))
        self.row_y = self._field(settings, "Pixel Y", str(self.config.row_end_pixel.y))
        self.row_r = self._field(settings, "Color R", str(self.config.row_end_pixel.rgb[0]))
        self.row_g = self._field(settings, "Color G", str(self.config.row_end_pixel.rgb[1]))
        self.row_b = self._field(settings, "Color B", str(self.config.row_end_pixel.rgb[2]))

        btn_row = tk.Frame(settings, bg=self.CARD)
        btn_row.pack(fill="x", pady=(10, 0))
        tk.Button(
            btn_row,
            text="Sample pixel  F9",
            font=("Segoe UI", 10),
            fg=self.TEXT,
            bg=self.BLUE,
            activebackground="#2563eb",
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._sample_pixel,
        ).pack(side="left", padx=(0, 8))
        tk.Button(
            btn_row,
            text="Save",
            font=("Segoe UI", 10),
            fg=self.TEXT,
            bg=self.BORDER,
            activebackground="#4b5563",
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._save_config,
        ).pack(side="left")

        log_card = tk.Frame(self.root, bg=self.CARD, padx=16, pady=14, highlightthickness=1, highlightbackground=self.BORDER)
        log_card.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        tk.Label(log_card, text="Log", font=("Segoe UI", 11, "bold"), fg=self.TEXT, bg=self.CARD).pack(anchor="w", pady=(0, 8))
        self.log = tk.Text(
            log_card,
            height=8,
            bg="#0b1220",
            fg=self.TEXT,
            relief="flat",
            font=("Consolas", 9),
            wrap="word",
            padx=8,
            pady=8,
        )
        self.log.pack(fill="both", expand=True)
        self.log.configure(state="disabled")
        self._log("Ready. Hover the orange HUD pixel and press F9.", "dim")

    def _field(self, parent: tk.Frame, label: str, value: str) -> tk.StringVar:
        row = tk.Frame(parent, bg=self.CARD)
        row.pack(fill="x", pady=3)
        tk.Label(row, text=label, font=("Segoe UI", 10), fg=self.MUTED, bg=self.CARD, width=14, anchor="w").pack(side="left")
        var = tk.StringVar(value=value)
        tk.Entry(
            row,
            textvariable=var,
            font=("Segoe UI", 10),
            bg="#0b1220",
            fg=self.TEXT,
            insertbackground=self.TEXT,
            relief="flat",
            width=10,
        ).pack(side="left", ipady=4)
        return var

    def _bind_hotkeys(self) -> None:
        self.root.bind("<F8>", lambda _e: self.toggle())
        self.root.bind("<Escape>", lambda _e: self.stop())
        self.root.bind("<F9>", lambda _e: self._sample_pixel())
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _log(self, message: str, level: LogLevel = "dim") -> None:
        def write() -> None:
            self.log.configure(state="normal")
            self.log.insert("end", message + "\n", level)
            self.log.tag_configure(level, foreground=self.LOG_COLORS[level])
            self.log.see("end")
            self.log.configure(state="disabled")

        self.root.after(0, write)

    def _set_state(self, state: str) -> None:
        def update() -> None:
            self.state_var.set(state)
            color = self.GREEN if state != "Idle" else self.AMBER
            self.state_label.configure(fg=color)

        self.root.after(0, update)

    def _refresh_stats(self) -> None:
        if self.runner.running:
            self.rows_var.set(f"{self.runner.stats.rows_completed} rows")
            self.scans_var.set(f"{self.runner.stats.scans} scans")
            self.root.after(200, self._refresh_stats)

    def _build_config_from_ui(self) -> MacroConfig:
        from garden_macro.detector import PixelTarget

        config = MacroConfig(
            row_end_pixel=PixelTarget(
                int(self.row_x.get()),
                int(self.row_y.get()),
                (int(self.row_r.get()), int(self.row_g.get()), int(self.row_b.get())),
                self.config.row_end_pixel.tolerance,
            ),
            poll_interval=self.config.poll_interval,
            forward_duration=float(self.forward.get()),
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
            self._log(f"Saved to {path.name}.", "ok")
        except Exception as exc:
            messagebox.showerror("Config error", str(exc))

    def _sample_pixel(self) -> None:
        if pyautogui is None:
            messagebox.showerror("Error", "pyautogui missing.")
            return
        x, y = pyautogui.position()
        rgb = pyautogui.pixel(x, y)
        self.row_x.set(str(x))
        self.row_y.set(str(y))
        self.row_r.set(str(rgb[0]))
        self.row_g.set(str(rgb[1]))
        self.row_b.set(str(rgb[2]))
        self._log(f"Sampled ({x}, {y}) RGB{rgb}", "accent")

    def start(self) -> None:
        if self.runner.running:
            return
        try:
            self.config = self._build_config_from_ui()
            self.runner.start(self.config)
            self._refresh_stats()
            self._log("Running.", "ok")
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
