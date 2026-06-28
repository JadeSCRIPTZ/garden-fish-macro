from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .detector import PixelTarget


APP_DIR = "GardenFarmMacro"
CONFIG_FILE = "config.json"


def app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def bundled_path(name: str) -> Path | None:
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS", app_dir()))
        candidate = base / name
        if candidate.exists():
            return candidate
    project_root = Path(__file__).resolve().parents[2]
    candidate = project_root / name
    return candidate if candidate.exists() else None


@dataclass
class KeyBindings:
    attack: str = "f"
    right: str = "d"
    left: str = "a"
    forward: str = "w"

    def validate(self) -> None:
        for name, key in asdict(self).items():
            if not key or len(key.strip()) != 1:
                raise ValueError(f"Key binding '{name}' must be a single character.")


@dataclass
class MacroConfig:
    row_end_pixel: PixelTarget = field(
        default_factory=lambda: PixelTarget(10, 10, (255, 140, 0), 25)
    )
    poll_interval: float = 0.05
    forward_duration: float = 0.35
    row_end_cooldown: float = 0.8
    keys: KeyBindings = field(default_factory=KeyBindings)

    def validate(self, screen_width: int | None = None, screen_height: int | None = None) -> None:
        if screen_width is not None and screen_height is not None:
            self.row_end_pixel.validate(screen_width, screen_height)
        if not 0.01 <= self.poll_interval <= 2:
            raise ValueError("Poll interval must be between 0.01 and 2 seconds.")
        for name in ("forward_duration", "row_end_cooldown"):
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
    local = app_dir() / CONFIG_FILE
    if local.exists():
        return local
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / APP_DIR / CONFIG_FILE
    return Path.home() / f".{APP_DIR.lower()}" / CONFIG_FILE


def default_config_path() -> Path:
    return app_dir() / CONFIG_FILE


def load_config(path: Path | None = None) -> MacroConfig:
    target = path or config_path()
    if not target.exists():
        example = bundled_path("config.example.json")
        if example is not None:
            return load_config(example)
        return MacroConfig()
    raw = json.loads(target.read_text(encoding="utf-8"))
    config = MacroConfig(
        row_end_pixel=_pixel_from_dict(raw["row_end_pixel"]),
        poll_interval=float(raw.get("poll_interval", 0.05)),
        forward_duration=float(raw.get("forward_duration", 0.35)),
        row_end_cooldown=float(raw.get("row_end_cooldown", 0.8)),
        keys=KeyBindings(**raw.get("keys", {})),
    )
    config.validate()
    return config


def save_config(config: MacroConfig, path: Path | None = None) -> Path:
    target = path or default_config_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "row_end_pixel": _pixel_to_dict(config.row_end_pixel),
        "poll_interval": config.poll_interval,
        "forward_duration": config.forward_duration,
        "row_end_cooldown": config.row_end_cooldown,
        "keys": asdict(config.keys),
    }
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return target
