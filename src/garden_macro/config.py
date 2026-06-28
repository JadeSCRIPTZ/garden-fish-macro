from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .detector import PixelTarget


APP_DIR = "GardenFishMacro"
CONFIG_FILE = "config.json"


@dataclass
class KeyBindings:
    attack: str = "f"
    right: str = "d"
    left: str = "a"
    forward: str = "w"
    set_home: str = "h"
    tp_plot: str = "g"
    go_home: str = "j"

    def validate(self) -> None:
        for name, key in asdict(self).items():
            if not key or len(key.strip()) != 1:
                raise ValueError(f"Key binding '{name}' must be a single character.")


@dataclass
class MacroConfig:
    fish_pixel: PixelTarget = field(
        default_factory=lambda: PixelTarget(10, 10, (255, 105, 180), 25)
    )
    row_end_pixel: PixelTarget = field(
        default_factory=lambda: PixelTarget(10, 30, (255, 140, 0), 25)
    )
    poll_interval: float = 0.05
    forward_duration: float = 0.35
    tp_delay: float = 0.4
    tp_wait: float = 1.5
    vacuum_duration: float = 3.0
    home_wait: float = 1.5
    fish_cooldown: float = 5.0
    row_end_cooldown: float = 0.8
    keys: KeyBindings = field(default_factory=KeyBindings)

    def validate(self, screen_width: int | None = None, screen_height: int | None = None) -> None:
        if screen_width is not None and screen_height is not None:
            self.fish_pixel.validate(screen_width, screen_height)
            self.row_end_pixel.validate(screen_width, screen_height)
        if not 0.01 <= self.poll_interval <= 2:
            raise ValueError("Poll interval must be between 0.01 and 2 seconds.")
        for name in (
            "forward_duration",
            "tp_delay",
            "tp_wait",
            "vacuum_duration",
            "home_wait",
            "fish_cooldown",
            "row_end_cooldown",
        ):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} cannot be negative.")
        self.keys.validate()


def _pixel_from_dict(data: dict[str, Any]) -> PixelTarget:
    return PixelTarget(
        x=int(data["x"]),
        y=int(data["y"]),
        rgb=(int(data["red"]), int(data["green"]), int(data["blue"])),
        tolerance=int(data.get("tolerance", 20)),
    )


def _pixel_to_dict(target: PixelTarget) -> dict[str, Any]:
    return {
        "x": target.x,
        "y": target.y,
        "red": target.rgb[0],
        "green": target.rgb[1],
        "blue": target.rgb[2],
        "tolerance": target.tolerance,
    }


def config_path() -> Path:
    local = Path.cwd() / CONFIG_FILE
    if local.exists():
        return local
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / APP_DIR / CONFIG_FILE
    return Path.home() / f".{APP_DIR.lower()}" / CONFIG_FILE


def default_config_path() -> Path:
    return Path.cwd() / CONFIG_FILE


def load_config(path: Path | None = None) -> MacroConfig:
    target = path or config_path()
    if not target.exists():
        example = Path(__file__).resolve().parents[2] / "config.example.json"
        if example.exists():
            return load_config(example)
        return MacroConfig()
    raw = json.loads(target.read_text(encoding="utf-8"))
    config = MacroConfig(
        fish_pixel=_pixel_from_dict(raw["fish_pixel"]),
        row_end_pixel=_pixel_from_dict(raw["row_end_pixel"]),
        poll_interval=float(raw.get("poll_interval", 0.05)),
        forward_duration=float(raw.get("forward_duration", 0.35)),
        tp_delay=float(raw.get("tp_delay", 0.4)),
        tp_wait=float(raw.get("tp_wait", 1.5)),
        vacuum_duration=float(raw.get("vacuum_duration", 3.0)),
        home_wait=float(raw.get("home_wait", 1.5)),
        fish_cooldown=float(raw.get("fish_cooldown", 5.0)),
        row_end_cooldown=float(raw.get("row_end_cooldown", 0.8)),
        keys=KeyBindings(**raw.get("keys", {})),
    )
    config.validate()
    return config


def save_config(config: MacroConfig, path: Path | None = None) -> Path:
    target = path or default_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "fish_pixel": _pixel_to_dict(config.fish_pixel),
        "row_end_pixel": _pixel_to_dict(config.row_end_pixel),
        "poll_interval": config.poll_interval,
        "forward_duration": config.forward_duration,
        "tp_delay": config.tp_delay,
        "tp_wait": config.tp_wait,
        "vacuum_duration": config.vacuum_duration,
        "home_wait": config.home_wait,
        "fish_cooldown": config.fish_cooldown,
        "row_end_cooldown": config.row_end_cooldown,
        "keys": asdict(config.keys),
    }
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return target
