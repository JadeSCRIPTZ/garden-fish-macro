from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable

try:
    import pyautogui
except ImportError:  # pragma: no cover
    pyautogui = None

from .config import MacroConfig
from .detector import read_match
from .input_controller import InputController


LogFn = Callable[[str, str], None]
StateFn = Callable[[str], None]


class FarmDirection(Enum):
    RIGHT = auto()
    LEFT = auto()


class FarmState(Enum):
    IDLE = "IDLE"
    FARMING_RIGHT = "FARMING_RIGHT"
    FARMING_LEFT = "FARMING_LEFT"
    MOVE_FORWARD = "MOVE_FORWARD"
    FISH_COLLECT = "FISH_COLLECT"


@dataclass
class RunStats:
    rows_completed: int = 0
    fish_collected: int = 0
    scans: int = 0
    started_at: float = 0.0


class GardenMacroRunner:
    def __init__(self, log: LogFn, state: StateFn) -> None:
        self._log = log
        self._state = state
        self._stop = threading.Event()
        self._fish_event = threading.Event()
        self._row_end_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._detector_thread: threading.Thread | None = None
        self.stats = RunStats()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, config: MacroConfig) -> None:
        if pyautogui is None:
            raise RuntimeError("pyautogui is not installed. Run pip install -r requirements.txt.")
        if self.running:
            return
        screen = pyautogui.size()
        config.validate(screen.width, screen.height)
        self._stop.clear()
        self._fish_event.clear()
        self._row_end_event.clear()
        self.stats = RunStats(started_at=time.time())
        self._detector_thread = threading.Thread(
            target=self._detector_loop, args=(config,), daemon=True
        )
        self._thread = threading.Thread(target=self._run_loop, args=(config,), daemon=True)
        self._detector_thread.start()
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._fish_event.set()
        self._row_end_event.set()

    def _sleep(self, seconds: float) -> None:
        end = time.time() + max(0.0, seconds)
        while time.time() < end and not self._stop.is_set():
            time.sleep(min(0.05, end - time.time()))

    def _detector_loop(self, config: MacroConfig) -> None:
        last_fish_trigger = 0.0
        last_row_trigger = 0.0
        try:
            while not self._stop.is_set():
                fish_rgb, fish_match = read_match(pyautogui, config.fish_pixel)
                row_rgb, row_match = read_match(pyautogui, config.row_end_pixel)
                self.stats.scans += 1
                now = time.time()

                if fish_match and now - last_fish_trigger >= config.fish_cooldown:
                    last_fish_trigger = now
                    self._fish_event.set()
                    self._log(
                        f"Fish spawn detected at RGB{fish_rgb}.",
                        "warn",
                    )

                if row_match and now - last_row_trigger >= config.row_end_cooldown:
                    last_row_trigger = now
                    self._row_end_event.set()
                    self._log(
                        f"Row end detected at RGB{row_rgb}.",
                        "accent",
                    )

                self._sleep(config.poll_interval)
        except Exception as exc:
            if not self._stop.is_set():
                self._log(f"Detector error: {exc}", "error")

    def _run_loop(self, config: MacroConfig) -> None:
        input_ctrl = InputController(config.keys, self._sleep)
        direction = FarmDirection.RIGHT
        farm_state = FarmState.FARMING_RIGHT

        self._state(farm_state.value)
        self._log("Garden macro started. Farming right.", "accent")
        input_ctrl.hold_farm_right()

        try:
            while not self._stop.is_set():
                if self._fish_event.is_set():
                    self._fish_event.clear()
                    resume_direction = direction
                    farm_state = FarmState.FISH_COLLECT
                    self._state(farm_state.value)
                    self._log("Running fish collection sequence.", "warn")
                    input_ctrl.fish_collection_sequence(config)
                    self.stats.fish_collected += 1
                    direction = resume_direction
                    if direction == FarmDirection.RIGHT:
                        farm_state = FarmState.FARMING_RIGHT
                        input_ctrl.hold_farm_right()
                    else:
                        farm_state = FarmState.FARMING_LEFT
                        input_ctrl.hold_farm_left()
                    self._state(farm_state.value)
                    self._log(f"Resumed farming {direction.name.lower()}.", "ok")

                if farm_state in (FarmState.FARMING_RIGHT, FarmState.FARMING_LEFT):
                    if self._row_end_event.is_set():
                        self._row_end_event.clear()
                        input_ctrl.release_all()
                        farm_state = FarmState.MOVE_FORWARD
                        self._state(farm_state.value)
                        self._log("Moving forward to next row.", "accent")
                        input_ctrl.tap_forward(config.forward_duration)
                        self.stats.rows_completed += 1

                        if direction == FarmDirection.RIGHT:
                            direction = FarmDirection.LEFT
                            farm_state = FarmState.FARMING_LEFT
                            input_ctrl.hold_farm_left()
                        else:
                            direction = FarmDirection.RIGHT
                            farm_state = FarmState.FARMING_RIGHT
                            input_ctrl.hold_farm_right()
                        self._state(farm_state.value)
                        self._log(f"Farming {direction.name.lower()}.", "ok")

                self._sleep(0.02)
        except pyautogui.FailSafeException:
            self._log("Failsafe triggered. Mouse moved to top-left corner.", "error")
        except Exception as exc:
            self._log(f"Runner error: {exc}", "error")
        finally:
            input_ctrl.release_everything()
            self._state(FarmState.IDLE.value)
            self._log("Garden macro stopped.", "dim")
